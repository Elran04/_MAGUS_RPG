"""
Tests for MGT (Movement Hindering Factor) mechanics.

MGT represents equipment burden from heavy armor and shields.
- Reduces Ügyesség (dexterity) and Gyorsaság (speed)
- Armor skill level 4+ negates armor MGT
- Shieldskill level 4+ negates shield MGT
"""

import pytest
from MAGUS_pygame.application.battle_service import compute_unit_ap
from MAGUS_pygame.domain.entities.unit import Unit
from MAGUS_pygame.domain.entities.weapon import Weapon
from MAGUS_pygame.domain.mechanics.armor import ArmorPiece, ArmorSystem
from MAGUS_pygame.domain.mechanics.equipment import (
    EquipmentContext,
    get_effective_attributes,
    get_effective_dexterity,
    get_effective_speed,
)
from MAGUS_pygame.domain.mechanics.damage import _get_attribute_value, _calculate_attribute_bonus
from MAGUS_pygame.domain.value_objects import Attributes, Skills, Position, CombatStats, ResourcePool


def make_skills(**skill_levels):
    """Helper to create Skills with specific skill levels.
    
    Args:
        **skill_levels: skill_name=level pairs (e.g., skill_heavy_armor=1)
    """
    ranks = {name.replace('_', '_'): level for name, level in skill_levels.items()}
    return Skills(ranks, {})


def make_unit(attrs=None, armor_system=None, weapon=None, skills=None):
    """Helper to create test units with required fields."""
    return Unit(
        id="test",
        name="Test",
        position=Position(0, 0),
        attributes=attrs or Attributes(),
        combat_stats=CombatStats(),
        fp=ResourcePool(20, 20),
        ep=ResourcePool(20, 20),
        armor_system=armor_system,
        weapon=weapon,
        skills=skills or Skills.empty(),
    )


class TestEquipmentContext:
    """Test EquipmentContext skill negation logic with armor types.
    
    Skill_heavy_armor negation rules:
    - Level 1: negates light & leather armor MGT
    - Level 4: negates flexible metal armor MGT
    - Level 5: negates plate armor MGT
    """

    def test_leather_armor_negated_at_skill_level_1(self):
        ctx = EquipmentContext(leather_armor_mgt=2, armor_skill_level=1)
        assert ctx.get_effective_armor_mgt() == 0

    def test_leather_armor_not_negated_at_skill_level_0(self):
        ctx = EquipmentContext(leather_armor_mgt=2, armor_skill_level=0)
        assert ctx.get_effective_armor_mgt() == 2

    def test_flexible_metal_negated_at_skill_level_4(self):
        ctx = EquipmentContext(flexible_metal_armor_mgt=3, armor_skill_level=4)
        assert ctx.get_effective_armor_mgt() == 0

    def test_flexible_metal_not_negated_at_skill_level_3(self):
        ctx = EquipmentContext(flexible_metal_armor_mgt=3, armor_skill_level=3)
        assert ctx.get_effective_armor_mgt() == 3

    def test_plate_armor_negated_at_skill_level_5(self):
        ctx = EquipmentContext(plate_armor_mgt=3, armor_skill_level=5)
        assert ctx.get_effective_armor_mgt() == 0

    def test_plate_armor_not_negated_at_skill_level_4(self):
        ctx = EquipmentContext(plate_armor_mgt=3, armor_skill_level=4)
        assert ctx.get_effective_armor_mgt() == 3

    def test_mixed_armor_types_skill_level_4(self):
        # At level 4: leather negated, flexible negated, plate not negated
        ctx = EquipmentContext(
            leather_armor_mgt=1,
            flexible_metal_armor_mgt=2,
            plate_armor_mgt=3,
            armor_skill_level=4
        )
        assert ctx.get_effective_armor_mgt() == 3  # Only plate remains

    def test_mixed_armor_types_skill_level_5(self):
        # At level 5: all negated
        ctx = EquipmentContext(
            leather_armor_mgt=1,
            flexible_metal_armor_mgt=2,
            plate_armor_mgt=3,
            armor_skill_level=5
        )
        assert ctx.get_effective_armor_mgt() == 0  # All negated

    def test_total_mgt_with_armor_only(self):
        ctx = EquipmentContext(plate_armor_mgt=3)
        assert ctx.get_total_mgt() == 3

    def test_total_mgt_with_armor_and_shield(self):
        ctx = EquipmentContext(plate_armor_mgt=3, shield_mgt=2)
        assert ctx.get_total_mgt() == 5

    def test_total_mgt_with_armor_skill_negation(self):
        ctx = EquipmentContext(plate_armor_mgt=3, armor_skill_level=5)
        assert ctx.get_total_mgt() == 0

    def test_total_mgt_with_shield_skill_negation(self):
        ctx = EquipmentContext(plate_armor_mgt=3, shield_mgt=2, shield_skill_level=4)
        assert ctx.get_total_mgt() == 3  # Shield negated, plate remains


class TestEffectiveAttributes:
    """Test effective attribute calculation with MGT."""

    def test_no_equipment_no_penalty(self):
        attrs = Attributes(speed=18, dexterity=16)
        unit = make_unit(attrs=attrs)
        effective = get_effective_attributes(unit)
        assert effective.speed == 18
        assert effective.dexterity == 16

    def test_plate_armor_mgt_reduces_speed_and_dexterity(self):
        attrs = Attributes(speed=18, dexterity=16)
        armor_system = ArmorSystem(pieces=[
            ArmorPiece(id="plate_armor", name="Plate Armor", parts={"mellvért": 5}, mgt=3, armor_type="plate")
        ])
        unit = make_unit(attrs=attrs, armor_system=armor_system)
        effective = get_effective_attributes(unit)
        assert effective.speed == 15  # 18 - 3 (plate MGT applies)
        assert effective.dexterity == 13  # 16 - 3
        assert effective.strength == attrs.strength  # Unchanged

    def test_leather_armor_mgt_applies_without_skill(self):
        attrs = Attributes(speed=18, dexterity=16)
        armor_system = ArmorSystem(pieces=[
            ArmorPiece(id="leather", name="Leather Armor", parts={"mellvért": 2}, mgt=1, armor_type="leather")
        ])
        unit = make_unit(attrs=attrs, armor_system=armor_system)
        effective = get_effective_attributes(unit)
        assert effective.speed == 17  # 18 - 1 (leather MGT applies)
        assert effective.dexterity == 15  # 16 - 1

    def test_leather_armor_mgt_negated_with_skill_level_1(self):
        attrs = Attributes(speed=18, dexterity=16)
        armor_system = ArmorSystem(pieces=[
            ArmorPiece(id="leather", name="Leather Armor", parts={"mellvért": 2}, mgt=1, armor_type="leather")
        ])
        skills = make_skills(skill_heavy_armor=1)  # Level 1 negates leather
        unit = make_unit(attrs=attrs, armor_system=armor_system, skills=skills)
        effective = get_effective_attributes(unit)
        assert effective.speed == 18  # 18 - 0 (leather MGT negated)
        assert effective.dexterity == 16  # 16 - 0

    # TODO: Shield tests need character_data setup with equipment slots
    # These will be restored once shield equipment system is fully integrated
    # def test_shield_mgt_reduces_speed_and_dexterity(self):
    # def test_combined_armor_and_shield_mgt(self):
    # def test_shield_skill_level_4_negates_shield_mgt(self):
    # def test_both_skills_negate_both_mgt(self):

    def test_armor_skill_level_4_negates_armor_mgt(self):
        attrs = Attributes(speed=18, dexterity=16)
        armor_system = ArmorSystem(pieces=[
            ArmorPiece(id="plate_armor", name="Plate Armor", parts={"mellvért": 5}, mgt=3, armor_type="plate")
        ])
        skills = Skills.from_sources(character_skills=[{"id": "skill_heavy_armor", "Szint": 5}])
        unit = make_unit(attrs=attrs, armor_system=armor_system, skills=skills)
        effective = get_effective_attributes(unit)
        assert effective.speed == 18  # 18 - 0 (plate armor skill negates at level 5)
        assert effective.dexterity == 16

    def test_speed_floor_at_1(self):
        """Ensure effective speed doesn't go below 1."""
        attrs = Attributes(speed=2, dexterity=2)
        armor_system = ArmorSystem(pieces=[
            ArmorPiece(id="plate_armor", name="Plate Armor", parts={"mellvért": 5}, mgt=5, armor_type="plate")
        ])
        unit = make_unit(attrs=attrs, armor_system=armor_system)
        effective = get_effective_attributes(unit)
        assert effective.speed == 1  # Floor at 1
        assert effective.dexterity == 1


class TestAPCalculationWithMGT:
    """Test that AP calculation uses effective speed."""

    def test_ap_no_equipment(self):
        attrs = Attributes(speed=18)
        unit = make_unit(attrs=attrs)
        ap = compute_unit_ap(unit)
        assert ap == 13  # 10 + (18 - 15)

    def test_ap_with_equipment_mgt(self):
        attrs = Attributes(speed=18)
        armor_system = ArmorSystem(pieces=[
            ArmorPiece(id="plate_armor", name="Plate Armor", parts={"mellvért": 5}, mgt=3, armor_type="plate")
        ])
        unit = make_unit(attrs=attrs, armor_system=armor_system)
        ap = compute_unit_ap(unit)
        # Effective speed: 18 - 3 = 15
        # AP: 10 + (15 - 15) = 10
        assert ap == 10

    def test_ap_with_skill_negation(self):
        attrs = Attributes(speed=18)
        armor_system = ArmorSystem(pieces=[
            ArmorPiece(id="plate_armor", name="Plate Armor", parts={"mellvért": 5}, mgt=3, armor_type="plate")
        ])
        skills = Skills.from_sources(character_skills=[{"id": "skill_heavy_armor", "Szint": 5}])
        unit = make_unit(attrs=attrs, armor_system=armor_system, skills=skills)
        ap = compute_unit_ap(unit)
        # Effective speed: 18 - 0 = 18 (armor skill level 5 negates plate armor)
        # AP: 10 + (18 - 15) = 13
        assert ap == 13


class TestDamageWithMGT:
    """Test that damage calculation uses effective dexterity."""

    def test_damage_bonus_with_effective_dexterity_no_equipment(self):
        attrs = Attributes(dexterity=18)  # 18 > 15, so bonus = 3
        weapon = Weapon(
            id="sword",
            name="Sword",
            damage_dice="1d8",
            damage_bonus_attributes=["Ügyesség"],
        )
        unit = make_unit(attrs=attrs, weapon=weapon)
        bonus = _calculate_attribute_bonus(unit, weapon)
        assert bonus == 3  # (18 - 15)

    def test_damage_bonus_with_equipment_reduces_bonus(self):
        attrs = Attributes(dexterity=18)
        armor_system = ArmorSystem(pieces=[
            ArmorPiece(id="plate_armor", name="Plate Armor", parts={"mellvért": 5}, mgt=2, armor_type="plate")
        ])
        weapon = Weapon(
            id="sword",
            name="Sword",
            damage_dice="1d8",
            damage_bonus_attributes=["Ügyesség"],
        )
        unit = make_unit(attrs=attrs, armor_system=armor_system, weapon=weapon)
        bonus = _calculate_attribute_bonus(unit, weapon)
        # Effective dexterity: 18 - 2 = 16, bonus = (16 - 15) = 1
        assert bonus == 1

    def test_damage_bonus_equipment_eliminates_bonus(self):
        attrs = Attributes(dexterity=16)  # 16 > 15, bonus would be 1
        armor_system = ArmorSystem(pieces=[
            ArmorPiece(id="plate_armor", name="Plate Armor", parts={"mellvért": 5}, mgt=2, armor_type="plate")
        ])
        weapon = Weapon(
            id="sword",
            name="Sword",
            damage_dice="1d8",
            damage_bonus_attributes=["Ügyesség"],
        )
        unit = make_unit(attrs=attrs, armor_system=armor_system, weapon=weapon)
        bonus = _calculate_attribute_bonus(unit, weapon)
        # Effective dexterity: 16 - 2 = 14, bonus = 0 (14 <= 15)
        assert bonus == 0

    def test_damage_bonus_skill_negation_restores_bonus(self):
        attrs = Attributes(dexterity=18)
        armor_system = ArmorSystem(pieces=[
            ArmorPiece(id="plate_armor", name="Plate Armor", parts={"mellvért": 5}, mgt=2)
        ])
        skills = Skills.from_sources(character_skills=[{"id": "skill_heavy_armor", "Szint": 4}])
        weapon = Weapon(
            id="sword",
            name="Sword",
            damage_dice="1d8",
            damage_bonus_attributes=["Ügyesség"],
        )
        unit = make_unit(attrs=attrs, armor_system=armor_system, skills=skills, weapon=weapon)
        bonus = _calculate_attribute_bonus(unit, weapon)
        # Effective dexterity: 18 - 0 = 18 (skill negates), bonus = (18 - 15) = 3
        assert bonus == 3


class TestGetAttributeValueWithMGT:
    """Test that _get_attribute_value returns effective values for Ügyesség."""

    def test_get_attribute_ugyesseg_with_mgt(self):
        attrs = Attributes(dexterity=18)
        armor_system = ArmorSystem(pieces=[
            ArmorPiece(id="plate_armor", name="Plate Armor", parts={"mellvért": 5}, mgt=3)
        ])
        unit = make_unit(attrs=attrs, armor_system=armor_system)
        value = _get_attribute_value(unit, "Ügyesség")
        assert value == 15  # 18 - 3

    def test_get_attribute_other_unchanged(self):
        attrs = Attributes(strength=17)
        armor_system = ArmorSystem(pieces=[
            ArmorPiece(id="plate_armor", name="Plate Armor", parts={"mellvért": 5}, mgt=3)
        ])
        unit = make_unit(attrs=attrs, armor_system=armor_system)
        value = _get_attribute_value(unit, "Erő")
        assert value == 17  # Unchanged by MGT


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
