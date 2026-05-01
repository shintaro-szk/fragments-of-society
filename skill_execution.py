from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from fragment_of_society.components.skills import Skill


class SkillExecutionMixin:
    def _execute_skill(
        self,
        skill: "Skill",
        targets: Optional[List] = None,
        attack_rotation: float = None
    ) -> None:
        if not skill.can_use(self):
            return

        targets = targets or []
        result = skill.use(self, targets)

        if not result.success:
            return

        rotation = attack_rotation if attack_rotation is not None else self.rotation

        if skill.has_attack_hitbox:
            self.attack_hitbox = skill.create_attack_hitbox(
                self.x,
                self.y,
                rotation
            )
            self.attack_hitbox_timer = 0.15

    def update_skills(self, dt: float) -> None:
        for skill_attr in ["basic_attack", "first_skill", "second_skill", "third_skill"]:
            skill = getattr(self, skill_attr, None)
            if skill:
                skill.update(dt)