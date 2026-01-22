"""Unit tests for injury condition system."""

import pytest
from MAGUS_pygame.domain.mechanics.injury import (
    InjuryCondition,
    InjuryModifiers,
    calculate_injury_condition,
    get_injury_modifiers,
)


class TestInjuryConditionCalculation:
    """Test injury condition determination based on FP/EP thresholds."""

    def test_healthy_full_resources(self):
        """No injury when FP and EP are above 75%."""
        condition = calculate_injury_condition(current_fp=100, max_fp=100, current_ep=100, max_ep=100)
        assert condition == InjuryCondition.NONE

    def test_healthy_at_76_percent(self):
        """No injury at exactly 76% FP/EP."""
        condition = calculate_injury_condition(current_fp=100, max_fp=100, current_ep=100, max_ep=100)
        assert condition == InjuryCondition.NONE

    def test_light_injury_fp_threshold(self):
        """Light injury when FP drops to 75% (rounded down)."""
        # 75% of 100 = 75, so current_fp=75 should trigger light
        condition = calculate_injury_condition(current_fp=75, max_fp=100, current_ep=100, max_ep=100)
        assert condition == InjuryCondition.LIGHT

    def test_light_injury_fp_below_threshold(self):
        """Light injury when FP below 75%."""
        condition = calculate_injury_condition(current_fp=60, max_fp=100, current_ep=100, max_ep=100)
        assert condition == InjuryCondition.LIGHT

    def test_serious_injury_any_ep_damage(self):
        """Serious injury overrides light when any EP damage taken."""
        condition = calculate_injury_condition(current_fp=75, max_fp=100, current_ep=99, max_ep=100)
        assert condition == InjuryCondition.SERIOUS

    def test_serious_injury_ep_below_max(self):
        """Serious injury when EP < max."""
        condition = calculate_injury_condition(current_fp=100, max_fp=100, current_ep=80, max_ep=100)
        assert condition == InjuryCondition.SERIOUS

    def test_critical_injury_ep_at_75_percent(self):
        """Critical injury when EP at exactly 75%."""
        # 75% of 100 = 75
        condition = calculate_injury_condition(current_fp=100, max_fp=100, current_ep=75, max_ep=100)
        assert condition == InjuryCondition.CRITICAL

    def test_critical_injury_ep_below_75_percent(self):
        """Critical injury when EP below 75%."""
        condition = calculate_injury_condition(current_fp=100, max_fp=100, current_ep=50, max_ep=100)
        assert condition == InjuryCondition.CRITICAL

    def test_critical_overrides_all(self):
        """Critical injury has highest priority."""
        # Both FP and EP low, critical should win
        condition = calculate_injury_condition(current_fp=10, max_fp=100, current_ep=60, max_ep=100)
        assert condition == InjuryCondition.CRITICAL

    def test_rounding_fp_threshold(self):
        """Test FP threshold rounding (int cast floors)."""
        # 75% of 13 = 9.75, int() = 9
        # current_fp=9 should trigger light (<=9)
        condition = calculate_injury_condition(current_fp=9, max_fp=13, current_ep=13, max_ep=13)
        assert condition == InjuryCondition.LIGHT

        # current_fp=10 should be healthy (>9)
        condition = calculate_injury_condition(current_fp=10, max_fp=13, current_ep=13, max_ep=13)
        assert condition == InjuryCondition.NONE

    def test_rounding_ep_threshold(self):
        """Test EP threshold rounding."""
        # 75% of 13 = 9.75, int() = 9
        # current_ep=9 should trigger critical (<=9)
        condition = calculate_injury_condition(current_fp=13, max_fp=13, current_ep=9, max_ep=13)
        assert condition == InjuryCondition.CRITICAL

        # current_ep=10 should be serious (any damage but not critical)
        condition = calculate_injury_condition(current_fp=13, max_fp=13, current_ep=10, max_ep=13)
        assert condition == InjuryCondition.SERIOUS


class TestInjuryModifiers:
    """Test injury modifier retrieval."""

    def test_healthy_no_penalties(self):
        """Healthy condition has no modifiers."""
        mods = get_injury_modifiers(InjuryCondition.NONE)
        assert mods.ke_mod == 0
        assert mods.te_mod == 0
        assert mods.ve_mod == 0
        assert mods.ce_mod == 0

    def test_light_injury_penalties(self):
        """Light injury: -5 KÉ, -10 TÉ, -10 VÉ, -5 CÉ."""
        mods = get_injury_modifiers(InjuryCondition.LIGHT)
        assert mods.ke_mod == -5
        assert mods.te_mod == -10
        assert mods.ve_mod == -10
        assert mods.ce_mod == -5

    def test_serious_injury_penalties(self):
        """Serious injury: -10 KÉ, -20 TÉ, -20 VÉ, -10 CÉ."""
        mods = get_injury_modifiers(InjuryCondition.SERIOUS)
        assert mods.ke_mod == -10
        assert mods.te_mod == -20
        assert mods.ve_mod == -20
        assert mods.ce_mod == -10

    def test_critical_injury_penalties(self):
        """Critical injury: -15 KÉ, -25 TÉ, -25 VÉ, -15 CÉ."""
        mods = get_injury_modifiers(InjuryCondition.CRITICAL)
        assert mods.ke_mod == -15
        assert mods.te_mod == -25
        assert mods.ve_mod == -25
        assert mods.ce_mod == -15


class TestInjuryProgression:
    """Test injury condition progression as damage accumulates."""

    def test_progression_fp_to_light(self):
        """Unit starts healthy, takes FP damage, becomes light."""
        # Start healthy
        condition = calculate_injury_condition(100, 100, 100, 100)
        assert condition == InjuryCondition.NONE

        # Take FP damage to 75%
        condition = calculate_injury_condition(75, 100, 100, 100)
        assert condition == InjuryCondition.LIGHT

    def test_progression_light_to_serious(self):
        """Light injury escalates to serious when EP damaged."""
        # Light (FP low, EP full)
        condition = calculate_injury_condition(50, 100, 100, 100)
        assert condition == InjuryCondition.LIGHT

        # Take any EP damage -> serious
        condition = calculate_injury_condition(50, 100, 99, 100)
        assert condition == InjuryCondition.SERIOUS

    def test_progression_serious_to_critical(self):
        """Serious injury escalates to critical when EP drops to 75%."""
        # Serious (any EP damage)
        condition = calculate_injury_condition(100, 100, 90, 100)
        assert condition == InjuryCondition.SERIOUS

        # EP drops to 75% -> critical
        condition = calculate_injury_condition(100, 100, 75, 100)
        assert condition == InjuryCondition.CRITICAL

    def test_direct_to_critical(self):
        """Massive EP damage can skip conditions."""
        # Start healthy
        condition = calculate_injury_condition(100, 100, 100, 100)
        assert condition == InjuryCondition.NONE

        # Massive hit drops EP to 50% -> critical
        condition = calculate_injury_condition(100, 100, 50, 100)
        assert condition == InjuryCondition.CRITICAL


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_fp_ep(self):
        """Zero FP/EP should be critical."""
        condition = calculate_injury_condition(0, 100, 0, 100)
        assert condition == InjuryCondition.CRITICAL

    def test_negative_values(self):
        """Negative current values (death) should still calculate correctly."""
        condition = calculate_injury_condition(-10, 100, -5, 100)
        assert condition == InjuryCondition.CRITICAL

    def test_low_max_values(self):
        """Small max values should calculate thresholds correctly."""
        # max_fp=10, 75%=7 (int), current=7 -> light
        condition = calculate_injury_condition(7, 10, 10, 10)
        assert condition == InjuryCondition.LIGHT

        # max_ep=10, 75%=7, current=7 -> critical
        condition = calculate_injury_condition(10, 10, 7, 10)
        assert condition == InjuryCondition.CRITICAL

    def test_single_point_thresholds(self):
        """Very low max values (1-2) edge cases."""
        # max_fp=1, 75%=0 (int), current=0 -> light
        condition = calculate_injury_condition(0, 1, 1, 1)
        assert condition == InjuryCondition.LIGHT

        # max_ep=1, 75%=0, current=0 -> critical
        condition = calculate_injury_condition(1, 1, 0, 1)
        assert condition == InjuryCondition.CRITICAL
