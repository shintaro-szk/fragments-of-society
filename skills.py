"""
Skills Module - Composable skill system for RPG games.
Framework-agnostic, works with any stats system.

Usage:
    from skills import SkillBuilder, SKILLS
    
    # Use pre-built skills
    player.skills = [SKILLS["strike"], SKILLS["fireball"]]
    
    # Or build custom skills
    custom = SkillBuilder.damage("Slash", 25, 10, 1.0, scaling_stat="strength")
    aoe = SkillBuilder.damage("Meteor", 50, 40, 5.0, scaling_stat="intelligence", aoe_radius=50)
    heal = SkillBuilder.heal("Heal", 30, 25, 3.0, scaling_stat="healing_power")
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Callable, Any, TYPE_CHECKING
from enum import Enum, auto
import math

if TYPE_CHECKING:
    from fragment_of_society.components.hitbox import OBB


class SkillType(Enum):
    DAMAGE = auto()
    HEAL = auto()
    BUFF = auto()
    DEBUFF = auto()
    SHIELD = auto()
    CUSTOM = auto()


class TargetType(Enum):
    SINGLE_ENEMY = auto()
    SINGLE_ALLY = auto()
    SELF = auto()
    AREA_ENEMY = auto()
    AREA_ALLY = auto()
    AREA_ALL = auto()


@dataclass
class SkillEffect:
    skill_type: SkillType
    base_value: float
    scaling_stat: Optional[str] = None
    scaling_factor: float = 1.0
    duration: float = 0
    stat_modifier: Optional[Dict[str, float]] = None
    on_apply: Optional[Callable] = None

    def apply(self, user: Any, target: Any) -> Tuple[float, float, List[str]]:
        value = self.base_value
        
        if self.scaling_stat and hasattr(user, self.scaling_stat):
            stat_value = getattr(user, self.scaling_stat)
            value *= (1 + stat_value / 100 * self.scaling_factor)
        
        if self.skill_type == SkillType.DAMAGE and hasattr(target, "take_damage"):
            actual = target.take_damage(value)
            return actual, 0, []
            
        elif self.skill_type == SkillType.HEAL and hasattr(target, "heal"):
            actual = target.heal(value)
            return 0, actual, []
            
        elif self.skill_type == SkillType.SHIELD:
            return 0, 0, [f"shield_{self.duration}s"]
            
        elif self.skill_type == SkillType.BUFF:
            return 0, 0, [f"buff_{self.duration}s"]
            
        elif self.skill_type == SkillType.DEBUFF:
            return 0, 0, [f"debuff_{self.duration}s"]
        
        if self.on_apply:
            self.on_apply(user, target, value)
        
        return 0, 0, []


class TickEffectType(Enum):
    DAMAGE = auto()
    HEAL = auto()


class PersistentSkillEffect:
    def __init__(
        self,
        skill: Skill,
        owner: Any,
        x: float,
        y: float,
    ):
        self.skill = skill
        self.owner = owner
        self.x = x
        self.y = y
        self.age = 0.0
        self.last_tick = 0.0
        self.hit_target_ids: set = field(default_factory=set)
        self.alive = True
        
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

    @property
    def follows_owner(self) -> bool:
        return self.skill.follows_owner

    def _calculate_tick_value(self) -> float:
        value = self.tick_value
        if self.skill.tick_scaling_stat and hasattr(self.owner, self.skill.tick_scaling_stat):
            stat_value = getattr(self.owner, self.skill.tick_scaling_stat)
            value *= (1 + stat_value / 100 * self.skill.tick_scaling_factor)
        return value

    def _get_targets_in_aoe(self, entities: List[Any]) -> List[Any]:
        if self.aoe_radius <= 0:
            return []
        
        targets = []
        for entity in entities:
            if entity.id == self.owner.id:
                continue
            if entity.id in self.hit_target_ids:
                continue
            dist = math.sqrt((entity.x - self.x) ** 2 + (entity.y - self.y) ** 2)
            if dist <= self.aoe_radius:
                targets.append(entity)
        return targets

    def tick(self, entities: List[Any]) -> Tuple[float, float]:
        if self.tick_interval <= 0 or self.tick_value <= 0:
            return 0.0, 0.0
            
        value = self._calculate_tick_value()
        targets = self._get_targets_in_aoe(entities)
        
        total_damage = 0.0
        total_healing = 0.0
        
        for target in targets:
            self.hit_target_ids.add(target.id)
            
            if self.tick_effect_type == TickEffectType.DAMAGE:
                if hasattr(target, "take_damage"):
                    actual = target.take_damage(value)
                    total_damage += actual
            elif self.tick_effect_type == TickEffectType.HEAL:
                if hasattr(target, "heal"):
                    actual = target.heal(value)
                    total_healing += actual
        
        return total_damage, total_healing

    def update(self, dt: float, entities: List[Any]) -> Tuple[float, float]:
        self.age += dt

        if self.follows_owner and hasattr(self.owner, "x") and hasattr(self.owner, "y"):
            self.x = self.owner.x
            self.y = self.owner.y

        if self.alive_duration > 0 and self.age >= self.alive_duration:
            self.alive = False
            return 0.0, 0.0

        total_damage = 0.0
        total_healing = 0.0

        if self.tick_interval > 0:
            while self.last_tick + self.tick_interval <= self.age:
                self.last_tick += self.tick_interval
                dmg, heal = self.tick(entities)
                total_damage += dmg
                total_healing += heal

        return total_damage, total_healing


@dataclass
class ActionResult:
    damage_dealt: float = 0
    healing_done: float = 0
    status_effects: List[str] = field(default_factory=list)
    success: bool = False
    message: str = ""
    targets_hit: int = 0
    resource_cost: float = 0


class Skill:
    def __init__(
        self,
        name: str,
        cooldown: float,
        cost: float,
        effects: List[SkillEffect],
        target_type: TargetType = TargetType.SINGLE_ENEMY,
        aoe_radius: float = 0,
        range: float = 100,
        cast_time: float = 0,
        channel_time: float = 0,
        resource_type: str = "mp",
        attack_width: float = 0,
        attack_height: float = 0,
        attack_offset_x: float = 0,
        attack_offset_y: float = 0,
        alive_duration: float = 0,
        tick_interval: float = 0,
        tick_value: float = 0,
        tick_effect_type: TickEffectType = TickEffectType.DAMAGE,
        tick_scaling_stat: Optional[str] = None,
        tick_scaling_factor: float = 1.0,
        follows_owner: bool = False,
    ):
        self.name = name
        self.cooldown = cooldown
        self.cost = cost
        self.effects = effects
        self.target_type = target_type
        self.aoe_radius = aoe_radius
        self.range = range
        self.cast_time = cast_time
        self.channel_time = channel_time
        self.resource_type = resource_type
        self.current_cooldown = 0
        self.is_casting = False
        self.cast_progress = 0
        self.attack_width = attack_width
        self.attack_height = attack_height
        self.attack_offset_x = attack_offset_x
        self.attack_offset_y = attack_offset_y
        self.alive_duration = alive_duration
        self.tick_interval = tick_interval
        self.tick_value = tick_value
        self.tick_effect_type = tick_effect_type
        self.tick_scaling_stat = tick_scaling_stat
        self.tick_scaling_factor = tick_scaling_factor
        self.follows_owner = follows_owner

    def can_use(self, user: Any) -> bool:
        if self.current_cooldown > 0:
            return False
        if hasattr(user, self.resource_type):
            if getattr(user, self.resource_type) < self.cost:
                return False
        return True

    @property
    def has_attack_hitbox(self) -> bool:
        return (self.attack_width > 0 and self.attack_height > 0) or self.aoe_radius > 0

    def create_attack_hitbox(
        self,
        user_x: float,
        user_y: float,
        user_rotation: float
    ) -> Optional["OBB"]:
        from fragment_of_society.components.hitbox import OBB
        if not self.has_attack_hitbox:
            return None

        from math import cos, sin

        if self.aoe_radius > 0 and self.attack_width == 0:
            size = self.aoe_radius * 2
            return OBB(
                x=user_x - self.aoe_radius,
                y=user_y - self.aoe_radius,
                width=size,
                height=size,
                rotation=0,
                offset_x=0,
                offset_y=0
            )

        offset_distance = self.attack_offset_x if self.attack_offset_x > 0 else 40
        perp_offset = self.attack_offset_y

        forward_x = offset_distance * cos(user_rotation)
        forward_y = offset_distance * sin(user_rotation)

        perp_x = -perp_offset * sin(user_rotation)
        perp_y = perp_offset * cos(user_rotation)

        center_x = user_x + forward_x + perp_x
        center_y = user_y + forward_y + perp_y

        return OBB(
            x=center_x - self.attack_width / 2,
            y=center_y - self.attack_height / 2,
            width=self.attack_width,
            height=self.attack_height,
            rotation=user_rotation,
            offset_x=0,
            offset_y=0
        )

    def use(self, user: Any, targets: List[Any]) -> ActionResult:
        if not self.can_use(user):
            return ActionResult(success=False, message="Cannot use skill")

        if hasattr(user, self.resource_type):
            setattr(user, self.resource_type, getattr(user, self.resource_type) - self.cost)

        self.current_cooldown = self.cooldown

        total_damage = 0
        total_healing = 0
        all_effects = []
        hit_count = 0

        for target in targets:
            hit_count += 1
            for effect in self.effects:
                dmg, heal, status = effect.apply(user, target)
                total_damage += dmg
                total_healing += heal
                all_effects.extend(status)

        return ActionResult(
            damage_dealt=total_damage,
            healing_done=total_healing,
            status_effects=all_effects,
            success=True,
            message=f"{self.name} hit {hit_count} target(s)",
            targets_hit=hit_count,
            resource_cost=self.cost,
        )

    def create_persistent_effect(self, user: Any, x: float, y: float) -> Optional[PersistentSkillEffect]:
        if self.alive_duration <= 0:
            return None
        return PersistentSkillEffect(skill=self, owner=user, x=x, y=y)

    @property
    def has_persistent_effect(self) -> bool:
        return self.alive_duration > 0 and self.tick_interval > 0 and self.tick_value > 0

    def update(self, dt: float):
        if self.current_cooldown > 0:
            self.current_cooldown = max(0, self.current_cooldown - dt)

    def reset(self):
        self.current_cooldown = 0

    def get_cooldown_percent(self) -> float:
        if self.cooldown == 0:
            return 1.0
        return 1.0 - (self.current_cooldown / self.cooldown)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "cooldown": self.cooldown,
            "cost": self.cost,
            "target_type": self.target_type.name,
            "aoe_radius": self.aoe_radius,
            "range": self.range,
        }


class SkillBuilder:
    @staticmethod
    def damage(
        name: str,
        base_damage: float,
        cost: float,
        cooldown: float,
        scaling_stat: str = "strength",
        scaling_factor: float = 1.0,
        aoe_radius: float = 0,
        range: float = 100,
        attack_width: float = 0,
        attack_height: float = 0,
        attack_offset_x: float = 0,
        attack_offset_y: float = 0,
        alive_duration: float = 0,
        tick_interval: float = 0,
        tick_value: float = 0,
        follows_owner: bool = False,
    ) -> Skill:
        return Skill(
            name=name,
            cooldown=cooldown,
            cost=cost,
            effects=[SkillEffect(
                skill_type=SkillType.DAMAGE,
                base_value=base_damage,
                scaling_stat=scaling_stat,
                scaling_factor=scaling_factor
            )],
            target_type=TargetType.AREA_ENEMY if aoe_radius > 0 else TargetType.SINGLE_ENEMY,
            aoe_radius=aoe_radius,
            range=range,
            attack_width=attack_width,
            attack_height=attack_height,
            attack_offset_x=attack_offset_x,
            attack_offset_y=attack_offset_y,
            alive_duration=alive_duration,
            tick_interval=tick_interval,
            tick_value=tick_value,
            follows_owner=follows_owner,
        )

    @staticmethod
    def heal(
        name: str,
        base_heal: float,
        cost: float,
        cooldown: float,
        scaling_stat: str = "healing_power",
        scaling_factor: float = 1.0,
        aoe: bool = False,
        range: float = 100
    ) -> Skill:
        return Skill(
            name=name,
            cooldown=cooldown,
            cost=cost,
            effects=[SkillEffect(
                skill_type=SkillType.HEAL,
                base_value=base_heal,
                scaling_stat=scaling_stat,
                scaling_factor=scaling_factor
            )],
            target_type=TargetType.AREA_ALLY if aoe else TargetType.SINGLE_ALLY,
            range=range
        )

    @staticmethod
    def buff(
        name: str,
        duration: float,
        cost: float,
        cooldown: float,
        stat: str = "damage",
        amount: float = 25,
        scaling_stat: Optional[str] = None,
        scaling_factor: float = 1.0,
        range: float = 100
    ) -> Skill:
        effects = [SkillEffect(
            skill_type=SkillType.BUFF,
            base_value=amount,
            duration=duration,
            scaling_stat=scaling_stat,
            scaling_factor=scaling_factor
        )]
        return Skill(
            name=name,
            cooldown=cooldown,
            cost=cost,
            effects=effects,
            target_type=TargetType.SINGLE_ALLY,
            range=range
        )

    @staticmethod
    def debuff(
        name: str,
        duration: float,
        cost: float,
        cooldown: float,
        stat: str = "damage",
        amount: float = 20,
        scaling_stat: Optional[str] = None,
        scaling_factor: float = 1.0,
        range: float = 100
    ) -> Skill:
        effects = [SkillEffect(
            skill_type=SkillType.DEBUFF,
            base_value=amount,
            duration=duration,
            scaling_stat=scaling_stat,
            scaling_factor=scaling_factor
        )]
        return Skill(
            name=name,
            cooldown=cooldown,
            cost=cost,
            effects=effects,
            target_type=TargetType.SINGLE_ENEMY,
            range=range
        )

    @staticmethod
    def shield(
        name: str,
        amount: float,
        duration: float,
        cost: float,
        cooldown: float,
        scaling_stat: Optional[str] = "intelligence",
        scaling_factor: float = 1.0,
        range: float = 100
    ) -> Skill:
        return Skill(
            name=name,
            cooldown=cooldown,
            cost=cost,
            effects=[SkillEffect(
                skill_type=SkillType.SHIELD,
                base_value=amount,
                scaling_stat=scaling_stat,
                scaling_factor=scaling_factor,
                duration=duration
            )],
            target_type=TargetType.SINGLE_ALLY,
            range=range
        )

    @staticmethod
    def combo(
        name: str,
        effects: List[SkillEffect],
        cost: float,
        cooldown: float,
        target_type: TargetType = TargetType.SINGLE_ENEMY,
        range: float = 100
    ) -> Skill:
        return Skill(
            name=name,
            cooldown=cooldown,
            cost=cost,
            effects=effects,
            target_type=target_type,
            range=range
        )

    @staticmethod
    def custom(
        name: str,
        effects: List[SkillEffect],
        cost: float = 0,
        cooldown: float = 1.0,
        target_type: TargetType = TargetType.SINGLE_ENEMY,
        aoe_radius: float = 0,
        range: float = 100,
        cast_time: float = 0,
        channel_time: float = 0,
        resource_type: str = "mp",
        alive_duration: float = 0,
        tick_interval: float = 0,
        tick_value: float = 0,
        tick_effect_type: TickEffectType = TickEffectType.DAMAGE,
        tick_scaling_stat: Optional[str] = None,
        tick_scaling_factor: float = 1.0,
    ) -> Skill:
        return Skill(
            name=name,
            cooldown=cooldown,
            cost=cost,
            effects=effects,
            target_type=target_type,
            aoe_radius=aoe_radius,
            range=range,
            cast_time=cast_time,
            channel_time=channel_time,
            resource_type=resource_type,
            alive_duration=alive_duration,
            tick_interval=tick_interval,
            tick_value=tick_value,
            tick_effect_type=tick_effect_type,
            tick_scaling_stat=tick_scaling_stat,
            tick_scaling_factor=tick_scaling_factor,
        )

    @staticmethod
    def tick_damage(
        name: str,
        tick_value: float,
        alive_duration: float,
        tick_interval: float = 1.0,
        cost: float = 0,
        cooldown: float = 1.0,
        aoe_radius: float = 50,
        scaling_stat: Optional[str] = "spell_power",
        scaling_factor: float = 1.0,
        range: float = 100,
    ) -> Skill:
        return Skill(
            name=name,
            cooldown=cooldown,
            cost=cost,
            effects=[],
            target_type=TargetType.AREA_ENEMY,
            aoe_radius=aoe_radius,
            range=range,
            alive_duration=alive_duration,
            tick_interval=tick_interval,
            tick_value=tick_value,
            tick_effect_type=TickEffectType.DAMAGE,
            tick_scaling_stat=scaling_stat,
            tick_scaling_factor=scaling_factor,
        )

    @staticmethod
    def tick_heal(
        name: str,
        tick_value: float,
        alive_duration: float,
        tick_interval: float = 1.0,
        cost: float = 0,
        cooldown: float = 1.0,
        aoe_radius: float = 50,
        scaling_stat: Optional[str] = "healing_power",
        scaling_factor: float = 1.0,
        range: float = 100,
    ) -> Skill:
        return Skill(
            name=name,
            cooldown=cooldown,
            cost=cost,
            effects=[],
            target_type=TargetType.AREA_ALLY,
            aoe_radius=aoe_radius,
            range=range,
            alive_duration=alive_duration,
            tick_interval=tick_interval,
            tick_value=tick_value,
            tick_effect_type=TickEffectType.HEAL,
            tick_scaling_stat=scaling_stat,
            tick_scaling_factor=scaling_factor,
        )


# Pre-built skill library - reuse across all characters
SKILLS: Dict[str, Skill] = {
    # Warrior skills
    "strike": SkillBuilder.damage("Strike", 20, 10, 1.0),
    "heavy_strike": SkillBuilder.damage("Heavy Strike", 35, 20, 1.5, scaling_factor=1.5),
    "whirlwind": SkillBuilder.damage("Whirlwind", 15, 30, 3.0, aoe_radius=40),
    
    # Mage skills
    "fireball": SkillBuilder.damage("Fireball", 40, 30, 2.0, scaling_stat="spell_power"),
    "meteor": SkillBuilder.damage("Meteor", 60, 50, 5.0, scaling_stat="spell_power", aoe_radius=50),
    "frostbolt": SkillBuilder.damage("Frostbolt", 25, 20, 1.5, scaling_stat="spell_power"),
    "arcane_explosion": SkillBuilder.damage("Arcane Explosion", 30, 25, 2.0, aoe_radius=30),
    
    # Priest skills
    "heal": SkillBuilder.heal("Heal", 30, 25, 3.0, scaling_stat="healing_power"),
    "mass_heal": SkillBuilder.heal("Mass Heal", 20, 40, 5.0, scaling_stat="healing_power", aoe=True),
    "smite": SkillBuilder.damage("Smite", 35, 35, 2.5, scaling_stat="faith"),
    "holy_fire": SkillBuilder.damage("Holy Fire", 45, 40, 3.0, scaling_stat="faith"),
    
    # Buffs
    "power_infusion": SkillBuilder.buff("Power Infusion", 10, 30, 15, amount=25),
    "blessing_of_might": SkillBuilder.buff("Blessing of Might", 10, 25, 12, amount=20),
    "arcane_intellect": SkillBuilder.buff("Arcane Intellect", 30, 30, 10, amount=30),
    
    # Debuffs
    "weaken": SkillBuilder.debuff("Weaken", 5, 25, 4, amount=20),
    "slow": SkillBuilder.debuff("Slow", 5, 20, 3, amount=30),
    "curse": SkillBuilder.debuff("Curse", 8, 35, 5, amount=25),
    
    # Shields
    "shield": SkillBuilder.shield("Shield", 50, 5, 20, 5.0),
    "ice_shield": SkillBuilder.shield("Ice Shield", 75, 8, 35, 6.0, scaling_stat="spell_power"),
    "power_word_shield": SkillBuilder.shield("Power Word: Shield", 60, 6, 25, 5.0),
    
    # Persistent tick effects
    "molotov": SkillBuilder.tick_damage(
        "Molotov", 
        tick_value=5, 
        alive_duration=5.0, 
        tick_interval=0.5,
        cost=30, 
        cooldown=4.0, 
        aoe_radius=40,
        scaling_stat="spell_power",
        scaling_factor=1.0,
    ),
    "healing_rain": SkillBuilder.tick_heal(
        "Healing Rain",
        tick_value=8,
        alive_duration=6.0,
        tick_interval=1.0,
        cost=40,
        cooldown=8.0,
        aoe_radius=60,
        scaling_stat="healing_power",
        scaling_factor=1.0,
    ),
}