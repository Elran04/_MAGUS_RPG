"""
Tests for weapon wielding mechanics.

Tests variable weapon wielding system including:
- Attribute requirement checking
- Wielding mode determination
- Combat stat bonuses
- Mode validation
"""

import pytest
from domain.entities import Unit, Weapon
from domain.mechanics.weapon_wielding import (
    WieldMode,
    calculate_wielding_bonuses,
    can_wield_one_handed,
    get_wielding_info,
    get_wielding_mode,
    validate_wielding_mode_change,
)
from domain.value_objects import Attributes, CombatStats, Position, ResourcePool

# --- Fixtures ---


@pytest.fixture
def weak_unit():
    """Unit with low attributes (can't wield 1-handed)."""
    return Unit(
        id="weak",
        name="Weak Fighter",
        position=Position(0, 0),
        fp=ResourcePool(20, 20),
        ep=ResourcePool(15, 15),
        attributes=Attributes(strength=12, dexterity=10),
        combat_stats=CombatStats(TE=50, VE=60),
    )


@pytest.fixture
def strong_unit():
    """Unit with high attributes (can wield 1-handed)."""
    return Unit(
        id="strong",
        name="Strong Fighter",
        position=Position(0, 0),
        fp=ResourcePool(20, 20),
        ep=ResourcePool(15, 15),
        attributes=Attributes(strength=18, dexterity=16),
        combat_stats=CombatStats(TE=60, VE=70),
    )


@pytest.fixture
def variable_weapon():
    """Variable weapon with bonuses."""
    return Weapon(
        id="longsword",
        name="Longsword",
        te_modifier=10,
        ve_modifier=8,
        damage_min=5,
        damage_max=15,
        size_category=3,
    )


@pytest.fixture
def fixed_weapon():
    """Non-variable weapon."""
    return Weapon(
        id="shortsword",
        name="Shortsword",
        te_modifier=8,
        ve_modifier=6,
        damage_min=3,
        damage_max=10,
        size_category=2,
    )


# --- Test Attribute Requirements ---


class TestAttributeRequirements:
    """Test attribute requirement checking for 1-handed wielding."""

    def test_meets_both_requirements(self, strong_unit, variable_weapon):
        """Unit with high STR and DEX can wield 1-handed."""
        assert can_wield_one_handed(strong_unit, variable_weapon, strength_req=16, dex_req=13)

    def test_fails_strength_requirement(self, weak_unit, variable_weapon):
        """Unit with low STR cannot wield 1-handed."""
        assert not can_wield_one_handed(weak_unit, variable_weapon, strength_req=16, dex_req=13)

    def test_fails_dexterity_requirement(self, strong_unit, variable_weapon):
        """Unit with low DEX cannot wield 1-handed."""
        # Temporarily lower dexterity
        unit = Unit(
            id="clumsy",
            name="Clumsy Fighter",
            position=Position(0, 0),
            fp=ResourcePool(20, 20),
            ep=ResourcePool(15, 15),
            attributes=Attributes(strength=18, dexterity=10),
            combat_stats=CombatStats(TE=60, VE=70),
        )
        assert not can_wield_one_handed(unit, variable_weapon, strength_req=16, dex_req=13)

    def test_exact_requirements(self, variable_weapon):
        """Unit with exact attribute values can wield 1-handed."""
        unit = Unit(
            id="exact",
            name="Exact Fighter",
            position=Position(0, 0),
            fp=ResourcePool(20, 20),
            ep=ResourcePool(15, 15),
            attributes=Attributes(strength=16, dexterity=13),
            combat_stats=CombatStats(TE=60, VE=70),
        )
        assert can_wield_one_handed(unit, variable_weapon, strength_req=16, dex_req=13)

    def test_one_below_requirement(self, variable_weapon):
        """Unit one point below requirement cannot wield 1-handed."""
        unit = Unit(
            id="almost",
            name="Almost Fighter",
            position=Position(0, 0),
            fp=ResourcePool(20, 20),
            ep=ResourcePool(15, 15),
            attributes=Attributes(strength=15, dexterity=13),
            combat_stats=CombatStats(TE=60, VE=70),
        )
        assert not can_wield_one_handed(unit, variable_weapon, strength_req=16, dex_req=13)

    def test_no_attributes(self, variable_weapon):
        """Unit without attributes cannot wield 1-handed."""
        unit = Unit(
            id="no_attrs",
            name="No Attributes",
            position=Position(0, 0),
            fp=ResourcePool(20, 20),
            ep=ResourcePool(15, 15),
            attributes=None,
            combat_stats=CombatStats(TE=60, VE=70),
        )
        assert not can_wield_one_handed(unit, variable_weapon, strength_req=16, dex_req=13)


# --- Test Wielding Bonuses ---


class TestWieldingBonuses:
    """Test bonus calculation for 2-handed wielding."""

    def test_bonuses_with_requirements_and_2h(self):
        """Bonuses apply when unit meets reqs and wields 2-handed."""
        bonuses = calculate_wielding_bonuses(
            can_wield_one_handed=True, wielding_two_handed=True, ke_bonus=2, te_bonus=5, ve_bonus=3
        )
        assert bonuses.ke_bonus == 2
        assert bonuses.te_bonus == 5
        assert bonuses.ve_bonus == 3
        assert bonuses.is_active()

    def test_no_bonuses_without_requirements(self):
        """No bonuses if unit doesn't meet requirements."""
        bonuses = calculate_wielding_bonuses(
            can_wield_one_handed=False, wielding_two_handed=True, ke_bonus=2, te_bonus=5, ve_bonus=3
        )
        assert bonuses.ke_bonus == 0
        assert bonuses.te_bonus == 0
        assert bonuses.ve_bonus == 0
        assert not bonuses.is_active()

    def test_no_bonuses_wielding_1h(self):
        """No bonuses if wielding 1-handed."""
        bonuses = calculate_wielding_bonuses(
            can_wield_one_handed=True, wielding_two_handed=False, ke_bonus=2, te_bonus=5, ve_bonus=3
        )
        assert bonuses.ke_bonus == 0
        assert bonuses.te_bonus == 0
        assert bonuses.ve_bonus == 0
        assert not bonuses.is_active()

    def test_zero_bonuses(self):
        """Handle weapons with zero bonuses."""
        bonuses = calculate_wielding_bonuses(
            can_wield_one_handed=True, wielding_two_handed=True, ke_bonus=0, te_bonus=0, ve_bonus=0
        )
        assert not bonuses.is_active()

    def test_partial_bonuses(self):
        """Some stats have bonuses, others don't."""
        bonuses = calculate_wielding_bonuses(
            can_wield_one_handed=True, wielding_two_handed=True, ke_bonus=0, te_bonus=5, ve_bonus=0
        )
        assert bonuses.ke_bonus == 0
        assert bonuses.te_bonus == 5
        assert bonuses.ve_bonus == 0
        assert bonuses.is_active()


# --- Test Wielding Mode Determination ---


class TestWieldingMode:
    """Test wielding mode determination."""

    def test_variable_with_requirements_defaults_1h(self, strong_unit, variable_weapon):
        """Variable weapon with requirements defaults to 1-handed."""
        mode = get_wielding_mode(
            strong_unit, variable_weapon, wield_mode=WieldMode.VARIABLE, strength_req=16, dex_req=13
        )
        assert mode == WieldMode.ONE_HANDED

    def test_variable_with_requirements_prefers_2h(self, strong_unit, variable_weapon):
        """Variable weapon with requirements respects 2-handed preference."""
        mode = get_wielding_mode(
            strong_unit,
            variable_weapon,
            wield_mode=WieldMode.VARIABLE,
            strength_req=16,
            dex_req=13,
            preference=WieldMode.TWO_HANDED,
        )
        assert mode == WieldMode.TWO_HANDED

    def test_variable_without_requirements_forced_2h(self, weak_unit, variable_weapon):
        """Variable weapon without requirements forces 2-handed."""
        mode = get_wielding_mode(
            weak_unit, variable_weapon, wield_mode=WieldMode.VARIABLE, strength_req=16, dex_req=13
        )
        assert mode == WieldMode.TWO_HANDED

    def test_variable_without_reqs_ignores_preference(self, weak_unit, variable_weapon):
        """Preference ignored if requirements not met."""
        mode = get_wielding_mode(
            weak_unit,
            variable_weapon,
            wield_mode=WieldMode.VARIABLE,
            strength_req=16,
            dex_req=13,
            preference=WieldMode.ONE_HANDED,
        )
        assert mode == WieldMode.TWO_HANDED

    def test_fixed_1h_weapon(self, strong_unit, fixed_weapon):
        """Fixed 1-handed weapon stays 1-handed."""
        mode = get_wielding_mode(
            strong_unit, fixed_weapon, wield_mode=WieldMode.ONE_HANDED, strength_req=0, dex_req=0
        )
        assert mode == WieldMode.ONE_HANDED

    def test_fixed_2h_weapon(self, strong_unit, variable_weapon):
        """Fixed 2-handed weapon stays 2-handed."""
        mode = get_wielding_mode(
            strong_unit, variable_weapon, wield_mode=WieldMode.TWO_HANDED, strength_req=0, dex_req=0
        )
        assert mode == WieldMode.TWO_HANDED


# --- Test Complete Wielding Info ---


class TestWieldingInfo:
    """Test complete wielding information."""

    def test_variable_strong_unit_1h(self, strong_unit, variable_weapon):
        """Strong unit with variable weapon choosing 1-handed."""
        info = get_wielding_info(
            strong_unit,
            variable_weapon,
            wield_mode=WieldMode.VARIABLE,
            strength_req=16,
            dex_req=13,
            te_bonus=5,
            ve_bonus=3,
        )
        assert info.mode == WieldMode.ONE_HANDED
        assert info.can_choose
        assert not info.forced_two_handed
        assert info.meets_requirements
        assert not info.bonuses.is_active()

    def test_variable_strong_unit_2h(self, strong_unit, variable_weapon):
        """Strong unit with variable weapon choosing 2-handed."""
        info = get_wielding_info(
            strong_unit,
            variable_weapon,
            wield_mode=WieldMode.VARIABLE,
            strength_req=16,
            dex_req=13,
            te_bonus=5,
            ve_bonus=3,
            preference=WieldMode.TWO_HANDED,
        )
        assert info.mode == WieldMode.TWO_HANDED
        assert info.can_choose
        assert not info.forced_two_handed
        assert info.meets_requirements
        assert info.bonuses.is_active()
        assert info.bonuses.te_bonus == 5
        assert info.bonuses.ve_bonus == 3

    def test_variable_weak_unit_forced_2h(self, weak_unit, variable_weapon):
        """Weak unit forced to use 2-handed (no bonuses)."""
        info = get_wielding_info(
            weak_unit,
            variable_weapon,
            wield_mode=WieldMode.VARIABLE,
            strength_req=16,
            dex_req=13,
            te_bonus=5,
            ve_bonus=3,
        )
        assert info.mode == WieldMode.TWO_HANDED
        assert not info.can_choose
        assert info.forced_two_handed
        assert not info.meets_requirements
        assert not info.bonuses.is_active()

    def test_fixed_1h_weapon_info(self, strong_unit, fixed_weapon):
        """Fixed 1-handed weapon info."""
        info = get_wielding_info(strong_unit, fixed_weapon, wield_mode=WieldMode.ONE_HANDED)
        assert info.mode == WieldMode.ONE_HANDED
        assert not info.can_choose
        assert not info.forced_two_handed
        assert info.meets_requirements
        assert not info.bonuses.is_active()

    def test_fixed_2h_weapon_info(self, strong_unit, variable_weapon):
        """Fixed 2-handed weapon info."""
        info = get_wielding_info(strong_unit, variable_weapon, wield_mode=WieldMode.TWO_HANDED)
        assert info.mode == WieldMode.TWO_HANDED
        assert not info.can_choose
        assert info.forced_two_handed
        assert info.meets_requirements
        assert not info.bonuses.is_active()


# --- Test Mode Validation ---


class TestModeValidation:
    """Test wielding mode change validation."""

    def test_can_change_to_1h_with_requirements(self, strong_unit, variable_weapon):
        """Can change to 1-handed if requirements met."""
        valid = validate_wielding_mode_change(
            strong_unit,
            variable_weapon,
            wield_mode=WieldMode.VARIABLE,
            new_mode=WieldMode.ONE_HANDED,
            strength_req=16,
            dex_req=13,
        )
        assert valid

    def test_cannot_change_to_1h_without_requirements(self, weak_unit, variable_weapon):
        """Cannot change to 1-handed without requirements."""
        valid = validate_wielding_mode_change(
            weak_unit,
            variable_weapon,
            wield_mode=WieldMode.VARIABLE,
            new_mode=WieldMode.ONE_HANDED,
            strength_req=16,
            dex_req=13,
        )
        assert not valid

    def test_can_always_change_to_2h(self, weak_unit, variable_weapon):
        """Can always change to 2-handed."""
        valid = validate_wielding_mode_change(
            weak_unit,
            variable_weapon,
            wield_mode=WieldMode.VARIABLE,
            new_mode=WieldMode.TWO_HANDED,
            strength_req=16,
            dex_req=13,
        )
        assert valid

    def test_cannot_change_fixed_weapon(self, strong_unit, fixed_weapon):
        """Cannot change mode of fixed weapon."""
        valid = validate_wielding_mode_change(
            strong_unit,
            fixed_weapon,
            wield_mode=WieldMode.ONE_HANDED,
            new_mode=WieldMode.TWO_HANDED,
            strength_req=0,
            dex_req=0,
        )
        assert not valid


# --- Test Edge Cases ---


class TestWieldingEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_all_zero_bonuses(self, strong_unit, variable_weapon):
        """Variable weapon with zero bonuses."""
        info = get_wielding_info(
            strong_unit,
            variable_weapon,
            wield_mode=WieldMode.VARIABLE,
            strength_req=16,
            dex_req=13,
            ke_bonus=0,
            te_bonus=0,
            ve_bonus=0,
            preference=WieldMode.TWO_HANDED,
        )
        assert not info.bonuses.is_active()

    def test_high_requirements(self, strong_unit, variable_weapon):
        """Requirements higher than unit's attributes."""
        info = get_wielding_info(
            strong_unit,
            variable_weapon,
            wield_mode=WieldMode.VARIABLE,
            strength_req=25,
            dex_req=25,
            te_bonus=10,
            ve_bonus=8,
        )
        assert info.forced_two_handed
        assert not info.bonuses.is_active()

    def test_zero_requirements(self, weak_unit, variable_weapon):
        """Variable weapon with zero requirements."""
        info = get_wielding_info(
            weak_unit,
            variable_weapon,
            wield_mode=WieldMode.VARIABLE,
            strength_req=0,
            dex_req=0,
            te_bonus=5,
            ve_bonus=3,
        )
        assert info.can_choose
        assert not info.forced_two_handed

    def test_unknown_wield_mode(self, strong_unit, variable_weapon):
        """Unknown wield mode defaults to 1-handed."""
        info = get_wielding_info(strong_unit, variable_weapon, wield_mode="unknown")
        assert info.mode == WieldMode.ONE_HANDED
        assert not info.can_choose
