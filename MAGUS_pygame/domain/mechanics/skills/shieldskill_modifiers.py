"""
Shield Skill Modifiers for MAGUS combat.

Implements the progressive shieldskill system from level 0 (untrained) to level 5 (master).

Key mechanics:
- Level 0: Untrained - heavy stat penalties, 2x stamina cost, front-only protection
- Level 1: Basic - penalties removed, still 2x stamina, front-only protection
- Level 2: Normal - no stamina penalty, protection zone expands (front + adjacent)
- Level 3: Control - shield bash action unlocked, stamina reduction on blocks
- Level 4: Mastery - reaction shield bash, shield MGT negated
- Level 5: Master - minimal stamina costs, near-complete protection coverage

Shield protection zones (based on attack angle relative to defender facing):
- Level 0-1: Only FRONT (angle 0)
- Level 2-4: FRONT, FRONT_LEFT, FRONT_RIGHT (angles 0, 1, 5)
- Level 5: All except BACK (angles 0, 1, 2, 4, 5)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.entities import Unit
    from domain.mechanics.attack_angle import AttackAngle


class UnskilledDebuff(str, Enum):
    """Types of unskilled equipment debuffs that can stack."""

    SHIELD = "unskilled_shield"  # Képzetlen pajzshasználat
    WEAPON = "unskilled_weapon"  # Képzetlen fegyverhasználat
    HEAVY_ARMOR = "unskilled_heavy_armor"  # Képzetlen nehézvérthasználat


@dataclass(frozen=True)
class ShieldskillModifiers:
    """Modifiers applied based on shield skill level.

    Attributes:
        level: Shield skill level (0-5)
        has_stat_penalties: Whether untrained penalties apply
        stamina_multiplier: Multiplier for block stamina cost (2.0 = double, 1.0 = normal)
        stamina_reduction: Flat stamina reduction on blocks
        attacker_stamina_cost: Stamina cost inflicted on attacker when blocked (dice expression)
        protection_angles: Set of AttackAngles where shield VÉ applies
        shield_bash_available: Whether shield bash special action is unlocked
        reaction_bash_available: Whether reaction shield bash is available
        mgt_negated: Whether shield MGT is negated
    """

    level: int
    has_stat_penalties: bool
    stamina_multiplier: float
    stamina_reduction: int
    attacker_stamina_cost: str  # e.g., "1d3", "1d6", "1d10"
    protection_angles: frozenset[int]  # Attack angle values (0-5) where shield protects
    shield_bash_available: bool
    reaction_bash_available: bool
    mgt_negated: bool


# Shield protection zones by level (relative to defender facing)
# AttackAngle enum values: FRONT=0, FRONT_RIGHT=1, BACK_RIGHT=2, BACK=3, BACK_LEFT=4, FRONT_LEFT=5
_PROTECTION_ZONES = {
    0: frozenset([0]),  # Only FRONT
    1: frozenset([0]),  # Only FRONT
    2: frozenset([0, 1, 5]),  # FRONT + FRONT_RIGHT + FRONT_LEFT
    3: frozenset([0, 1, 5]),  # Same as level 2
    4: frozenset([0, 1, 5]),  # Same as level 2
    5: frozenset([0, 1, 2, 4, 5]),  # All except BACK (3)
}

# Skill level progression table
_SKILL_MODIFIERS = {
    0: ShieldskillModifiers(
        level=0,
        has_stat_penalties=True,  # -10 KÉ, -25 TÉ, -20 VÉ, -30 CÉ
        stamina_multiplier=2.0,
        stamina_reduction=0,
        attacker_stamina_cost="0",
        protection_angles=_PROTECTION_ZONES[0],
        shield_bash_available=False,
        reaction_bash_available=False,
        mgt_negated=False,
    ),
    1: ShieldskillModifiers(
        level=1,
        has_stat_penalties=False,
        stamina_multiplier=2.0,
        stamina_reduction=0,
        attacker_stamina_cost="0",
        protection_angles=_PROTECTION_ZONES[1],
        shield_bash_available=False,
        reaction_bash_available=False,
        mgt_negated=False,
    ),
    2: ShieldskillModifiers(
        level=2,
        has_stat_penalties=False,
        stamina_multiplier=1.0,  # Normal stamina cost
        stamina_reduction=0,
        attacker_stamina_cost="0",
        protection_angles=_PROTECTION_ZONES[2],
        shield_bash_available=False,
        reaction_bash_available=False,
        mgt_negated=False,
    ),
    3: ShieldskillModifiers(
        level=3,
        has_stat_penalties=False,
        stamina_multiplier=1.0,
        stamina_reduction=3,  # -3 stamina on blocks (min 1)
        attacker_stamina_cost="1d3",  # Attacker loses 1-3 stamina
        protection_angles=_PROTECTION_ZONES[3],
        shield_bash_available=True,  # Shield bash action unlocked
        reaction_bash_available=False,
        mgt_negated=False,
    ),
    4: ShieldskillModifiers(
        level=4,
        has_stat_penalties=False,
        stamina_multiplier=1.0,
        stamina_reduction=5,  # -5 stamina on blocks
        attacker_stamina_cost="1d6",  # Attacker loses 1-6 stamina
        protection_angles=_PROTECTION_ZONES[4],
        shield_bash_available=True,
        reaction_bash_available=True,  # Reaction bash after successful block (1/round)
        mgt_negated=True,  # Shield MGT no longer applies
    ),
    5: ShieldskillModifiers(
        level=5,
        has_stat_penalties=False,
        stamina_multiplier=1.0,
        stamina_reduction=10,  # -10 stamina on blocks (min 1)
        attacker_stamina_cost="1d10",  # Attacker loses 1-10 stamina
        protection_angles=_PROTECTION_ZONES[5],  # All except direct back
        shield_bash_available=True,
        reaction_bash_available=True,
        mgt_negated=True,
    ),
}


def get_shieldskill_modifiers(skill_level: int) -> ShieldskillModifiers:
    """
    Get shield skill modifiers for a given skill level.

    Args:
        skill_level: Shield skill level (0-5)

    Returns:
        ShieldskillModifiers for that level
    """
    # Clamp to valid range
    level = max(0, min(5, skill_level))
    return _SKILL_MODIFIERS[level]


def shield_protects_from_angle(skill_level: int, attack_angle: AttackAngle) -> bool:
    """
    Check if shield protects against an attack from the given angle.

    Args:
        skill_level: Defender's shield skill level
        attack_angle: AttackAngle enum value

    Returns:
        True if shield VÉ applies to this attack angle
    """
    modifiers = get_shieldskill_modifiers(skill_level)
    return attack_angle.value in modifiers.protection_angles


def get_unskilled_shield_penalty() -> dict[str, int]:
    """
    Get stat penalties for unskilled shield use (level 0).

    Returns:
        Dictionary with stat modifiers: {KE: -10, TE: -25, VE: -20, CE: -30}
    """
    return {"KE": -10, "TE": -25, "VE": -20, "CE": -30}


def has_shield_equipped(unit: Unit) -> bool:
    """
    Check if unit has a shield equipped in main_hand or off_hand.

    Args:
        unit: Unit to check

    Returns:
        True if shield is equipped
    """
    if not unit.character_data or "equipment" not in unit.character_data:
        return False

    equipment = unit.character_data.get("equipment", {})
    main_hand_id = equipment.get("main_hand")
    off_hand_id = equipment.get("off_hand")

    # Check if either slot has a shield
    from domain.value_objects.weapon_type_check import is_shield
    from infrastructure.repositories import EquipmentRepository

    # Need to access equipment data - simplified check using equipment_list
    equipment_list = unit.character_data.get("equipment_list", [])

    for item in equipment_list:
        item_id = item.get("id")
        if item_id in (main_hand_id, off_hand_id) and is_shield(item):
            return True

    return False


def calculate_block_stamina_cost(
    base_cost: int, skill_level: int, is_unskilled: bool = False
) -> int:
    """
    Calculate stamina cost for blocking with shield.

    Args:
        base_cost: Base stamina cost of the block
        skill_level: Defender's shield skill level
        is_unskilled: Whether defender has untrained shield penalty

    Returns:
        Final stamina cost (minimum 1)
    """
    modifiers = get_shieldskill_modifiers(skill_level)

    # Apply multiplier (level 0-1: 2x)
    cost = base_cost * modifiers.stamina_multiplier

    # Apply flat reduction (level 3+)
    cost -= modifiers.stamina_reduction

    # Minimum 1 stamina
    return max(1, int(cost))


def get_attacker_stamina_cost_dice(skill_level: int) -> str:
    """
    Get dice expression for attacker stamina cost on successful block.

    Args:
        skill_level: Defender's shield skill level

    Returns:
        Dice expression string (e.g., "1d3", "1d6", "0" for none)
    """
    modifiers = get_shieldskill_modifiers(skill_level)
    return modifiers.attacker_stamina_cost


def can_use_shield_bash(unit: Unit) -> bool:
    """
    Check if unit can use shield bash special action.

    Requires:
    - Shield equipped (main_hand or off_hand)
    - Shield skill level 3+

    Args:
        unit: Unit to check

    Returns:
        True if shield bash is available
    """
    if not has_shield_equipped(unit):
        return False

    skill_level = unit.skills.get_rank("shieldskill", 0)
    modifiers = get_shieldskill_modifiers(skill_level)
    return modifiers.shield_bash_available


def can_use_reaction_bash(unit: Unit, reactions_used: int) -> bool:
    """
    Check if unit can use reaction shield bash.

    Requires:
    - Shield equipped
    - Shield skill level 4+
    - Successful block from protected angle
    - Less than 1 reaction bash used this round

    Args:
        unit: Unit to check
        reactions_used: Number of reaction bashes already used this round

    Returns:
        True if reaction bash is available
    """
    if not has_shield_equipped(unit):
        return False

    if reactions_used >= 1:
        return False

    skill_level = unit.skills.get_rank("shieldskill", 0)
    modifiers = get_shieldskill_modifiers(skill_level)
    return modifiers.reaction_bash_available
