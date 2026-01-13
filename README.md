# CC:Tweaked Media Player

**Multimedia toolchain for Minecraft ComputerCraft (CC:Tweaked).**

---

## 📦 Toolchain Overview

### 1. Vidmator (Updated!)
A all-in-one Windows application featuring:
*   **Video Converter:** Convert `.mp4`, `.avi`, etc., into the `.mcanim` format with Floyd-Steinberg dithering.
*   **Audio Visualizer:** Generate mirrored spectrum music videos from any audio file.
*   **Project Editor:** Preview animations, crop dimensions, trim time, and manage DFPWM audio tracks.
*   **FFmpeg Integration:** Ensures 1:1 audio quality for in-game speakers.

### 2. Standalone Animation Editor (Pixel Art Tool)
A Pygame-based tool dedicated to drawing frame-by-frame pixel art animations from scratch.

> 🚧 **ROADMAP UPDATE** 🚧
>
> **Improving the Standalone Animation Editor is the next major target!**
> While fully functional, I plan to overhaul the UI.

### 3. Lua Player (In-Game)
A optimized, multi-threaded Lua player that handles:
*   Binary delta decompression (Zlib/Base64).
*   `term.blit` rendering in 20 FPS playback.
*   Synchronized (as much as possible) DFPWM audio streaming.

---

## 🛠️ PC Installation & Setup

### Prerequisites
1.  **Python 3.10+**: [Download Here](https://www.python.org/downloads/)
2.  **FFmpeg**: [Download Here](https://ffmpeg.org/download.html) (Essential for audio processing)

### Installation
1.  Clone or download this repository.
2.  Open a terminal in the folder and install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Critical:** Extract `ffmpeg.exe` from the FFmpeg download and place it in the **same folder** as `vidmator.py`.

---

## 💻 Usage Guide

### Using Vidmator 2.0
Run the main app:
```bash
python vidmator.py
```

*   **Video Converter:** Select a video, set your monitor size (e.g., 4x3 blocks), set FPS (up to 20), and convert.
*   **Visualizer:** Select a song, choose your color palette, and generate a visualizer.
*   **Editor:** Load a `.mcanim` file to check how it looks, trim the length, or swap the audio track.

### Using the Animation Editor
Run the standalone editor:
```bash
python animation_editor.py
```
1.  Set your canvas size.
2.  **Controls:**
    *   **Left Click:** Draw
    *   **Right Click:** Erase / Color Pick (Hold)
    *   **Middle Click / Drag:** Pan Camera
    *   **Scroll:** Zoom
    *   **`N`**: New Frame
    *   **`D`**: Delete Frame
    *   **`O`**: Toggle Onion Skinning
    *   **Arrows:** Navigate Frames
    *   More information in app
3.  Press **`Ctrl+E`** to export to `.mcanim`.

---

## 🎮 In-Game Installation (Minecraft)

### 1. Requirements
*   **Advanced Monitor** (Size must match your conversion settings).
*   **Speaker** Only if you want to play audio.

### 2. Libraries
The player requires specific compression libraries. Download these onto your turtle/computer:
*   `zlib_decompress.lua`
*   `base64.lua`

### 3. Setup
1.  Copy `player.lua` and `animlib.lua` to your computer.
2.  Ensure `animlib.lua` correctly requires the zlib and base64 libraries at the top of the file.

### 4. Importing Files
1.  Vidmator creates a **folder** containing the `.mcanim` file and several `_chunk` files.
2.  Drag and drop that **entire folder** into your Minecraft computer's directory:
    *   Path: `.minecraft/saves/YOUR_WORLD/computercraft/computer/ID/`
3.  Run `player` in-game and select your animation!

---

## 📂 File Format (.mcanim)
The format is designed for maximum storage efficiency within ComputerCraft's limits:
*   **Header:** JSON metadata (Dimensions, Palette, FPS).
*   **Chunks:** Data is split into smaller files to avoid Lua "Out of Memory" errors.
*   **Compression:** Frames use binary delta encoding (storing only changed pixels) compressed via Zlib and Base64.

---

**Created by [NeuGoga](https://github.com/NeuGoga)**
```