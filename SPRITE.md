# Sprite System Guide

Simple guide to using sprites, animations, and rendering in your game.

---

## Table of Contents
1. [Asset Organization](#asset-organization)
2. [Basic Sprite Loading](#basic-sprite-loading)
3. [Sprite Renderer](#sprite-renderer)
4. [Animation System](#animation-system)
5. [Entity Integration](#entity-integration)
6. [State Machine](#state-machine)
7. [Complete Example](#complete-example)

---

## Asset Organization

Put your sprite files in:
```
src/fragment_of_society/assets/
```

**Supported formats:** `.png`, `.jpg`, `.jpeg`

### File Naming

| Type | Example |
|------|---------|
| Single sprite | `player.png`, `goblin.png`, `tree.png` |
| Animation frames | `warrior_idle_0.png`, `warrior_idle_1.png`, `warrior_walk_0.png` |

---

## Basic Sprite Loading

### Quick Start

```python
from fragment_of_society.renderers import SpriteLoader

# Load a single sprite
sprite = SpriteLoader.load("player")

if sprite:
    print(f"Loaded: {sprite.name}, Size: {sprite.width}x{sprite.height}")
```

### Available Methods

```python
# Load sprite (returns None if not found)
sprite = SpriteLoader.load("my_sprite")

# Check if sprite exists without loading
exists = SpriteLoader.exists("my_sprite")  # True/False

# Preload multiple sprites (good for game startup)
sprites = SpriteLoader.preload(["player", "enemy", "tree"])

# Clear cache (rarely needed)
SpriteLoader.clear_cache()
```

---

## Sprite Renderer

The `SpriteRenderer` handles drawing sprites to the screen with rotation support.

### Setup

```python
from fragment_of_society.renderers import SpriteRenderer

renderer = SpriteRenderer()
```

### Rendering Methods

```python
# Render entity's base sprite (no animation)
renderer.render(surface, entity, camera_offset)

# Render a specific sprite at position
renderer.render_frame(
    surface=screen,
    frame_key="player_idle_0",
    x=100, y=200,
    rotation=45,  # degrees
    camera_offset=(0, 0)
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `surface` | pygame.Surface | Screen to draw on |
| `entity` | Entity | Entity with `.x`, `.y`, `.rotation` |
| `camera_offset` | tuple | Camera position `(x, y)` |
| `frame_key` | str | Sprite name to render |
| `x`, `y` | float | World position |
| `rotation` | float | Rotation in degrees |

---

## Animation System

### What is Animation?

An animation is a sequence of frames played over time.

```python
from fragment_of_society.renderers import Animation, AnimationController
```

### Creating an Animation

```python
# Simple animation with 3 frames
walk_anim = Animation(
    name="walk",
    frame_keys=["warrior_walk_0", "warrior_walk_1", "warrior_walk_2"],
    frame_duration=0.1,  # seconds per frame
    loop=True
)

# One-time animation (like attack)
attack_anim = Animation(
    name="attack",
    frame_keys=["warrior_attack_0", "warrior_attack_1", "warrior_attack_2"],
    frame_duration=0.15,
    loop=False  # stops at last frame
)
```

### AnimationController

Manages which animation is playing and advances frames.

```python
# Create controller with animations
animations = {
    "idle": Animation("idle", ["warrior_idle_0", "warrior_idle_1"], 0.2),
    "walk": Animation("walk", ["warrior_walk_0", "warrior_walk_1", "warrior_walk_2"], 0.1),
    "attack": Animation("attack", ["warrior_attack_0", "warrior_attack_1"], 0.15, loop=False)
}

controller = AnimationController(animations, default_state="idle")

# Change animation state
controller.set_state("walk")

# Update every frame (call in game loop)
controller.update(dt)  # dt = delta time in seconds

# Get current frame key for rendering
current_frame = controller.current_frame_key  # e.g., "warrior_walk_1"

# Control playback
controller.pause()
controller.play()
controller.reset()
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `current_state` | str | Current animation name |
| `current_frame` | int | Current frame index |
| `current_frame_key` | str | Current sprite key |
| `current_animation` | Animation | Animation object |
| `playing` | bool | Is animation playing? |

---

## Entity Integration

### Entity Fields

Every entity has these sprite-related fields:

```python
entity.sprite_key   # str: Base sprite name (e.g., "warrior")
entity.animations   # dict: {"idle": "warrior_idle", "walk": "warrior_walk"}
entity.entity_type  # EntityType: PLAYER, ENEMY, NPC, or OBJECT
```

### Setting Up a Character

In your character class (like `Generic`):

```python
class MyCharacter(Character):
    def __init__(self, x, y):
        stats = Stats(max_hp=100, attack=10, ...)
        
        # Define animations
        animations = {
            "idle": "knight_idle",
            "walk": "knight_walk",
            "attack": "knight_attack",
            "jump": "knight_jump"
        }
        
        # Pass to parent
        super().__init__(x, y, stats, sprite_key="knight", animations=animations)
```

### Updating Animation in Game Loop

```python
# In your game update
player = game.player

# Simple: change based on movement
if player.is_moving:
    player.animation_controller.set_state("walk")
else:
    player.animation_controller.set_state("idle")

# Update animation frame
player.animation_controller.update(dt)

# Get current frame to render
frame_key = player.animation_controller.current_frame_key
renderer.render_frame(screen, frame_key, player.x, player.y, player.rotation, camera.offset)
```

---

## Complete Example

### 1. Prepare Assets

```
assets/
├── warrior_idle_0.png
├── warrior_idle_1.png
├── warrior_walk_0.png
├── warrior_walk_1.png
├── warrior_walk_2.png
├── warrior_attack_0.png
├── warrior_attack_1.png
└── warrior.png
```

### 2. Character Class

```python
from fragment_of_society.entities import Entity, EntityType
from fragment_of_society.components import Stats
from fragment_of_society.renderers import Animation, AnimationController

class Warrior(Entity):
    def __init__(self, x, y):
        stats = Stats(max_hp=100, attack=15, defence=10, speed=10)
        
        animations = {
            "idle": Animation("idle", ["warrior_idle_0", "warrior_idle_1"], 0.2),
            "walk": Animation("walk", ["warrior_walk_0", "warrior_walk_1", "warrior_walk_2"], 0.1),
            "attack": Animation("attack", ["warrior_attack_0", "warrior_attack_1"], 0.15, loop=False)
        }
        
        super().__init__(x, y, stats, entity_type=EntityType.PLAYER, sprite_key="warrior", animations=animations)
        
        # Create animation controller
        self.animation_controller = AnimationController(animations, "idle")
```

### 3. Game Loop

```python
from fragment_of_society.renderers import SpriteRenderer

# Setup
renderer = SpriteRenderer()
player = Warrior(x=100, y=100)

# Game loop
running = True
while running:
    dt = clock.tick(60) / 1000  # delta time in seconds
    
    # Update player
    player.update(dt)
    
    # Update animation
    if player.is_attacking:
        player.animation_controller.set_state("attack")
    elif player.is_moving:
        player.animation_controller.set_state("walk")
    else:
        player.animation_controller.set_state("idle")
    
    player.animation_controller.update(dt)
    
    # Render
    screen.fill((50, 50, 50))
    
    frame_key = player.animation_controller.current_frame_key or player.sprite_key
    renderer.render_frame(screen, frame_key, player.x, player.y, player.rotation, camera.offset)
    
    pygame.display.flip()
```

---

## Troubleshooting

### Sprite not loading?
- Check file is in `assets/` folder
- Check filename matches (case-sensitive!)
- Use `SpriteLoader.exists("name")` to verify

### Animation not changing?
- Make sure to call `controller.set_state()` when state should change
- Non-looping animations stop automatically - call `controller.reset()` or `set_state()` to restart

### Rotation looks wrong?
- Rotation is in degrees
- pygame rotates counter-clockwise

### Entity showing wrong sprite?
- Check `entity.sprite_key` is set correctly
- Check `entity.animations` dict has correct keys

---

## Quick Reference

```python
# Load sprite
SpriteLoader.load("name")

# Check exists
SpriteLoader.exists("name")

# Create animation
Animation(name, [frames], duration, loop=True)

# Control animation
controller.set_state("idle")
controller.update(dt)
controller.current_frame_key

# Render
renderer.render(surface, entity, offset)
renderer.render_frame(surface, "sprite_name", x, y, rotation, offset)
```


## State Machine

Simple state machine that maps state names to animation keys.

### Quick Start

```python
from fragment_of_society.states import StateMachine

# Create state machine with states
state_machine = StateMachine(
    owner=self,  # the entity
    states={
        "idle": "warrior_idle",
        "walk": "warrior_walk",
        "attack": "warrior_attack",
    },
    initial="idle"
)

# Change state
state_machine.set_state("walk")

# Get current animation key
animation_key = state_machine.animation_key  # "warrior_walk"
```

### Methods

| Method | Description |
|--------|-------------|
| `set_state(name)` | Change to a new state |
| `update(dt)` | Update (can be extended) |
| `animation_key` | Current animation key |

### Integration with Entity

```python
from fragment_of_society.states import StateMachine

class MyCharacter(Character):
    def __init__(self, x, y):
        super().__init__(x, y)
        
        # Create state machine
        self.state_machine = StateMachine(
            owner=self,
            states={
                "idle": "knight_idle",
                "walk": "knight_walk",
                "attack": "knight_attack",
            },
            initial="idle"
        )
```

### Game Loop Example

```python
# In update loop
player = game.player
movement = player.movement_input

if movement != (0, 0):
    player.state_machine.set_state("walk")
else:
    player.state_machine.set_state("idle")

# For attack, change temporarily
if player.attacking:
    player.state_machine.set_state("attack")

# Update (Entity.update() calls this automatically)
player.update(dt)

# Get animation key for rendering
frame_key = player.state_machine.animation_key
```

### Using with AnimationController

Combine with `AnimationController` for full animation support:

```python
from fragment_of_society.states import StateMachine
from fragment_of_society.renderers import AnimationController, Animation

class Fighter(Character):
    def __init__(self, x, y):
        super().__init__(x, y)
        
        # Define animations
        animations = {
            "idle": Animation("idle", ["knight_idle_0", "knight_idle_1"], 0.2),
            "walk": Animation("walk", ["knight_walk_0", "knight_walk_1"], 0.1),
            "attack": Animation("attack", ["knight_attack_0", "knight_attack_1"], 0.15, loop=False)
        }
        
        self.animation_controller = AnimationController(animations, "idle")
        
        self.state_machine = StateMachine(
            owner=self,
            states={"idle": "idle", "walk": "walk", "attack": "attack"},
            initial="idle"
        )
    
    def update(self, dt):
        super().update(dt)
        
        # Update state machine -> animation controller
        self.animation_controller.set_state(self.state_machine.current)
        self.animation_controller.update(dt)
```


---

## See Also

- [TRELLO_TRACKER.md](./TRELLO_TRACKER.md) - Development progress
- [README.md](./README.md) - Project overview
