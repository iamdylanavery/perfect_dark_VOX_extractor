import os
import struct
import subprocess
import shutil

DAT_FILE = "XMASpeech.dat"
MAPPING_FILE = "vox_mapping.txt"

TEMP_DIR = "temp_xma"
BASE_WAVS_DIR = "xbla_base_wavs"
OUT_VOX_DIR = "ext_vox"

def find_vgmstream():
    # 1. First, check if the executable is placed directly in the script folder.
    # We check common names for Unix (Mac/Linux) and Windows.
    local_names = ["vgmstream-cli", "vgmstream", "vgmstream-cli.exe", "vgmstream.exe"]
    for name in local_names:
        local_path = os.path.abspath(name)
        if os.path.exists(local_path):
            return local_path

    # 2. Check if it is installed globally in the system PATH.
    for cmd in ["vgmstream-cli", "vgmstream"]:
        if shutil.which(cmd):
            return cmd

    # 3. Fallback for common macOS global directories.
    common_mac_paths = [
        "/opt/homebrew/bin/vgmstream-cli",
        "/opt/homebrew/bin/vgmstream",
        "/usr/local/bin/vgmstream-cli",
        "/usr/local/bin/vgmstream"
    ]
    for path in common_mac_paths:
        if os.path.exists(path):
            return path
            
    return None

def main():
    if not os.path.exists(DAT_FILE):
        print(f"ERROR: Cannot find {DAT_FILE}")
        return
    if not os.path.exists(MAPPING_FILE):
        print(f"ERROR: Cannot find {MAPPING_FILE}.")
        return

    vgmstream_path = find_vgmstream()
    if not vgmstream_path:
        print("ERROR: Could not find 'vgmstream-cli' or 'vgmstream' on your system.")
        print("Please ensure vgmstream is installed globally or placed directly in this folder.")
        return

    os.makedirs(TEMP_DIR, exist_ok=True)
    os.makedirs(BASE_WAVS_DIR, exist_ok=True)
    os.makedirs(OUT_VOX_DIR, exist_ok=True)

    with open(DAT_FILE, "rb") as f:
        data = f.read()

    # 1. Parse 4J's proprietary Table of Contents
    file_count = struct.unpack_from(">I", data, 0)[0]
    print(f"Found proprietary 4J Table of Contents! {file_count} unique voice streams detected.")

    toc_entries = []
    for i in range(file_count):
        # 8 bytes per entry: (PCM_Size, Offset)
        pcm_size, offset = struct.unpack_from(">II", data, 4 + (i * 8))
        toc_entries.append({"id": i, "pcm_size": pcm_size, "offset": offset})

    # 2. Carve Streams, Compile RIFF Headers, and Decode
    print("Carving, compiling, and decoding XMA2 streams via vgmstream...")
    for i in range(file_count):
        entry = toc_entries[i]
        
        if i < file_count - 1:
            chunk_len = toc_entries[i+1]["offset"] - entry["offset"]
        else:
            chunk_len = len(data) - entry["offset"]

        raw_xma = data[entry["offset"] : entry["offset"] + chunk_len]
        
        # Squeeze the 52-byte XMA2 header and the audio payload
        xma2_header = raw_xma[:52]
        payload = raw_xma[52:]
        payload_size = len(payload)

        # COMPILE GENUINE MICROSOFT RIFF/XMA2 HEADER
        riff_header = struct.pack('<4sI4s4sI', 
            b'RIFF',
            20 + len(raw_xma), # RIFF chunk size
            b'WAVE',
            b'fmt ',
            52 # fmt chunk size
        )
        
        data_header = struct.pack('<4sI',
            b'data',
            payload_size # data chunk size
        )

        xma_path = os.path.join(TEMP_DIR, f"{entry['id']}.wav") # Use .wav so vgmstream triggers the RIFF parser
        wav_path = os.path.join(BASE_WAVS_DIR, f"{entry['id']}.wav")

        with open(xma_path, "wb") as f_xma:
            f_xma.write(riff_header)
            f_xma.write(xma2_header)
            f_xma.write(data_header)
            f_xma.write(payload)

        # Decode standard Microsoft RIFF container
        subprocess.run([vgmstream_path, "-o", wav_path, xma_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # 3. Apply N64 Mappings
    print(f"\nApplying N64 mappings from {MAPPING_FILE}...")
    success_count = 0
    
    with open(MAPPING_FILE, "r") as f:
        lines = f.readlines()

    for line in lines[1:]: # Skip header
        parts = line.strip().split(',')
        if len(parts) == 2:
            xma_id = int(parts[0])
            n64_name = parts[1]

            if n64_name.endswith('M') or n64_name.endswith('m'):
                source_wav = os.path.join(BASE_WAVS_DIR, f"{xma_id}.wav")
                dest_wav = os.path.join(OUT_VOX_DIR, f"{n64_name}.wav")
                
                if os.path.exists(source_wav):
                    shutil.copy2(source_wav, dest_wav)
                    success_count += 1

    # Clean up temporary folders
    print("Cleaning up temporary workspace files...")
    shutil.rmtree(TEMP_DIR)
    shutil.rmtree(BASE_WAVS_DIR)

    print(f"\nExtracted and mapped {success_count} Perfect voice lines to '{OUT_VOX_DIR}/'.")

if __name__ == "__main__":
    main()
