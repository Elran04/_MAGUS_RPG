"""
Unit tests for damage calculation mechanics.

Tests cover:
- Attribute bonus calculation (threshold at 15)
- Damage multipliers (charge)
- Armor absorption
- Edge cases (no weapon, zero damage, high absorption)
"""

import pytest
from domain.entities import Unit, Weapon
from domain.mechanics.damage import (
    DamageContext,
    _calculate_attribute_bonus,
    _get_attribute_value,
    calculate_final_damage,
)
from domain.value_objects import Attributes, CombatStats, Facing, Position, ResourcePool

# --- Fixtures ---


@pytest.fixture
def basic_unit():
    """Create a basic unit with standard attributes (all 10)."""
    return Unit(
        id="test_unit",
        name="Test Unit",
        position=Position(0, 0),
        fp=ResourcePool(20, 20),
        ep=ResourcePool(15, 15),
        attributes=Attributes(),  # All 10 by default
        combat_stats=CombatStats(),
        facing=Facing(0),
    )


@pytest.fixture
def strong_unit():
    """Create a unit with high strength and dexterity."""
    return Unit(
        id="strong_unit",
        name="Strong Unit",
        position=Position(0, 0),
        fp=ResourcePool(20, 20),
        ep=ResourcePool(15, 15),
        attributes=Attributes(strength=18, dexterity=16),
        combat_stats=CombatStats(),
        facing=Facing(0),
    )


@pytest.fixture
def basic_weapon():
    """Create a basic weapon with strength and dexterity damage bonuses."""
    return Weapon(
        id="test_sword",
        name="Test Sword",
        damage_min=2,
        damage_max=10,
        damage_bonus_attributes=["erő", "ügyesség"],
    )


@pytest.fixture
def strength_weapon():
    """Create a weapon with only strength damage bonus."""
    return Weapon(
        id="test_mace",
        name="Test Mace",
        damage_min=3,
        damage_max=12,
        damage_bonus_attributes=["erő"],
    )


# --- Test Attribute Value Retrieval ---


class TestAttributeRetrieval:
    """Test attribute value lookup with Hungarian keys."""

    def test_lowercase_hungarian_keys(self, strong_unit):
        """Test lowercase Hungarian attribute keys."""
        assert _get_attribute_value(strong_unit, "erő") == 18
        assert _get_attribute_value(strong_unit, "ügyesség") == 16

    def test_capitalized_hungarian_keys(self, strong_unit):
        """Test capitalized Hungarian attribute keys."""
        assert _get_attribute_value(strong_unit, "Erő") == 18
        assert _get_attribute_value(strong_unit, "Ügyesség") == 16

    def test_all_attributes(self):
        """Test all attribute mappings."""
        unit = Unit(
            id="test",
            name="Test",
            position=Position(0, 0),
            fp=ResourcePool(10, 10),
            ep=ResourcePool(10, 10),
            attributes=Attributes(
                strength=11,
                dexterity=12,
                speed=13,
                endurance=14,
                health=15,
                charisma=16,
                intelligence=17,
                willpower=18,
                astral=19,
                perception=20,
            ),
        )

        assert _get_attribute_value(unit, "erő") == 11
        assert _get_attribute_value(unit, "ügyesség") == 12
        assert _get_attribute_value(unit, "gyorsaság") == 13
        assert _get_attribute_value(unit, "állóképesség") == 14
        assert _get_attribute_value(unit, "egészség") == 15
        assert _get_attribute_value(unit, "karizma") == 16
        assert _get_attribute_value(unit, "intelligencia") == 17
        assert _get_attribute_value(unit, "akaraterő") == 18
        assert _get_attribute_value(unit, "asztrál") == 19
        assert _get_attribute_value(unit, "érzékelés") == 20

    def test_unknown_attribute(self, basic_unit):
        """Test unknown attribute returns 0."""
        assert _get_attribute_value(basic_unit, "nonexistent") == 0
        assert _get_attribute_value(basic_unit, "") == 0


# --- Test Attribute Bonus Calculation ---


class TestAttributeBonus:
    """Test attribute-based damage bonus calculation."""

    def test_no_bonus_at_threshold(self, basic_unit, basic_weapon):
        """Attributes at or below 15 give no bonus."""
        unit = Unit(
            id="test",
            name="Test",
            position=Position(0, 0),
            fp=ResourcePool(10, 10),
            ep=ResourcePool(10, 10),
            attributes=Attributes(strength=15, dexterity=15),
        )
        bonus = _calculate_attribute_bonus(unit, basic_weapon)
        assert bonus == 0

    def test_bonus_above_threshold(self, strong_unit, basic_weapon):
        """Attributes above 15 give (value - 15) bonus."""
        # strength 18 (+3), dexterity 16 (+1) = +4 total
        bonus = _calculate_attribute_bonus(strong_unit, basic_weapon)
        assert bonus == 4

    def test_single_attribute_bonus(self, strong_unit, strength_weapon):
        """Weapon with single bonus attribute."""
        # Only strength 18 (+3)
        bonus = _calculate_attribute_bonus(strong_unit, strength_weapon)
        assert bonus == 3

    def test_no_weapon_no_bonus(self, strong_unit):
        """No weapon means no bonus."""
        bonus = _calculate_attribute_bonus(strong_unit, None)
        assert bonus == 0

    def test_weapon_without_bonus_attributes(self, strong_unit):
        """Weapon with empty damage_bonus_attributes."""
        weapon = Weapon(
            id="test",
            name="Test",
            damage_min=1,
            damage_max=6,
            damage_bonus_attributes=[],
        )
        bonus = _calculate_attribute_bonus(strong_unit, weapon)
        assert bonus == 0

    def test_high_attributes(self):
        """Test with very high attribute values."""
        unit = Unit(
            id="test",
            name="Test",
            position=Position(0, 0),
            fp=ResourcePool(10, 10),
            ep=ResourcePool(10, 10),
            attributes=Attributes(strength=25),
        )
        weapon = Weapon(
            id="test",
            name="Test",
            damage_min=1,
            damage_max=6,
            damage_bonus_attributes=["erő"],
        )
        bonus = _calculate_attribute_bonus(unit, weapon)
        assert bonus == 10  # 25 - 15


# --- Test Final Damage Calculation ---


class TestFinalDamage:
    """Test complete damage calculation pipeline."""

    def test_basic_damage_no_modifiers(self, basic_unit, basic_weapon):
        """Basic damage with no bonuses or modifiers."""
        result = calculate_final_damage(basic_unit, basic_weapon, base_damage=5)

        assert result.base_damage == 5
        assert result.final_damage == 5  # No bonuses (attributes at 10)
        assert result.armor_absorbed == 0
        assert not result.penetrated

    def test_damage_with_attribute_bonus(self, strong_unit, basic_weapon):
        """Damage with attribute bonuses."""
        result = calculate_final_damage(strong_unit, basic_weapon, base_damage=5)

        assert result.base_damage == 5
        assert result.final_damage == 9  # 5 + 4 (str+3, dex+1)
        assert result.armor_absorbed == 0

    def test_damage_with_charge_multiplier(self, strong_unit, basic_weapon):
        """Damage with charge multiplier."""
        ctx = DamageContext(charge_multiplier=2)
        result = calculate_final_damage(strong_unit, basic_weapon, base_damage=5, ctx=ctx)

        assert result.base_damage == 5
        assert result.final_damage == 18  # (5 + 4) * 2
        assert result.armor_absorbed == 0

    def test_damage_with_armor_absorption(self, strong_unit, basic_weapon):
        """Damage with armor absorption."""
        ctx = DamageContext(armor_absorption=5)
        result = calculate_final_damage(strong_unit, basic_weapon, base_damage=7, ctx=ctx)

        assert result.base_damage == 7
        assert result.final_damage == 6  # (7 + 4) - 5
        assert result.armor_absorbed == 5
        assert result.penetrated  # Damage (11) exceeded armor (5)

    def test_damage_penetrates_armor(self, strong_unit, basic_weapon):
        """Damage that exceeds armor absorption."""
        ctx = DamageContext(armor_absorption=3)
        result = calculate_final_damage(strong_unit, basic_weapon, base_damage=10, ctx=ctx)

        assert result.base_damage == 10
        assert result.final_damage == 11  # (10 + 4) - 3
        assert result.armor_absorbed == 3
        assert result.penetrated  # Armor not fully effective

    def test_armor_blocks_all_damage(self, basic_unit, basic_weapon):
        """Armor absorption exceeds damage."""
        ctx = DamageContext(armor_absorption=20)
        result = calculate_final_damage(basic_unit, basic_weapon, base_damage=5, ctx=ctx)

        assert result.base_damage == 5
        assert result.final_damage == 0  # Fully blocked
        assert result.armor_absorbed == 5  # Only absorbed actual damage
        assert not result.penetrated

    def test_combined_multiplier_and_armor(self, strong_unit, basic_weapon):
        """Charge multiplier and armor absorption combined."""
        ctx = DamageContext(charge_multiplier=3, armor_absorption=10)
        result = calculate_final_damage(strong_unit, basic_weapon, base_damage=5, ctx=ctx)

        # (5 + 4) * 3 = 27, then - 10 = 17
        assert result.base_damage == 5
        assert result.final_damage == 17
        assert result.armor_absorbed == 10
        assert result.penetrated

    def test_zero_base_damage(self, strong_unit, basic_weapon):
        """Zero base damage still gets attribute bonus."""
        result = calculate_final_damage(strong_unit, basic_weapon, base_damage=0)

        assert result.base_damage == 0
        assert result.final_damage == 4  # Only attribute bonus

    def test_negative_base_damage_clamped(self, strong_unit, basic_weapon):
        """Negative base damage is clamped to 0."""
        result = calculate_final_damage(strong_unit, basic_weapon, base_damage=-5)

        assert result.base_damage == 0  # Clamped
        assert result.final_damage == 4  # Only attribute bonus

    def test_no_weapon_no_bonuses(self, strong_unit):
        """Damage without weapon means no attribute bonuses."""
        result = calculate_final_damage(strong_unit, None, base_damage=8)

        assert result.base_damage == 8
        assert result.final_damage == 8  # No bonuses without weapon
        assert result.armor_absorbed == 0


# --- Test Edge Cases ---


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_maximum_charge_multiplier(self, basic_unit, basic_weapon):
        """Very high charge multiplier."""
        ctx = DamageContext(charge_multiplier=10)
        result = calculate_final_damage(basic_unit, basic_weapon, base_damage=3, ctx=ctx)

        assert result.final_damage == 30  # 3 * 10

    def test_zero_charge_multiplier_clamped(self, basic_unit, basic_weapon):
        """Zero or negative multiplier clamped to 1."""
        ctx = DamageContext(charge_multiplier=0)
        result = calculate_final_damage(basic_unit, basic_weapon, base_damage=5, ctx=ctx)

        assert result.final_damage == 5  # Multiplier clamped to 1

    def test_negative_charge_multiplier_clamped(self, basic_unit, basic_weapon):
        """Negative multiplier clamped to 1."""
        ctx = DamageContext(charge_multiplier=-2)
        result = calculate_final_damage(basic_unit, basic_weapon, base_damage=5, ctx=ctx)

        assert result.final_damage == 5  # Multiplier clamped to 1

    def test_negative_armor_absorption_ignored(self, basic_unit, basic_weapon):
        """Negative armor absorption treated as 0."""
        ctx = DamageContext(armor_absorption=-5)
        result = calculate_final_damage(basic_unit, basic_weapon, base_damage=5, ctx=ctx)

        assert result.final_damage == 5
        assert result.armor_absorbed == 0

    def test_default_context(self, basic_unit, basic_weapon):
        """No context uses default values."""
        result = calculate_final_damage(basic_unit, basic_weapon, base_damage=5, ctx=None)

        # Should be same as no modifiers
        assert result.base_damage == 5
        assert result.final_damage == 5
        assert result.armor_absorbed == 0


# --- Test DamageService ---


class TestDamageService:
    """Test DamageService integration."""

    def test_resolve_attack_applies_damage(self, strong_unit, basic_unit, basic_weapon):
        """Attack resolution applies damage to defender."""
        from domain.mechanics.damage import DamageService

        service = DamageService()
        initial_ep = basic_unit.ep.current

        result = service.resolve_attack(
            attacker=strong_unit,
            defender=basic_unit,
            weapon=basic_weapon,
            rolled_damage=6,
        )

        # Damage: 6 + 4 (attribute bonus) = 10
        assert result.final_damage == 10
        assert basic_unit.ep.current == initial_ep - 10

    def test_resolve_attack_with_context(self, strong_unit, basic_unit, basic_weapon):
        """Attack with damage context."""
        from domain.mechanics.damage import DamageService

        service = DamageService()
        initial_ep = basic_unit.ep.current

        ctx = DamageContext(charge_multiplier=2, armor_absorption=5)
        result = service.resolve_attack(
            attacker=strong_unit,
            defender=basic_unit,
            weapon=basic_weapon,
            rolled_damage=6,
            ctx=ctx,
        )

        # (6 + 4) * 2 - 5 = 15
        assert result.final_damage == 15
        assert basic_unit.ep.current == initial_ep - 15

    def test_resolve_attack_cannot_kill_below_zero(self, strong_unit, basic_unit, basic_weapon):
        """Damage cannot reduce EP below 0."""
        basic_unit.ep = ResourcePool(5, 15)  # Low health

        from domain.mechanics.damage import DamageService

        service = DamageService()

        result = service.resolve_attack(
            attacker=strong_unit,
            defender=basic_unit,
            weapon=basic_weapon,
            rolled_damage=20,  # Massive overkill
        )

        # Should not go negative
        assert basic_unit.ep.current == 0
        assert not basic_unit.is_alive()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
