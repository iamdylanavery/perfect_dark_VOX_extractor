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

To run this tool, you must place the following files in the same directory:
* `XMASpeech.dat` (Extracted from the XBLA STFS container)
* `vox_mapping.txt` (Generated via the PC Port's `romdata.c` initialization routine)

You must also have **vgmstream** installed on your system:
* **macOS:** `brew install vgmstream`

## Usage

Run the automated extractor:
```bash
python3 pd_vox_extractor.py
