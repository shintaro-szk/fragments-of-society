from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Optional, Any, List

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


@dataclass
class Sprite:
    name: str
    texture: Any
    width: int
    height: int


@dataclass
class Animation:
    name: str
    frame_keys: List[str]
    frame_duration: float = 0.1
    loop: bool = True


class AnimationController:
    def __init__(self, animations: Dict[str, Animation], default_state: str = "idle"):
        self.animations = animations
        self.current_state = default_state
        self.current_frame = 0
        self.timer = 0.0
        self.playing = True

    @property
    def current_animation(self) -> Optional[Animation]:
        return self.animations.get(self.current_state)

    @property
    def current_frame_key(self) -> Optional[str]:
        anim = self.current_animation
        if not anim or not anim.frame_keys:
            return None
        return anim.frame_keys[self.current_frame]

    def set_state(self, state: str) -> bool:
        if state not in self.animations:
            return False
        if state != self.current_state:
            self.current_state = state
            self.current_frame = 0
            self.timer = 0.0
        return True

    def update(self, dt: float) -> None:
        if not self.playing:
            return

        anim = self.current_animation
        if not anim or len(anim.frame_keys) <= 1:
            return

        self.timer += dt
        if self.timer >= anim.frame_duration:
            self.timer -= anim.frame_duration
            self.current_frame += 1

            if self.current_frame >= len(anim.frame_keys):
                if anim.loop:
                    self.current_frame = 0
                else:
                    self.current_frame = len(anim.frame_keys) - 1
                    self.playing = False

    def play(self) -> None:
        self.playing = True

    def pause(self) -> None:
        self.playing = False

    def reset(self) -> None:
        self.current_frame = 0
        self.timer = 0.0
        self.playing = True


class SpriteLoader:
    _cache: Dict[str, Sprite] = {}
    _initialized: bool = False

    @staticmethod
    def get_assets_path() -> Path:
        base_dir = Path(__file__).parent
        return base_dir / "assets"

    @staticmethod
    def _ensure_initialized() -> None:
        if not SpriteLoader._initialized:
            assets_path = SpriteLoader.get_assets_path()
            if not assets_path.exists():
                assets_path.mkdir(parents=True, exist_ok=True)
            SpriteLoader._initialized = True

    @staticmethod
    def load(sprite_key: str) -> Optional[Sprite]:
        SpriteLoader._ensure_initialized()

        if sprite_key in SpriteLoader._cache:
            return SpriteLoader._cache[sprite_key]

        assets_dir = SpriteLoader.get_assets_path()

        sprite_path = assets_dir / f"{sprite_key}.png"
        if not sprite_path.exists():
            sprite_path = assets_dir / f"{sprite_key}.jpg"

        if not sprite_path.exists():
            sprite_path = assets_dir / f"{sprite_key}.jpeg"

        if not sprite_path.exists():
            return None

        if not PYGAME_AVAILABLE:
            return None

        from pygame import image

        try:
            texture = image.load(str(sprite_path))
            sprite = Sprite(
                name=sprite_key,
                texture=texture,
                width=texture.get_width(),
                height=texture.get_height()
            )
            SpriteLoader._cache[sprite_key] = sprite
            return sprite
        except Exception:
            return None
        
    @staticmethod
    def load_spritesheet(sheet_filename: str, frame_width: int, frame_height: int, animation_map: dict, scale_factor: float = 1.0) -> None:
        """
        Slices a spritesheet into individual frames, scaling them up if needed.
        """
        SpriteLoader._ensure_initialized()
        sheet_path = SpriteLoader.get_assets_path() / sheet_filename

        if not sheet_path.exists() or not PYGAME_AVAILABLE:
            print(f"Warning: Could not find spritesheet {sheet_path}")
            return

        from pygame import image, Surface, Rect, transform
        try:
            sheet = image.load(str(sheet_path)).convert_alpha()
            sheet_w, sheet_h = sheet.get_size()
            cols = sheet_w // frame_width

            for anim_name, frame_indices in animation_map.items():
                for i, frame_idx in enumerate(frame_indices):
                    row = frame_idx // cols
                    col = frame_idx % cols
                    
                    rect = Rect(col * frame_width, row * frame_height, frame_width, frame_height)
                    frame_surf = Surface((frame_width, frame_height), pygame.SRCALPHA)
                    frame_surf.blit(sheet, (0, 0), rect)
                    new_w = int(frame_width * scale_factor)
                    new_h = int(frame_height * scale_factor)
                    if scale_factor != 1.0:
                        frame_surf = transform.scale(frame_surf, (new_w, new_h))
                    
                    frame_key = f"{anim_name}_{i}"
                    SpriteLoader._cache[frame_key] = Sprite(
                        name=frame_key, texture=frame_surf, 
                        width=new_w, height=new_h
                    )
            print(f"Successfully sliced and scaled {sheet_filename}!")
        except Exception as e:
            print(f"Error slicing spritesheet: {e}")

    @staticmethod
    def preload(sprite_keys: list[str]) -> Dict[str, Sprite]:
        loaded = {}
        for key in sprite_keys:
            sprite = SpriteLoader.load(key)
            if sprite:
                loaded[key] = sprite
        return loaded

    @staticmethod
    def clear_cache() -> None:
        SpriteLoader._cache.clear()

    @staticmethod
    def exists(sprite_key: str) -> bool:
        assets_dir = SpriteLoader.get_assets_path()
        for ext in [".png", ".jpg", ".jpeg"]:
            if (assets_dir / f"{sprite_key}{ext}").exists():
                return True
        return False


class SpriteRenderer:
    def __init__(self):
        self._sprite_cache: Dict[str, Sprite] = {}

    def get_sprite(self, key: str) -> Optional[Sprite]:
        if key in self._sprite_cache:
            return self._sprite_cache[key]

        sprite = SpriteLoader.load(key)
        if sprite:
            self._sprite_cache[key] = sprite
        return sprite

    def render(self, surface: Any, entity: Any, camera_offset: tuple[float, float] = (0, 0)) -> None:
        if not PYGAME_AVAILABLE:
            return

        from pygame import transform

        sprite = self.get_sprite(entity.sprite_key)
        if not sprite:
            return

        screen_x = entity.x - camera_offset[0]
        screen_y = entity.y - camera_offset[1]

        rotated = transform.rotate(sprite.texture, entity.rotation)
        rect = rotated.get_rect(center=(screen_x, screen_y))

        surface.blit(rotated, rect)

    def render_frame(self, surface: Any, frame_key: str, x: float, y: float,
                     rotation: float = 0, camera_offset: tuple[float, float] = (0, 0)) -> None:
        if not PYGAME_AVAILABLE:
            return

        from pygame import transform

        sprite = self.get_sprite(frame_key)
        if not sprite:
            return

        screen_x = x - camera_offset[0]
        screen_y = y - camera_offset[1]

        rotated = transform.rotate(sprite.texture, rotation)
        rect = rotated.get_rect(center=(screen_x, screen_y))

        surface.blit(rotated, rect)

    def clear_cache(self) -> None:
        self._sprite_cache.clear()