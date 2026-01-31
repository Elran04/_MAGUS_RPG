"""
Opportunity Attack Reaction

Triggered when a unit's movement path passes through an enemy's zone of control (ZoC).
This includes entering the zone, moving within the zone, or leaving the zone.
Only the starting position is exempt from triggering opportunity attacks.

This reaction performs a free attack against the moving unit. Pure computation:
returns a ReactionResult with embedded AttackResult payload. Application layer
is responsible for applying damage and truncating movement if instructed.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from domain.entities import Unit, Weapon
from domain.mechanics.attack_resolution import AttackResult as CoreAttackResult
from domain.mechanics.attack_resolution import resolve_attack
from domain.mechanics.lucky_unlucky_roll import (
    LuckyRollType,
    resolve_lucky_roll,
    should_use_lucky_roll,
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
        """Check if movement path passes through THIS attacker's ZoC.

        Triggers when:
        - Any hex in the path (excluding start position) is within attacker's reach (entering/moving within zone)
        - Start position is in the zone and mover moves away (leaving/disengaging)

        This covers all engagement scenarios:
        - Entering the zone from outside
        - Moving while already inside the zone
        - Leaving the zone (disengaging)
        """
        if attacker is None or mover is None:
            return (False, "Attacker and mover required")
        if not path or len(path) < 2:
            return (False, "Path must have at least 2 hexes (start and destination)")

        # Import here to avoid circular dependency
        from domain.mechanics.reach import compute_reach_hexes

        # Compute THIS attacker's zone of control
        attacker_zone = compute_reach_hexes(attacker, attacker.weapon)

        start_hex = path[0]
        start_in_zone = start_hex in attacker_zone

        # Check if any hex in the path (excluding start) is in this attacker's zone
        for i, hex_pos in enumerate(path):
            if i > 0 and hex_pos in attacker_zone:
                return (True, f"Path passes through {attacker.name}'s zone at hex {hex_pos}")

        # If start is in zone but no other hex is, the mover is leaving/disengaging
        if start_in_zone:
            return (True, f"Mover disengages from {attacker.name}'s zone")

        return (False, f"Path does not interact with {attacker.name}'s zone of control")

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
            wpn = weapon or attacker.weapon
            if should_use_lucky_roll(attacker, LuckyRollType.ATTACK_ROLL, wpn, weapon_skill_level):
                roll_1 = random.randint(1, 100)
                roll_2 = random.randint(1, 100)
                attack_roll, _ = resolve_lucky_roll(roll_1, roll_2)
            else:
                attack_roll = random.randint(1, 100)
        if base_damage_roll is None:
            wpn = weapon or attacker.weapon
            if wpn is not None:
                if should_use_lucky_roll(attacker, LuckyRollType.DAMAGE_ROLL, wpn, weapon_skill_level):
                    roll_1 = random.randint(wpn.damage_min, wpn.damage_max)
                    roll_2 = random.randint(wpn.damage_min, wpn.damage_max)
                    base_damage_roll, _ = resolve_lucky_roll(roll_1, roll_2)
                else:
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

        # Format detailed message like normal attacks
        outcome_str = core_result.outcome.value.replace("_", " ").title()
        msg = f"Opportunity!: TÉ {core_result.all_te} ({core_result.attack_roll}) vs VÉ {core_result.all_ve} | {outcome_str}"

        # Add damage details if hit
        if core_result.hit and not core_result.requires_dodge_check:
            pre_armor_damage = core_result.damage_to_fp + core_result.armor_absorbed
            if core_result.hit_zone:
                msg += f"\n{core_result.hit_zone} (SFÉ:{core_result.zone_sfe}) | DMG: {pre_armor_damage}"
            else:
                msg += f"\nDMG: {pre_armor_damage}"

            # Damage breakdown
            damage_parts = []
            if core_result.damage_to_fp > 0:
                damage_parts.append(f"FP: {core_result.damage_to_fp}")

            total_ep = core_result.damage_to_ep + core_result.mandatory_ep_loss
            if total_ep > 0:
                if core_result.mandatory_ep_loss > 0 and core_result.damage_to_ep > 0:
                    damage_parts.append(
                        f"ÉP: {total_ep} ({core_result.mandatory_ep_loss}+{core_result.damage_to_ep})"
                    )
                elif core_result.mandatory_ep_loss > 0:
                    damage_parts.append(f"ÉP: {core_result.mandatory_ep_loss}")
                else:
                    damage_parts.append(f"ÉP: {core_result.damage_to_ep}")

            if damage_parts:
                msg += f"\n{' | '.join(damage_parts)}"
        elif core_result.outcome.name in ("BLOCKED", "PARRIED"):
            if core_result.stamina_spent_defender > 0:
                msg += f"\nStamina: {core_result.stamina_spent_defender}"

        if interrupts:
            msg += "\nMovement interrupted!"

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
