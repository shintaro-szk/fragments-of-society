from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Stats:
    max_hp: int = 10
    attack: int = 10
    defence: int = 10
    speed: int = 10
    hp: int = field(init=False)

    def __post_init__(self):
        self.hp = self.max_hp

    def get_hp(self) -> int:
        return int(self.hp)

    def take_damage(self, amount: int) -> int:
        actual = min(amount - self.defence, self.hp)
        self.hp -= actual
        return actual

    def heal(self, amount: int) -> int:
        actual = min(amount, self.max_hp - self.hp)
        self.hp += actual
        return actual

    # def use_mp(self, cost: float) -> bool:
    #     if self.mp >= cost:
    #         self.mp -= cost
    #         return True
    #     return False

    def is_alive(self) -> bool:
        return self.get_hp() > 0


@dataclass
class MageStats(Stats):
    max_mp: int = 100

@dataclass
class PriestStats(Stats):
    max_holyp: int = 100



# @dataclass
# class WarriorStats(CharacterStats):
#     def __init__(self, position: Tuple[float, float] = (0, 0)):
#         super().__init__(
#             hp=150, max_hp=150, mp=50, max_mp=50,
#             position=position, speed=3.0,
#             class_type=CharacterClass.WARRIOR,
#             class_stats={"strength": 10, "armor": 5, "rage": 0}
#         )
#
#     @property
#     def strength(self) -> float:
#         return self.class_stats["strength"]
#
#     @property
#     def armor(self) -> float:
#         return self.class_stats["armor"]
#
#     @property
#     def rage(self) -> float:
#         return self.class_stats["rage"]
#
#     def add_rage(self, amount: float):
#         self.class_stats["rage"] = min(100, self.class_stats["rage"] + amount)
#
#
# @dataclass
# class MageStats(CharacterStats):
#     def __init__(self, position: Tuple[float, float] = (0, 0)):
#         super().__init__(
#             hp=80, max_hp=80, mp=150, max_mp=150,
#             position=position, speed=2.5,
#             class_type=CharacterClass.MAGE,
#             class_stats={"intelligence": 12, "mana_regen": 2, "spell_power": 15}
#         )
#
#     @property
#     def intelligence(self) -> float:
#         return self.class_stats["intelligence"]
#
#     @property
#     def mana_regen(self) -> float:
#         return self.class_stats["mana_regen"]
#
#     @property
#     def spell_power(self) -> float:
#         return self.class_stats["spell_power"]
#
#     def update(self, dt: float):
#         self.mp = min(self.max_mp, self.mp + self.mana_regen * dt)
#
#
# @dataclass
# class PriestStats(CharacterStats):
#     def __init__(self, position: Tuple[float, float] = (0, 0)):
#         super().__init__(
#             hp=100, max_hp=100, mp=120, max_mp=120,
#             position=position, speed=2.5,
#             class_type=CharacterClass.PRIEST,
#             class_stats={"faith": 10, "healing_power": 8, "spirit": 5}
#         )
#
#     @property
#     def faith(self) -> float:
#         return self.class_stats["faith"]
#
#     @property
#     def healing_power(self) -> float:
#         return self.class_stats["healing_power"]
#
#     @property
#     def spirit(self) -> float:
#         return self.class_stats["spirit"]
#
#     def update(self, dt: float):
#         self.mp = min(self.max_mp, self.mp + self.spirit * dt)
