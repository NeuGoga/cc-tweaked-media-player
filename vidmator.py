import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import cv2
import numpy as np
from PIL import Image
import json
import zlib
import base64
import threading
import queue
import os

CC_COLORS_RGB = np.array([
    [240, 240, 240], [242, 178, 51], [229, 127, 216], [153, 178, 242],
    [222, 222, 108], [127, 204, 25], [242, 178, 204], [76, 76, 76],
    [204, 204, 204], [76, 229, 229], [178, 102, 229], [51, 102, 178],
    [127, 102, 76], [102, 127, 51], [216, 76, 76], [25, 25, 25]
])
COLOR_NAMES = [
    "white", "orange", "magenta", "lightBlue", "yellow", "lime", "pink", "gray",
    "lightGray", "cyan", "purple", "blue", "brown", "green", "red", "black"
]
HEX_CHARS = "0123456789abcdef"

class VideoConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CC Video to .canim Converter")
        self.root.geometry("420x550")
        self.root.resizable(False, False)

        self.filepath = tk.StringVar(value="No file selected")
        self.monitor_x = tk.StringVar(value="2")
        self.monitor_y = tk.StringVar(value="1")
        self.scale = tk.StringVar(value="1.0")
        self.fps = tk.StringVar(value="10")
        self.chunk_size = tk.StringVar(value="10")
        self.status = tk.StringVar(value="Ready to convert.")
        self._filepath_full = ""

        self.update_queue = queue.Queue()

        self.setup_ui()

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        file_frame = ttk.Labelframe(main_frame, text="Source Video", padding="10")
        file_frame.pack(fill=tk.X, pady=(0, 15))

        btn_select = ttk.Button(file_frame, text="Select .MP4 File", command=self.select_file)
        btn_select.pack(side=tk.LEFT, padx=(0, 10))
        
        lbl_file = ttk.Label(file_frame, textvariable=self.filepath, foreground="gray")
        lbl_file.pack(side=tk.LEFT, fill=tk.X, expand=True)

        mon_frame = ttk.Labelframe(main_frame, text="Monitor Configuration", padding="10")
        mon_frame.pack(fill=tk.X, pady=(0, 15))

        mon_frame.columnconfigure(1, weight=1)
        
        ttk.Label(mon_frame, text="Width (Blocks):").grid(row=0, column=0, sticky=tk.W, pady=5)
        combo_x = ttk.Combobox(mon_frame, textvariable=self.monitor_x, state="readonly", width=10)
        combo_x['values'] = [str(i) for i in range(1, 9)]
        combo_x.grid(row=0, column=1, sticky=tk.E, pady=5)

        ttk.Label(mon_frame, text="Height (Blocks):").grid(row=1, column=0, sticky=tk.W, pady=5)
        combo_y = ttk.Combobox(mon_frame, textvariable=self.monitor_y, state="readonly", width=10)
        combo_y['values'] = [str(i) for i in range(1, 7)]
        combo_y.grid(row=1, column=1, sticky=tk.E, pady=5)

        ttk.Label(mon_frame, text="Text Scale:").grid(row=2, column=0, sticky=tk.W, pady=5)
        combo_scale = ttk.Combobox(mon_frame, textvariable=self.scale, state="readonly", width=10)
        combo_scale['values'] = ["0.5", "1.0", "1.5"]
        combo_scale.grid(row=2, column=1, sticky=tk.E, pady=5)

        anim_frame = ttk.Labelframe(main_frame, text="Animation Settings", padding="10")
        anim_frame.pack(fill=tk.X, pady=(0, 15))
        
        anim_frame.columnconfigure(1, weight=1)

        ttk.Label(anim_frame, text="Target FPS:").grid(row=0, column=0, sticky=tk.W, pady=5)
        combo_fps = ttk.Combobox(anim_frame, textvariable=self.fps, width=10)
        combo_fps['values'] = ["5", "10", "20"]
        combo_fps.grid(row=0, column=1, sticky=tk.E, pady=5)

        ttk.Label(anim_frame, text="Frames per Chunk:").grid(row=1, column=0, sticky=tk.W, pady=5)
        entry_chunk = ttk.Entry(anim_frame, textvariable=self.chunk_size, width=13)
        entry_chunk.grid(row=1, column=1, sticky=tk.E, pady=5)

        self.convert_button = ttk.Button(main_frame, text="START CONVERSION", command=self.start_conversion)
        self.convert_button.pack(fill=tk.X, pady=(10, 10), ipady=5)

        self.progress = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, mode='determinate')
        self.progress.pack(fill=tk.X, pady=(0, 10))

        self.lbl_status = ttk.Label(main_frame, textvariable=self.status, anchor="center", font=("Arial", 9))
        self.lbl_status.pack(fill=tk.X)

    def select_file(self):
        path = filedialog.askopenfilename(filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")])
        if path:
            filename = os.path.basename(path)
            if len(filename) > 30: filename = filename[:27] + "..."
            self.filepath.set(filename)
            self._filepath_full = path

    def start_conversion(self):
        if not self._filepath_full:
            messagebox.showwarning("Warning", "Please select a video file first.")
            return
            
        self.convert_button.config(state="disabled")
        self.status.set("Initializing...")
        self.progress['value'] = 0

        self.conversion_thread = threading.Thread(target=self.convert_video, daemon=True)
        self.conversion_thread.start()
        
        self.root.after(100, self.check_queue)

    def check_queue(self):
        try:
            while True:
                message_type, value = self.update_queue.get_nowait()
                if message_type == "progress":
                    self.progress['value'] = value
                elif message_type == "status":
                    self.status.set(value)
        except queue.Empty:
            pass

        if self.conversion_thread.is_alive():
            self.root.after(100, self.check_queue)
        else:
            self.convert_button.config(state="normal")

    def convert_video(self):
        try:
            vid_path = self._filepath_full
            mon_x, mon_y = int(self.monitor_x.get()), int(self.monitor_y.get())
            scale, fps = float(self.scale.get()), int(self.fps.get())
            chunk_size = max(1, int(self.chunk_size.get()))

            cc_width = round((64 * mon_x - 20) / (6 * scale))
            cc_height = round((64 * mon_y - 20) / (9 * scale))
            self.update_queue.put(("status", f"Grid: {cc_width}x{cc_height} chars | FPS: {fps}"))

            cap = cv2.VideoCapture(vid_path)
            source_fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_skip = source_fps / fps if fps > 0 else source_fps

            processed_frames = []
            frame_count = 0
            
            while True:
                pos_frames = int(frame_count * frame_skip)
                if pos_frames >= total_frames: break
                
                cap.set(cv2.CAP_PROP_POS_FRAMES, pos_frames)
                ret, frame = cap.read()
                if not ret: break

                if frame_count % 5 == 0:
                    self.update_queue.put(("status", f"Processing frame {len(processed_frames)+1}..."))
                    self.update_queue.put(("progress", (frame_count / (total_frames / frame_skip)) * 100))

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(frame_rgb)
                resized_img = pil_img.resize((cc_width, cc_height), Image.Resampling.LANCZOS)
                
                dither_array = np.array(resized_img, dtype=float)
                output_indices = np.zeros((cc_height, cc_width), dtype=int)

                for y in range(cc_height):
                    for x in range(cc_width):
                        old_pixel = dither_array[y, x]
                        
                        distances = np.sqrt(np.sum((old_pixel - CC_COLORS_RGB)**2, axis=1))
                        closest_index = np.argmin(distances)
                        new_pixel = CC_COLORS_RGB[closest_index]
                        
                        output_indices[y, x] = closest_index
                        
                        quant_error = old_pixel - new_pixel
                        
                        if x + 1 < cc_width:
                            dither_array[y, x + 1] += quant_error * 7 / 16
                        if y + 1 < cc_height:
                            if x - 1 >= 0:
                                dither_array[y + 1, x - 1] += quant_error * 3 / 16
                            dither_array[y + 1, x] += quant_error * 5 / 16
                            if x + 1 < cc_width:
                                dither_array[y + 1, x + 1] += quant_error * 1 / 16

                cc_frame_indices = output_indices.flatten()
                cc_frame = [COLOR_NAMES[i] for i in cc_frame_indices]
                
                processed_frames.append([cc_frame[i:i+cc_width] for i in range(0, len(cc_frame), cc_width)])
                frame_count += 1
            
            cap.release()

            self.update_queue.put(("status", "Exporting to .canim format..."))
            self.export_animation(processed_frames, cc_width, cc_height, fps, scale, chunk_size)
            
        except Exception as e:
            self.update_queue.put(("status", f"Error: {e}"))
            print(e)
        finally:
            self.update_queue.put(("progress", 100))
            self.convert_button.config(state="normal")

    def export_animation(self, animation, width, height, fps, scale, chunk_size):
        CHUNK_SIZE = chunk_size 
        base_filename = "animation"
        output_folder = base_filename

        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        self.update_queue.put(("status", "Generating chunks..."))
        
        palette_map = {HEX_CHARS[i]: name for i, name in enumerate(COLOR_NAMES)}
        color_to_hex = {name: HEX_CHARS[i] for i, name in enumerate(COLOR_NAMES)}
        
        chunk_filenames = []
        
        for chunk_index, i in enumerate(range(0, len(animation), CHUNK_SIZE)):
            chunk_data = animation[i : i + CHUNK_SIZE]
            chunk_output_filename = f"{base_filename}_{chunk_index}.canim"
            chunk_filenames.append(chunk_output_filename)
            
            chunk_frames = []
            
            keyframe_bgs = "".join([color_to_hex[chunk_data[0][y][x]] for y in range(height) for x in range(width)])
            chunk_frames.append({"type": "full", "bgs": keyframe_bgs})

            for frame_idx in range(1, len(chunk_data)):
                prev_frame, curr_frame = chunk_data[frame_idx-1], chunk_data[frame_idx]
                changes = []
                for y in range(height):
                    for x in range(width):
                        if prev_frame[y][x] != curr_frame[y][x]:
                            changes.append({"x": x + 1, "y": y + 1, "bg": color_to_hex[curr_frame[y][x]]})
                
                chunk_frames.append({"type": "delta", "changes": changes})

            chunk_json_string = json.dumps({"frames": chunk_frames}, separators=(',', ':'))
            compressed_data = zlib.compress(chunk_json_string.encode('utf-8'))
            base64_string = base64.b64encode(compressed_data).decode('ascii')
            
            with open(os.path.join(output_folder, chunk_output_filename), "w") as f:
                f.write(base64_string)

        master_output = {
            "header": { "width": width, "height": height, "fps": fps, "scale": scale, "palette": palette_map },
            "chunks": chunk_filenames
        }
        
        with open(os.path.join(output_folder, f"{base_filename}.mcanim"), "w") as f:
            json.dump(master_output, f, indent=2)
            
        self.update_queue.put(("status", f"Done! Check folder '{output_folder}'"))

if __name__ == "__main__":
    root = tk.Tk()
    try:
        style = ttk.Style()
        style.theme_use('clam') 
    except: pass
    
    app = VideoConverterApp(root)
    root.mainloop()