"""
Basic attack action using domain attack resolution mechanics.

This action is pure: it computes attack resolution and returns an ActionResult
containing an AttackResult payload. The application layer is responsible for
applying the effects to the defender (mutating EP/FP) using apply_attack_result.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import random

from domain.entities import Unit, Weapon
from domain.mechanics.attack_resolution import (
    resolve_attack,
    apply_attack_result,
    AttackResult as CoreAttackResult,
)
from domain.mechanics.armor import ArmorPiece
from .base import Action, ActionCategory, ActionCost, ActionResult


@dataclass
class AttackAction(Action):
    """Perform a basic weapon attack from attacker to defender."""

    ap_cost: int = 5  # Default AP cost; application layer can override

    @property
    def category(self) -> ActionCategory:
        return ActionCategory.ATTACK

    @property
    def cost(self) -> ActionCost:
        return ActionCost(ap=self.ap_cost)

    def can_execute(
        self,
        *,
        attacker: Unit,
        defender: Unit,
        weapon: Optional[Weapon] = None,
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
        attack_roll: Optional[int] = None,
        base_damage_roll: Optional[int] = None,
        weapon: Optional[Weapon] = None,
        defender_armor: Optional[list[ArmorPiece]] = None,
        weapon_skill_level: int = 0,
        shield_ve: int = 0,
        dodge_modifier: int = 0,
        attacker_conditions: int = 0,
        defender_conditions: int = 0,
        overpower_threshold: int = 50,
        stamina_block: Optional[dict] = None,
        stamina_parry: Optional[dict] = None,
        stamina_dodge: Optional[dict] = None,
    ) -> ActionResult:
        """Execute basic attack and return domain ActionResult.

        Caller may pass deterministic attack_roll/base_damage_roll for testing.
        """
        # Default random rolls if not provided (still pure wrt game state)
        if attack_roll is None:
            attack_roll = random.randint(1, 100)
        if base_damage_roll is None:
            # If weapon provided/exists, use its min/max range; else 1
            wpn = weapon or attacker.weapon
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
            weapon=weapon,
            defender_armor=defender_armor,
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

        # Build a human-readable message (lightweight)
        outcome = core_result.outcome.value.replace("_", " ").title()
        msg = f"Attack: {outcome}. TE {core_result.all_te} vs VE {core_result.all_ve}."
        if core_result.hit and not core_result.requires_dodge_check:
            total_ep = core_result.damage_to_ep + core_result.mandatory_ep_loss
            if core_result.damage_to_fp > 0:
                msg += f" FP {core_result.damage_to_fp}."
            if total_ep > 0:
                msg += f" EP {total_ep}."

        return ActionResult(
            success=True,
            message=msg,
            ap_spent=self.ap_cost,
            stamina_spent=0,
            data={"attack_result": core_result},
        )
