# Fragment of Society - Documentation

## Quick Links

- [Systems Documentation](./Systems/OVERVIEW.md) - Architecture and how-to guides
- [Input System](./Systems/INPUT.md) - Keyboard and mouse input
- [Entity System](./Systems/ENTITY.md) - Entities, characters, controllers
- [Game Engine](./Systems/GAMEENGINE.md) - Core game logic for RL

---

## Project Overview

**Fragment of Society** is a 2D top-down dungeon crawler built with Python/Pygame. Designed for both human playability and RL training.

### Architecture

```
┌─────────────────────┐     ┌─────────────────────┐
│   Game (Pygame)     │────▶│   GameEngine        │
│  (Window, Render)   │     │  (Pure Python)      │
└─────────────────────┘     └─────────────────────┘
         │                          │
         ▼                          ▼
┌─────────────────────┐     ┌─────────────────────┐
│   Renderers         │     │   Player/Entities   │
│  Camera, Debug      │     │  Generic Character  │
└─────────────────────┘     └─────────────────────┘
         │
         ▼
┌─────────────────────┐     ┌─────────────────────┐
│   Components        │     │   Inputs            │
│  Stats, Hitbox     │     │  InputManager       │
└─────────────────────┘     └─────────────────────┘
```

- **Game** - Pygame layer (window, rendering, input handling)
- **GameEngine** - Pure Python game logic (RL-friendly)
- **PlayerController** - Player input handling and state
- **Generic** - Base character class with movement, stats, hitbox
- **Renderers** - Camera, debug rendering, hitbox visualization
- **Components** - Stats, Hitbox (ECS-style component system)
- **Inputs** - InputManager for keyboard/mouse handling

---

## Key Features

| Feature | Status |
|---------|--------|
| Entity System | ✅ Done |
| Character System | ✅ Done |
| Player Account & Controller | ✅ Done |
| Input System (Keyboard/Mouse) | ✅ Done |
| Game Engine (RL-ready) | ✅ Done |
| Renderer | ✅ Done |
| Camera System | ✅ Done |
| Skills System | ✅ Done |
| Attack System | ✅ Done |

---

## Planned Features

| Feature | Status |
|---------|--------|
| Enemy AI | 🔲 TODO |
| Map/Level System | 🔲 TODO |
| UI System | 🔲 TODO |
| Sprite Renderer | 🔲 TODO |

---

## For RL Developers

```python
from fragment_of_society.game_engine import GameEngine
from fragment_of_society.inputs import InputManager

engine = GameEngine()
input_manager = InputManager.get_instance()

# Get state - entities, player stats, positions
state = engine.entities

# Update with input and delta time
engine.update(dt=0.016, camera_offset=(0, 0))
```

See [GameEngine](./Systems/GAMEENGINE.md) for full RL integration guide.

---

## Running the Game

```bash
cd src
python -m fragment_of_society.main
```

Or:

```bash
python src/fragment_of_society/main.py
```

---

## GitHub

[Repository](https://github.com/aaronmfs/team-sanction)
