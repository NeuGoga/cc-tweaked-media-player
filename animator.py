import pygame
import json

DEFAULT_MONITOR_BLOCKS_X = 2
DEFAULT_MONITOR_BLOCKS_Y = 1
MIN_WINDOW_WIDTH = 640
MIN_WINDOW_HEIGHT = 480
BASE_CELL_SIZE = 16
UI_WIDTH = 250
MAX_MONITOR_BLOCKS_X = 8
MAX_MONITOR_BLOCKS_Y = 6
MAX_FPS = 20
ONION_SKIN_ALPHA = 90

CC_COLORS = {
    "white": (240, 240, 240), "orange": (242, 178, 51), "magenta": (229, 127, 216),
    "lightBlue": (153, 178, 242), "yellow": (222, 222, 108), "lime": (127, 204, 25),
    "pink": (242, 178, 204), "gray": (76, 76, 76), "lightGray": (204, 204, 204),
    "cyan": (76, 229, 229), "purple": (178, 102, 229), "blue": (51, 102, 178),
    "brown": (127, 102, 76), "green": (102, 127, 51), "red": (216, 76, 76),
    "black": (25, 25, 25)
}
COLOR_NAMES = list(CC_COLORS.keys())
COLOR_PALETTE = list(CC_COLORS.values())
HEX_CHARS = "0123456789abcdef"

class AnimationEditor:
    def __init__(self):
        pygame.init()
        self.ui_font = pygame.font.Font(pygame.font.get_default_font(), 16)
        self.ui_font_small = pygame.font.Font(pygame.font.get_default_font(), 14)
        self.clock = pygame.time.Clock()

        self.current_bg_color = "black"
        self.onion_skin_enabled = True
        
        self.monitor_blocks_x = DEFAULT_MONITOR_BLOCKS_X
        self.monitor_blocks_y = DEFAULT_MONITOR_BLOCKS_Y
        self.scale = 1.0
        self.fps = 10
        self.chunk_size = 10
        self.cc_width, self.cc_height = 0, 0

        self.monitor_x_str = str(self.monitor_blocks_x)
        self.monitor_y_str = str(self.monitor_blocks_y)
        self.chunk_size_str = str(self.chunk_size)
        self.fps_str = str(self.fps)
        self.active_input = None
        self.ui_rects = {}

        self.zoom_level = 1.0
        self.camera_offset_x = 0
        self.camera_offset_y = 0
        self.panning = False
        self.color_before_erase = None

        self.reinitialize_grid(set_initial_size=True)
        self.reset_animation()

    def reinitialize_grid(self, set_initial_size=False):
        try:
            self.monitor_blocks_x = min(max(1, int(self.monitor_x_str)), MAX_MONITOR_BLOCKS_X)
            self.monitor_blocks_y = min(max(1, int(self.monitor_y_str)), MAX_MONITOR_BLOCKS_Y)
            self.fps = min(max(1, int(self.fps_str)), MAX_FPS)
            self.monitor_x_str = str(self.monitor_blocks_x)
            self.monitor_y_str = str(self.monitor_blocks_y)
            self.chunk_size = int(self.chunk_size_str)
        except (ValueError, TypeError):
            self.monitor_x_str = str(self.monitor_blocks_x)
            self.monitor_y_str = str(self.monitor_blocks_y)

        self.cc_width = round((64 * self.monitor_blocks_x - 20) / (6 * self.scale))
        self.cc_height = round((64 * self.monitor_blocks_y - 20) / (9 * self.scale))
        self.pixels_dims = f"{self.cc_width * 2} x {self.cc_height * 3}"
        self.bixels_dims = f"{self.cc_width} x {int(self.cc_height * 1.5)}"

        if set_initial_size:
            screen_width = max(MIN_WINDOW_WIDTH, self.cc_width * BASE_CELL_SIZE + UI_WIDTH)
            screen_height = max(MIN_WINDOW_HEIGHT, self.cc_height * BASE_CELL_SIZE)
            self.screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
        
        pygame.display.set_caption("ComputerCraft Animator")
        print(f"Grid resized to: {self.cc_width}x{self.cc_height} characters.")

    def reset_animation(self):
        print("Animation has been reset due to size change.")
        frame = [["black" for _ in range(self.cc_width)] for _ in range(self.cc_height)]
        self.animation = [frame]
        self.current_frame_index = 0

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                elif event.type == pygame.VIDEORESIZE: self.screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                self.handle_input(event)
            self.handle_continuous_input()
            self.draw()
            self.clock.tick(60)
        pygame.quit()

    def handle_continuous_input(self):
        mx, my = pygame.mouse.get_pos()
        grid_width = self.screen.get_width() - UI_WIDTH
        
        if self.panning:
            dx, dy = pygame.mouse.get_rel()
            self.camera_offset_x -= dx / (BASE_CELL_SIZE * self.zoom_level)
            self.camera_offset_y -= dy / (BASE_CELL_SIZE * self.zoom_level)

        elif pygame.mouse.get_pressed()[0]:
            if mx < grid_width:
                world_x, world_y = self.screen_to_world(mx, my)
                if 0 <= world_x < self.cc_width and 0 <= world_y < self.cc_height:
                    self.animation[self.current_frame_index][world_y][world_x] = self.current_bg_color
        
        elif pygame.mouse.get_pressed()[2]:
            if mx < grid_width:
                self.current_bg_color = "black"
                world_x, world_y = self.screen_to_world(mx, my)
                if 0 <= world_x < self.cc_width and 0 <= world_y < self.cc_height:
                    self.animation[self.current_frame_index][world_y][world_x] = "black"

    def handle_input(self, event):
        if event.type == pygame.MOUSEWHEEL:
            mx, my = pygame.mouse.get_pos()
            world_x_before, world_y_before = self.screen_to_world(mx, my)
            self.zoom_level *= 1.1 if event.y > 0 else 1/1.1
            self.zoom_level = max(0.2, min(self.zoom_level, 5.0))
            world_x_after, world_y_after = self.screen_to_world(mx, my)
            self.camera_offset_x += world_x_before - world_x_after
            self.camera_offset_y += world_y_before - world_y_after

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: self.handle_ui_click(pygame.mouse.get_pos())
            elif event.button == 2:
                self.panning = True
                pygame.mouse.get_rel()
            elif event.button == 3:
                 self.color_before_erase = self.current_bg_color
                 mx, my = pygame.mouse.get_pos()
                 if mx < self.screen.get_width() - UI_WIDTH:
                     world_x, world_y = self.screen_to_world(mx, my)
                     if 0 <= world_x < self.cc_width and 0 <= world_y < self.cc_height:
                         self.current_bg_color = self.animation[self.current_frame_index][world_y][world_x]
        
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 2: self.panning = False
            if event.button == 3 and self.color_before_erase:
                self.current_bg_color = self.color_before_erase
                self.color_before_erase = None

        if event.type == pygame.KEYDOWN:
            if self.active_input:
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER): self.reinitialize_grid(); self.reset_animation(); self.active_input = None
                elif event.key == pygame.K_BACKSPACE:
                    if self.active_input == 'x': self.monitor_x_str = self.monitor_x_str[:-1]
                    elif self.active_input == 'y': self.monitor_y_str = self.monitor_y_str[:-1]
                    elif self.active_input == 'fps': self.fps_str = self.fps_str[:-1]
                    elif self.active_input == 'chunk_size': self.chunk_size_str = self.chunk_size_str[:-1] 
                elif event.unicode.isdigit():
                    if self.active_input == 'x': self.monitor_x_str += event.unicode
                    elif self.active_input == 'y': self.monitor_y_str += event.unicode
                    elif self.active_input == 'fps': self.fps_str += event.unicode
                    elif self.active_input == 'chunk_size': self.chunk_size_str += event.unicode
                return

            if event.key == pygame.K_RIGHT: self.current_frame_index = min(self.current_frame_index + 1, len(self.animation) - 1)
            elif event.key == pygame.K_LEFT: self.current_frame_index = max(self.current_frame_index - 1, 0)
            elif event.key == pygame.K_n:
                new_frame = [row[:] for row in self.animation[self.current_frame_index]]
                self.animation.insert(self.current_frame_index + 1, new_frame); self.current_frame_index += 1
            elif event.key == pygame.K_d:
                if len(self.animation) > 1: self.animation.pop(self.current_frame_index); self.current_frame_index = max(0, self.current_frame_index - 1)
            elif event.key == pygame.K_o: self.onion_skin_enabled = not self.onion_skin_enabled
            elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL: self.export_animation()
            elif event.key == pygame.K_F11: pygame.display.toggle_fullscreen()

    def handle_ui_click(self, pos):
        ui_x = self.screen.get_width() - UI_WIDTH
        if pos[0] < ui_x: self.active_input = None; return
        
        self.active_input = None
        for name, rect in self.ui_rects.items():
            if rect.collidepoint(pos):
                if name == 'input_x': self.active_input = 'x'; return
                if name == 'input_y': self.active_input = 'y'; return
                if name == 'input_fps': self.active_input = 'fps'; return
                if name == 'input_chunk_size': self.active_input = 'chunk_size'; return
                if name.startswith('scale_'): self.scale = float(name.split('_')[1]); self.reinitialize_grid(); self.reset_animation(); return
                if name.startswith('color_'): self.current_bg_color = name.split('_')[1]; return

    def screen_to_world(self, screen_x, screen_y):
        cell_size = BASE_CELL_SIZE * self.zoom_level
        world_x = int(screen_x / cell_size + self.camera_offset_x)
        world_y = int(screen_y / cell_size + self.camera_offset_y)
        return world_x, world_y

    def draw(self):
        self.screen.fill((50, 50, 50))
        grid_surface = pygame.Surface((self.screen.get_width() - UI_WIDTH, self.screen.get_height()), pygame.SRCALPHA)
        grid_surface.fill((25, 25, 25))
        if self.onion_skin_enabled and self.current_frame_index > 0:
            self.draw_frame(self.animation[self.current_frame_index - 1], alpha=60)
        self.draw_frame(self.animation[self.current_frame_index])
        self.draw_grid()
        self.draw_ui()
        pygame.display.flip()

    def draw_frame(self, frame_data, alpha=255):
        cell_size = BASE_CELL_SIZE * self.zoom_level
        
        start_x = max(0, int(self.camera_offset_x))
        start_y = max(0, int(self.camera_offset_y))
        end_x = min(self.cc_width, int(self.camera_offset_x + self.screen.get_width() / cell_size) + 2)
        end_y = min(self.cc_height, int(self.camera_offset_y + self.screen.get_height() / cell_size) + 2)

        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                screen_x = (x - self.camera_offset_x) * cell_size
                screen_y = (y - self.camera_offset_y) * cell_size
                rect = pygame.Rect(screen_x, screen_y, cell_size, cell_size)
                
                bg_color = frame_data[y][x]
                bg_rgb = CC_COLORS[bg_color]
                
                if alpha != 255:
                    if bg_color != "black":
                        s = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
                        s.fill((*bg_rgb, alpha))
                        self.screen.blit(s, rect.topleft)
                
                else:
                    is_onion_skin_active = self.onion_skin_enabled and self.current_frame_index > 0
                    
                    if is_onion_skin_active and bg_color == "black":
                        s = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
                        s.fill((bg_rgb[0], bg_rgb[1], bg_rgb[2], 100))
                        self.screen.blit(s, rect.topleft)
                    else:
                        pygame.draw.rect(self.screen, bg_rgb, rect)

    def draw_grid(self):
        cell_size = BASE_CELL_SIZE * self.zoom_level
        grid_width = self.screen.get_width() - UI_WIDTH
        grid_height = self.screen.get_height()
        offset_x = -self.camera_offset_x * cell_size
        offset_y = -self.camera_offset_y * cell_size

        for x in range(self.cc_width + 1):
            line_x = x * cell_size + offset_x
            if 0 <= line_x <= grid_width:
                pygame.draw.line(self.screen, (100, 100, 100), (line_x, 0), (line_x, grid_height))
        
        for y in range(self.cc_height + 1):
            line_y = y * cell_size + offset_y
            if 0 <= line_y <= grid_height:
                pygame.draw.line(self.screen, (100, 100, 100), (0, line_y), (grid_width, line_y))

    def draw_ui(self):
        ui_x = self.screen.get_width() - UI_WIDTH
        pygame.draw.rect(self.screen, (30, 30, 30), (ui_x, 0, UI_WIDTH, self.screen.get_height()))
        self.ui_rects = {}

        for i, color in enumerate(COLOR_PALETTE):
            rect = pygame.Rect(ui_x + 20, i * (BASE_CELL_SIZE + 2) + 20, BASE_CELL_SIZE, BASE_CELL_SIZE)
            self.ui_rects[f'color_{COLOR_NAMES[i]}'] = rect
            pygame.draw.rect(self.screen, color, rect)

        info_y = 30; ui_content_x = ui_x + 50
        self.screen.blit(self.ui_font.render(f"Frame: {self.current_frame_index + 1} / {len(self.animation)}", True, (220, 220, 220)), (ui_content_x, info_y))
        
        info_y += 50
        self.screen.blit(self.ui_font.render("Monitor Size (Blocks):", True, (220, 220, 220)), (ui_content_x, info_y))
        x_box = pygame.Rect(ui_content_x + 30, info_y + 25, 40, 25); self.ui_rects['input_x'] = x_box
        y_box = pygame.Rect(ui_content_x + 100, info_y + 25, 40, 25); self.ui_rects['input_y'] = y_box
        pygame.draw.rect(self.screen, (20, 20, 20) if self.active_input == 'x' else (80, 80, 80), x_box); pygame.draw.rect(self.screen, (120,120,120), x_box, 2)
        pygame.draw.rect(self.screen, (20, 20, 20) if self.active_input == 'y' else (80, 80, 80), y_box); pygame.draw.rect(self.screen, (120,120,120), y_box, 2)
        self.screen.blit(self.ui_font_small.render("X:", True, (220, 220, 220)), (x_box.x - 20, x_box.y + 5)); self.screen.blit(self.ui_font_small.render("Y:", True, (220, 220, 220)), (y_box.x - 20, y_box.y + 5))
        self.screen.blit(self.ui_font.render(self.monitor_x_str, True, (255, 255, 255)), (x_box.x + 5, x_box.y + 5)); self.screen.blit(self.ui_font.render(self.monitor_y_str, True, (255, 255, 255)), (y_box.x + 5, y_box.y + 5))

        info_y += 70
        self.screen.blit(self.ui_font.render("FPS:", True, (220, 220, 220)), (ui_content_x, info_y))
        fps_box = pygame.Rect(ui_content_x + 60, info_y - 5, 50, 30); self.ui_rects['input_fps'] = fps_box
        pygame.draw.rect(self.screen, (20, 20, 20) if self.active_input == 'fps' else (80, 80, 80), fps_box); pygame.draw.rect(self.screen, (120,120,120), fps_box, 2)
        self.screen.blit(self.ui_font.render(self.fps_str, True, (255, 255, 255)), (fps_box.x + 5, fps_box.y + 5))

        info_y += 70
        self.screen.blit(self.ui_font.render("Chuck size:", True, (220, 220, 220)), (ui_content_x, info_y))
        chunk_box = pygame.Rect(ui_content_x + 60, info_y - 5, 50, 30); self.ui_rects['input_chunk_size'] = chunk_box
        pygame.draw.rect(self.screen, (20, 20, 20) if self.active_input == 'chunk_size' else (80, 80, 80), chunk_box); pygame.draw.rect(self.screen, (120,120,120), chunk_box, 2)
        self.screen.blit(self.ui_font.render(self.chunk_size_str, True, (255, 255, 255)), (chunk_box.x + 5, chunk_box.y + 5))

        info_y += 70
        self.screen.blit(self.ui_font.render("Scale:", True, (220, 220, 220)), (ui_content_x, info_y))
        scales = [0.5, 1.0, 1.25, 1.5]
        for i, s in enumerate(scales):
            btn_rect = pygame.Rect(ui_content_x + i*55, info_y + 25, 45, 25)
            self.ui_rects[f'scale_{s}'] = btn_rect
            pygame.draw.rect(self.screen, (120, 120, 120) if self.scale == s else (80, 80, 80), btn_rect)
            self.screen.blit(self.ui_font_small.render(str(s), True, (255, 255, 255)), (btn_rect.x + 8, btn_rect.y + 5))
        
        info_y += 70
        self.screen.blit(self.ui_font.render(f"Chars: {self.cc_width}x{self.cc_height}", True, (220, 220, 220)), (ui_content_x, info_y))
        self.screen.blit(self.ui_font.render(f"Pixels: {self.pixels_dims}", True, (220, 220, 220)), (ui_content_x, info_y + 25))
        self.screen.blit(self.ui_font.render(f"Bixels: {self.bixels_dims}", True, (220, 220, 220)), (ui_content_x, info_y + 50))

        info_y += 90
        self.screen.blit(self.ui_font.render("BG Color:", True, (220, 220, 220)), (ui_content_x, info_y))
        pygame.draw.rect(self.screen, CC_COLORS[self.current_bg_color], (ui_content_x + 80, info_y, 30, 20))
        
        instructions = [ "--- Controls ---", "LMB Drag: Draw", "RMB Drag: Erase", "RMB Click: Pick Color", "MMB Drag: Pan", "Scroll: Zoom", "Left/Right: Change Frame", "N: New Frame", "D: Delete Frame", "O: Toggle Onion Skin", "Ctrl+S: Export", "F11: Fullscreen" ]
        for i, line in enumerate(instructions):
            self.screen.blit(self.ui_font_small.render(line, True, (180, 180, 180)), (ui_content_x, self.screen.get_height() - 220 + i * 18))

    def export_animation(self):
        import zlib
        import base64
        import os

        CHUNK_SIZE = self.chunk_size 
        
        print("Exporting and chunking animation...")
        
        palette_map = {HEX_CHARS[i]: name for i, name in enumerate(COLOR_NAMES)}
        color_to_hex = {name: HEX_CHARS[i] for i, name in enumerate(COLOR_NAMES)}
        
        base_filename = "animation"
        chunk_filenames = []

        output_folder = base_filename
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        print(f"Exporting animation to folder: '{output_folder}'...")
        
        for chunk_index, i in enumerate(range(0, len(self.animation), CHUNK_SIZE)):
            chunk_data = self.animation[i : i + CHUNK_SIZE]
            chunk_output_filename = f"{base_filename}_{chunk_index}.canim"
            chunk_filenames.append(chunk_output_filename)
            
            print(f"  Processing chunk {chunk_index+1} ({len(chunk_data)} frames)...")

            chunk_frames = []
            
            keyframe_bgs = "".join([color_to_hex[chunk_data[0][y][x]] for y in range(self.cc_height) for x in range(self.cc_width)])
            chunk_frames.append({"type": "full", "bgs": keyframe_bgs})

            for frame_idx in range(1, len(chunk_data)):
                prev_frame, curr_frame = chunk_data[frame_idx-1], chunk_data[frame_idx]
                changes = []
                for y in range(self.cc_height):
                    for x in range(self.cc_width):
                        if prev_frame[y][x] != curr_frame[y][x]:
                            changes.append({"x": x + 1, "y": y + 1, "bg": color_to_hex[curr_frame[y][x]]})
                
                if changes:
                    chunk_frames.append({"type": "delta", "changes": changes})
                else:
                    chunk_frames.append({"type": "delta", "changes": []})

            chunk_json_string = json.dumps({"frames": chunk_frames}, separators=(',', ':'))
            compressed_data = zlib.compress(chunk_json_string.encode('utf-8'))
            base64_string = base64.b64encode(compressed_data).decode('ascii')

            chunk_filepath = os.path.join(output_folder, chunk_output_filename)

            with open(chunk_filepath, "w") as f:
                f.write(base64_string)

        master_output = {
            "header": {
                "width": self.cc_width,
                "height": self.cc_height,
                "fps": self.fps,
                "scale": self.scale,
                "palette": palette_map
            },
            "chunks": chunk_filenames
        }

        master_filepath = os.path.join(output_folder, f"{base_filename}.mcanim")
        with open(master_filepath, "w") as f:
            json.dump(master_output, f, indent=2)
            
        print(f"\nExport complete! Master file and {len(chunk_filenames)} chunks saved to '{output_folder}' folder.")

if __name__ == "__main__":
    editor = AnimationEditor()
    editor.run()