from __future__ import annotations
from typing import Any, Dict, Optional


class StateMachine:
    def __init__(self, owner: Any, states: Dict[str, str], initial: str) -> None:
        self.owner = owner
        self.states = states
        self.current = initial

    @property
    def animation_key(self) -> str:
        return self.states[self.current]

    def set_state(self, state: str) -> None:
        if state in self.states:
            self.current = state

    def update(self, dt: float) -> None:
        pass