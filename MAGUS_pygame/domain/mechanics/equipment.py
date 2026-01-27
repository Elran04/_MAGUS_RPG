"""
Equipment mechanics including MGT (Movement Hindering Factor) system.

MGT represents how much heavy equipment (armor, shields) encumbers a unit.
Effects:
  - Reduces Ügyesség (dexterity) and Gyorsaság (speed)

Skill_heavy_armor Negation Rules (by armor type and skill level):
  - Level 1: Negates light armor (könnyűvértek) and leather armor (bőrvértek) MGT
  - Level 4: Negates flexible heavy armor (rugalmas nehézvértek) MGT
  - Level 5: Negates rigid heavy armor (merev nehézvértek/plate) MGT

Shield MGT Negation:
  - Shieldskill level 4+: Negates all shield MGT

Example:
  - Unit with base Gyorsaság=18, equipped with plate armor MGT=3, skill_heavy_armor level 1
  - Plate armor MGT NOT negated at level 1: effective speed = 18 - 3 = 15
  - With skill_heavy_armor level 5: effective speed = 18 (plate armor MGT negated)
  - With shield (MGT=2) equipped: effective speed = 18 - 2 = 16
"""

from dataclasses import dataclass, field
from typing import Any

from domain.entities.unit import Unit
from domain.value_objects import Attributes
from domain.value_objects.weapon_type_check import is_shield


@dataclass
class EquipmentContext:
    """Context for calculating equipment burden effects.

    Tracks MGT separately by armor type to apply skill negation correctly.
    """
    light_armor_mgt: int = 0
    leather_armor_mgt: int = 0
    flexible_metal_armor_mgt: int = 0
    plate_armor_mgt: int = 0
    shield_mgt: int = 0
    armor_skill_level: int = 0
    shield_skill_level: int = 0

    def get_effective_armor_mgt(self) -> int:
        """Get total armor MGT after skill negation.

        Skill_heavy_armor negation rules:
          - Level 1+: negates light & leather armor MGT
          - Level 4+: negates flexible metal armor MGT
          - Level 5+: negates plate armor MGT
        """
        total = 0

        # Light and leather armor: negated at level 1+
        if self.armor_skill_level < 1:
            total += self.light_armor_mgt + self.leather_armor_mgt

        # Flexible metal armor: negated at level 4+
        if self.armor_skill_level < 4:
            total += self.flexible_metal_armor_mgt

        # Plate armor: negated at level 5+
        if self.armor_skill_level < 5:
            total += self.plate_armor_mgt

        return total

    def get_effective_shield_mgt(self) -> int:
        """Get shield MGT after skill negation (shieldskill level 4+)."""
        if self.shield_skill_level >= 4:
            return 0
        return self.shield_mgt

    def get_total_mgt(self) -> int:
        """Total MGT after skill negation."""
        return self.get_effective_armor_mgt() + self.get_effective_shield_mgt()


def _get_equipped_shield_mgt(unit: Unit) -> int:
    """Extract MGT from shield if equipped in off-hand slot.

    Returns 0 if no shield equipped or if character_data is missing.
    """
    # Check if character_data exists and has equipment
    if not unit.character_data or "equipment" not in unit.character_data:
        return 0

    equipment = unit.character_data.get("equipment", {})
    off_hand_id = equipment.get("off_hand")

    # If no off-hand item, no shield MGT
    if not off_hand_id:
        return 0

    # Find the shield data in equipment list
    equipment_list = unit.character_data.get("equipment_list", [])
    for item in equipment_list:
        if item.get("id") == off_hand_id and is_shield(item):
            return item.get("mgt", 0) or 0

    return 0


def build_equipment_context(unit: Unit) -> EquipmentContext:
    """Extract equipment context from a unit (armor/shield MGT by type and skill levels).

    Categorizes armor MGT by type to allow skill-level-dependent negation:
      - light armor (könnyűvértek)
      - leather armor (bőrvértek)
      - flexible metal armor (rugalmas nehézvértek)
      - plate armor (merev nehézvértek)
    """
    light_armor_mgt = 0
    leather_armor_mgt = 0
    flexible_metal_armor_mgt = 0
    plate_armor_mgt = 0
    shield_mgt = 0
    armor_skill_level = 0
    shield_skill_level = 0

    # Get armor MGT by type
    if unit.armor_system:
        for piece in unit.armor_system.pieces:
            armor_type = getattr(piece, 'armor_type', 'leather')
            mgt = getattr(piece, 'mgt', 0)

            if armor_type == "light":
                light_armor_mgt += mgt
            elif armor_type == "leather":
                leather_armor_mgt += mgt
            elif armor_type == "flexible_metal":
                flexible_metal_armor_mgt += mgt
            elif armor_type == "plate":
                plate_armor_mgt += mgt

    # Get shield MGT (only if equipped)
    shield_mgt = _get_equipped_shield_mgt(unit)

    # Get skill levels
    armor_skill_level = unit.skills.get_rank("skill_heavy_armor", 0)
    shield_skill_level = unit.skills.get_rank("shieldskill", 0)

    return EquipmentContext(
        light_armor_mgt=light_armor_mgt,
        leather_armor_mgt=leather_armor_mgt,
        flexible_metal_armor_mgt=flexible_metal_armor_mgt,
        plate_armor_mgt=plate_armor_mgt,
        shield_mgt=shield_mgt,
        armor_skill_level=armor_skill_level,
        shield_skill_level=shield_skill_level,
    )


def get_effective_attributes(unit: Unit) -> Attributes:
    """
    Compute effective attributes by applying MGT penalties.

    Returns a new Attributes object with:
      - dexterity reduced by effective_mgt
      - speed reduced by effective_mgt
    Other attributes unchanged.

    Args:
        unit: Combat unit to compute effective attributes for

    Returns:
        New Attributes object with MGT penalties applied
    """
    ctx = build_equipment_context(unit)
    total_mgt = ctx.get_total_mgt()

    # Create new Attributes with reduced speed and dexterity
    base_attrs = unit.attributes
    effective_speed = max(1, base_attrs.speed - total_mgt)
    effective_dexterity = max(1, base_attrs.dexterity - total_mgt)

    return Attributes(
        strength=base_attrs.strength,
        dexterity=effective_dexterity,
        speed=effective_speed,
        endurance=base_attrs.endurance,
        health=base_attrs.health,
        charisma=base_attrs.charisma,
        intelligence=base_attrs.intelligence,
        willpower=base_attrs.willpower,
        astral=base_attrs.astral,
        perception=base_attrs.perception,
    )


def get_effective_speed(unit: Unit) -> int:
    """Get effective speed after equipment burden."""
    effective_attrs = get_effective_attributes(unit)
    return effective_attrs.speed


def get_effective_dexterity(unit: Unit) -> int:
    """Get effective dexterity after equipment burden."""
    effective_attrs = get_effective_attributes(unit)
    return effective_attrs.dexterity
