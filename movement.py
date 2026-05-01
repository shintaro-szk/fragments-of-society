from typing import Tuple

class MovementMixin:
    @staticmethod
    def get_movement_vector(up: bool, down: bool, left: bool, right: bool) -> Tuple[float, float]:
        x = 0.0
        y = 0.0
        if up:
            y -= 1
        if down:
            y += 1
        if left:
            x -= 1
        if right:
            x += 1

        length = (x * x + y * y) ** 0.5
        if length > 0:
            x /= length
            y /= length
        return (x, y)
