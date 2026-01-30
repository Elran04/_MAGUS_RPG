"""
Unskilled equipment penalty subsystem for MAGUS combat engine.

Models penalties for using equipment without proper training:
- Unskilled shield (Képzetlen pajzshasználat): Shield equipped, no shieldskill
- Unskilled weapon (Képzetlen fegyverhasználat): Weapon equipped, missing weaponskill
- Unskilled heavy armor (Képzetlen nehézvérthasználat): Heavy armor without skill_heavy_armor

These conditions can STACK - a unit can have multiple active at once.
All three apply the same penalties: -10 KÉ, -25 TÉ, -20 VÉ, -30 CÉ
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.entities import Unit


class UnskilledType(str, Enum):
    """Types of unskilled equipment penalties."""

    SHIELD = "Képzetlen pajzshasználat"
    WEAPON = "Képzetlen fegyverhasználat"
    HEAVY_ARMOR = "Képzetlen nehézvérthasználat"


@dataclass(frozen=True)
class UnskilledModifiers:
    """Combat stat penalties from unskilled equipment use.

    All values are negative (penalties).
    """

    ke_mod: int = 0
    te_mod: int = 0
    ve_mod: int = 0
    ce_mod: int = 0


# Single penalty applied per unskilled condition
UNSKILLED_PENALTY = UnskilledModifiers(
    ke_mod=-10,
    te_mod=-25,
    ve_mod=-20,
    ce_mod=-30,
)


@dataclass(frozen=True)
class UnskilledConditions:
    """Active unskilled conditions for a unit.

    Each boolean indicates if that penalty is active.
    """

    shield: bool = False
    weapon: bool = False
    heavy_armor: bool = False

    def has_any(self) -> bool:
        """Check if any unskilled condition is active."""
        return self.shield or self.weapon or self.heavy_armor

    def count(self) -> int:
        """Count number of active unskilled conditions."""
        return sum([self.shield, self.weapon, self.heavy_armor])

    def get_types(self) -> list[UnskilledType]:
        """Get list of active unskilled condition types."""
        types = []
        if self.shield:
            types.append(UnskilledType.SHIELD)
        if self.weapon:
            types.append(UnskilledType.WEAPON)
        if self.heavy_armor:
            types.append(UnskilledType.HEAVY_ARMOR)
        return types


def check_unskilled_shield(unit: Unit) -> bool:
    """
    Check if unit has unskilled shield penalty.

    Requirements:
    - Shield equipped (main_hand or off_hand)
    - Shield skill level 0 (no skill trained)

    Args:
        unit: Unit to check

    Returns:
        True if unskilled shield penalty applies
    """
    # Check if shield equipped
    if not unit.character_data or "equipment" not in unit.character_data:
        return False

    equipment = unit.character_data.get("equipment", {})
    main_hand_id = equipment.get("main_hand")
    off_hand_id = equipment.get("off_hand")

    if not main_hand_id and not off_hand_id:
        return False

    # Check if either slot has a shield
    from domain.value_objects.weapon_type_check import is_shield

    equipment_list = unit.character_data.get("equipment_list", [])
    has_shield = False

    for item in equipment_list:
        item_id = item.get("id")
        if item_id in (main_hand_id, off_hand_id) and is_shield(item):
            has_shield = True
            break

    if not has_shield:
        return False

    # Check skill level (0 = untrained)
    shield_skill_level = unit.skills.get_rank("shieldskill", 0) if unit.skills else 0
    return shield_skill_level == 0


def check_unskilled_weapon(unit: Unit) -> bool:
    """
    Check if unit has unskilled weapon penalty.

    Requirements:
    - Weapon equipped
    - Missing the weaponskill that governs that weapon category

    Args:
        unit: Unit to check

    Returns:
        True if unskilled weapon penalty applies
    """
    if not unit.weapon:
        return False

    # Get weapon's skill_id (e.g., "weaponskill_longswords")
    weapon_skill_id = getattr(unit.weapon, "skill_id", None)
    if not weapon_skill_id:
        # No skill required for this weapon
        return False

    # Check if unit has this skill
    weapon_skill_level = unit.skills.get_rank(weapon_skill_id, 0) if unit.skills else 0
    return weapon_skill_level == 0


def check_unskilled_heavy_armor(unit: Unit) -> bool:
    """
    Check if unit has unskilled heavy armor penalty.

    Requirements for penalty:
    - Wearing flexible_metal armor without skill_heavy_armor level 1+
    - OR wearing plate armor without skill_heavy_armor level 2+

    Args:
        unit: Unit to check

    Returns:
        True if unskilled heavy armor penalty applies
    """
    if not unit.armor_system or not unit.armor_system.pieces:
        return False

    armor_skill_level = unit.skills.get_rank("skill_heavy_armor", 0) if unit.skills else 0

    # Check each armor piece
    for piece in unit.armor_system.pieces:
        armor_type = getattr(piece, "armor_type", "leather")

        # Flexible metal requires level 1+
        if armor_type == "flexible_metal" and armor_skill_level < 1:
            return True

        # Plate requires level 2+
        if armor_type == "plate" and armor_skill_level < 2:
            return True

    return False


def check_all_unskilled_conditions(unit: Unit) -> UnskilledConditions:
    """
    Check all unskilled equipment conditions for a unit.

    Should be called:
    - On battle start
    - After weapon switch
    - After armor change
    - After any equipment modification

    Args:
        unit: Unit to check

    Returns:
        UnskilledConditions with all active penalties
    """
    return UnskilledConditions(
        shield=check_unskilled_shield(unit),
        weapon=check_unskilled_weapon(unit),
        heavy_armor=check_unskilled_heavy_armor(unit),
    )


def get_combined_unskilled_modifiers(conditions: UnskilledConditions) -> UnskilledModifiers:
    """
    Get combined modifiers from all active unskilled conditions.

    Since all conditions apply the same penalty and they stack,
    multiply the base penalty by the number of active conditions.

    Args:
        conditions: Active unskilled conditions

    Returns:
        Combined modifiers (penalties multiply)
    """
    count = conditions.count()
    if count == 0:
        return UnskilledModifiers()

    return UnskilledModifiers(
        ke_mod=UNSKILLED_PENALTY.ke_mod * count,
        te_mod=UNSKILLED_PENALTY.te_mod * count,
        ve_mod=UNSKILLED_PENALTY.ve_mod * count,
        ce_mod=UNSKILLED_PENALTY.ce_mod * count,
    )


def get_unskilled_modifiers_for_unit(unit: Unit) -> UnskilledModifiers:
    """
    Get current unskilled equipment modifiers for a unit.

    Convenience function that checks all conditions and returns combined modifiers.

    Args:
        unit: Unit to check

    Returns:
        Combined unskilled modifiers
    """
    conditions = check_all_unskilled_conditions(unit)
    return get_combined_unskilled_modifiers(conditions)
