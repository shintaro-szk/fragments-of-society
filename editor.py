import pygame
import glob
from fragment_of_society.inputs import GameAction

class LevelEditor:
    def __init__(self, game):
        self.game = game
        self.ui_state = "hidden" 
        self.input_text = ""
        self.file_list = []
        self.ui_font = pygame.font.SysFont(None, 36)
        
        # Main Toolbar Palette
        self.palette = {
            -1: ("Void (Cut)", (15, 15, 15)),
            -2: ("Restore", (100, 150, 100)),
            0: ("Floor", (60, 100, 60)),     
            1: ("Wall", (100, 100, 100)),
            2: ("Forcefield", (0, 255, 255)),
            50: ("Enemies...", (255, 50, 50)),
            70: ("Atk Buff", (255, 165, 0)),
            97: ("Tutor Door", (150, 0, 255)),
            98: ("Stage 1 Door", (150, 0, 255)),
            99: ("Player Spawn", (0, 255, 0))
        }
        
        # Enemy Submenu Palette
        self.enemy_palette = {
            50: ("Smog Mob", (200, 80, 80)),
            51: ("Gang Mob", (220, 40, 40)),
            52: ("Corrupt Mob", (180, 0, 0)),
            53: ("BOSS", (255, 0, 0))
        }
        
        self.active_id = 1 
        self.toolbar_height = 80
        self.button_width = 100 

    def _refresh_files(self):
        self.file_list = [f for f in glob.glob("*.json")]

    def handle_events(self, event) -> bool:
        if self.ui_state != "hidden":
            return self._handle_menu_events(event)

        # Shortcuts
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_o:
                self.ui_state = "save"
                self.input_text = ""
                return True
            elif event.key == pygame.K_p:
                self.ui_state = "load"
                self._refresh_files()
                return True

        # Mouse Wheel Zooming
        if event.type == pygame.MOUSEWHEEL:
            current_zoom = getattr(self.game.camera, 'zoom', 1.0)
            if event.y > 0: self.game.camera.zoom = min(3.0, current_zoom + 0.1)
            elif event.y < 0: self.game.camera.zoom = max(0.2, current_zoom - 0.1)
            return True

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            screen_w, screen_h = self.game.screen.get_size()
            
            # PLAYTEST Button
            play_btn_rect = pygame.Rect(screen_w - 140, 230, 120, 40)
            if play_btn_rect.collidepoint(mouse_x, mouse_y):
                self._enter_playtest_mode()
                return True

            # Resize Map Buttons
            if self._handle_resize_clicks(mouse_x, mouse_y):
                return True

            toolbar_w = len(self.palette) * self.button_width
            toolbar_x = (screen_w - toolbar_w) // 2
            toolbar_y = screen_h - self.toolbar_height - 20
            
            # Enemy Submenu Click
            if 50 <= self.active_id <= 59:
                sub_w = 120
                sub_h = len(self.enemy_palette) * 40
                enemy_btn_idx = list(self.palette.keys()).index(50)
                sub_x = toolbar_x + (enemy_btn_idx * self.button_width)
                sub_y = toolbar_y - sub_h - 10
                
                if sub_x <= mouse_x <= sub_x + sub_w and sub_y <= mouse_y <= sub_y + sub_h:
                    idx = (mouse_y - sub_y) // 40
                    keys = list(self.enemy_palette.keys())
                    if idx < len(keys):
                        self.active_id = keys[idx]
                    return True

            # Sleek Floating Toolbar Click
            if toolbar_x <= mouse_x <= toolbar_x + toolbar_w and mouse_y >= toolbar_y:
                idx = (mouse_x - toolbar_x) // self.button_width
                keys = list(self.palette.keys())
                if idx < len(keys):
                    self.active_id = keys[idx]
                return True
                
        # Grid Drawing, Erasing, and Pipette
        buttons = pygame.mouse.get_pressed()
        if buttons[0] or buttons[2]: 
            mouse_x, mouse_y = pygame.mouse.get_pos()
            screen_h = self.game.screen.get_size()[1]
            
            # Prevent drawing when clicking UI
            if mouse_y < screen_h - self.toolbar_height - 20 and mouse_y > 100:
                zoom = getattr(self.game.camera, 'zoom', 1.0)
                world_x = (mouse_x / zoom) + self.game.camera.offset_x
                world_y = (mouse_y / zoom) + self.game.camera.offset_y
                row, col = self.game.tilemap.world_to_tile(world_x, world_y)
                
                keys = pygame.key.get_pressed()
                
                # ALT-Click Pipette Tool
                if keys[pygame.K_LALT] and buttons[0]:
                    if 0 <= row < self.game.tilemap.height and 0 <= col < self.game.tilemap.width:
                        for l in [2, 1, 0]:
                            try:
                                t = self.game.tilemap.layers[l][row][col]
                                if t != 0:
                                    self.active_id = t
                                    break
                            except: pass
                    return True
                
                # Standard Draw/Erase
                erase_mode = buttons[2]
                self._modify_grid(row, col, erase=erase_mode)
                return True

        return False

    def _handle_resize_clicks(self, mouse_x, mouse_y) -> bool:
        if 40 <= mouse_y <= 60:
            if 70 <= mouse_x <= 90: self._resize_map(-1, 0)
            elif 130 <= mouse_x <= 150: self._resize_map(1, 0)
            else: return False
            return True
        elif 70 <= mouse_y <= 90:
            if 70 <= mouse_x <= 90: self._resize_map(0, -1)
            elif 130 <= mouse_x <= 150: self._resize_map(0, 1)
            else: return False
            return True
        return False

    def _resize_map(self, dw, dh):
        tm = self.game.tilemap
        new_w = max(5, tm.width + dw)
        new_h = max(5, tm.height + dh)
        layers_list = tm.layers.values() if isinstance(tm.layers, dict) else tm.layers
        for layer in layers_list:
            while len(layer) < new_h: layer.append([0] * tm.width)
            while len(layer) > new_h: layer.pop()
            for row in layer:
                while len(row) < new_w: row.append(0)
                while len(row) > new_w: row.pop()
        tm.width = new_w
        tm.height = new_h

    def _enter_playtest_mode(self):
        self.game.apply_map_spawns()
        self.game.edit_mode = False

    def _handle_menu_events(self, event) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: self.ui_state = "hidden"
            elif self.ui_state == "save":
                if event.key == pygame.K_RETURN and self.input_text.strip():
                    filename = self.input_text.strip()
                    if not filename.endswith(".json"): filename += ".json"
                    self.game.tilemap.save(filename)
                    self.ui_state = "hidden"
                elif event.key == pygame.K_BACKSPACE: self.input_text = self.input_text[:-1]
                else: self.input_text += event.unicode
        elif event.type == pygame.MOUSEBUTTONDOWN and self.ui_state == "load":
            mouse_y = event.pos[1]
            start_y = (self.game.screen.get_height() - 400) // 2 + 60
            clicked_idx = (mouse_y - start_y) // 35
            if 0 <= clicked_idx < len(self.file_list):
                self.game.load_level(self.file_list[clicked_idx])
                self.ui_state = "hidden"
        return True

    def _modify_grid(self, row, col, erase=False):
        if 0 <= row < self.game.tilemap.height and 0 <= col < self.game.tilemap.width:
            try:
                if erase or self.active_id <= 0:
                    val = 0 if (erase or self.active_id == -2 or self.active_id == 0) else self.active_id
                    self.game.tilemap.layers[1][row][col] = val
                    if erase or self.active_id == -1 or self.active_id == -2:
                        try: self.game.tilemap.layers[2][row][col] = 0
                        except: pass
                else:
                    layer_idx = 2 if self.active_id >= 50 else 1
                    self.game.tilemap.layers[layer_idx][row][col] = self.active_id 
            except Exception: pass

    def update(self, dt: float):
        # Free Camera Movement (Mapped to GameAction)
        cam_speed = 600 * dt
        if self.game.input_manager.is_action_pressed(GameAction.MOVE_UP): self.game.camera.offset_y -= cam_speed
        if self.game.input_manager.is_action_pressed(GameAction.MOVE_DOWN): self.game.camera.offset_y += cam_speed
        if self.game.input_manager.is_action_pressed(GameAction.MOVE_LEFT): self.game.camera.offset_x -= cam_speed
        if self.game.input_manager.is_action_pressed(GameAction.MOVE_RIGHT): self.game.camera.offset_x += cam_speed

    def draw_world_overlays(self, render_surf, cx, cy, view_w, view_h):
        """Draws directly to the unscaled render_surf (editor_3.py logic)"""
        ts = self.game.tilemap.tile_size
        
        # 1. Draw Void Squares
        for r in range(self.game.tilemap.height):
            for c in range(self.game.tilemap.width):
                try:
                    if self.game.tilemap.layers[1][r][c] == -1:
                        px = c * ts - cx
                        py = r * ts - cy
                        pygame.draw.rect(render_surf, (15, 15, 15), (px, py, ts, ts))
                except: pass

        # 2. Draw BOUNDED Canvas Grid Lines (No more double scaling!)
        for col in range(self.game.tilemap.width + 1):
            x = col * ts - cx
            if 0 <= x <= view_w:
                y_start = max(0, -cy)
                y_end = min(view_h, self.game.tilemap.height * ts - cy)
                if y_start < y_end:
                    pygame.draw.line(render_surf, (60, 60, 70), (x, y_start), (x, y_end))
                
        for row in range(self.game.tilemap.height + 1):
            y = row * ts - cy
            if 0 <= y <= view_h:
                x_start = max(0, -cx)
                x_end = min(view_w, self.game.tilemap.width * ts - cx)
                if x_start < x_end:
                    pygame.draw.line(render_surf, (60, 60, 70), (x_start, y), (x_end, y))

        # 3. Draw Wall Hitboxes
        for wall in self.game.tilemap.get_wall_hitboxes():
            pygame.draw.rect(render_surf, (255, 0, 0), (wall.x - cx, wall.y - cy, wall.width, wall.height), 2)
            
        # 4. Perfect Hover Highlight Math (using world coords)
        mx, my = pygame.mouse.get_pos()
        screen_h = self.game.screen.get_size()[1]
        
        # Only draw ghost if we aren't hovering over UI
        if my < screen_h - self.toolbar_height - 20:
            zoom = getattr(self.game.camera, 'zoom', 1.0)
            world_x = (mx / zoom) + cx
            world_y = (my / zoom) + cy
            row, col = self.game.tilemap.world_to_tile(world_x, world_y)
            
            if 0 <= row < self.game.tilemap.height and 0 <= col < self.game.tilemap.width:
                view_x = col * ts - cx
                view_y = row * ts - cy
                
                ghost_surf = pygame.Surface((ts, ts), pygame.SRCALPHA)
                
                if self.active_id == -1: ghost_surf.fill((15, 15, 15, 128))
                elif self.active_id == -2: ghost_surf.fill((100, 150, 100, 128))
                elif 50 <= self.active_id <= 59:
                    c = self.enemy_palette.get(self.active_id, (255, 0, 0))[1]
                    ghost_surf.fill((*c, 128))
                else:
                    self.game.tile_renderer.render(ghost_surf, self.active_id, 0, 0)
                    ghost_surf.set_alpha(128)
                
                render_surf.blit(ghost_surf, (view_x, view_y))
                
                # Selection Box Outline
                box_color = (0, 255, 255) if self.active_id == 2 else (255, 255, 255)
                pygame.draw.rect(render_surf, box_color, (view_x, view_y, ts, ts), 2)

    def _draw_minimap(self, screen, screen_w, screen_h):
        """Your preferred minimap logic from editor_3.py"""
        max_dim = 200.0
        px_scale_x = max_dim / max(1, self.game.tilemap.width)
        px_scale_y = max_dim / max(1, self.game.tilemap.height)
        pixel_size = max(1.0, min(8.0, min(px_scale_x, px_scale_y)))
        
        map_w = int(self.game.tilemap.width * pixel_size)
        map_h = int(self.game.tilemap.height * pixel_size)
        mm_x = screen_w - map_w - 20
        mm_y = 20
        
        minimap_surf = pygame.Surface((map_w, map_h))
        minimap_surf.fill((20, 20, 20))
        
        for r in range(self.game.tilemap.height):
            for c in range(self.game.tilemap.width):
                color = None
                try:
                    t2, t1, t0 = self.game.tilemap.layers[2][r][c], self.game.tilemap.layers[1][r][c], self.game.tilemap.layers[0][r][c]
                    if t1 == -1: color = (15, 15, 15) 
                    elif t2 == 99: color = (0, 0, 255) 
                    elif 50 <= t2 <= 59: color = (255, 0, 0) 
                    elif t2 == 98: color = (255, 0, 255)
                    elif t2 == 70: color = (255, 215, 0)
                    elif t1 == 1: color = (100, 100, 100) 
                    elif t1 == 2: color = (0, 255, 255) 
                    elif t0 != 0: color = (50, 100, 50) 
                    if color: pygame.draw.rect(minimap_surf, color, (int(c * pixel_size), int(r * pixel_size), int(pixel_size)+1, int(pixel_size)+1))
                except: pass
                
        zoom = getattr(self.game.camera, 'zoom', 1.0)
        rect_x = int((self.game.camera.offset_x / self.game.tilemap.tile_size) * pixel_size)
        rect_y = int((self.game.camera.offset_y / self.game.tilemap.tile_size) * pixel_size)
        rect_w = int((((screen_w / zoom) / self.game.tilemap.tile_size) * pixel_size))
        rect_h = int((((screen_h / zoom) / self.game.tilemap.tile_size) * pixel_size))
        
        pygame.draw.rect(minimap_surf, (255, 0, 0), (rect_x, rect_y, rect_w, rect_h), max(1, int(pixel_size/2)))
        screen.blit(minimap_surf, (mm_x, mm_y))
        pygame.draw.rect(screen, (255, 255, 255), (mm_x, mm_y, map_w, map_h), 2)

    def draw_ui(self, screen):
        font = pygame.font.SysFont(None, 24)
        screen_w, screen_h = screen.get_size()

        # Instructions
        inst_font = pygame.font.SysFont(None, 22)
        inst_text = inst_font.render("L-Click: Draw | R-Click: Erase | ALT: Pipette | Scroll: Zoom | 'O': Save | 'P': Load", True, (200, 200, 200))
        screen.blit(inst_text, (10, 10))

        # MAP RESIZER
        pygame.draw.rect(screen, (30, 30, 30), (10, 35, 150, 60), border_radius=8)
        pygame.draw.rect(screen, (100, 100, 100), (10, 35, 150, 60), width=1, border_radius=8)
        
        w_text = font.render(f"W: {self.game.tilemap.width}", True, (255, 255, 255))
        screen.blit(w_text, (20, 42))
        pygame.draw.rect(screen, (80, 50, 50), (70, 40, 20, 20), border_radius=4) 
        pygame.draw.rect(screen, (50, 80, 50), (130, 40, 20, 20), border_radius=4) 
        screen.blit(font.render("-", True, (255,255,255)), (76, 42))
        screen.blit(font.render("+", True, (255,255,255)), (134, 42))

        h_text = font.render(f"H: {self.game.tilemap.height}", True, (255, 255, 255))
        screen.blit(h_text, (20, 72))
        pygame.draw.rect(screen, (80, 50, 50), (70, 70, 20, 20), border_radius=4) 
        pygame.draw.rect(screen, (50, 80, 50), (130, 70, 20, 20), border_radius=4) 
        screen.blit(font.render("-", True, (255,255,255)), (76, 72))
        screen.blit(font.render("+", True, (255,255,255)), (134, 72))

        # Draw Minimap from Editor 3
        self._draw_minimap(screen, screen_w, screen_h)

        # PLAYTEST BUTTON
        play_btn_rect = pygame.Rect(screen_w - 140, 230, 120, 40)
        pygame.draw.rect(screen, (50, 200, 50), play_btn_rect, border_radius=5)
        play_text = font.render("▶ TEST LEVEL", True, (255, 255, 255))
        screen.blit(play_text, (play_btn_rect.x + 10, play_btn_rect.y + 12))

        # SLEEK FLOATING PALETTE TOOLBAR
        toolbar_w = len(self.palette) * self.button_width
        toolbar_x = (screen_w - toolbar_w) // 2
        toolbar_y = screen_h - self.toolbar_height - 20 
        
        panel = pygame.Surface((toolbar_w, self.toolbar_height), pygame.SRCALPHA)
        pygame.draw.rect(panel, (20, 20, 25, 230), (0, 0, toolbar_w, self.toolbar_height), border_radius=15)
        pygame.draw.rect(panel, (100, 100, 120, 150), (0, 0, toolbar_w, self.toolbar_height), width=2, border_radius=15)
        screen.blit(panel, (toolbar_x, toolbar_y))
        
        for i, (t_id, (name, color)) in enumerate(self.palette.items()):
            btn_x = toolbar_x + (i * self.button_width)
            
            is_active = (t_id == self.active_id) or (t_id == 50 and 50 <= self.active_id <= 59)
            
            if is_active:
                highlight = pygame.Surface((self.button_width, self.toolbar_height), pygame.SRCALPHA)
                pygame.draw.rect(highlight, (80, 80, 100, 150), (0, 0, self.button_width, self.toolbar_height), border_radius=12)
                screen.blit(highlight, (btn_x, toolbar_y))
            
            pygame.draw.rect(screen, color, (btn_x + 30, toolbar_y + 15, 40, 20), border_radius=8)
            pygame.draw.rect(screen, (200, 200, 200), (btn_x + 30, toolbar_y + 15, 40, 20), 1, border_radius=8)
            text = font.render(name, True, (240, 240, 255))
            screen.blit(text, (btn_x + (self.button_width - text.get_width())//2, toolbar_y + 45))
            
            if i < len(self.palette) - 1:
                pygame.draw.line(screen, (70, 70, 80), (btn_x + self.button_width, toolbar_y + 15), (btn_x + self.button_width, toolbar_y + self.toolbar_height - 15))

        # ENEMY SUBMENU POPUP
        if 50 <= self.active_id <= 59:
            sub_w = 120
            sub_h = len(self.enemy_palette) * 40
            enemy_btn_idx = list(self.palette.keys()).index(50)
            sub_x = toolbar_x + (enemy_btn_idx * self.button_width)
            sub_y = toolbar_y - sub_h - 10
            
            sub_panel = pygame.Surface((sub_w, sub_h), pygame.SRCALPHA)
            pygame.draw.rect(sub_panel, (30, 30, 35, 240), (0, 0, sub_w, sub_h), border_radius=8)
            pygame.draw.rect(sub_panel, (150, 100, 100, 180), (0, 0, sub_w, sub_h), width=2, border_radius=8)
            screen.blit(sub_panel, (sub_x, sub_y))
            
            for j, (e_id, (e_name, e_color)) in enumerate(self.enemy_palette.items()):
                y_offset = sub_y + (j * 40)
                if e_id == self.active_id:
                    pygame.draw.rect(screen, (80, 50, 50), (sub_x, y_offset, sub_w, 40), border_radius=8)
                
                pygame.draw.rect(screen, e_color, (sub_x + 10, y_offset + 12, 16, 16), border_radius=4)
                e_text = font.render(e_name, True, (255, 255, 255))
                screen.blit(e_text, (sub_x + 35, y_offset + 12))

        # SAVE/LOAD MODALS
        if self.ui_state != "hidden":
            menu_w, menu_h = 400, 400
            menu_x = (screen_w - menu_w) // 2
            menu_y = (screen_h - menu_h) // 2
            overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            pygame.draw.rect(screen, (20, 20, 20), (menu_x, menu_y, menu_w, menu_h), border_radius=10)
            pygame.draw.rect(screen, (200, 200, 200), (menu_x, menu_y, menu_w, menu_h), 2, border_radius=10)
            
            title_font = pygame.font.SysFont(None, 36)
            title = title_font.render(f"{self.ui_state.upper()} LEVEL", True, (255, 255, 0))
            screen.blit(title, (menu_x + 20, menu_y + 15))
            
            if self.ui_state == "save":
                prompt = font.render("Type filename and press Enter:", True, (200, 200, 200))
                screen.blit(prompt, (menu_x + 20, menu_y + 60))
                pygame.draw.rect(screen, (10, 10, 10), (menu_x + 20, menu_y + 90, menu_w - 40, 40))
                cursor = "_" if (pygame.time.get_ticks() // 500) % 2 == 0 else ""
                text_surf = title_font.render(self.input_text + cursor, True, (255, 255, 255))
                screen.blit(text_surf, (menu_x + 30, menu_y + 100))
                
            elif self.ui_state == "load":
                prompt = font.render("Click a file to load:", True, (200, 200, 200))
                screen.blit(prompt, (menu_x + 20, menu_y + 60))
                for i, file_name in enumerate(self.file_list):
                    text_y = menu_y + 90 + (i * 35)
                    if menu_x <= pygame.mouse.get_pos()[0] <= menu_x + menu_w:
                        if text_y - 5 <= pygame.mouse.get_pos()[1] < text_y + 30:
                            pygame.draw.rect(screen, (60, 60, 60), (menu_x + 20, text_y - 5, menu_w - 40, 30))
                    f_text = font.render(file_name, True, (255, 255, 255))
                    screen.blit(f_text, (menu_x + 30, text_y))