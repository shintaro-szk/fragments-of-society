import pygame
import math
import time
from fragment_of_society.entities.base import Entity

class Portal(Entity):
    def __init__(self, x: float, y: float, destination: str):
        super().__init__(x=x, y=y, sprite_key="portal")
        self.name = "Dimensional Portal"
        
        self.destination = destination
        
        self.color = (138, 43, 226) 
        self.radius = 40
        self.hitbox.width = 20
        self.hitbox.height = 20

    def draw(self, screen, camera_offset_x: float = 0, camera_offset_y: float = 0) -> None:
        self.camera_x = camera_offset_x
        self.camera_y = camera_offset_y
        
        px = int(self.x - camera_offset_x)
        py = int(self.y - camera_offset_y)
        
        # Use a sine wave based on time to create a breathing/pulsing effect
        pulse = math.sin(time.time() * 5) * 5
        
        # Draw outer glow
        pygame.draw.circle(screen, self.color, (px, py), int(self.radius + pulse))
        # Draw bright inner core
        pygame.draw.circle(screen, (255, 255, 255), (px, py), int(self.radius * 0.5 + pulse), 2)