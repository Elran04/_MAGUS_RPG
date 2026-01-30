"""
Mastery buff subsystem for MAGUS combat engine.

Models positive skill-based buffs that improve combat performance:
- Weapon skill mastery (Mesteri fegyverhasználat): Level 4+ grants stat bonuses
- Shield skill mastery (Mesteri pajzshasználat): Level 5+ grants stat bonuses
- Armor skill mastery (Mesteri nehézvérthasználat): Future expansion

These are separate from skill mechanics - they represent actual combat proficiency bonuses
that stack with other modifiers.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.entities import Unit


class MasteryType(str, Enum):
    """Types of mastery-level skill buffs."""

    WEAPON = "Mesteri fegyverhasználat"  # Weapon skill level 4+
    SHIELD = "Mesteri pajzshasználat"  # Shield skill level 5+
    HEAVY_ARMOR = "Mesteri nehézvérthasználat"  # Heavy armor skill level 5+ (future)


@dataclass(frozen=True)
class MasteryModifiers:
    """Combat stat bonuses from mastery-level skill training.

    All values are positive (bonuses).
    """

    ke_mod: int = 0
    te_mod: int = 0
    ve_mod: int = 0
    ce_mod: int = 0


@dataclass(frozen=True)
class ActiveMasteries:
    """Active mastery-level buffs for a unit.

    Each boolean indicates if that mastery buff is active.
    """

    weapon: bool = False
    shield: bool = False
    heavy_armor: bool = False

    def has_any(self) -> bool:
        """Check if any mastery buff is active."""
        return self.weapon or self.shield or self.heavy_armor

    def count(self) -> int:
        """Count number of active mastery buffs."""
        return sum([self.weapon, self.shield, self.heavy_armor])

    def get_types(self) -> list[MasteryType]:
        """Get list of active mastery buff types."""
        types = []
        if self.weapon:
            types.append(MasteryType.WEAPON)
        if self.shield:
            types.append(MasteryType.SHIELD)
        if self.heavy_armor:
            types.append(MasteryType.HEAVY_ARMOR)
        return types


# Mastery-level bonuses (applied when skill reaches mastery level)
WEAPON_MASTERY_BONUS = MasteryModifiers(
    ke_mod=5,
    te_mod=10,
    ve_mod=10,
    ce_mod=10,
)

SHIELD_MASTERY_BONUS = MasteryModifiers(
    ke_mod=0,
    te_mod=0,
    ve_mod=10,
    ce_mod=0,
)

HEAVY_ARMOR_MASTERY_BONUS = MasteryModifiers(
    ke_mod=5,
    te_mod=0,
    ve_mod=5,
    ce_mod=0,
)


def check_weapon_mastery(unit: Unit) -> bool:
    """
    Check if unit has weapon skill mastery buff.

    Requirements:
    - Weapon equipped
    - Weapon skill level 4+ (mesteri level)

    Args:
        unit: Unit to check

    Returns:
        True if weapon mastery buff applies
    """
    if not unit.weapon:
        return False

    # Get weapon's skill_id
    weapon_skill_id = getattr(unit.weapon, "skill_id", None)
    if not weapon_skill_id:
        return False

    # Level 4+ grants mastery
    weapon_skill_level = unit.skills.get_rank(weapon_skill_id, 0) if unit.skills else 0
    return weapon_skill_level >= 4


def check_shield_mastery(unit: Unit) -> bool:
    """
    Check if unit has shield skill mastery buff.

    Requirements:
    - Shield equipped
    - Shield skill level 5+ (mesteri level)

    Args:
        unit: Unit to check

    Returns:
        True if shield mastery buff applies
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

    # Level 5+ grants mastery
    shield_skill_level = unit.skills.get_rank("shieldskill", 0) if unit.skills else 0
    return shield_skill_level >= 5


def check_heavy_armor_mastery(unit: Unit) -> bool:
    """
    Check if unit has heavy armor skill mastery buff.

    Requirements:
    - Wearing heavy armor (flexible_metal or plate)
    - Heavy armor skill level 5+ (mesteri level)

    Args:
        unit: Unit to check

    Returns:
        True if heavy armor mastery buff applies
    """
    if not unit.armor_system or not unit.armor_system.pieces:
        return False

    armor_skill_level = unit.skills.get_rank("skill_heavy_armor", 0) if unit.skills else 0

    # Level 5+ grants mastery
    if armor_skill_level < 5:
        return False

    # Must be wearing at least one heavy armor piece
    for piece in unit.armor_system.pieces:
        armor_type = getattr(piece, "armor_type", "leather")
        if armor_type in ("flexible_metal", "plate"):
            return True

    return False


def check_all_masteries(unit: Unit) -> ActiveMasteries:
    """
    Check all mastery-level skill buffs for a unit.

    Should be called:
    - On battle start
    - After weapon switch
    - After armor change
    - After skill level up (future)

    Args:
        unit: Unit to check

    Returns:
        ActiveMasteries with all active buffs
    """
    return ActiveMasteries(
        weapon=check_weapon_mastery(unit),
        shield=check_shield_mastery(unit),
        heavy_armor=check_heavy_armor_mastery(unit),
    )


def get_combined_mastery_modifiers(masteries: ActiveMasteries) -> MasteryModifiers:
    """
    Get combined modifiers from all active mastery buffs.

    Masteries stack - a unit can have multiple active at once.

    Args:
        masteries: Active mastery buffs

    Returns:
        Combined modifiers (bonuses add together)
    """
    total_ke = 0
    total_te = 0
    total_ve = 0
    total_ce = 0

    if masteries.weapon:
        total_ke += WEAPON_MASTERY_BONUS.ke_mod
        total_te += WEAPON_MASTERY_BONUS.te_mod
        total_ve += WEAPON_MASTERY_BONUS.ve_mod
        total_ce += WEAPON_MASTERY_BONUS.ce_mod

    if masteries.shield:
        total_ke += SHIELD_MASTERY_BONUS.ke_mod
        total_te += SHIELD_MASTERY_BONUS.te_mod
        total_ve += SHIELD_MASTERY_BONUS.ve_mod
        total_ce += SHIELD_MASTERY_BONUS.ce_mod

    if masteries.heavy_armor:
        total_ke += HEAVY_ARMOR_MASTERY_BONUS.ke_mod
        total_te += HEAVY_ARMOR_MASTERY_BONUS.te_mod
        total_ve += HEAVY_ARMOR_MASTERY_BONUS.ve_mod
        total_ce += HEAVY_ARMOR_MASTERY_BONUS.ce_mod

    return MasteryModifiers(
        ke_mod=total_ke,
        te_mod=total_te,
        ve_mod=total_ve,
        ce_mod=total_ce,
    )


def get_mastery_modifiers_for_unit(unit: Unit) -> MasteryModifiers:
    """
    Get current mastery-level skill buffs for a unit.

    Convenience function that checks all masteries and returns combined modifiers.

    Args:
        unit: Unit to check

    Returns:
        Combined mastery modifiers
    """
    masteries = check_all_masteries(unit)
    return get_combined_mastery_modifiers(masteries)
