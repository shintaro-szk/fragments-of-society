import pygame
import json
from fragment_of_society.components.hitbox import Hitbox 

class TileMap:
    def __init__(self):
        self.tile_size = 64
        self.width = 6
        self.height = 5
        self.layers = [
            [[0 for _ in range(self.width)] for _ in range(self.height)] 
            for _ in range(3)
        ]
        self.labels = [] 
        
        # Build a temporary box on Layer 1 just so the default map isn't empty
        for r in range(self.height):
            for c in range(self.width):
                if r == 0 or r == self.height-1 or c == 0 or c == self.width-1:
                    self.layers[1][r][c] = 1

    def draw(self, screen, cam_x, cam_y, tile_renderer, edit_mode=False, active_layers=[True, True, True]):
        for layer_idx in range(3):
            if not active_layers[layer_idx]: # Skip if toggled off
                continue
            for row in range(self.height):
                for col in range(self.width):
                    tile = self.layers[layer_idx][row][col]
                    
                    # On layers 1 and 2, '0' just means transparent empty space
                    if layer_idx > 0 and tile == 0:
                        continue
                        
                    screen_x = col * self.tile_size - cam_x
                    screen_y = row * self.tile_size - cam_y
                    
                    # Draw the tile using our renderer
                    tile_renderer.render(screen, tile, screen_x, screen_y)
                    
                    # Draw Editor Overlays (Only draw once, so we do it on layer 2)
                    if edit_mode and layer_idx == 2:
                        pygame.draw.rect(screen, (255, 255, 0), (screen_x, screen_y, self.tile_size, self.tile_size), 1)
                        center_x, center_y = screen_x + self.tile_size // 2, screen_y + self.tile_size // 2
                        radius = self.tile_size // 3
                        
                        if tile == 99:
                            pygame.draw.circle(screen, (0, 0, 255), (center_x, center_y), radius)
                        elif tile == 50:
                            pygame.draw.circle(screen, (255, 0, 0), (center_x, center_y), radius)
                        elif tile == 98: 
                            pygame.draw.circle(screen, (255, 0, 255), (center_x, center_y), radius)
                            
    def flood_fill(self, start_row, start_col, fill_value):
        """Fills an enclosed area with the selected tile, respecting our Smart Layers."""
        if not (0 <= start_row < self.height and 0 <= start_col < self.width):
            return

        # 1. Figure out which layer we are targeting based on the brush
        target_layer = 0
        if fill_value in [1, 2]: target_layer = 1
        elif fill_value in [50, 98, 99]: target_layer = 2

        # 2. Get the tile we are trying to overwrite
        target_value = self.layers[target_layer][start_row][start_col]
        if target_value == fill_value:
            return

        # 3. The Iterative Flood Fill algorithm
        stack = [(start_row, start_col)]
        
        while stack:
            r, c = stack.pop()
            if 0 <= r < self.height and 0 <= c < self.width:
                if self.layers[target_layer][r][c] == target_value:
                    self.set_tile(r, c, fill_value)
                    # Add all 4 neighbors (Up, Down, Left, Right) to the stack
                    stack.append((r + 1, c))
                    stack.append((r - 1, c))
                    stack.append((r, c + 1))
                    stack.append((r, c - 1))

    def get_entity_spawns(self, entity_id: int):
        spawns = []
        for row in range(self.height):
            for col in range(self.width):
                if self.layers[2][row][col] == entity_id:
                    x = col * self.tile_size + self.tile_size // 2
                    y = row * self.tile_size + self.tile_size // 2
                    spawns.append((x, y))
        return spawns

    def get_wall_hitboxes(self, doors_locked=True):
        hitboxes = []
        for row in range(self.height):
            for col in range(self.width):
                tile = self.layers[1][row][col]
                is_wall = (tile == 1) or (tile == 2 and doors_locked)
                
                if is_wall:
                    x = col * self.tile_size
                    y = row * self.tile_size
                    hitboxes.append(Hitbox(x, y, self.tile_size, self.tile_size))
        return hitboxes

    def set_tile(self, row, col, value):
        """Smart Brush: Automatically puts the tile on the correct layer."""
        if 0 <= row < self.height and 0 <= col < self.width:
            if value == 0: 
                # ERASER: Wipes everything back to a base floor
                self.layers[0][row][col] = 0
                self.layers[1][row][col] = 0
                self.layers[2][row][col] = 0
            elif value in [1, 2]: 
                # ENVIRONMENT: Goes to Layer 1
                self.layers[1][row][col] = value
                # Optional: Ensure there is a floor underneath it on Layer 0!
                if self.layers[0][row][col] != 0:
                    self.layers[0][row][col] = 0 
            elif value in [50, 98, 99]: 
                # ENTITIES: Goes to Layer 2
                self.layers[2][row][col] = value
                # Ensure there is a floor underneath the spawn point
                if self.layers[0][row][col] != 0:
                    self.layers[0][row][col] = 0
    
    def world_to_tile(self, x, y):
        col = int(x // self.tile_size)
        row = int(y // self.tile_size)
        return row, col
    
    def save(self, filename="map.json"):
        data = {
            "layers": self.layers,
            "labels": self.labels
        }
        with open(filename, "w") as f:
            json.dump(data, f)

    def load(self, filename="map.json"):
        with open(filename, "r") as f:
            data = json.load(f)
            
            # Legacy Map Converter (Array-based)
            if isinstance(data, list):
                if not isinstance(data[0][0], list):
                    print(f"Upgrading 2D legacy map '{filename}'...")
                    self.height, self.width = len(data), len(data[0])
                    self.layers = [[[0 for _ in range(self.width)] for _ in range(self.height)] for _ in range(3)]
                    for r in range(self.height):
                        for c in range(self.width):
                            self.set_tile(r, c, data[r][c]) 
                else:
                    self.layers = data
                    self.height, self.width = len(self.layers[0]), len(self.layers[0][0])
                self.labels = [] # Initialize empty labels for old maps
            
            # New Map Format (Dict-based)
            elif isinstance(data, dict):
                self.layers = data.get("layers", self.layers)
                self.labels = data.get("labels", [])
                self.height, self.width = len(self.layers[0]), len(self.layers[0][0])

    def resize(self, new_width: int, new_height: int):
        new_layers = [[[0 for _ in range(new_width)] for _ in range(new_height)] for _ in range(3)]
        
        for layer_idx in range(3):
            for row in range(new_height):
                for col in range(new_width):
                    if row < self.height and col < self.width:
                        new_layers[layer_idx][row][col] = self.layers[layer_idx][row][col]
                        
        self.width = new_width
        self.height = new_height
        self.layers = new_layers