import math
from fragment_of_society.components import Hitbox

class Projectile:
    def __init__(self, x: float, y: float, rotation: float, speed: float, damage: float):
        self.x = x
        self.y = y
        self.rotation = rotation
        self.speed = speed
        self.damage = damage
        self.sprite_key = "Arrow"
        
        self.hitbox = Hitbox(x, y, 24, 24)
        self.alive = True
        self.lifetime = 2.0

    def update(self, dt: float):
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False
        
        self.x += math.cos(self.rotation) * self.speed * dt
        self.y += math.sin(self.rotation) * self.speed * dt
        self.hitbox.update_center(self.x, self.y)

    def draw(self, screen, camera_x, camera_y, sprite_renderer):
        # Apply 2.5x rotation-based rendering offset or scale if supported by your renderer
        angle_deg = -math.degrees(self.rotation) - 90
        sprite_renderer.render_frame(screen, self.sprite_key, self.x, self.y, angle_deg, (camera_x, camera_y))