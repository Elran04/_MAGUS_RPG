"""
Opportunity Attack Reaction

Triggered when a unit's movement path enters an enemy's zone of control (ZoC).
This reaction performs a free attack against the moving unit. Pure computation:
returns a ReactionResult with embedded AttackResult payload. Application layer
is responsible for applying damage and truncating movement if instructed.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from domain.entities import Unit, Weapon
from domain.mechanics.attack_resolution import (
    AttackResult as CoreAttackResult,
)
from domain.mechanics.attack_resolution import (
    resolve_attack,
)

from .base import Reaction, ReactionCategory, ReactionResult


@dataclass
class OpportunityAttackReaction(Reaction):
    """Opportunity attack when enemy enters reach during movement."""

    # Opportunity attacks are typically free (no AP cost). Stamina may apply later if rules expand.
    name: str = "opportunity_attack"
    ap_cost: int = 0
    stamina_cost: int = 0

    @property
    def category(self) -> ReactionCategory:
        return ReactionCategory.OPPORTUNITY

    def should_trigger(
        self,
        *,
        path: list[tuple[int, int]],
        intersects_zoc: bool,
        intersection_index: int | None,
        attacker: Unit,
        mover: Unit,
        **_: object,
    ) -> tuple[bool, str]:
        """Check if movement path entered attacker's ZoC."""
        if attacker is None or mover is None:
            return (False, "Attacker and mover required")
        if not intersects_zoc or intersection_index is None:
            return (False, "Path does not enter zone of control")
        return (True, "")

    def execute(
        self,
        *,
        attacker: Unit,
        mover: Unit,
        intersection_index: int,
        path: list[tuple[int, int]],
        attack_roll: int | None = None,
        base_damage_roll: int | None = None,
        weapon: Weapon | None = None,
        weapon_skill_level: int = 0,
        shield_ve: int = 0,
        dodge_modifier: int = 0,
        attacker_conditions: int = 0,
        mover_conditions: int = 0,
        overpower_threshold: int = 50,
        stamina_block: dict | None = None,
        stamina_parry: dict | None = None,
        stamina_dodge: dict | None = None,
    ) -> ReactionResult:
        """Resolve the opportunity attack and indicate if movement should be interrupted.

        Movement interruption rule (initial simple version):
        - If attack results in EP damage that would drop mover to 0 EP OR
        - If attack outcome is CRITICAL_OVERPOWER
        Then movement is interrupted at the intersection index hex.
        """
        if attack_roll is None:
            attack_roll = random.randint(1, 100)
        if base_damage_roll is None:
            wpn = weapon or attacker.weapon
            if wpn is not None:
                base_damage_roll = random.randint(wpn.damage_min, wpn.damage_max)
            else:
                base_damage_roll = 1

        core_result: CoreAttackResult = resolve_attack(
            attacker=attacker,
            defender=mover,
            attack_roll=attack_roll,
            base_damage_roll=base_damage_roll,
            weapon=weapon,
            weapon_skill_level=weapon_skill_level,
            shield_ve=shield_ve,
            dodge_modifier=dodge_modifier,
            attacker_conditions=attacker_conditions,
            defender_conditions=mover_conditions,
            overpower_threshold=overpower_threshold,
            stamina_block=stamina_block,
            stamina_parry=stamina_parry,
            stamina_dodge=stamina_dodge,
        )

        # Determine interruption
        interrupts = False
        if core_result.hit and not core_result.requires_dodge_check:
            total_ep_damage = core_result.damage_to_ep + core_result.mandatory_ep_loss
            if total_ep_damage >= mover.ep.current:
                interrupts = True
            if core_result.outcome.name == "CRITICAL_OVERPOWER":
                interrupts = True
        # (Future: exhaustion or special effects could also interrupt.)

        outcome = core_result.outcome.value.replace("_", " ").title()
        msg = f"Opportunity attack: {outcome} vs mover {mover.name}."
        if interrupts:
            msg += " Movement interrupted."

        data = {
            "attack_result": core_result,
            "path": path,
            "intersection_index": intersection_index,
        }

        return ReactionResult(
            success=True,
            message=msg,
            ap_spent=self.ap_cost,
            stamina_spent=0,
            data=data,
            interrupts_movement=interrupts,
            interrupt_index=intersection_index if interrupts else None,
            triggered_by=self.name,
        )
