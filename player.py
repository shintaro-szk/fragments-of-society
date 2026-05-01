import math
from typing import Optional, TYPE_CHECKING

import pygame

from fragment_of_society.entities.base import Entity
from fragment_of_society.entities.characters.generic import Archer 
from fragment_of_society.entities.states import StateMachine
from fragment_of_society.inputs import InputManager, GameAction
from fragment_of_society.rendering import SpriteRenderer

if TYPE_CHECKING:
    from fragment_of_society.components.skills import Skill

class Player(Entity):
    def __init__(self, x: float = 0, y: float = 0) -> None:
        char = Archer(x, y)
        super().__init__(
            x=char.x,
            y=char.y,
            stats=char.stats,
            sprite_key=char.sprite_key,
            animations=char.animations
        )
        self.name = char.name
        self.basic_attack = char.basic_attack
        self.invincibility_timer = 0.0
        self.facing = "left"
        self.projectiles = []         
        self.attack_rotation = 0.0

        self.color = (255, 0, 0)
        self.radius = 40

        self.state_machine = StateMachine(self, self.animations, "idle_left")
        self.sprite_renderer = SpriteRenderer()
        self._animation_frame = 0
        self._animation_timer = 0.0
        self._frame_duration = 0.1
        self.persistent_effects: list = []
        self.hit_targets: set = set()
        self.max_hp = 100
        self.hp = self.max_hp
        self.is_dead = False
        self.invincibility_timer = 0.0
        self.facing = "left"

    def handle_input(self, input_manager: InputManager) -> None:
        x, y = 0.0, 0.0
        if input_manager.is_action_pressed(GameAction.MOVE_UP):
            y -= 1
        if input_manager.is_action_pressed(GameAction.MOVE_DOWN):
            y += 1
        if input_manager.is_action_pressed(GameAction.MOVE_LEFT):
            x -= 1
            self.facing = "left"  
        if input_manager.is_action_pressed(GameAction.MOVE_RIGHT):
            x += 1
            self.facing = "right" 

        length = (x * x + y * y) ** 0.5
        if length > 0:
            x /= length
            y /= length

        self.set_movement(x, y)

        if input_manager.is_action_just_pressed(GameAction.INTERACT):
            mouse_pos = input_manager.get_mouse_position()
            self._handle_attack(mouse_pos)

        if input_manager.is_action_just_pressed(GameAction.SKILL_1):
            self._handle_skill(getattr(self, 'first_skill', None), "skill1_timer", "skill1")
        if input_manager.is_action_just_pressed(GameAction.SKILL_2):
            self._handle_skill(getattr(self, 'second_skill', None), "skill2_timer", "skill2")
        if input_manager.is_action_just_pressed(GameAction.SKILL_3):
            self._handle_skill(getattr(self, 'third_skill', None), "skill3_timer", "skill3")

    def _handle_attack(self, mouse_pos: tuple[int, int]) -> None:
        if not self.basic_attack or not self.basic_attack.can_use(self):
            return

        dx = mouse_pos[0] - (self.x - getattr(self, 'camera_x', 0))
        dy = mouse_pos[1] - (self.y - getattr(self, 'camera_y', 0))
        self.attack_rotation = math.atan2(dy, dx)

        self._execute_skill(self.basic_attack, self.attack_rotation, "attack")
        
        self.attack_hitbox = None 
        self.attack_hitbox_timer = 0.15 # Keep the timer so the bow animation plays
        
        from fragment_of_society.entities.projectile import Projectile
        arrow = Projectile(self.x, self.y, self.attack_rotation, speed=800, damage=15.0)
        self.projectiles.append(arrow)

    def _handle_skill(self, skill: Optional["Skill"], timer_attr: str, state_key: str) -> None:
        if not skill or not skill.can_use(self):
            return

        self._execute_skill(skill, state_key=state_key)
        setattr(self, timer_attr, 0.3)

    def _execute_skill(self, skill: "Skill", attack_rotation: float = None, state_key: str = "attack") -> None:
        if not skill.can_use(self):
            return

        rotation = attack_rotation if attack_rotation is not None else self.rotation
        if self.state_machine:
            target_state = f"{state_key}_{self.facing}"
            if self.state_machine.current != target_state:
                self._animation_frame = 0 
            self.state_machine.set_state(target_state)

        skill.use(self, [])

        if getattr(skill, 'has_attack_hitbox', False):
            self.attack_hitbox = skill.create_attack_hitbox(self.x, self.y, rotation)
            self.attack_hitbox_timer = 0.15
            self.hit_targets.clear()

        if getattr(skill, 'has_persistent_effect', False):
            effect = skill.create_persistent_effect(self, self.x, self.y)
            if effect:
                self.persistent_effects.append(effect)

    def take_damage(self, amount: float):
        if self.invincibility_timer > 0 or self.is_dead:
            return
            
        self.hp -= amount
        print(f"Player hit! HP: {self.hp}/{self.max_hp}")
        
        self.invincibility_timer = 1.0 
        
        if self.hp <= 0:
            self.hp = 0
            self.is_dead = True
            print("GAME OVER - Player has died!")

    def draw(self, screen, camera_offset_x: float = 0, camera_offset_y: float = 0) -> None:
        self.camera_x = camera_offset_x
        self.camera_y = camera_offset_y

        sprite_rendered = False

        if self.state_machine:
            animation_key = self.state_machine.animation_key
            frame_key = f"{animation_key}_{self._animation_frame}"
            sprite = self.sprite_renderer.get_sprite(frame_key)
            
            if sprite:
                self.sprite_renderer.render_frame(
                    screen,
                    frame_key,
                    self.x,
                    self.y,
                    self.rotation,
                    (camera_offset_x, camera_offset_y)
                )
                sprite_rendered = True
                
            if getattr(self, 'attack_hitbox_timer', 0) > 0:
                # Calculate which of the 6 frames to show based on the 0.15s timer
                progress = 1.0 - (self.attack_hitbox_timer / 0.15)
                frame_idx = min(5, int(progress * 6))
                angle_deg = -math.degrees(getattr(self, 'attack_rotation', 0)) + 90
                
                self.sprite_renderer.render_frame(
                    screen, 
                    f"bow_shoot_{frame_idx}", 
                    self.x, self.y, 
                    angle_deg, 
                    (camera_offset_x, camera_offset_y)
                )

        for p in self.projectiles:
            p.draw(screen, camera_offset_x, camera_offset_y, self.sprite_renderer)
                
        if self.invincibility_timer > 0:
            if int(self.invincibility_timer * 15) % 2 == 0:
                return

        if not sprite_rendered:
            px = int(self.x - camera_offset_x)
            py = int(self.y - camera_offset_y)
            pygame.draw.circle(screen, self.color, (px, py), self.radius)

        self._draw_hitbox(screen, camera_offset_x, camera_offset_y)
        self._draw_persistent_effects(screen, camera_offset_x, camera_offset_y)

    def _draw_persistent_effects(self, screen, camera_offset_x: float, camera_offset_y: float) -> None:
        for effect in self.persistent_effects:
            px = int(effect.x - effect.aoe_radius - camera_offset_x)
            py = int(effect.y - effect.aoe_radius - camera_offset_y)
            size = int(effect.aoe_radius * 2)
            pygame.draw.rect(screen, (255, 165, 0), (px, py, size, size), 2)

    def _draw_hitbox(self, screen, camera_offset_x: float, camera_offset_y: float) -> None:
        hb = self.hitbox
        x = int(hb.x - camera_offset_x)
        y = int(hb.y - camera_offset_y)
        w = int(hb.width)
        h = int(hb.height)
        pygame.draw.rect(screen, (0, 255, 0), (x, y, w, h), 1)

    def update(self, dt: float) -> None:
        super().update(dt)

        if self.invincibility_timer > 0:
            self.invincibility_timer -= dt
            
        if self.basic_attack:
            self.basic_attack.update(dt)
        if getattr(self, 'first_skill', None):
            self.first_skill.update(dt)
        if getattr(self, 'second_skill', None):
            self.second_skill.update(dt)
        if getattr(self, 'third_skill', None):
            self.third_skill.update(dt)

        self.persistent_effects = [e for e in self.persistent_effects if e.alive]
        for effect in self.persistent_effects:
            effect.update(dt, [])
            
        for p in self.projectiles:
            p.update(dt)

        if self.state_machine:
            self.state_machine.update(dt)

            self._animation_timer += dt
            if self._animation_timer >= self._frame_duration:
                self._animation_timer = 0.0
                
                current_state = self.state_machine.current if self.state_machine else "idle"
                max_frames = 6 if "walk" in current_state else 4
                self._animation_frame = (self._animation_frame + 1) % max_frames

            s1 = getattr(self, 'skill1_timer', 0)
            s2 = getattr(self, 'skill2_timer', 0)
            s3 = getattr(self, 'skill3_timer', 0)
            atk = getattr(self, 'attack_hitbox_timer', 0)
            
            if s1 <= 0 and s2 <= 0 and s3 <= 0 and atk <= 0:
                if self.movement_input[0] != 0 or self.movement_input[1] != 0:
                    base_state = "walk"
                else:
                    base_state = "idle"
                
                target_state = f"{base_state}_{self.facing}"
                if self.state_machine.current != target_state:
                    self._animation_frame = 0 
                    
                self.state_machine.set_state(target_state)