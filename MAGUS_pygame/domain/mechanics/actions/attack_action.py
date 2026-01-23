"""
Basic attack action using domain attack resolution mechanics.

This action is pure: it computes attack resolution and returns an ActionResult
containing an AttackResult payload. The application layer is responsible for
applying the effects to the defender (mutating EP/FP) using apply_attack_result.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from domain.entities import Unit, Weapon
from domain.mechanics.attack_resolution import AttackResult as CoreAttackResult
from domain.mechanics.attack_resolution import resolve_attack

from .base import Action, ActionCategory, ActionCost, ActionResult


@dataclass
class AttackAction(Action):
    """Perform a basic weapon attack from attacker to defender."""

    # NOTE: ap_cost is determined dynamically from weapon's attack_time
    # This is just a fallback for unarmed attacks
    ap_cost: int = 5  # Default AP cost for unarmed

    @property
    def category(self) -> ActionCategory:
        return ActionCategory.ATTACK

    @property
    def cost(self) -> ActionCost:
        # Cost is dynamic, determined in execute() from weapon
        return ActionCost(ap=self.ap_cost)

    def can_execute(
        self,
        *,
        attacker: Unit,
        defender: Unit,
        weapon: Weapon | None = None,
        attacker_conditions: int = 0,
        defender_conditions: int = 0,
        shield_ve: int = 0,
        dodge_modifier: int = 0,
        overpower_threshold: int = 50,
        **_: object,
    ) -> tuple[bool, str]:
        """Validate that required inputs are present.
        Reach validation is left to caller (UI may pre-filter targets).
        """
        if attacker is None or defender is None:
            return (False, "Attacker and defender are required")
        return (True, "")

    def execute(
        self,
        *,
        attacker: Unit,
        defender: Unit,
        attack_roll: int | None = None,
        base_damage_roll: int | None = None,
        weapon: Weapon | None = None,
        weapon_skill_level: int = 0,
        shield_ve: int = 0,
        dodge_modifier: int = 0,
        attacker_conditions: int = 0,
        defender_conditions: int = 0,
        overpower_threshold: int = 50,
        stamina_block: dict | None = None,
        stamina_parry: dict | None = None,
        stamina_dodge: dict | None = None,
    ) -> ActionResult:
        """Execute basic attack and return domain ActionResult.

        Caller may pass deterministic attack_roll/base_damage_roll for testing.
        """
        # Determine weapon to use (passed explicitly or from attacker)
        wpn = weapon or attacker.weapon

        # Get AP cost from weapon's attack_time (or default for unarmed)
        actual_ap_cost = wpn.attack_time if wpn is not None else self.ap_cost

        # Default random rolls if not provided (still pure wrt game state)
        if attack_roll is None:
            attack_roll = random.randint(1, 100)
        if base_damage_roll is None:
            # If weapon exists, use its min/max range; else 1
            if wpn is not None:
                import random as _rand

                base_damage_roll = _rand.randint(wpn.damage_min, wpn.damage_max)
            else:
                base_damage_roll = 1

        core_result: CoreAttackResult = resolve_attack(
            attacker=attacker,
            defender=defender,
            attack_roll=attack_roll,
            base_damage_roll=base_damage_roll,
            weapon=wpn,
            weapon_skill_level=weapon_skill_level,
            shield_ve=shield_ve,
            dodge_modifier=dodge_modifier,
            attacker_conditions=attacker_conditions,
            defender_conditions=defender_conditions,
            overpower_threshold=overpower_threshold,
            stamina_block=stamina_block,
            stamina_parry=stamina_parry,
            stamina_dodge=stamina_dodge,
        )

        return ActionResult(
            success=True,
            message="",  # Message formatting done in presentation layer
            ap_spent=actual_ap_cost,  # Use weapon's attack_time
            stamina_spent=0,
            data={"attack_result": core_result},
        )
