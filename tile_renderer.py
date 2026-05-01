import pygame
from typing import Dict
from fragment_of_society.rendering.sprite import SpriteLoader

class TileRenderer:
    def __init__(self, tile_size: int):
        self.tile_size = tile_size
        self.scaled_cache: Dict[int, pygame.Surface] = {}
        
        self.tile_mapping = {
            0: "floor",
            1: "wall",
            2: "forcefield"
        }

    def _get_texture(self, tile_id: int) -> pygame.Surface | None:
        """Fetches the sprite and scales it perfectly to the tile size."""
        if tile_id in self.scaled_cache:
            return self.scaled_cache[tile_id]
            
        if tile_id in self.tile_mapping:
            sprite_key = self.tile_mapping[tile_id]
            sprite = SpriteLoader.load(sprite_key)
            
            if sprite and sprite.texture:
                scaled = pygame.transform.scale(sprite.texture, (self.tile_size, self.tile_size))
                self.scaled_cache[tile_id] = scaled
                return scaled
            else:
                print(f"DEBUG: I am looking for '{sprite_key}.png' inside: {SpriteLoader.get_assets_path()}")
                
        return None

    def render(self, surface: pygame.Surface, tile_id: int, screen_x: float, screen_y: float):
        """Draws the tile, falling back to colored squares if the image is missing."""
        texture = self._get_texture(tile_id)
        
        if texture:
            surface.blit(texture, (screen_x, screen_y))
            return

        if tile_id == 1:
            pygame.draw.rect(surface, (50, 50, 50), (screen_x, screen_y, self.tile_size, self.tile_size))
        elif tile_id == 2: 
            pygame.draw.rect(surface, (0, 255, 255), (screen_x, screen_y, self.tile_size, self.tile_size))
        elif tile_id == 0:
            pygame.draw.rect(surface, (100, 200, 100), (screen_x, screen_y, self.tile_size, self.tile_size))