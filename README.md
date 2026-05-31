# Perfect Dark XBLA Dialogue (VOX) Extractor & Mapper

A highly automated Python toolchain designed to extract, reconstruct, decode, and map the high-quality dialogue (VOX) assets from the Xbox Live Arcade (XBLA) remaster of *Perfect Dark* (2010) to match the open-source PC port's file naming system.

This script parses the proprietary, headerless XBLA voice package, reconstructs standard Microsoft audio containers, decodes the proprietary XMA2 audio codec, and renames the resulting WAV files to match their original N64 equivalents (e.g. `Aa51elv01M.wav`).

## How It Works (The Technical Perspective)

The original N64 release of *Perfect Dark* relied on heavily compressed, low-bitrate software MP3 decoding for its voice acting. For the 2010 XBLA remaster, 4J Studios upgraded these voice lines to pristine, high-fidelity **MPEG-4 Xbox Media Audio (XMA2)**.

Rather than packing these voice lines into standard Microsoft containers (like an XACT Wave Bank), 4J Studios compiled them into a single, proprietary archive: `XMASpeech.dat`.

### The Custom 4J Container
The `XMASpeech.dat` file has no global headers and is completely unparseable by standard media tools out of the box. 

1. **The Table of Contents:** The file begins with a 4-byte Big-Endian integer declaring the total unique voice streams (exactly `548`). Following this is a tightly packed table of 8-byte entries mapping `(Decoded_PCM_Size, Byte_Offset)`.
2. **The Audio Chunks:** The actual audio payloads begin immediately after the TOC. Interestingly, each individual chunk begins with a 52-byte standard Microsoft `XMA2WAVEFORMAT` header, followed by raw, headerless XMA2 frame packets. 

### The Reconstruction Process
Because the audio data is raw, standard decoders cannot read it. This Python script programmatically "heals" the files:
1. It parses the custom TOC in `XMASpeech.dat` to find the exact offset and length of each voice stream.
2. For each chunk, it carves out the bytes and splits the 52-byte XMA2 header from the audio payload.
3. It dynamically compiles a genuine **Microsoft RIFF / WAVE container** around them, writing a new little-endian `RIFF` header, a `fmt ` chunk holding the 52-byte XMA2 header, and a `data` chunk holding the raw payload.
4. It invokes `vgmstream-cli` to decode this freshly compiled, valid XMA2 file into an uncompressed, standard 16-bit PCM `.wav` file.
5. It parses `vox_mapping.txt` (which links the XBLA sequential IDs to their N64 filename equivalents), filters out non-voice data (such as background segments mapped to `0`), and renames the decoded WAV files perfectly.

## Requirements

To run this tool, place the following files together in the exact same folder:
* `XMASpeech.dat` (Extracted from the XBLA STFS container)
* `vox_mapping.txt` (Generated via the PC Port's `romdata.c` initialization routine)

You must also have the **vgmstream** command-line tool installed or placed in this folder so the script can decode the Xbox 360 audio. Follow the instructions below for your operating system:

### 🖥️ Windows (Easiest Method)
1. Go to [vgmstream.org](https://vgmstream.org).
2. Click and download **Command-line (64-bit) Win**.
3. Open the downloaded `.zip` folder.
4. Drag and drop **every single file** inside that zip (including `vgmstream-cli.exe` and all the accompanying `.dll` files) directly into the folder where your Python script is located.

### 🍎 macOS
**Method A (If you use Homebrew):**
1. Open your Terminal.
2. Paste this command and press Enter:
   ```bash
   brew install vgmstream

**Method B (Manual Download):**

1.  Go to vgmstream.org.
2.  Click and download Command-line (static build) Mac.
3.  Move the downloaded file into your script folder and rename it exactly to:
    vgmstream-cli
4.  Open your Terminal, navigate to your script folder, and run this command to
    allow your system to run it:
    chmod +x vgmstream-cli

### 🐧 Linux

1.  Go to vgmstream.org.
2.  Click and download Command-line (static build) Linux.
3.  Move the downloaded file into your script folder and rename it exactly to:
    vgmstream-cli
4.  Open your Terminal, navigate to your script folder, and make the tool
    executable by running:
    chmod +x vgmstream-cli

## Usage

Once your files and vgmstream are placed in the folder, run the automated
extractor from your terminal:

python3 pd_vox_extractor_final.py
