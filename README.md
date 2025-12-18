# CC:Tweaked Animation Library and Toolchain

**An animation library for CC:Tweaked, complete with a video-to-animation converter and a dedicated frame-by-frame animation editor.**

This project provides the tools and the in-game library necessary to display animations and videos on CC:Tweaked monitors.

---

## Features

*   **Advanced Animation Format (`.canim`)**:
    *   Utilizes zlib compression and Base64 encoding for optimized file sizes.
    *   Supports delta-framing, only storing changes between frames to dramatically reduce data overhead.
    *   Includes a full color palette and metadata for scale, dimensions, and FPS.

*   **Video to `.canim` Converter (Tkinter GUI)**:
    *   Converts standard video files (`.mp4`, etc.) into the `.canim` format.
    *   Implements Floyd-Steinberg dithering to beautifully map video colors to the 16-color ComputerCraft palette.
    *   Customizable output dimensions, FPS, and monitor scaling.

*   **Animation Editor (Pygame GUI)**:
    *   A tool for creating and editing animations frame by frame.
    *   Full suite of drawing tools: paint, erase, and color picking.

*   **In-Game Animation Library (Lua)**:
    *   A lightweight Lua library designed to parse and play `.canim` files on CC:Tweaked computers.
    *   Handles decompression and rendering to in-game monitors.

---

## Toolchain Installation

To use the video converter and animation editor, you need Python 3 and the following libraries.

*   **Install Python**: Make sure you have Python 3 installed on your system.
*   **Install Libraries**: Run the following command in your terminal:
    ```bash
    pip install opencv-python numpy Pillow pygame
    ```
    *   **Using the Video Converter**:
    1.  Run the `video_converter.py` script.
    2.  Select your video file.
    3.  Configure the target monitor size (in blocks), scale, and desired FPS.
    4.  Click "Convert". The output file, `animation.canim`, will be saved in the same directory.

*   **Using the Animation Editor**:
    1.  Run the `animation_editor.py` script.
    2.  Set your desired canvas size and scale in the UI.
    3.  Use the controls to draw your animation frame by frame.
        *   **`N`**: Create a new frame.
        *   **`D`**: Delete the current frame.
        *   **Left/Right Arrows**: Navigate between frames.
        *   **`O`**: Toggle onion skinning.
    4.  Press `Ctrl+E` to export your work as `animation.canim`.

