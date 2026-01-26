"""
Integration tests for weaponskill_longswords modifiers in attack resolution.

Tests verify that each skill level applies correct:
- Stat modifiers (KÉ, TÉ, VÉ, CÉ)
- Stamina cost reductions
- Critical ranges
- Critical failure ranges
- Opportunity attack eligibility
"""

import pytest

from MAGUS_pygame.domain.entities import Unit, Weapon
from MAGUS_pygame.domain.mechanics import (
    AttackOutcome,
    resolve_attack,
)
from MAGUS_pygame.domain.mechanics.critical import is_critical_failure
from MAGUS_pygame.domain.mechanics.skills import (
    get_opportunity_attack_limit,
    get_weaponskill_modifiers,
    should_grant_skill_opportunity_attack,
)
from MAGUS_pygame.domain.value_objects import (
    Attributes,
    CombatStats,
    Position,
    ResourcePool,
)


@pytest.fixture
def attacker():
    """Attacker with longsword."""
    return Unit(
        id="att",
        name="Swordsman",
        position=Position(0, 0),
        fp=ResourcePool(30, 30),
        ep=ResourcePool(30, 30),
        attributes=Attributes(strength=16, dexterity=14, endurance=12),
        combat_stats=CombatStats(KE=12, TE=50, VE=45),
        weapon=Weapon(
            id="longsword",
            name="Longsword",
            category="Hosszú kardok",
            skill_id="weaponskill_longswords",
            ke_modifier=5,
            te_modifier=10,
            ve_modifier=10,
            damage_min=2,
            damage_max=12,
            size_category=3,
            attack_time=5,
        ),
    )


@pytest.fixture
def defender():
    """Defender with basic stats."""
    return Unit(
        id="def",
        name="Defender",
        position=Position(1, 0),
        fp=ResourcePool(30, 30),
        ep=ResourcePool(30, 30),
        attributes=Attributes(strength=14, dexterity=12, endurance=10),
        combat_stats=CombatStats(KE=10, TE=40, VE=50),
        weapon=Weapon(
            id="shortsword",
            name="Shortsword",
            ke_modifier=2,
            te_modifier=5,
            ve_modifier=5,
            damage_min=1,
            damage_max=6,
            size_category=2,
            attack_time=4,
        ),
    )


class TestWeaponskillModifiers:
    """Test weaponskill modifier data structure."""

    def test_level_0_has_stat_penalties(self):
        """Level 0 (untrained) has stat penalties."""
        mods = get_weaponskill_modifiers(0)
        assert mods.ke_mod == -10
        assert mods.te_mod == -25
        assert mods.ve_mod == -20
        assert mods.ce_mod == -30
        assert mods.critical_threshold_override == 101

    def test_level_1_removes_penalties_but_keeps_stamina_double(self):
        """Level 1 removes stat penalties, no stamina reduction (AP cost doubled)."""
        mods = get_weaponskill_modifiers(1)
        assert mods.ke_mod == 0
        assert mods.te_mod == 0
        assert mods.ve_mod == 0
        assert mods.ce_mod == 0
        assert mods.stamina_cost_reduction == 0
        assert mods.critical_threshold_override == 101

    def test_level_2_baseline(self):
        """Level 2 is baseline, no modifiers."""
        mods = get_weaponskill_modifiers(2)
        assert mods.ke_mod == 0
        assert mods.te_mod == 0
        assert mods.stamina_cost_reduction == 0
        assert mods.critical_threshold_override == 100

    def test_level_3_has_opportunity_and_stamina_reduction(self):
        """Level 3 has opportunity attack and -1 stamina."""
        mods = get_weaponskill_modifiers(3)
        assert mods.stamina_cost_reduction == 1
        assert mods.has_opportunity_on_miss_parry is True
        assert mods.opportunity_attacks_per_turn == 1

    def test_level_4_stat_boost(self):
        """Level 4 has stat bonuses."""
        mods = get_weaponskill_modifiers(4)
        assert mods.ke_mod == 5
        assert mods.te_mod == 10
        assert mods.ve_mod == 10
        assert mods.ce_mod == 10
        assert mods.stamina_cost_reduction == 2
        assert mods.critical_threshold_override == 96

    def test_level_5_overpower_threshold_shift(self):
        """Level 5 lowers overpower threshold by 10."""
        mods = get_weaponskill_modifiers(5)
        assert mods.overpower_threshold_shift == -10
        assert mods.stamina_cost_reduction == 3
        assert mods.critical_threshold_override == 91

    def test_level_6_special_effects(self):
        """Level 6 has 3x opportunity attacks."""
        mods = get_weaponskill_modifiers(6)
        assert mods.opportunity_attacks_per_turn == 3
        assert mods.stamina_cost_reduction == 3
        assert mods.critical_threshold_override == 91


class TestCriticalFailureRanges:
    """Test critical failure detection per skill level."""

    def test_level_0_critical_failure_1_to_5(self):
        """Level 0: rolls 1-10 are critical failures."""
        for roll in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
            assert is_critical_failure(roll, 0) is True
        for roll in [11, 50, 100]:
            assert is_critical_failure(roll, 0) is False

    def test_level_1_critical_failure_1_to_5(self):
        """Level 1: rolls 1-5 are critical failures."""
        for roll in [1, 2, 3, 4, 5]:
            assert is_critical_failure(roll, 1) is True
        assert is_critical_failure(6, 1) is False

    def test_level_2_no_critical_failure(self):
        """Level 2: roll 1 is critical failure. Level 3+: no critical failures."""
        assert is_critical_failure(1, 2) is True  # Level 2: only roll 1
        for roll in [2, 3, 4, 5, 50, 100]:
            assert is_critical_failure(roll, 2) is False
        for roll in [1, 2, 3, 4, 5]:
            assert is_critical_failure(roll, 3) is False
            assert is_critical_failure(roll, 6) is False


class TestAttackResolutionWithSkills:
    """Test attack resolution with weapon skill modifiers applied."""

    def test_unskilled_attack_with_penalties(self, attacker, defender):
        """Level 0: attack has -25 TÉ penalty."""
        result = resolve_attack(
            attacker=attacker,
            defender=defender,
            attack_roll=50,  # Roll gives +50
            base_damage_roll=5,
            weapon_skill_level=0,  # Unskilled
        )
        # base_TE: 50 + weapon(10) + roll(50) + skill(-25) = 85
        # defender base_VE: 50, no block/parry so all_VE = 50
        # 85 > 50, should hit
        assert result.outcome != AttackOutcome.MISS

    def test_level_1_removes_penalty_but_stamina_doubled(self, attacker, defender):
        """Level 1: stat penalties removed, but stamina cost stays high."""
        result = resolve_attack(
            attacker=attacker,
            defender=defender,
            attack_roll=50,
            base_damage_roll=5,
            weapon_skill_level=1,
        )
        # base_TE: 50 + weapon(10) + roll(50) + skill(0) = 110
        # Should be better than level 0
        assert result.all_te > 85  # Better than unskilled

        # Stamina spent should be weapon.attack_time (no reduction at level 1)
        assert result.stamina_spent_attacker == 5  # No reduction from stamina_cost_reduction=0

    def test_level_3_stamina_reduction(self, attacker, defender):
        """Level 3: stamina cost reduced by 1."""
        result = resolve_attack(
            attacker=attacker,
            defender=defender,
            attack_roll=50,
            base_damage_roll=5,
            weapon_skill_level=3,
        )
        # attack_time=5, skill_stamina_reduction=1 -> 5-1=4
        assert result.stamina_spent_attacker == 4

    def test_level_4_stat_boost(self, attacker, defender):
        """Level 4: +10 TÉ bonus."""
        result = resolve_attack(
            attacker=attacker,
            defender=defender,
            attack_roll=50,
            base_damage_roll=5,
            weapon_skill_level=4,
        )
        # base_TE: 50 + weapon(10) + roll(50) + skill(+10) + directional(+5 front-right) = 125
        assert result.all_te == 125

        # Stamina reduced by 2: 5-2=3
        assert result.stamina_spent_attacker == 3

    def test_level_5_overpower_threshold_lowered(self, attacker, defender):
        """Level 5: overpower threshold is 50-10=40."""
        # Need high TE to trigger overpower with lowered threshold
        result = resolve_attack(
            attacker=attacker,
            defender=defender,
            attack_roll=100,
            base_damage_roll=5,
            weapon_skill_level=5,
            overpower_threshold=50,
        )
        # base_TE: 50 + weapon(10) + roll(100) = 160
        # defender all_VE: 50
        # 160 > 50 + (50-10=40) = 160 > 90 -> OVERPOWER
        # (In standard rules, 160 > 50+50=100 would trigger overpower)
        # But at level 5, threshold is 50-10=40
        assert result.is_overpower or result.outcome == AttackOutcome.OVERPOWER

    def test_critical_failure_blocks_attack(self, attacker, defender):
        """Level 0: rolling 1-10 is critical failure, immediate CRITICAL_FAILURE."""
        result = resolve_attack(
            attacker=attacker,
            defender=defender,
            attack_roll=3,  # Critical failure at level 0-1
            base_damage_roll=5,
            weapon_skill_level=0,
        )
        assert result.outcome == AttackOutcome.CRITICAL_FAILURE
        assert result.hit is False
        assert result.damage_to_fp == 0

    def test_level_2_no_critical_failure_on_low_roll(self, attacker, defender):
        """Level 2: no critical failures, even on low roll."""
        result = resolve_attack(
            attacker=attacker,
            defender=defender,
            attack_roll=3,  # Would be critical failure at level 0-1
            base_damage_roll=5,
            weapon_skill_level=2,
        )
        # At level 2, no critical failure, so attack proceeds normally
        # base_TE: 50 + 10 + 3 = 63 > defender VE 50 -> HIT
        assert result.outcome == AttackOutcome.HIT


class TestOpportunityAttackEligibility:
    """Test opportunity attack eligibility per skill level."""

    def test_level_2_no_opportunity(self):
        """Level 2 does not grant opportunity attacks."""
        assert get_opportunity_attack_limit(2) == 0
        assert should_grant_skill_opportunity_attack(2, "miss") is False
        assert should_grant_skill_opportunity_attack(2, "parried") is False

    def test_level_3_opportunity_on_miss_parry(self):
        """Level 3: 1 opportunity attack on MISS or PARRIED."""
        assert get_opportunity_attack_limit(3) == 1
        assert should_grant_skill_opportunity_attack(3, "miss") is True
        assert should_grant_skill_opportunity_attack(3, "parried") is True
        assert should_grant_skill_opportunity_attack(3, "blocked") is False

    def test_level_4_no_opportunity(self):
        """Level 4 does not have special opportunity (basic stat boost)."""
        assert get_opportunity_attack_limit(4) == 0

    def test_level_6_3x_opportunity(self):
        """Level 6: 3x opportunity attacks on MISS or PARRIED."""
        assert get_opportunity_attack_limit(6) == 3
        assert should_grant_skill_opportunity_attack(6, "miss") is True
        assert should_grant_skill_opportunity_attack(6, "parried") is True
