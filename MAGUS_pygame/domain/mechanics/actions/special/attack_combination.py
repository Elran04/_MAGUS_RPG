"""
Attack Combination (Támadás kombináció) special action for dagger skill level 3+.

This is a melee special attack that chains consecutive strikes:
- Level 3: 4 attacks, 10 AP, +10 TÉ per successful hit
- Level 6: 5 attacks, 8 AP, +15 TÉ per successful hit

Mechanics:
- Only usable in melee range (adjacent hex to target)
- Each attack is resolved sequentially
- On each successful hit, the next attack gains +TÉ bonus
- Damages are calculated separately and summed
- Armor (SFÉ) is applied to each hit separately

Attack Combination is a weapon skill special effect, not a standalone action.
It's triggered via resolve_attack with special parameters.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from domain.mechanics.actions.base import Action, ActionCategory, ActionCost, ActionResult
from domain.mechanics.attack_resolution import AttackOutcome
from domain.mechanics.attack_resolution import AttackResult as CoreAttackResult
from domain.mechanics.attack_resolution import resolve_attack
from domain.mechanics.lucky_unlucky_roll import (
    LuckyRollType,
    resolve_lucky_roll,
    should_use_lucky_roll,
)

if TYPE_CHECKING:
    from domain.entities import Unit, Weapon


@dataclass(frozen=True)
class AttackCombinationConfig:
    """Configuration for attack combination at a given skill level."""

    level: int
    attack_count: int  # Number of attacks in the sequence
    ap_cost: int  # Total AP cost
    te_bonus_per_hit: int  # TÉ bonus gained per successful hit


# Attack Combination configurations per dagger skill level
ATTACK_COMBINATION_CONFIGS = {
    3: AttackCombinationConfig(
        level=3,
        attack_count=4,
        ap_cost=10,
        te_bonus_per_hit=10,
    ),
    6: AttackCombinationConfig(
        level=6,
        attack_count=5,
        ap_cost=8,
        te_bonus_per_hit=15,
    ),
}


def get_attack_combination_config(weapon_skill_level: int) -> AttackCombinationConfig | None:
    """Get attack combination configuration for dagger skill level.

    Args:
        weapon_skill_level: Dagger skill level (0-6+)

    Returns:
        AttackCombinationConfig if available at this level, else None
    """
    if weapon_skill_level >= 6:
        return ATTACK_COMBINATION_CONFIGS[6]
    elif weapon_skill_level >= 3:
        return ATTACK_COMBINATION_CONFIGS[3]
    return None


def can_use_attack_combination(
    attacker: Unit,
    defender: Unit,
    weapon_skill_level: int,
) -> bool:
    """Check if attack combination can be used.

    Requirements:
    - Weapon skill level 3+ with dagger
    - Attacker and defender must be in melee range (adjacent)
    - Attacker must have enough AP

    Args:
        attacker: Attacking unit
        defender: Defending unit
        weapon_skill_level: Dagger skill level

    Returns:
        True if attack combination can be used
    """
    # Must be skill level 3+
    if weapon_skill_level < 3:
        return False

    # Must be in melee range (adjacent hex)
    # This check would be done at application layer with actual distance calculation
    # For now, we assume validation happens before calling resolve_attack with combination flag

    # Must have enough AP
    config = get_attack_combination_config(weapon_skill_level)
    if not config:
        return False

    # Check if attacker has enough AP
    if attacker.ap.current < config.ap_cost:
        return False

    return True


@dataclass
class AttackCombinationResult:
    """Result of a complete attack combination sequence.

    Attributes:
        success: Whether combination was executed
        total_damage_to_fp: Sum of all FP damage from all hits
        total_damage_to_ep: Sum of all EP damage from all hits
        total_armor_absorbed: Sum of all armor absorption
        hits_landed: Number of successful hits in the sequence
        total_attacks: Total attacks in the sequence
        individual_results: List of AttackResult for each attack in sequence
    """

    success: bool
    total_damage_to_fp: int = 0
    total_damage_to_ep: int = 0
    total_armor_absorbed: int = 0
    hits_landed: int = 0
    total_attacks: int = 0
    individual_results: list[CoreAttackResult] = None

    def __post_init__(self):
        if self.individual_results is None:
            object.__setattr__(self, "individual_results", [])


@dataclass
class AttackCombinationAction(Action):
    """Execute dagger attack combination (Támadás kombináció)."""

    ap_cost: int = 10

    @property
    def category(self) -> ActionCategory:
        return ActionCategory.SPECIAL_ATTACK

    @property
    def cost(self) -> ActionCost:
        return ActionCost(ap=self.ap_cost)

    def can_execute(
        self,
        *,
        attacker: Unit,
        defender: Unit,
        weapon: Weapon | None = None,
        weapon_skill_level: int = 0,
        **_: object,
    ) -> tuple[bool, str]:
        if attacker is None or defender is None:
            return (False, "Attacker and defender are required")

        wpn = weapon or attacker.weapon
        if wpn is None:
            return (False, "No weapon equipped")

        if getattr(wpn, "skill_id", "") != "weaponskill_daggers":
            return (False, "Attack combination requires a dagger")

        config = get_attack_combination_config(weapon_skill_level)
        if not config:
            return (False, "Attack combination requires dagger skill level 3+")

        if attacker.position.distance_to(defender.position) != 1:
            return (False, "Attack combination requires adjacent target")

        return (True, "")

    def execute(
        self,
        *,
        attacker: Unit,
        defender: Unit,
        attack_rolls: list[int] | None = None,
        damage_rolls: list[int] | None = None,
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
        wpn = weapon or attacker.weapon
        config = get_attack_combination_config(weapon_skill_level)
        if wpn is None or config is None:
            return ActionResult(success=False, message="Attack combination not available")

        attack_results: list[CoreAttackResult] = []
        te_bonus_total = 0
        te_bonus_applied: list[int] = []

        lucky_attack_rolls: list[tuple[int, int, int]] = []
        lucky_damage_rolls: list[tuple[int, int, int]] = []

        for idx in range(config.attack_count):
            # Resolve attack roll
            if attack_rolls and idx < len(attack_rolls):
                attack_roll = attack_rolls[idx]
            else:
                if should_use_lucky_roll(attacker, LuckyRollType.ATTACK_ROLL, wpn, weapon_skill_level):
                    roll_1 = random.randint(1, 100)
                    roll_2 = random.randint(1, 100)
                    attack_roll, _ = resolve_lucky_roll(roll_1, roll_2)
                    lucky_attack_rolls.append((roll_1, roll_2, attack_roll))
                else:
                    attack_roll = random.randint(1, 100)

            # Resolve damage roll
            if damage_rolls and idx < len(damage_rolls):
                base_damage_roll = damage_rolls[idx]
            else:
                if should_use_lucky_roll(attacker, LuckyRollType.DAMAGE_ROLL, wpn, weapon_skill_level):
                    roll_1 = random.randint(wpn.damage_min, wpn.damage_max)
                    roll_2 = random.randint(wpn.damage_min, wpn.damage_max)
                    base_damage_roll, _ = resolve_lucky_roll(roll_1, roll_2)
                    lucky_damage_rolls.append((roll_1, roll_2, base_damage_roll))
                else:
                    base_damage_roll = random.randint(wpn.damage_min, wpn.damage_max)

            # Apply accumulated TÉ bonus to this attack
            te_bonus_applied.append(te_bonus_total)
            core_result = resolve_attack(
                attacker=attacker,
                defender=defender,
                attack_roll=attack_roll,
                base_damage_roll=base_damage_roll,
                weapon=wpn,
                weapon_skill_level=weapon_skill_level,
                shield_ve=shield_ve,
                dodge_modifier=dodge_modifier,
                attacker_conditions=attacker_conditions + te_bonus_total,
                defender_conditions=defender_conditions,
                overpower_threshold=overpower_threshold,
                stamina_block=stamina_block,
                stamina_parry=stamina_parry,
                stamina_dodge=stamina_dodge,
            )

            attack_results.append(core_result)

            # On success, increase next attack's TÉ bonus
            if core_result.outcome not in (AttackOutcome.MISS, AttackOutcome.CRITICAL_FAILURE):
                te_bonus_total += config.te_bonus_per_hit

        data = {
            "attack_results": attack_results,
            "special_attack": "dagger_combo",
            "combo_config": config,
            "attack_count": config.attack_count,
            "te_bonus_per_hit": config.te_bonus_per_hit,
            "te_bonus_applied": te_bonus_applied,
        }

        if lucky_attack_rolls:
            data["lucky_attack_rolls"] = lucky_attack_rolls
        if lucky_damage_rolls:
            data["lucky_damage_rolls"] = lucky_damage_rolls

        return ActionResult(
            success=True,
            message="",
            ap_spent=config.ap_cost,
            stamina_spent=0,
            data=data,
        )


# Note: Actual resolution of attack combinations is handled in attack_resolution.py
# This module defines the structure and configuration only.
# The attack_resolution.resolve_attack_combination() function will use these configs
# to execute the chain of attacks with proper TÉ bonuses and damage accumulation.
