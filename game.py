import pygame

from fragment_of_society.core import config
from fragment_of_society.entities import Player, Enemy, Portal
from fragment_of_society.world.tile_map import TileMap
from fragment_of_society.rendering import Camera, HitboxRenderer, TileRenderer
from fragment_of_society.inputs import InputManager, GameAction
from fragment_of_society.components import Collision
from fragment_of_society.tools.editor import LevelEditor

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        pygame.display.set_caption("Fragment of Society")
        self.clock = pygame.time.Clock()

        from fragment_of_society.rendering.sprite import SpriteLoader
        
        self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        # ... (rest of your init)

        # Core Systems
        self.player = Player(x=200, y=200)
        self.player.base_speed = 300 
        self.enemies = []
        self.portal = None
        self.tilemap = TileMap()
        self.tile_renderer = TileRenderer(self.tilemap.tile_size)
        self.camera = Camera(config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
        self.camera.follow(self.player)
        self.hitbox_renderer = HitboxRenderer(self.screen)        
        # Input
        self.input_manager = InputManager.get_instance()
        self.input_manager.map_key(pygame.K_TAB, GameAction.EDITOR_TOGGLE)
        self.input_manager.map_key(pygame.K_o, GameAction.EDITOR_SAVE)
        self.input_manager.map_key(pygame.K_p, GameAction.EDITOR_LOAD)

        # State
        self.running = True
        self.dt = 0.0
        self.ui_font = pygame.font.SysFont(None, 36)
        self.game_state = "PLAYING"
        self.stage_playlist = []
        self.current_level = "tutorial.json" 
        
        # Hook in the new Editor Module
        self.edit_mode = False
        self.level_editor = LevelEditor(self)
        self.editor = LevelEditor(self) 

        self.load_level(self.current_level)
        
        girl_animations = {
        "girl_idle_left": [0, 1, 2, 3],
        "girl_idle_right": [4, 5, 6, 7],
        "girl_walk_left": [8, 9, 10, 11, 12, 13],
        "girl_walk_right": [14, 15, 16, 17, 18, 19]
        }
        
        SpriteLoader.load_spritesheet("Girl-SheetV2.png", 24, 24, girl_animations, scale_factor=2.5)

        bow_animations = {"bow_shoot": [0, 1, 2, 3, 4, 5]}

        SpriteLoader.load_spritesheet("Bow.png", 48, 48, bow_animations, scale_factor=2.5)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            # Route events to the editor if active
            if self.edit_mode:
                if self.editor.handle_events(event):
                    continue

    def update(self):
        self.input_manager.update()
        
        if self.input_manager.is_action_just_pressed(GameAction.EDITOR_TOGGLE):
            self.edit_mode = not self.edit_mode

        if self.edit_mode:
            self.editor.update(self.dt)
            return

        # --- NORMAL GAMEPLAY LOGIC ---
        if self.game_state == "GAME_OVER":
            if pygame.key.get_pressed()[pygame.K_r]:
                self.player.hp = self.player.max_hp
                self.player.is_dead = False
                self.apply_map_spawns()
                self.game_state = "PLAYING"
            return 

        if self.game_state == "ROOM_CLEARED":
            if pygame.key.get_pressed()[pygame.K_RETURN]:
                self.apply_map_spawns()
                self.game_state = "PLAYING"
            return

        # Check for Temporary Buffs! (Tutorial logic)
        row, col = self.tilemap.world_to_tile(self.player.x, self.player.y)
        if 0 <= row < self.tilemap.height and 0 <= col < self.tilemap.width:
            if self.tilemap.layers[2][row][col] == 70:
                self.player.stats.attack += 10
                self.tilemap.layers[2][row][col] = 0
                print("Picked up temporary Attack Buff!")

        self.player.handle_input(self.input_manager)
        
        # Unlock forcefields if all enemies are dead
        doors_locked = len(self.enemies) > 0
        walls = self.tilemap.get_wall_hitboxes(doors_locked=doors_locked)

        self._move_and_collide(self.player, walls, self.dt)
        for enemy in self.enemies:
            self._move_and_collide(enemy, walls, self.dt)

        if self.player.attack_hitbox:
            for enemy in self.enemies:
                if enemy.id not in self.player.hit_targets and Collision.check_collision(self.player.attack_hitbox, enemy.hitbox):
                    enemy.take_damage(15) 
                    self.player.hit_targets.add(enemy.id) 
                    
        for proj in self.player.projectiles:
            for wall in walls:
                if Collision.check_collision(proj.hitbox, wall):
                    proj.alive = False
                    break
            
            if proj.alive:
                for enemy in self.enemies:
                    if Collision.check_collision(proj.hitbox, enemy.hitbox):
                        enemy.take_damage(proj.damage)
                        proj.alive = False
                        break
                        
        self.player.projectiles = [p for p in self.player.projectiles if p.alive]

        if not self.player.is_dead:
            for enemy in self.enemies:
                if Collision.check_collision(enemy.hitbox, self.player.hitbox):
                    self.player.take_damage(10) 
                    
        if self.player.is_dead:
            self.game_state = "GAME_OVER"

        self.player.update(self.dt)
        for enemy in self.enemies:
            enemy.update(self.dt)
            
        self.enemies = [e for e in self.enemies if not e.is_dead]

        if len(self.enemies) == 0 and self.portal is None and self.current_level != "hub.json":
            end_spawns = self.tilemap.get_entity_spawns(98)
            if end_spawns:
                dest = "hub.json" if self.current_level == "tutorial.json" else "NEXT_ROOM"
                self.portal = Portal(x=end_spawns[0][0], y=end_spawns[0][1], destination=dest)
                print(f"Level Clear! Portal opened to {dest}!")
                
        if self.portal:
            self.portal.hitbox.update_center(self.portal.x, self.portal.y)
            if Collision.check_collision(self.player.hitbox, self.portal.hitbox):
                dest = self.portal.destination
                if dest == "STAGE_1":
                    self.stage_playlist = ["stage1_1.json", "stage1_2.json", "stage1_3.json"]
                    self.load_level(self.stage_playlist.pop(0))
                elif dest == "NEXT_ROOM":
                    if len(self.stage_playlist) > 0:
                        self.load_level(self.stage_playlist.pop(0))
                    else:
                        self.load_level("hub.json")
                else:
                    self.load_level(dest)

        self.camera.update()

    def load_level(self, filename: str):
        self.current_level = filename
        try:
            self.tilemap.load(filename)
            print(f"Loaded Level: {filename}")
        except FileNotFoundError:
            print(f"Warning: {filename} not found! Loading default map.")
        self.apply_map_spawns()
        self.game_state = "PLAYING"

    def apply_map_spawns(self):
        player_spawns = self.tilemap.get_entity_spawns(99)
        if player_spawns:
            self.player.x, self.player.y = player_spawns[0]
            self.player.hitbox.update_center(self.player.x, self.player.y)
            
        from fragment_of_society.entities.enemy import Slime, KingSlime 

        self.enemies.clear() 

        # Spawn Slimes (ID 50)
        for ex, ey in self.tilemap.get_entity_spawns(50):
            self.enemies.append(Slime(x=ex, y=ey, target=self.player))

        # Spawn King Slime Boss (ID 53)
        for ex, ey in self.tilemap.get_entity_spawns(53):
            self.enemies.append(KingSlime(x=ex, y=ey, target=self.player))
            
        self.portal = None
            
        self.portal = None 
        if self.current_level == "hub.json":
            end_spawns = self.tilemap.get_entity_spawns(98)
            if end_spawns:
                self.portal = Portal(x=end_spawns[0][0], y=end_spawns[0][1], destination="STAGE_1")
            
    def _move_and_collide(self, entity, walls, dt):
        final_speed = entity.base_speed * (1 + getattr(entity, 'stats', type('obj', (object,), {'speed': 0})).speed / 100 if hasattr(entity, 'stats') else 1)
        dx = entity.movement_input[0] * final_speed * dt
        dy = entity.movement_input[1] * final_speed * dt

        entity.x += dx
        entity.hitbox.update_center(entity.x, entity.y)
        for wall in walls:
            if Collision.check_collision(entity.hitbox, wall):
                response = Collision.get_response(entity.hitbox, wall)
                if response:
                    entity.x += response.x
                    entity.hitbox.update_center(entity.x, entity.y)

        entity.y += dy
        entity.hitbox.update_center(entity.x, entity.y)
        for wall in walls:
            if Collision.check_collision(entity.hitbox, wall):
                response = Collision.get_response(entity.hitbox, wall)
                if response:
                    entity.y += response.y
                    entity.hitbox.update_center(entity.x, entity.y)

    def draw(self):
        zoom = getattr(self.camera, 'zoom', 1.0)
        cx, cy = self.camera.offset_x, self.camera.offset_y
        
        # Virtual Surface Setup
        if self.edit_mode and zoom != 1.0:
            view_w, view_h = int(config.SCREEN_WIDTH / zoom), int(config.SCREEN_HEIGHT / zoom)
            render_surf = pygame.Surface((view_w, view_h))
        else:
            render_surf = self.screen
            view_w, view_h = config.SCREEN_WIDTH, config.SCREEN_HEIGHT
            
        render_surf.fill((10, 10, 10))
        
        # Draw World
        self.tilemap.draw(render_surf, cx, cy, self.tile_renderer, self.edit_mode)
        
        for enemy in self.enemies:
            if hasattr(enemy, 'image'):
                render_surf.blit(enemy.image, (enemy.x - cx, enemy.y - cy))
            else:
                # Fallback for generic enemies without animation
                enemy.draw(render_surf, cx, cy)
                
        self.player.draw(render_surf, cx, cy)

        # Route drawing to Editor
        if self.edit_mode:
            self.editor.draw_world_overlays(render_surf, cx, cy, view_w, view_h)
                
        # Scale back to screen
        if render_surf != self.screen:
            self.screen.blit(pygame.transform.smoothscale(render_surf, (config.SCREEN_WIDTH, config.SCREEN_HEIGHT)), (0, 0))
            
        # UI Layer
        if self.edit_mode:
            self.editor.draw_ui(self.screen)
        
        # Game State Overlays
        if self.game_state == "GAME_OVER":
            overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((50, 0, 0, 180)) 
            self.screen.blit(overlay, (0, 0))
            self.screen.blit(self.ui_font.render("YOU DIED", True, (255, 50, 50)), (config.SCREEN_WIDTH//2 - 50, config.SCREEN_HEIGHT//2 - 20))
            self.screen.blit(self.ui_font.render("Press 'R' to Restart", True, (255, 255, 255)), (config.SCREEN_WIDTH//2 - 100, config.SCREEN_HEIGHT//2 + 20))

        elif self.game_state == "ROOM_CLEARED":
            overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 50, 0, 180)) 
            self.screen.blit(overlay, (0, 0))
            self.screen.blit(self.ui_font.render("ROOM CLEARED!", True, (50, 255, 50)), (config.SCREEN_WIDTH//2 - 100, config.SCREEN_HEIGHT//2 - 20))

        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.dt = self.clock.tick(60) / 1000
        pygame.quit()