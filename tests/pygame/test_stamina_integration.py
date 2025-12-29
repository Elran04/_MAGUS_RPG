"""Integration tests for stamina costs inside attack resolution and regeneration/fatigue hooks."""

import pytest
from domain.entities import Unit, Weapon
from domain.mechanics import (
    AttackOutcome,
    Stamina,
    StaminaState,
    apply_attack_result,
    create_fatigue_condition,
    resolve_attack,
)
from domain.value_objects import Attributes, CombatStats, Position, ResourcePool

# --- Fixtures ---


@pytest.fixture
def attacker():
    return Unit(
        id="att",
        name="Attacker",
        position=Position(0, 0),
        fp=ResourcePool(40, 40),
        ep=ResourcePool(30, 30),
        attributes=Attributes(strength=16, dexterity=14, endurance=12),
        combat_stats=CombatStats(TE=50),
        weapon=Weapon(
            id="sword",
            name="Sword",
            te_modifier=10,
            ve_modifier=8,
            damage_min=2,
            damage_max=8,
            size_category=2,
        ),
    )


@pytest.fixture
def defender():
    return Unit(
        id="def",
        name="Defender",
        position=Position(1, 0),
        fp=ResourcePool(40, 40),
        ep=ResourcePool(30, 30),
        attributes=Attributes(strength=14, dexterity=12, endurance=10),
        combat_stats=CombatStats(VE=55),
        weapon=Weapon(
            id="parry",
            name="Parry Blade",
            te_modifier=5,
            ve_modifier=6,
            damage_min=1,
            damage_max=6,
            size_category=2,
        ),
    )


# --- Helper ---


def fp(defender):
    return defender.fp.current


# --- Tests ---


class TestBlockParryStamina:
    def test_block_stamina_cost(self, attacker, defender):
        # Make attack roll fall into BLOCKED range: base_VE < all_TE <= block_VE
        # base VE 55, give shield_ve 5 -> block_ve 60; attack TE = 50+10+55 =115 > threshold, adjust with conditions
        # We'll lower attack roll artificially to get into window.
        attacker.combat_stats = CombatStats(TE=10)  # reduce TE for controlled range
        start_fp = fp(defender)
        result = resolve_attack(
            attacker,
            defender,
            attack_roll=5,  # TE: 10 + 10 + 5 = 25
            base_damage_roll=5,
            shield_ve=5,  # modest shield bonus
            stamina_block={"skill_level": 0},
        )
        # base_VE=55 -> block_ve=60; all_te=25 => MISS
        assert result.outcome == AttackOutcome.MISS
        # Adjust into block window: increase attack_roll to land between 56 and 60
        result = resolve_attack(
            attacker,
            defender,
            attack_roll=40,  # all_te = 10 +10 +40 =60 -> BLOCK (==block_ve)
            base_damage_roll=5,
            shield_ve=5,
            stamina_block={"skill_level": 0},
        )
        assert result.outcome == AttackOutcome.BLOCKED
        # Need to apply result to modify defender FP
        apply_attack_result(result, defender)
        apply_fp_loss = start_fp - defender.fp.current
        assert apply_fp_loss == result.damage_to_fp
        assert result.damage_to_fp > 0

    def test_parry_stamina_cost(self, attacker, defender):
        attacker.combat_stats = CombatStats(TE=15)
        start_fp = fp(defender)
        result = resolve_attack(
            attacker,
            defender,
            attack_roll=35,  # all_te = 15 + 10 + 35 = 60 -> PARRIED (between 56..61)
            base_damage_roll=6,
            shield_ve=0,
            stamina_parry={"skill_level": 0},
        )
        assert result.outcome == AttackOutcome.PARRIED
        # Apply to mutate defender
        apply_attack_result(result, defender)
        assert result.damage_to_fp > 0
        assert defender.fp.current < start_fp


class TestDodgeStamina:
    def test_dodge_attempt_costs_stamina(self, attacker, defender):
        attacker.combat_stats = CombatStats(TE=20)
        start_fp = fp(defender)
        # Need all_te between parry_ve+1 and dodge_ve inclusive.
        # Defender VE=55, weapon ve=6 -> parry_ve=61. Use dodge_modifier=10 -> dodge_ve=71.
        # Configure attacker TE low enough to land in that band.
        attacker.combat_stats = CombatStats(TE=5)
        result = resolve_attack(
            attacker,
            defender,
            attack_roll=50,  # all_te = 5 + weapon_te(10) + 50 = 65 -> within dodge window (62..71)
            base_damage_roll=4,
            dodge_modifier=10,
            stamina_dodge={"min_cost": 4, "multiplier": 1.0},
        )
        assert result.outcome == AttackOutcome.DODGE_ATTEMPT
        # Dodge consumes stamina immediately
        # Must apply to mutate defender FP
        apply_attack_result(result, defender)
        assert result.stamina_spent_defender > 0
        assert defender.fp.current == start_fp - result.stamina_spent_defender


class TestRegeneration:
    def test_regenerate_tick_resting(self):
        sta = Stamina.from_attribute(10)
        sta.apply_cost(30)
        before = sta.current_stamina
        gained = sta.regenerate_tick(resting=True)
        assert gained > 0
        assert sta.current_stamina == before + gained

    def test_regenerate_tick_intense(self):
        sta = Stamina.from_attribute(10)
        sta.apply_cost(20)
        before = sta.current_stamina
        gained = sta.regenerate_tick(intense=True)
        assert gained == 0
        assert sta.current_stamina == before


class TestFatigueConditionHook:
    def test_fatigue_condition_creation(self):
        sta = Stamina.from_attribute(10)
        sta.current_stamina = 15  # 15% -> Kimerült
        _, state = sta.get_state()
        cond = create_fatigue_condition(state, note="Turn penalty TBD")
        assert cond.severity == StaminaState.KIMERULT
        assert "penalty" in cond.note.lower()
