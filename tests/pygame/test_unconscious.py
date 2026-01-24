"""Unit tests for unconscious mechanics in combat."""

import pytest

from MAGUS_pygame.domain.entities import Unit, Weapon
from MAGUS_pygame.domain.mechanics.attack_resolution import (
    AttackOutcome,
    calculate_attack_value,
    calculate_defense_values,
    resolve_attack,
)
from MAGUS_pygame.domain.mechanics.stamina import Stamina
from MAGUS_pygame.domain.value_objects import Attributes, CombatStats, Position, ResourcePool


@pytest.fixture
def base_weapon():
    """Standard weapon for testing."""
    return Weapon(
        id="sword",
        name="Sword",
        te_modifier=10,
        ve_modifier=8,
        damage_min=5,
        damage_max=10,
        size_category=2,
        damage_bonus_attributes=["erő"],
        attack_time=5,
    )


@pytest.fixture
def conscious_attacker(base_weapon):
    """Attacker with stamina above zero."""
    unit = Unit(
        id="att",
        name="Attacker",
        position=Position(0, 0),
        fp=ResourcePool(20, 20),
        ep=ResourcePool(15, 15),
        attributes=Attributes(strength=16, endurance=10),
        combat_stats=CombatStats(TE=50, VE=45),
        weapon=base_weapon,
    )
    unit.stamina = Stamina.from_attribute(10)  # 100 stamina
    return unit


@pytest.fixture
def unconscious_attacker(base_weapon):
    """Attacker with zero stamina (unconscious)."""
    unit = Unit(
        id="att_unc",
        name="Unconscious Attacker",
        position=Position(0, 0),
        fp=ResourcePool(20, 20),
        ep=ResourcePool(15, 15),
        attributes=Attributes(strength=16, endurance=10),
        combat_stats=CombatStats(TE=50, VE=45),
        weapon=base_weapon,
    )
    unit.stamina = Stamina.from_attribute(10)
    unit.stamina.current_stamina = 0  # Set to unconscious
    return unit


@pytest.fixture
def conscious_defender(base_weapon):
    """Defender with stamina above zero."""
    unit = Unit(
        id="def",
        name="Defender",
        position=Position(1, 0),
        fp=ResourcePool(20, 20),
        ep=ResourcePool(15, 15),
        attributes=Attributes(strength=14, endurance=10),
        combat_stats=CombatStats(TE=45, VE=60),
        weapon=base_weapon,
    )
    unit.stamina = Stamina.from_attribute(10)
    return unit


@pytest.fixture
def unconscious_defender(base_weapon):
    """Defender with zero stamina (unconscious)."""
    unit = Unit(
        id="def_unc",
        name="Unconscious Defender",
        position=Position(1, 0),
        fp=ResourcePool(20, 20),
        ep=ResourcePool(15, 15),
        attributes=Attributes(strength=14, endurance=10),
        combat_stats=CombatStats(TE=45, VE=60),
        weapon=base_weapon,
    )
    unit.stamina = Stamina.from_attribute(10)
    unit.stamina.current_stamina = 0
    return unit


class TestUnconsciousAttacker:
    """Test unconscious attacker mechanics."""

    def test_unconscious_attacker_zero_attack_value(self, unconscious_attacker, base_weapon):
        """Unconscious attacker has attack value forced to zero."""
        attack_value = calculate_attack_value(
            attacker=unconscious_attacker,
            attack_roll=75,  # Would normally contribute
            weapon=base_weapon,
        )
        assert attack_value == 0

    def test_unconscious_attacker_cannot_crit(self, unconscious_attacker, conscious_defender):
        """Unconscious attacker cannot land critical hits."""
        result = resolve_attack(
            attacker=unconscious_attacker,
            defender=conscious_defender,
            attack_roll=99,  # Would normally be critical
            base_damage_roll=8,
            weapon_skill_level=5,  # High skill
        )
        assert result.is_critical is False

    def test_unconscious_attacker_always_misses(self, unconscious_attacker, conscious_defender):
        """Unconscious attacker always misses due to zero TÉ."""
        result = resolve_attack(
            attacker=unconscious_attacker,
            defender=conscious_defender,
            attack_roll=100,  # Max roll
            base_damage_roll=10,
        )
        assert result.outcome == AttackOutcome.MISS
        assert result.hit is False
        assert result.damage_to_fp == 0
        assert result.damage_to_ep == 0


class TestUnconsciousDefender:
    """Test unconscious defender mechanics."""

    def test_unconscious_defender_zero_defense_values(self, unconscious_defender):
        """Unconscious defender has all defense values set to zero."""
        defense = calculate_defense_values(unconscious_defender)
        assert defense.base_ve == 0
        assert defense.block_ve == 0
        assert defense.parry_ve == 0
        assert defense.dodge_ve == 0
        assert defense.all_ve == 0

    def test_unconscious_defender_auto_hit(self, conscious_attacker, unconscious_defender):
        """Attacks against unconscious defenders always hit."""
        result = resolve_attack(
            attacker=conscious_attacker,
            defender=unconscious_defender,
            attack_roll=50,  # Avoid critical failure (level 1: 1-5 fail)
            base_damage_roll=5,
            weapon_skill_level=1,  # Level 1: failures on 1-5
        )
        # With zero VÉ, even low TÉ should hit
        assert result.hit is True
        assert result.outcome in (
            AttackOutcome.HIT,
            AttackOutcome.CRITICAL,
            AttackOutcome.OVERPOWER,
        )

    def test_unconscious_defender_takes_full_damage(self, conscious_attacker, unconscious_defender):
        """Unconscious defenders cannot block/parry/dodge."""
        result = resolve_attack(
            attacker=conscious_attacker,
            defender=unconscious_defender,
            attack_roll=50,
            base_damage_roll=8,
        )
        # Should be a normal hit or better (not blocked/parried/dodged)
        assert result.outcome not in (
            AttackOutcome.BLOCKED,
            AttackOutcome.PARRIED,
            AttackOutcome.DODGE_ATTEMPT,
        )
        assert result.damage_to_fp > 0 or result.damage_to_ep > 0


class TestBothUnconscious:
    """Test interactions when both units are unconscious."""

    def test_both_unconscious_no_damage(self, unconscious_attacker, unconscious_defender):
        """When both are unconscious, no damage occurs."""
        result = resolve_attack(
            attacker=unconscious_attacker,
            defender=unconscious_defender,
            attack_roll=50,
            base_damage_roll=8,
        )
        assert result.outcome == AttackOutcome.MISS
        assert result.damage_to_fp == 0
        assert result.damage_to_ep == 0


class TestStaminaThreshold:
    """Test unconscious threshold detection."""

    def test_is_unconscious_at_zero(self):
        """is_unconscious() returns True at exactly 0 stamina."""
        stamina = Stamina.from_attribute(10)
        stamina.current_stamina = 0
        assert stamina.is_unconscious() is True

    def test_not_unconscious_above_zero(self):
        """is_unconscious() returns False above 0 stamina."""
        stamina = Stamina.from_attribute(10)
        stamina.current_stamina = 1
        assert stamina.is_unconscious() is False

    def test_exhausted_not_unconscious(self):
        """Kimerült (exhausted) state is not unconscious."""
        stamina = Stamina.from_attribute(10)  # 100
        stamina.current_stamina = 10  # 10% - Kimerült
        assert stamina.is_exhausted() is True
        assert stamina.is_unconscious() is False


class TestUnconsciousWithInjury:
    """Test unconscious combined with injury conditions."""

    def test_unconscious_overrides_injury_penalties(self, unconscious_attacker, conscious_defender):
        """Unconscious state sets combat values to zero regardless of injury."""
        # Give attacker critical injury (low EP) by damaging
        unconscious_attacker.take_damage(10)  # Reduce EP

        # But unconscious overrides everything
        attack_value = calculate_attack_value(
            attacker=unconscious_attacker,
            attack_roll=50,
            weapon=unconscious_attacker.weapon,
        )
        assert attack_value == 0  # Unconscious forces zero

    def test_unconscious_defender_with_injury(self, conscious_attacker, unconscious_defender):
        """Unconscious defender has zero VÉ regardless of injury penalties."""
        # Give defender injury (shouldn't matter) by damaging
        unconscious_defender.spend_fatigue(15)  # Reduce FP

        defense = calculate_defense_values(unconscious_defender)
        assert defense.all_ve == 0  # Unconscious forces zero


class TestRecoveryFromUnconscious:
    """Test mechanics when stamina recovers from zero."""

    def test_recovery_restores_combat_capability(self, unconscious_attacker, conscious_defender):
        """Recovering stamina restores ability to attack."""
        # Initially unconscious
        attack_value_before = calculate_attack_value(
            attacker=unconscious_attacker, attack_roll=50, weapon=unconscious_attacker.weapon
        )
        assert attack_value_before == 0

        # Recover stamina
        unconscious_attacker.stamina.recover(10)

        # Now can attack
        attack_value_after = calculate_attack_value(
            attacker=unconscious_attacker, attack_roll=50, weapon=unconscious_attacker.weapon
        )
        assert attack_value_after > 0

    def test_recovery_restores_defense(self, unconscious_defender):
        """Recovering stamina restores defense values."""
        # Initially zero
        defense_before = calculate_defense_values(unconscious_defender)
        assert defense_before.all_ve == 0

        # Recover stamina
        unconscious_defender.stamina.recover(10)

        # Defense restored
        defense_after = calculate_defense_values(unconscious_defender)
        assert defense_after.all_ve > 0
