from __future__ import annotations

from typing import Tuple


class Camera:
    def __init__(self, screen_width: int, screen_height: int) -> None:
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.offset_x: float = 0.0
        self.offset_y: float = 0.0
        self.zoom = 1.0
        self.target = None

    def follow(self, target) -> None:
        self.target = target

    @property
    def offset(self) -> Tuple[float, float]:
        return (self.offset_x, self.offset_y)

    def update(self) -> None:
        if self.target is not None:
            self.offset_x = self.target.x - self.screen_width / 2
            self.offset_y = self.target.y - self.screen_height / 2

    def world_to_screen(self, x: float, y: float) -> Tuple[int, int]:
        return (int(x - self.offset_x), int(y - self.offset_y))

    def screen_to_world(self, screen_x: int, screen_y: int) -> Tuple[float, float]:
        return (screen_x + self.offset_x, screen_y + self.offset_y)