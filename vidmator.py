import tkinter as tk
from tkinter import filedialog, ttk, messagebox, simpledialog
import cv2
import numpy as np
from PIL import Image, ImageTk
import ctypes
from ctypes import windll
import json
import zlib
import base64
import threading
import queue
import os
import wave
import math
import subprocess
import shutil
import sys
import time
import traceback
import tempfile
import winsound

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

BG_DARK = "#202020"
BG_HEADER = "#2d2d2d"
BG_PANEL = "#2b2b2b"
ACCENT = "#4e9a06"
TEXT_MAIN = "#ffffff"
TEXT_DIM = "#aaaaaa"

def get_ffmpeg_path():
    if getattr(sys, 'frozen', False):
        script_dir = os.path.dirname(sys.executable)
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    local_ffmpeg = os.path.join(script_dir, "ffmpeg.exe")
    if os.path.exists(local_ffmpeg): return local_ffmpeg
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg: return system_ffmpeg
    return None

def export_mcanim(animation, width, height, fps, scale, chunk_size, folder, name, has_audio):
    rev_pal = {n: HEX_CHARS[i] for i, n in enumerate(COLOR_NAMES)}
    chunks = []
    palette_map = {HEX_CHARS[i]: n for i, n in enumerate(COLOR_NAMES)}
    
    for i in range(0, len(animation), chunk_size):
        chunk_data = animation[i:i+chunk_size]
        chunk_frames = []
        
        full_str = "".join([rev_pal[c] for c in chunk_data[0]])
        chunk_frames.append({"type": "full", "bgs": full_str})
        
        for f in range(1, len(chunk_data)):
            prev = chunk_data[f-1]
            curr = chunk_data[f]
            
            changes_bin = []
            
            for px in range(len(curr)):
                if prev[px] != curr[px]:
                    x = (px % width) + 1
                    y = (px // width) + 1
                    c = rev_pal[curr[px]]

                    changes_bin.append(chr(x) + chr(y) + c)
            
            chunk_frames.append({"type": "bin_delta", "data": "".join(changes_bin)})

        json_str = json.dumps({"frames": chunk_frames}, separators=(',', ':'))
        compressed = zlib.compress(json_str.encode())
        b64_str = base64.b64encode(compressed).decode()
        
        c_name = f"{name}_{len(chunks)}.canim"
        with open(os.path.join(folder, c_name), "w") as f: f.write(b64_str)
        chunks.append(c_name)

    master = {
        "header": {"width": width, "height": height, "fps": fps, "scale": scale, "palette": palette_map},
        "chunks": chunks,
        "audio": "audio.dfpwm" if has_audio else None
    }
    with open(os.path.join(folder, f"{name}.mcanim"), "w") as f:
        json.dump(master, f, indent=2)

def process_audio_track(filepath, output_folder):
    ffmpeg_exe = get_ffmpeg_path()
    if not ffmpeg_exe:
        messagebox.showerror("Error", "FFmpeg not found!\nPlease place ffmpeg.exe in this folder.")
        return False, None
    temp_wav = os.path.join(output_folder, "temp_vis.wav")
    output_dfpwm = os.path.join(output_folder, "audio.dfpwm")
    try:
        subprocess.run([ffmpeg_exe, "-y", "-v", "error", "-i", filepath, "-ac", "1", "-ar", "48000", temp_wav], check=True)
        with wave.open(temp_wav, 'rb') as wf:
            frames = wf.readframes(wf.getnframes())
            audio_int16 = np.frombuffer(frames, dtype=np.int16)
            audio_float = audio_int16.astype(np.float32) / 32768.0
        subprocess.run([ffmpeg_exe, "-y", "-v", "error", "-i", temp_wav, "-c:a", "dfpwm", output_dfpwm], check=True)
        if os.path.exists(temp_wav): os.remove(temp_wav)
        return True, audio_float
    except Exception as e:
        print(f"Error: {e}")
        return False, None

def setup_theme(root):
    style = ttk.Style()
    style.theme_use('clam')
    
    style.configure("TFrame", background=BG_DARK)
    style.configure("TLabelframe", background=BG_PANEL, foreground=ACCENT, bordercolor="#444", borderwidth=1)
    style.configure("TLabelframe.Label", background=BG_PANEL, foreground=ACCENT, font=("Segoe UI", 10, "bold"))
    style.configure("TLabel", background=BG_DARK, foreground=TEXT_MAIN, font=("Segoe UI", 9))
    style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"), foreground=ACCENT, background=BG_DARK)
    
    style.configure("TButton", background="#3a3a3a", foreground="white", borderwidth=0, font=("Segoe UI", 9))
    style.map("TButton", background=[('active', ACCENT), ('disabled', '#333')], foreground=[('disabled', '#555')])
    
    style.configure("TEntry", fieldbackground="#333", foreground="white", insertcolor="white", bordercolor="#444")
    style.configure("TCombobox", fieldbackground="#333", foreground="white", arrowcolor="white", bordercolor="#444")
    style.map("TCombobox", fieldbackground=[('readonly', '#333')], selectbackground=[('readonly', '#333')], selectforeground=[('readonly', 'white')])

    style.configure("TNotebook", background=BG_DARK, borderwidth=0)
    style.configure("TNotebook.Tab", background="#333", foreground="#aaa", padding=[15, 8], font=("Segoe UI", 9))
    style.map("TNotebook.Tab", background=[("selected", BG_PANEL)], foreground=[("selected", ACCENT)])
    
    style.configure("Horizontal.TProgressbar", background=ACCENT, troughcolor="#333", bordercolor=BG_DARK)
    
    style.configure("Panel.TFrame", background=BG_PANEL)
    
    root.configure(bg=BG_DARK)

class CustomTitleBar(tk.Frame):
    def __init__(self, parent, title_text, close_cmd, min_cmd):
        super().__init__(parent, height=35, bg=BG_HEADER)
        self.parent = parent
        self.pack(fill=tk.X, side=tk.TOP)
        self.pack_propagate(False)
        
        self.bind("<Button-1>", self.start_move)
        self.bind("<B1-Motion>", self.do_move)
        
        lbl = tk.Label(self, text=title_text, bg=BG_HEADER, fg="white", font=("Segoe UI", 10))
        lbl.pack(side=tk.LEFT, padx=15)
        lbl.bind("<Button-1>", self.start_move)
        lbl.bind("<B1-Motion>", self.do_move)
        
        btn_close = tk.Button(self, text="✕", bg=BG_HEADER, fg="white", bd=0, 
                              activebackground="red", activeforeground="white", command=close_cmd, width=4)
        btn_close.pack(side=tk.RIGHT, fill=tk.Y)
        
        btn_min = tk.Button(self, text="─", bg=BG_HEADER, fg="white", bd=0, 
                            activebackground="#444", activeforeground="white", command=min_cmd, width=4)
        btn_min.pack(side=tk.RIGHT, fill=tk.Y)
        
        tk.Frame(self.parent, height=1, bg=ACCENT).pack(fill=tk.X, side=tk.TOP)

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.parent.winfo_x() + deltax
        y = self.parent.winfo_y() + deltay
        self.parent.geometry(f"+{x}+{y}")

class VideoConvertTab(ttk.Frame):
    def __init__(self, parent, status_queue):
        super().__init__(parent)
        self.queue = status_queue
        self.filepath = tk.StringVar(value="No file selected")
        self.monitor_x = tk.StringVar(value="2")
        self.monitor_y = tk.StringVar(value="1")
        self.scale = tk.StringVar(value="1.0")
        self.fps = tk.StringVar(value="10")
        self.chunk_size = tk.StringVar(value="10")
        self.process_audio = tk.BooleanVar(value=True)
        self._full_path = ""
        self.setup_ui()

    def setup_ui(self):
        ttk.Label(self, text="VIDEO CONVERTER", style="Header.TLabel").pack(pady=(20,10))
        fr_file = ttk.Labelframe(self, text="Input Source", padding=15)
        fr_file.pack(fill=tk.X, padx=20, pady=5)
        ttk.Button(fr_file, text="Browse Video", command=self.select_file, width=15).pack(side=tk.LEFT)
        ttk.Label(fr_file, textvariable=self.filepath, background=BG_PANEL).pack(side=tk.LEFT, padx=10)

        fr_conf = ttk.Labelframe(self, text="Output Settings", padding=15)
        fr_conf.pack(fill=tk.X, padx=20, pady=10)
        grid_opts = {'padx': 5, 'pady': 8, 'sticky': 'w'}
        
        ttk.Label(fr_conf, text="Width (Blocks):", background=BG_PANEL).grid(row=0, column=0, **grid_opts)
        ttk.Combobox(fr_conf, textvariable=self.monitor_x, values=[str(i) for i in range(1,9)], width=5).grid(row=0, column=1, **grid_opts)
        ttk.Label(fr_conf, text="Height (Blocks):", background=BG_PANEL).grid(row=0, column=2, **grid_opts)
        ttk.Combobox(fr_conf, textvariable=self.monitor_y, values=[str(i) for i in range(1,7)], width=5).grid(row=0, column=3, **grid_opts)
        ttk.Label(fr_conf, text="Scale:", background=BG_PANEL).grid(row=1, column=0, **grid_opts)
        ttk.Combobox(fr_conf, textvariable=self.scale, values=["0.5", "1.0", "1.5"], width=5).grid(row=1, column=1, **grid_opts)
        ttk.Label(fr_conf, text="FPS:", background=BG_PANEL).grid(row=1, column=2, **grid_opts)
        ttk.Combobox(fr_conf, textvariable=self.fps, values=["5", "10", "20"], width=5).grid(row=1, column=3, **grid_opts)
        ttk.Label(fr_conf, text="Frames/Chunk:", background=BG_PANEL).grid(row=2, column=0, **grid_opts)
        ttk.Entry(fr_conf, textvariable=self.chunk_size, width=7).grid(row=2, column=1, **grid_opts)
        
        cb = ttk.Checkbutton(fr_conf, text="Export Audio (DFPWM)", variable=self.process_audio, style="TCheckbutton")
        cb.grid(row=3, column=0, columnspan=4, pady=10, sticky="w")
        
        self.btn_run = ttk.Button(self, text="START CONVERSION", command=self.run)
        self.btn_run.pack(fill=tk.X, padx=20, pady=20, ipady=5)

    def select_file(self):
        p = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.avi *.mkv *.mov")])
        if p:
            self._full_path = p
            self.filepath.set(os.path.basename(p))

    def run(self):
        if not self._full_path: return messagebox.showwarning("Error", "Select a file")
        self.btn_run.config(state="disabled")
        threading.Thread(target=self.process, daemon=True).start()

    def process(self):
        try:
            self.queue.put(("status", "Initializing..."))
            vid_path = self._full_path
            base_name = "anim_" + os.path.splitext(os.path.basename(vid_path))[0]
            out_folder = base_name.replace(" ", "_")
            if not os.path.exists(out_folder): os.makedirs(out_folder)
            
            audio_ok = False
            if self.process_audio.get():
                self.queue.put(("status", "Processing Audio..."))
                audio_ok, _ = process_audio_track(vid_path, out_folder)

            mon_x, mon_y = int(self.monitor_x.get()), int(self.monitor_y.get())
            scale = float(self.scale.get())
            fps = int(self.fps.get())
            cc_w, cc_h = round((64*mon_x-20)/(6*scale)), round((64*mon_y-20)/(9*scale))
            
            cap = cv2.VideoCapture(vid_path)
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            src_fps = cap.get(cv2.CAP_PROP_FPS)
            if src_fps <= 0: src_fps = 30
            
            step = src_fps / fps if fps > 0 else 1.0
            
            processed = []
            current_src_frame = 0
            target_src_frame = 0.0
            
            while True:
                while current_src_frame < int(target_src_frame):
                    if not cap.grab():
                        break
                    current_src_frame += 1
                
                if current_src_frame < int(target_src_frame): break

                ret, frame = cap.read()
                current_src_frame += 1
                
                if not ret: break
                
                if len(processed) % 10 == 0: 
                    self.queue.put(("progress", (current_src_frame/total)*100))

                target_src_frame += step
                
                pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).resize((cc_w, cc_h), Image.Resampling.LANCZOS)
                arr = np.array(pil, dtype=float)
                indices = np.zeros((cc_h, cc_w), dtype=int)
                
                for y in range(cc_h):
                    for x in range(cc_w):
                        old = arr[y,x]
                        diff = CC_COLORS_RGB - old
                        idx = np.argmin(np.einsum('ij,ij->i', diff, diff))
                        indices[y,x] = idx
                        quant = old - CC_COLORS_RGB[idx]
                        if x+1<cc_w: arr[y,x+1] += quant * 0.4375
                        if y+1<cc_h:
                            if x>0: arr[y+1,x-1] += quant * 0.1875
                            arr[y+1,x] += quant * 0.3125
                            if x+1<cc_w: arr[y+1,x+1] += quant * 0.0625
                processed.append([COLOR_NAMES[i] for i in indices.flatten()])
            
            cap.release()
            self.queue.put(("status", "Saving..."))
            export_mcanim(processed, cc_w, cc_h, fps, scale, int(self.chunk_size.get()), out_folder, base_name, audio_ok)
            self.queue.put(("status", "Done!"))
            self.queue.put(("done", True))
        except Exception as e:
            self.queue.put(("status", f"Error: {e}"))
            self.queue.put(("done", True))

class AudioVisTab(ttk.Frame):
    def __init__(self, parent, status_queue):
        super().__init__(parent)
        self.queue = status_queue
        self.filepath = tk.StringVar(value="No file selected")
        self.monitor_x = tk.StringVar(value="2")
        self.monitor_y = tk.StringVar(value="1")
        self.fps = tk.StringVar(value="20")
        self.bg_color = tk.StringVar(value="black")
        self.bar_color = tk.StringVar(value="cyan") 
        self._full_path = ""
        self.setup_ui()

    def setup_ui(self):
        ttk.Label(self, text="AUDIO VISUALIZER", style="Header.TLabel").pack(pady=(20,10))
        fr_file = ttk.Labelframe(self, text="Input Source", padding=15)
        fr_file.pack(fill=tk.X, padx=20, pady=5)
        ttk.Button(fr_file, text="Browse Audio", command=self.select_file, width=15).pack(side=tk.LEFT)
        ttk.Label(fr_file, textvariable=self.filepath, background=BG_PANEL).pack(side=tk.LEFT, padx=10)

        fr_conf = ttk.Labelframe(self, text="Settings", padding=15)
        fr_conf.pack(fill=tk.X, padx=20, pady=10)
        grid_opts = {'padx': 5, 'pady': 8, 'sticky': 'w'}
        
        ttk.Label(fr_conf, text="Width:", background=BG_PANEL).grid(row=0, column=0, **grid_opts)
        ttk.Combobox(fr_conf, textvariable=self.monitor_x, values=[str(i) for i in range(1,9)], width=5).grid(row=0, column=1, **grid_opts)
        ttk.Label(fr_conf, text="Height:", background=BG_PANEL).grid(row=0, column=2, **grid_opts)
        ttk.Combobox(fr_conf, textvariable=self.monitor_y, values=[str(i) for i in range(1,7)], width=5).grid(row=0, column=3, **grid_opts)
        ttk.Label(fr_conf, text="FPS:", background=BG_PANEL).grid(row=1, column=0, **grid_opts)
        ttk.Combobox(fr_conf, textvariable=self.fps, values=["10", "20", "30"], width=5).grid(row=1, column=1, **grid_opts)
        ttk.Label(fr_conf, text="Background:", background=BG_PANEL).grid(row=1, column=2, **grid_opts)
        ttk.Combobox(fr_conf, textvariable=self.bg_color, values=COLOR_NAMES, width=8).grid(row=1, column=3, **grid_opts)
        
        ttk.Label(fr_conf, text="Bar Color:", background=BG_PANEL).grid(row=2, column=0, **grid_opts)
        ttk.Combobox(fr_conf, textvariable=self.bar_color, values=COLOR_NAMES, width=8).grid(row=2, column=1, **grid_opts)

        self.btn_run = ttk.Button(self, text="GENERATE VISUALIZER", command=self.run)
        self.btn_run.pack(fill=tk.X, padx=20, pady=20, ipady=5)
        ttk.Label(self, text="* Mirrored Spectrum Style *", foreground="gray", background=BG_DARK).pack()

    def select_file(self):
        p = filedialog.askopenfilename(filetypes=[("Media", "*.mp3 *.wav *.mp4 *.avi *.flac")])
        if p:
            self._full_path = p
            self.filepath.set(os.path.basename(p))

    def run(self):
        if not self._full_path: return messagebox.showwarning("Error", "Select a file")
        self.btn_run.config(state="disabled")
        threading.Thread(target=self.process, daemon=True).start()

    def process(self):
        try:
            self.queue.put(("status", "Processing Audio..."))
            vid_path = self._full_path
            base_name = "vis_" + os.path.splitext(os.path.basename(vid_path))[0]
            out_folder = base_name.replace(" ", "_")
            if not os.path.exists(out_folder): os.makedirs(out_folder)

            audio_ok, audio_data = process_audio_track(vid_path, out_folder)
            if not audio_ok or audio_data is None: raise Exception("Audio failed")

            self.queue.put(("status", "Generating Visuals..."))
            mon_x, mon_y = int(self.monitor_x.get()), int(self.monitor_y.get())
            fps = int(self.fps.get())
            cc_w, cc_h = round((64*mon_x-20)/6), round((64*mon_y-20)/9)
            
            bg_col = self.bg_color.get()
            bar_col = self.bar_color.get()

            sample_rate, samples_per_frame = 48000, int(48000 / fps)
            total_frames = math.ceil(len(audio_data) / samples_per_frame)
            frames = []
            
            num_bars = max(1, cc_w // 2)
            log_freqs = np.logspace(np.log10(20), np.log10(12000), num_bars + 1)
            bin_indices = np.floor(log_freqs * samples_per_frame / sample_rate).astype(int)
            previous_heights = np.zeros(num_bars)
            
            for i in range(total_frames):
                if i % 50 == 0: self.queue.put(("progress", (i/total_frames)*100))
                start = i * samples_per_frame
                end = min(start + samples_per_frame, len(audio_data))
                chunk = audio_data[start:end]
                if len(chunk) < samples_per_frame: chunk = np.pad(chunk, (0, samples_per_frame - len(chunk)))

                fft_res = np.abs(np.fft.rfft(chunk * np.hanning(len(chunk))))
                band_energies = []
                for b in range(num_bars):
                    b_start, b_end = bin_indices[b], bin_indices[b+1]
                    if b_end <= b_start: b_end = b_start + 1
                    mag = np.mean(fft_res[b_start:min(b_end, len(fft_res))])
                    band_energies.append(mag)
                
                db_energies = 20 * np.log10(np.array(band_energies) + 1e-6)
                norm_heights = np.clip((db_energies - -60) / (45 - -60), 0, 1)
                previous_heights = np.maximum(norm_heights, previous_heights - 0.2)
                
                grid = np.full((cc_h, cc_w), bg_col, dtype=object)
                center_y = cc_h / 2.0
                
                for b_idx in range(num_bars):
                    h_val = previous_heights[b_idx]
                    total_bar_h = h_val * cc_h
                    half_h = total_bar_h / 2.0
                    y_start, y_end = center_y - half_h, center_y + half_h
                    
                    x_pos = b_idx * 2 
                    
                    if x_pos < cc_w:
                        for y in range(cc_h):
                            if y >= y_start and y <= y_end:
                                grid[y][x_pos] = bar_col
                            
                frames.append(grid.flatten().tolist())

            self.queue.put(("status", "Saving..."))
            export_mcanim(frames, cc_w, cc_h, fps, 1.0, 20, out_folder, base_name, True)
            self.queue.put(("status", "Done!"))
            self.queue.put(("done", True))
        except Exception as e:
            traceback.print_exc()
            self.queue.put(("status", f"Error: {e}"))
            self.queue.put(("done", True))

class EditorTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.frames = [] 
        self.width = 0
        self.height = 0
        self.palette_lookup = []
        self.is_playing = False
        self.current_frame_idx = 0
        
        self.is_user_scrolling = False
        self.is_auto_updating = False 
        
        self.current_file_path = None
        self.audio_file = None
        self.new_audio_path = None 
        
        self.temp_wav_full = None
        self.temp_wav_slice = None
        self.audio_enabled = True
        
        self.setup_ui()

    def setup_ui(self):
        ttk.Label(self, text="EDITOR / PREVIEWER", style="Header.TLabel").pack(pady=(15,10))
        
        fr_controls = ttk.Frame(self, style="Panel.TFrame")
        fr_controls.pack(fill=tk.X, padx=10, ipady=5)
        
        ttk.Button(fr_controls, text="Open .mcanim", command=self.load_file_thread).pack(side=tk.LEFT, padx=5)
        ttk.Button(fr_controls, text="Save As...", command=self.save_file).pack(side=tk.LEFT, padx=5)
        
        tk.Frame(fr_controls, width=1, bg="#555").pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=2)
        
        ttk.Button(fr_controls, text="Resize/Crop", command=self.crop_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(fr_controls, text="Trim (Time)", command=self.trim_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(fr_controls, text="Audio Options", command=self.audio_options).pack(side=tk.LEFT, padx=2)

        self.lbl_info = ttk.Label(fr_controls, text="No file loaded", background=BG_PANEL, foreground="#888")
        self.lbl_info.pack(side=tk.RIGHT, padx=10)
        
        self.canvas_frame = ttk.Frame(self, style="TFrame")
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.canvas = tk.Canvas(self.canvas_frame, bg="black", highlightthickness=0, bd=0)
        self.canvas.pack(anchor="center", expand=True)
        
        fr_play = ttk.Frame(self)
        fr_play.pack(fill=tk.X, padx=10, pady=10)
        ttk.Button(fr_play, text="<", width=3, command=lambda: self.seek(-1)).pack(side=tk.LEFT)
        self.btn_play = ttk.Button(fr_play, text="PLAY", command=self.toggle_play)
        self.btn_play.pack(side=tk.LEFT, padx=5)
        ttk.Button(fr_play, text=">", width=3, command=lambda: self.seek(1)).pack(side=tk.LEFT)
        self.slider = ttk.Scale(fr_play, from_=0, to=100, orient=tk.HORIZONTAL, command=self.on_scroll)
        self.slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        self.lbl_frame = ttk.Label(fr_play, text="0 / 0")
        self.lbl_frame.pack(side=tk.RIGHT)

    def load_file_thread(self):
        path = filedialog.askopenfilename(filetypes=[("MCAnim", "*.mcanim")])
        if not path: return
        self.current_file_path = path
        self.lbl_info.config(text="Loading...")
        threading.Thread(target=self.load_file, args=(path,), daemon=True).start()

    def load_file(self, path):
        try:
            winsound.PlaySound(None, 0)
            self.temp_wav_full = None
            
            with open(path, 'r') as f: data = json.load(f)
            self.header = data['header']
            self.width, self.height = self.header['width'], self.header['height']
            self.audio_file = data.get('audio') 
            self.new_audio_path = None 

            self.palette_lookup = [(0,0,0)] * 16
            pal_map = self.header['palette']
            for hex_char, name in pal_map.items():
                try:
                    idx = int(hex_char, 16)
                    col_idx = COLOR_NAMES.index(name)
                    self.palette_lookup[idx] = tuple(CC_COLORS_RGB[col_idx].astype(int))
                except: pass

            self.frames = []
            base_dir = os.path.dirname(path)
            current_buffer = bytearray([15] * (self.width * self.height)) 
            
            for chunk_file in data['chunks']:
                c_path = os.path.join(base_dir, chunk_file)
                with open(c_path, 'r') as f: b64 = f.read()
                json_str = zlib.decompress(base64.b64decode(b64)).decode()
                chunk_data = json.loads(json_str)
                
                for frame_dat in chunk_data['frames']:
                    if frame_dat['type'] == 'full':
                        bgs = frame_dat['bgs']
                        for i, char in enumerate(bgs):
                            current_buffer[i] = int(char, 16)
                    elif frame_dat['type'] == 'delta':
                        for change in frame_dat['changes']:
                            idx = (change['y']-1) * self.width + (change['x']-1)
                            if 0 <= idx < len(current_buffer):
                                current_buffer[idx] = int(change['bg'], 16)
                    self.frames.append(bytearray(current_buffer))
            
            if self.audio_file:
                ffmpeg = get_ffmpeg_path()
                src_audio = os.path.join(base_dir, self.audio_file)
                if ffmpeg and os.path.exists(src_audio):
                    temp_dir = tempfile.gettempdir()
                    self.temp_wav_full = os.path.join(temp_dir, "vidmator_preview_full.wav")
                    subprocess.run([ffmpeg, "-y", "-v", "error", "-f", "dfpwm", "-ar", "48k", "-ac", "1", "-i", src_audio, self.temp_wav_full], check=True)

            self.after(0, self.finish_loading)
        except Exception:
            err = traceback.format_exc()
            self.after(0, lambda: messagebox.showerror("Error", f"Failed to load:\n{err}"))

    def finish_loading(self):
        self.slider.config(to=len(self.frames)-1)
        self.current_frame_idx = 0
        self.update_info_label()
        
        self.canvas.update_idletasks() 
        view_w = self.canvas.winfo_width()
        view_h = self.canvas.winfo_height()
        if view_w < 50: view_w = 580
        if view_h < 50: view_h = 400
        scale_x = (view_w - 20) / max(1, self.width)
        scale_y = (view_h - 20) / max(1, self.height)
        self.scale_fac = max(1, min(int(min(scale_x, scale_y)), 20)) 
        self.canvas.config(width=self.width*self.scale_fac, height=self.height*self.scale_fac)
        
        self.show_frame()

    def update_info_label(self):
        aud_txt = " (Audio)" if (self.audio_file or self.new_audio_path) else ""
        self.lbl_info.config(text=f"{self.width}x{self.height} | {len(self.frames)} frames{aud_txt}")

    def crop_dialog(self):
        if not self.frames: return
        res = simpledialog.askstring("Resize / Crop", f"Enter: X, Y, Width, Height\nCurrent: 0, 0, {self.width}, {self.height}")
        if not res: return
        try:
            x, y, w, h = map(int, res.replace(',', ' ').split())
            if w <= 0 or h <= 0: raise ValueError
            new_frames = []
            for fr in self.frames:
                new_buf = bytearray([15] * (w * h))
                for ny in range(h):
                    for nx in range(w):
                        ox, oy = x + nx, y + ny
                        if 0 <= ox < self.width and 0 <= oy < self.height:
                            old_idx = oy * self.width + ox
                            new_idx = ny * w + nx
                            new_buf[new_idx] = fr[old_idx]
                new_frames.append(new_buf)
            self.frames = new_frames
            self.width, self.height = w, h
            self.finish_loading()
        except: messagebox.showerror("Error", "Invalid dimensions.")

    def trim_dialog(self):
        if not self.frames: return
        total = len(self.frames)
        res = simpledialog.askstring("Trim Animation", f"Enter Start Frame, End Frame\nTotal Frames: {total}")
        if not res: return
        try:
            start, end = map(int, res.replace(',', ' ').split())
            if start < 0: start = 0
            if end > total: end = total
            if start >= end: raise ValueError
            self.frames = self.frames[start:end]
            self.finish_loading()
            messagebox.showinfo("Trim", f"Animation trimmed to {len(self.frames)} frames.")
        except: messagebox.showerror("Error", "Invalid range.")

    def audio_options(self):
        def add_audio():
            path = filedialog.askopenfilename(filetypes=[("Audio", "*.mp3 *.wav *.ogg *.flac")])
            if not path: return
            
            ffmpeg = get_ffmpeg_path()
            if not ffmpeg: 
                messagebox.showerror("Error", "FFmpeg not found.")
                return

            try:
                temp_dir = tempfile.gettempdir()
                self.temp_wav_full = os.path.join(temp_dir, "vidmator_preview_full.wav")
                subprocess.run([ffmpeg, "-y", "-v", "error", "-i", path, "-ac", "1", "-ar", "48000", self.temp_wav_full], check=True)
                
                temp_dfpwm = os.path.join(temp_dir, "vidmator_temp.dfpwm")
                subprocess.run([ffmpeg, "-y", "-v", "error", "-i", self.temp_wav_full, "-c:a", "dfpwm", temp_dfpwm], check=True)
                
                self.new_audio_path = temp_dfpwm
                self.audio_file = "audio.dfpwm"
                self.update_info_label()
                messagebox.showinfo("Success", "Audio track imported! (Will be saved with Save As)")
                top.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", f"Conversion failed: {e}")

        def remove_audio():
            self.audio_file = None
            self.new_audio_path = None
            self.temp_wav_full = None
            winsound.PlaySound(None, 0)
            self.update_info_label()
            top.destroy()

        def extract_audio():
            if not self.current_file_path or not self.audio_file: return
            base_dir = os.path.dirname(self.current_file_path)
            src_audio = os.path.join(base_dir, self.audio_file)
            if self.new_audio_path: src_audio = self.new_audio_path
            
            save_path = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("WAV", "*.wav")])
            if save_path:
                ffmpeg = get_ffmpeg_path()
                subprocess.run([ffmpeg, "-y", "-v", "error", "-f", "dfpwm", "-ar", "48k", "-ac", "1", "-i", src_audio, save_path])
                top.destroy()

        top = tk.Toplevel(self)
        top.title("Audio Tools")
        top.geometry("300x200")
        setup_theme(top)
        
        lbl_txt = "No Track"
        if self.audio_file: lbl_txt = "Track Present"
        if self.new_audio_path: lbl_txt = "New Track (Unsaved)"
        
        ttk.Label(top, text=lbl_txt, foreground="#888").pack(pady=10)
        ttk.Button(top, text="Import / Replace Audio", command=add_audio).pack(fill=tk.X, padx=20, pady=5)
        if self.audio_file:
            ttk.Button(top, text="Extract to WAV", command=extract_audio).pack(fill=tk.X, padx=20, pady=5)
            ttk.Button(top, text="Remove Track", command=remove_audio).pack(fill=tk.X, padx=20, pady=5)

    def save_file(self):
        if not self.frames: return
        chunk_size = simpledialog.askinteger("Export Settings", "Frames per Chunk file:", minvalue=1, maxvalue=5000, initialvalue=20)
        if not chunk_size: return
        out_path = filedialog.asksaveasfilename(defaultextension=".mcanim", filetypes=[("MCAnim", "*.mcanim")])
        if not out_path: return
        
        base_name = os.path.splitext(os.path.basename(out_path))[0]
        out_folder = os.path.dirname(out_path)
        
        export_data = []
        for fr_bytes in self.frames:
            frame_colors = []
            for byte in fr_bytes:
                hex_c = hex(byte)[2:]
                col_name = self.header['palette'].get(hex_c, "black")
                frame_colors.append(col_name)
            export_data.append(frame_colors)

        has_audio = False
        dst_audio = os.path.join(out_folder, "audio.dfpwm")
        
        if self.new_audio_path and os.path.exists(self.new_audio_path):
            try:
                shutil.copy(self.new_audio_path, dst_audio)
                has_audio = True
            except: pass
        elif self.audio_file and self.current_file_path and not self.new_audio_path:
            src_dir = os.path.dirname(self.current_file_path)
            src_audio = os.path.join(src_dir, self.audio_file)
            if os.path.exists(src_audio):
                try:
                    shutil.copy(src_audio, dst_audio)
                    has_audio = True
                except: pass

        try:
            export_mcanim(export_data, self.width, self.height, self.header['fps'], 
                          self.header.get('scale', 1.0), chunk_size, out_folder, base_name, has_audio)
            messagebox.showinfo("Success", "Project Saved!")
        except Exception as e:
            messagebox.showerror("Error", f"Save failed: {e}")

    def show_frame(self):
        if not self.frames: return
        self.canvas.delete("all")
        frame_bytes = self.frames[self.current_frame_idx]
        s = self.scale_fac
        
        for i, color_idx in enumerate(frame_bytes):
            if color_idx == 15: continue
            x, y = (i % self.width), (i // self.width)
            rgb = self.palette_lookup[color_idx]
            hex_c = "#%02x%02x%02x" % rgb
            self.canvas.create_rectangle(x*s, y*s, (x+1)*s, (y+1)*s, fill=hex_c, outline="")

        self.lbl_frame.config(text=f"{self.current_frame_idx+1} / {len(self.frames)}")
        
        if not self.is_user_scrolling:
            self.is_auto_updating = True
            self.slider.set(self.current_frame_idx)
            self.is_auto_updating = False

    def toggle_play(self):
        if self.is_playing:
            self.is_playing = False
            self.btn_play.config(text="PLAY")
            winsound.PlaySound(None, 0)
        else:
            self.is_playing = True
            self.btn_play.config(text="PAUSE")
            
            if self.temp_wav_full and os.path.exists(self.temp_wav_full):
                fps = self.header.get('fps', 10)
                start_sec = self.current_frame_idx / fps
                
                ffmpeg = get_ffmpeg_path()
                if ffmpeg:
                    temp_dir = tempfile.gettempdir()
                    self.temp_wav_slice = os.path.join(temp_dir, "vidmator_slice.wav")
                    threading.Thread(target=self.play_audio_slice, args=(ffmpeg, start_sec), daemon=True).start()

            threading.Thread(target=self.play_loop, daemon=True).start()

    def play_audio_slice(self, ffmpeg, start_sec):
        try:
            subprocess.run([ffmpeg, "-y", "-v", "error", "-ss", str(start_sec), "-i", self.temp_wav_full, self.temp_wav_slice], check=True)
            
            if self.is_playing:
                winsound.PlaySound(self.temp_wav_slice, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except: pass

    def play_loop(self):
        fps = self.header.get('fps', 10)
        delay = 1.0 / fps
        while self.is_playing and self.current_frame_idx < len(self.frames) - 1:
            start = time.time()
            self.current_frame_idx += 1
            self.after(0, self.show_frame)
            elapsed = time.time() - start
            time.sleep(max(0, delay - elapsed))
        if self.current_frame_idx >= len(self.frames) - 1:
            self.is_playing = False
            winsound.PlaySound(None, 0)
            self.after(0, lambda: self.btn_play.config(text="REPLAY"))
            self.current_frame_idx = 0

    def seek(self, delta):
        winsound.PlaySound(None, 0)
        self.is_playing = False
        self.btn_play.config(text="PLAY")
        new_idx = self.current_frame_idx + delta
        if 0 <= new_idx < len(self.frames):
            self.current_frame_idx = new_idx
            self.show_frame()

    def on_scroll(self, val):
        if self.is_auto_updating: return

        self.is_user_scrolling = True
        winsound.PlaySound(None, 0)
        self.is_playing = False
        self.btn_play.config(text="PLAY")
        try:
            idx = int(float(val))
            if idx != self.current_frame_idx:
                self.current_frame_idx = idx
                self.show_frame()
        finally:
            self.is_user_scrolling = False

class VidmatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Vidmator 2.0")
        self.root.geometry("600x670")
        self.root.overrideredirect(True) 
        
        self.root.update()
        self.root.after(10, self.set_app_window) 
        
        setup_theme(root)
        CustomTitleBar(root, "Vidmator 2.0 (Custom Edition)", self.close_app, self.minimize_app)
        
        main_frame = tk.Frame(root, bg=BG_DARK)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        self.queue = queue.Queue()
        self.nb = ttk.Notebook(main_frame)
        self.nb.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.tab1 = VideoConvertTab(self.nb, self.queue)
        self.tab2 = AudioVisTab(self.nb, self.queue)
        self.tab3 = EditorTab(self.nb)
        self.nb.add(self.tab1, text="  Video Converter  ")
        self.nb.add(self.tab2, text="  Audio Visualizer  ")
        self.nb.add(self.tab3, text="  Preview / Editor  ")
        
        self.status_var = tk.StringVar(value="Checking System...")
        self.prog_bar = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, mode='determinate')
        self.prog_bar.pack(fill=tk.X, padx=10, pady=(0,5))
        ttk.Label(main_frame, textvariable=self.status_var, anchor="center", font=("Consolas", 8)).pack(fill=tk.X, pady=(0,5))
        
        self.root.after(100, self.check_queue)
        self.check_ffmpeg()

    def set_app_window(self):
        GWL_EXSTYLE = -20
        WS_EX_APPWINDOW = 0x00040000
        WS_EX_TOOLWINDOW = 0x00000080
        
        hwnd = windll.user32.GetParent(self.root.winfo_id())
        
        style = windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        
        style = style & ~WS_EX_TOOLWINDOW
        style = style | WS_EX_APPWINDOW
    
        windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        
        self.root.wm_withdraw()
        self.root.after(10, lambda: self.root.wm_deiconify())

    def close_app(self):
        winsound.PlaySound(None, 0)
        self.root.destroy()
        sys.exit()
        
    def minimize_app(self):
        self.root.overrideredirect(False)
        self.root.iconify()
        self.root.bind("<FocusIn>", self.on_deiconify)

    def on_deiconify(self, event):
        self.root.overrideredirect(True)
        self.root.unbind("<FocusIn>")

    def check_ffmpeg(self):
        path = get_ffmpeg_path()
        if path: self.status_var.set(f"System Ready. (FFmpeg Active)")
        else: self.status_var.set("FFMPEG MISSING. Audio features disabled.")

    def check_queue(self):
        try:
            while True:
                msg, val = self.queue.get_nowait()
                if msg == "status": self.status_var.set(val)
                elif msg == "progress": self.prog_bar['value'] = val
                elif msg == "done":
                    self.tab1.btn_run.config(state="normal")
                    self.tab2.btn_run.config(state="normal")
        except queue.Empty: pass
        self.root.after(100, self.check_queue)

if __name__ == "__main__":
    root = tk.Tk()
    app = VidmatorApp(root)
    root.mainloop()