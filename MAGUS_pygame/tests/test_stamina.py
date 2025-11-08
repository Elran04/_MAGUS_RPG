"""Tests for stamina subsystem."""

import math
import pytest

from domain.mechanics import (
    Stamina,
    StaminaState,
    CombatModifiers,
    DEFAULT_COMBAT_MODIFIERS,
)


class TestInitialization:
    def test_from_attribute_full(self):
        s = Stamina.from_attribute(allokepesseg=12)  # 12 * 10 = 120
        assert s.max_stamina == 120
        assert s.current_stamina == 120
        assert s.attribute_ref == 12

    def test_from_attribute_with_bonus_and_half(self):
        s = Stamina.from_attribute(allokepesseg=10, skill_bonus_max=15, start_full=False)
        # 10*10 + 15 = 115, half start rounds down
        assert s.max_stamina == 115
        assert s.current_stamina == 57


class TestApplyCost:
    def test_basic_cost(self):
        s = Stamina.from_attribute(10)  # 100
        spent = s.apply_cost(12)
        assert spent == 12
        assert s.current_stamina == 88

    def test_zero_cost(self):
        s = Stamina.from_attribute(10)
        spent = s.apply_cost(0)
        assert spent == 0
        assert s.current_stamina == 100

    def test_skill_absorption(self):
        s = Stamina.from_attribute(10)  # 100
        # base=10, skill_level=3 -> absorb 3 -> cost=7
        spent = s.apply_cost(10, {"skill_level": 3})
        assert spent == 7
        assert s.current_stamina == 93

    def test_absorption_and_flat_reduction(self):
        s = Stamina.from_attribute(10)
        # base=12, absorb=4 -> 8, flat_reduction=3 -> 5
        spent = s.apply_cost(12, {"absorption": 4, "flat_reduction": 3})
        assert spent == 5
        assert s.current_stamina == 95

    def test_multiplier_penalty(self):
        s = Stamina.from_attribute(10)
        # base=10, *1.5 -> 15 (rounded)
        spent = s.apply_cost(10, {"multiplier": 1.5})
        assert spent == 15
        assert s.current_stamina == 85

    def test_multiple_multipliers(self):
        s = Stamina.from_attribute(10)
        # base=10, *1.2*1.1=1.32 -> 13 (rounded)
        spent = s.apply_cost(10, {"multipliers": [1.2, 1.1]})
        assert spent == 13
        assert s.current_stamina == 87

    def test_min_cost_floor(self):
        s = Stamina.from_attribute(10)
        # base=10, absorb 9 -> 1, min_cost 3 -> 3
        spent = s.apply_cost(10, {"absorption": 9, "min_cost": 3})
        assert spent == 3
        assert s.current_stamina == 97

    def test_cannot_go_negative(self):
        s = Stamina.from_attribute(1)  # 10
        spent = s.apply_cost(50)
        assert spent == 10
        assert s.current_stamina == 0


class TestRecovery:
    def test_recover_basic(self):
        s = Stamina.from_attribute(10)  # 100
        s.apply_cost(30)
        rec = s.recover(15)
        assert rec == 15
        assert s.current_stamina == 85

    def test_recover_caps_at_max(self):
        s = Stamina.from_attribute(10)  # 100
        s.apply_cost(5)
        rec = s.recover(50)
        assert rec == 5
        assert s.current_stamina == 100


class TestThresholds:
    def test_state_boundaries(self):
        s = Stamina.from_attribute(10)  # 100
        # 100 -> FRISS
        r, st = s.get_state()
        assert st == StaminaState.FRISS
        # 80 -> FRISS (80%)
        s.current_stamina = 80
        r, st = s.get_state()
        assert st == StaminaState.FRISS
        # 79 -> FELPEZSDULT
        s.current_stamina = 79
        r, st = s.get_state()
        assert st == StaminaState.FELPEZSDULT
        # 60 -> FELPEZSDULT
        s.current_stamina = 60
        r, st = s.get_state()
        assert st == StaminaState.FELPEZSDULT
        # 59 -> KIFULLADT
        s.current_stamina = 59
        r, st = s.get_state()
        assert st == StaminaState.KIFULLADT
        # 40 -> KIFULLADT
        s.current_stamina = 40
        r, st = s.get_state()
        assert st == StaminaState.KIFULLADT
        # 39 -> KIFARADT
        s.current_stamina = 39
        r, st = s.get_state()
        assert st == StaminaState.KIFARADT
        # 20 -> KIFARADT
        s.current_stamina = 20
        r, st = s.get_state()
        assert st == StaminaState.KIFARADT
        # 19 -> KIMERULT
        s.current_stamina = 19
        r, st = s.get_state()
        assert st == StaminaState.KIMERULT
        # 0 -> KIMERULT
        s.current_stamina = 0
        r, st = s.get_state()
        assert st == StaminaState.KIMERULT

    def test_ratio_bounds(self):
        s = Stamina.from_attribute(10)
        s.current_stamina = -10
        assert s.ratio() == 0.0
        s.current_stamina = 150
        assert s.ratio() == 1.0


class TestCombatModifiers:
    def test_default_mapping(self):
        s = Stamina.from_attribute(10)  # FRISS
        mods = s.get_combat_modifiers()
        assert mods.te_mod == 0 and mods.ve_mod == 0
        s.current_stamina = 70  # FELPEZSDULT
        mods = s.get_combat_modifiers()
        assert mods.te_mod <= 0 and mods.ve_mod <= 0
        s.current_stamina = 10  # KIMERULT
        mods = s.get_combat_modifiers()
        assert mods.te_mod <= -6 and mods.ve_mod <= -6

    def test_custom_mapping(self):
        custom = dict(DEFAULT_COMBAT_MODIFIERS)
        custom[StaminaState.KIMERULT] = CombatModifiers(-10, -10)
        s = Stamina.from_attribute(10, start_full=False, combat_modifiers_map=custom)
        s.current_stamina = 10
        mods = s.get_combat_modifiers()
        assert mods.te_mod == -10 and mods.ve_mod == -10


class TestFlags:
    def test_exhausted_and_unconscious(self):
        s = Stamina.from_attribute(10)
        assert not s.is_exhausted()
        assert not s.is_unconscious()
        s.current_stamina = 10  # 10%
        assert s.is_exhausted()
        assert not s.is_unconscious()
        s.current_stamina = 0
        assert s.is_unconscious()
        assert s.requires_exhaustion_save() is False  # already unconscious


class TestSpendAP:
    def test_spend_action_points_alias(self):
        s = Stamina.from_attribute(10)
        spent = s.spend_action_points(5, multiplier=2.0)
        assert spent == 10
        assert s.current_stamina == 90
