# DRY Implementation Guide

This document outlines the DRY (Don't Repeat Yourself) violations found in the codebase and provides comprehensive fixes.

---

## Overview

| Category | Count |
|----------|-------|
| Duplicate rendering logic | 1 |
| Duplicate input handling | 3 |
| Duplicate hitbox/bounding box code | 6 |
| Duplicate skill handling patterns | 2 |
| Hardcoded values | 1 |
| Other duplicated patterns | 5 |
| **Total DRY Violations** | **18** |

---

## 1. Duplicate Rendering Logic

### Problem

Both `HitboxRenderer` and `DebugRenderer` have identical OBB/AABB rendering logic:

**hitbox_renderer.py:13-36**
```python
def render(self, hitbox, color, offset_x=0.0, offset_y=0.0):
    if isinstance(hitbox, OBB):
        self._render_obb(hitbox, color, offset_x, offset_y)
    else:
        x, y, width, height = hitbox.bounds
        rect = pygame.Rect(int(x - offset_x), int(y - offset_y), int(width), int(height))
        pygame.draw.rect(self._surface, color, rect, 1)

def _render_obb(self, obb, color, offset_x=0.0, offset_y=0.0):
    corners = obb.corners
    points = [(int(c.x - offset_x), int(c.y - offset_y)) for c in corners]
    pygame.draw.polygon(self._surface, color, points, 1)
```

**debug_renderer.py:17-28**
```python
def render_hitbox(self, hitbox, color):
    if isinstance(hitbox, OBB):
        self._render_obb(hitbox, color)
    elif isinstance(hitbox, AABB):
        x, y, width, height = hitbox.bounds
        rect = pygame.Rect(int(x), int(y), int(width), int(height))
        pygame.draw.rect(self._surface, color, rect, 1)

def _render_obb(self, obb, color):
    corners = obb.corners
    points = [(int(c.x), int(c.y)) for c in corners]
    pygame.draw.polygon(self._surface, color, points, 1)
```

### Solution

Create a shared utility module:

```python
# src/fragment_of_society/utils/hitbox_render.py

import pygame
from typing import Tuple

def render_aabb(surface, aabb, color, offset_x: float = 0, offset_y: float = 0):
    x, y, width, height = aabb.bounds
    rect = pygame.Rect(int(x - offset_x), int(y - offset_y), int(width), int(height))
    pygame.draw.rect(surface, color, rect, 1)

def render_obb(surface, obb, color, offset_x: float = 0, offset_y: float = 0):
    corners = obb.corners
    points = [(int(c.x - offset_x), int(c.y - offset_y)) for c in corners]
    pygame.draw.polygon(surface, color, points, 1)

def render_hitbox(surface, hitbox, color, offset_x: float = 0, offset_y: float = 0):
    from fragment_of_society.components.hitbox import OBB
    if isinstance(hitbox, OBB):
        render_obb(surface, hitbox, color, offset_x, offset_y)
    else:
        render_aabb(surface, hitbox, color, offset_x, offset_y)
```

Then simplify both renderers to use the utility:

```python
# In HitboxRenderer
def render(self, hitbox, color, offset_x=0.0, offset_y=0.0):
    from fragment_of_society.utils.hitbox_render import render_hitbox
    render_hitbox(self._surface, hitbox, color, offset_x, offset_y)

# In DebugRenderer
def render_hitbox(self, hitbox, color):
    from fragment_of_society.utils.hitbox_render import render_hitbox
    render_hitbox(self._surface, hitbox, color)
```

---

## 2. Duplicate Input State Initialization

### Problem

`KeyboardInput` and `MouseInput` have identical state initialization:

**input.py:85-88 (KeyboardInput)**
```python
self._pressed: Dict[GameAction, bool] = {a: False for a in GameAction}
self._just_pressed: Dict[GameAction, bool] = {a: False for a in GameAction}
```

**input.py:112-113 (MouseInput)**
```python
self._pressed: Dict[GameAction, bool] = {a: False for a in GameAction}
self._just_pressed: Dict[GameAction, bool] = {a: False for a in GameAction}
```

### Solution

Create a base class:

```python
# src/fragment_of_society/inputs/input_source.py

from abc import ABC, abstractmethod
from typing import Dict
from fragment_of_society.inputs.action import GameAction

class InputSource(ABC):
    def __init__(self):
        self._pressed: Dict[GameAction, bool] = {a: False for a in GameAction}
        self._just_pressed: Dict[GameAction, bool] = {a: False for a in GameAction}

    def _clear_just_pressed(self):
        self._just_pressed = {a: False for a in GameAction}

    @abstractmethod
    def update(self, dt: float):
        pass

    def is_action_pressed(self, action: GameAction) -> bool:
        return self._pressed.get(action, False)

    def is_action_just_pressed(self, action: GameAction) -> bool:
        return self._just_pressed.get(action, False)
```

Then simplify the subclasses:

```python
# In KeyboardInput
class KeyboardInput(InputSource):
    def __init__(self):
        super().__init__()
        # keyboard-specific init
        
    def update(self, dt: float):
        self._clear_just_pressed()
        # keyboard-specific update logic

# In MouseInput
class MouseInput(InputSource):
    def __init__(self):
        super().__init__()
        # mouse-specific init
        
    def update(self, dt: float):
        self._clear_just_pressed()
        # mouse-specific update logic
```

---

## 3. Duplicate BoundingBox Properties (AABB & OBB)

### Problem

`AABB` and `OBB` classes in `hitbox.py` share 6+ identical properties/methods:

| Property/Method | AABB Location | OBB Location |
|-----------------|---------------|--------------|
| `center` | lines 106-110 | lines 186-190 |
| `center_vector` | lines 113-115 | lines 193-195 |
| `offset` | lines 117-119 | lines 198-199 |
| `update_position` | lines 121-123 | lines 233-235 |
| `update_center` | lines 125-127 | lines 237-239 |
| `to_dict` | lines 135-144 | lines 264-274 |
| `from_dict` | lines 146-155 | lines 276-286 |

### Solution

Create an abstract base class:

```python
# src/fragment_of_society/components/hitbox.py (add before AABB class)

from abc import ABC, abstractmethod
from typing import Tuple, Dict
from pymunk import Vec2

class BoundingBox(ABC):
    def __init__(self, x: float, y: float, width: float, height: float, offset_x: float = 0, offset_y: float = 0):
        self.x = float(x)
        self.y = float(y)
        self.width = float(width)
        self.height = float(height)
        self.offset_x = float(offset_x)
        self.offset_y = float(offset_y)

    @property
    def center(self) -> Tuple[float, float]:
        return (
            self.x + self.width / 2 + self.offset_x,
            self.y + self.height / 2 + self.offset_y
        )

    @property
    def center_vector(self) -> Vec2:
        cx, cy = self.center
        return Vec2(cx, cy)

    @property
    def offset(self) -> Tuple[float, float]:
        return (self.offset_x, self.offset_y)

    def update_position(self, x: float, y: float):
        self.x = float(x)
        self.y = float(y)

    def update_center(self, cx: float, cy: float):
        self.x = float(cx - self.width / 2 - self.offset_x)
        self.y = float(cy - self.height / 2 - self.offset_y)

    def to_dict(self) -> dict:
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "offset_x": self.offset_x,
            "offset_y": self.offset_y,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            x=data["x"],
            y=data["y"],
            width=data["width"],
            height=data["height"],
            offset_x=data.get("offset_x", 0),
            offset_y=data.get("offset_y", 0),
        )
```

Then simplify `AABB` and `OBB`:

```python
class AABB(BoundingBox):
    def __init__(self, x: float, y: float, width: float, height: float, offset_x: float = 0, offset_y: float = 0):
        super().__init__(x, y, width, height, offset_x, offset_y)

    @property
    def bounds(self) -> Tuple[float, float, float, float]:
        return (self.x, self.y, self.width, self.height)

    def to_dict(self) -> dict:
        data = super().to_dict()
        data["type"] = "AABB"
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'AABB':
        return cls(
            x=data["x"],
            y=data["y"],
            width=data["width"],
            height=data["height"],
            offset_x=data.get("offset_x", 0),
            offset_y=data.get("offset_y", 0),
        )

class OBB(BoundingBox):
    def __init__(self, x: float, y: float, width: float, height: float, rotation: float = 0, offset_x: float = 0, offset_y: float = 0):
        super().__init__(x, y, width, height, offset_x, offset_y)
        self.rotation = float(rotation)

    @property
    def bounds(self) -> Tuple[float, float, float, float]:
        return self._calculate_bounds()

    @property
    def corners(self) -> List[Vec2]:
        # OBB-specific corner calculation
        pass

    def to_dict(self) -> dict:
        data = super().to_dict()
        data["type"] = "OBB"
        data["rotation"] = self.rotation
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'OBB':
        return cls(
            x=data["x"],
            y=data["y"],
            width=data["width"],
            height=data["height"],
            rotation=data.get("rotation", 0),
            offset_x=data.get("offset_x", 0),
            offset_y=data.get("offset_y", 0),
        )
```

---

## 4. Duplicate Skill Execution Pattern

### Problem

`PlayerController.handle_attacks()` has repeated code for each skill:

**player_controller.py:36-41 (basic attack)**
```python
if input_manager.is_action_just_pressed(GameAction.INTERACT):
    if self.character and self.character.basic_attack:
        attack_rotation = self.get_attack_rotation(input_manager, camera_offset)
        self._execute_skill(self.character.basic_attack, entities or [], attack_rotation)
```

**player_controller.py:67-70 (skill_1)**
```python
if input_manager.is_action_just_pressed(GameAction.SKILL_1):
    if self.character and self.character.first_skill:
        attack_rotation = self.get_attack_rotation(input_manager, camera_offset)
        self._execute_skill(self.character.first_skill, entities or [], attack_rotation)
```

### Solution

Refactor into a generic handler:

```python
# In PlayerController

SKILL_ACTION_MAP = {
    GameAction.INTERACT: 'basic_attack',
    GameAction.SKILL_1: 'first_skill',
    GameAction.SKILL_2: 'second_skill',
    GameAction.SKILL_3: 'third_skill',
    GameAction.SKILL_4: 'fourth_skill',
}

def handle_skills(self, input_manager, entities, camera_offset=(0, 0)):
    if not self.character:
        return
    
    for action, skill_attr in self.SKILL_ACTION_MAP.items():
        skill = getattr(self.character, skill_attr, None)
        if skill and input_manager.is_action_just_pressed(action):
            attack_rotation = self.get_attack_rotation(input_manager, camera_offset)
            self._execute_skill(skill, entities or [], attack_rotation)

def update_skills(self, dt: float):
    if not self.character:
        return
    
    skill_attrs = ['basic_attack', 'first_skill', 'second_skill', 'third_skill', 'fourth_skill']
    for skill_attr in skill_attrs:
        skill = getattr(self.character, skill_attr, None)
        if skill:
            skill.update(dt)
```

---

## 5. Hardcoded Base Speed

### Problem

`entity.py` has hardcoded `650` instead of using `self.base_speed`:

**entity.py:34**
```python
self.base_speed: float = 650
```

**entity.py:56**
```python
final_speed = 650 * (1 + self.stats.speed / 100)
```

### Solution

```python
# Line 56 in apply_movements method:
final_speed = self.base_speed * (1 + self.stats.speed / 100)
```

---

## 6. Duplicate Singleton Implementation

### Problem

`InputManager` has duplicate singleton code:

**input.py:141-145**
```python
def __new__(cls):
    if cls._instance is None:
        cls._instance = super().__new__(cls)
    return cls._instance
```

**input.py:210-214**
```python
@classmethod
def get_instance(cls):
    if cls._instance is None:
        cls._instance = cls()
    return cls._instance
```

### Solution

Remove one and use consistently:

```python
# Keep only __new__ or get_instance, not both
# Remove get_instance method and use InputManager() directly
# Or remove __new__ and keep get_instance as the factory method
```

---

## 7. Repeated Pass-through Properties

### Problem

`PersistentSkillEffect` has many pass-through properties:

**skills.py:107-125**
```python
@property
def alive_duration(self) -> float:
    return self.skill.alive_duration

@property
def tick_interval(self) -> float:
    return self.skill.tick_interval

@property
def tick_effect_type(self) -> TickEffectType:
    return self.skill.tick_effect_type

@property
def tick_value(self) -> float:
    return self.skill.tick_value

@property
def aoe_radius(self) -> float:
    return self.skill.aoe_radius
```

### Solution

Use `__getattr__`:

```python
def __getattr__(self, name: str):
    return getattr(self.skill, name)
```

Or use `__init_subclass__` for more explicit control.

---

## 8. Similar Dataclass Patterns

### Problem

`MageStats` and `PriestStats` follow the same pattern:

**stats.py:39-45**
```python
@dataclass
class MageStats(Stats):
    max_mp: int = 100

@dataclass
class PriestStats(Stats):
    max_holyp: int = 100
```

### Solution

Create a more flexible resource system:

```python
@dataclass
class Stats:
    health: int = 100
    
    def add_resource(self, resource_name: str, amount: int):
        if not hasattr(self, resource_name):
            setattr(self, resource_name, 0)
        current = getattr(self, resource_name)
        setattr(self, resource_name, current + amount)

# Then for specific classes:
@dataclass
class MageStats(Stats):
    max_mp: int = 100
    mp: int = 100
```

Or use composition:

```python
@dataclass
class Resource:
    name: str
    current: int
    max: int

@dataclass
class Stats:
    health: Resource
    resources: List[Resource] = field(default_factory=list)
```

---

## Priority Fix Order

| Priority | Issue | Files to Modify |
|----------|-------|-----------------|
| High | BoundingBox base class | `hitbox.py` |
| High | Skill execution refactor | `player_controller.py` |
| High | Hitbox render utility | `hitbox_render.py`, `hitbox_renderer.py`, `debug_renderer.py` |
| Medium | InputSource base class | `input.py`, `input_source.py` |
| Medium | Base speed fix | `entity.py` |
| Low | Singleton cleanup | `input.py` |
| Low | Pass-through properties | `skills.py` |
| Low | Resource system | `stats.py` |

---

## Migration Checklist

- [ ] Create `BoundingBox` base class in `hitbox.py`
- [ ] Refactor AABB and OBB to inherit from BoundingBox
- [ ] Create hitbox render utility module
- [ ] Update HitboxRenderer to use utility
- [ ] Update DebugRenderer to use utility
- [ ] Create InputSource base class
- [ ] Refactor KeyboardInput and MouseInput
- [ ] Refactor handle_attacks to use SKILL_ACTION_MAP
- [ ] Fix hardcoded base_speed in entity.py
- [ ] Clean up duplicate singleton in InputManager
- [ ] Optimize PersistentSkillEffect with __getattr__
- [ ] Consider resource system refactor
