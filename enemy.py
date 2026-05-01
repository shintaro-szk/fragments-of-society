import pygame
import os
from fragment_of_society.entities.base import Entity
from fragment_of_society.components import Hitbox

# --- ANIMATION HELPERS ---

def load_sprite_sheet(sheet_path, frame_width, frame_height, scale=1.0):
    full_path = os.path.join("fragment_of_society", "rendering", "assets", sheet_path)
    sheet = pygame.image.load(full_path).convert_alpha()
    sheet_width, _ = sheet.get_size()
    frames = []
    
    for x in range(0, sheet_width, frame_width):
        frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
        frame.blit(sheet, (0, 0), (x, 0, frame_width, frame_height))
        
        if scale != 1.0:
            new_size = (int(frame_width * scale), int(frame_height * scale))
            frame = pygame.transform.scale(frame, new_size)
        frames.append(frame)
    return frames

def load_folder_frames(filenames, scale=1.0):
    frames = []
    for name in filenames:
        full_path = os.path.join("fragment_of_society", "rendering", "assets", name)
        img = pygame.image.load(full_path).convert_alpha()
        
        if scale != 1.0:
            w, h = img.get_size()
            img = pygame.transform.scale(img, (int(w * scale), int(h * scale)))
        frames.append(img)
    return frames

# --- BASE ENEMY CLASS ---

class Enemy(Entity):
    def __init__(self, x, y, target):
        super().__init__(x=x, y=y, sprite_key="enemy") 
        self.target = target
        self.base_speed = 100
        self.hp = 30
        self.is_dead = False 

    def take_damage(self, amount: int):
        """Standard damage method expected by the collision logic."""
        self.hp -= amount
        if self.hp <= 0:
            self.is_dead = True

    def update(self, dt):
        # Follow Logic[cite: 9]
        dx = self.target.x - self.x
        dy = self.target.y - self.y
        dist = (dx**2 + dy**2)**0.5
        
        # Use the official setter from base.py[cite: 10]
        if dist > 0:
            self.set_movement(dx / dist, dy / dist)
        else:
            self.set_movement(0.0, 0.0)
            
        super().update(dt)

# --- SPECIALIZED ANIMATED ENEMIES ---

class Slime(Enemy):
    def __init__(self, x, y, target):
        super().__init__(x, y, target)
        scale = 1.5  # Increased visibility[cite: 9]
        self.animation_frames = {
            "idle": load_sprite_sheet("slime_idle.png", 32, 32, scale=scale),
            "move": load_sprite_sheet("slime_run.png", 32, 32, scale=scale),
            "die":  load_sprite_sheet("slime_die.png", 32, 32, scale=scale)
        }
        self.state = "idle"
        self.frame_index = 0
        self.image = self.animation_frames[self.state][0]
        
        # Adjust Hitbox to match scale[cite: 9]
        self._hitbox_width = int(32 * scale)
        self._hitbox_height = int(32 * scale)
        self._hitbox = Hitbox(self.x, self.y, self._hitbox_width, self._hitbox_height)

    def update(self, dt):
        if self.movement_input[0] != 0 or self.movement_input[1] != 0:
            self.state = "move"
        else:
            self.state = "idle"

        super().update(dt)
        self.frame_index += 10 * dt
        if self.frame_index >= len(self.animation_frames[self.state]):
            self.frame_index = 0
        self.image = self.animation_frames[self.state][int(self.frame_index)]

class KingSlime(Enemy):
    def __init__(self, x, y, target):
        super().__init__(x=x, y=y, target=target)
        self.hp = 200
        self.base_speed = 50
        scale = 2.0  # Boss scale[cite: 9]
        
        self.animation_frames = {
            "idle": load_folder_frames(["KingSlime_Idle1.png", "KingSlime_Idle2.png", "KingSlime_Idle3.png", "KingSlime_Idle4.png"], scale=scale),
            "move": load_folder_frames(["KingSlime_Moving1.png", "KingSlime_Moving2.png", "KingSlime_Moving3.png"], scale=scale),
            "attack": load_folder_frames(["KingSlimeAttack1.png", "KingSlimeAttack2.png", "KingSlimeAttack3.png", "KingSlimeAttack4.png", "KingSlimeAttack5.png"], scale=scale)
        }
        self.state = "idle"
        self.frame_index = 0
        self.image = self.animation_frames[self.state][0]
        
        # Boss Hitbox[cite: 9]
        img_w, img_h = self.image.get_size()
        self._hitbox_width = img_w
        self._hitbox_height = img_h
        self._hitbox = Hitbox(self.x, self.y, self._hitbox_width, self._hitbox_height)

    def update(self, dt):
        super().update(dt)
        self.frame_index += 8 * dt
        if self.frame_index >= len(self.animation_frames[self.state]):
            self.frame_index = 0
            if self.state == "attack": self.state = "idle"
        self.image = self.animation_frames[self.state][int(self.frame_index)]