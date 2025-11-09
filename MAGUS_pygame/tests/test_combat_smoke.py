"""
Quick smoke test for combat mechanics.
Run from project root: python -m MAGUS_pygame.tests.test_combat_smoke
"""

import sys
from pathlib import Path

# Add MAGUS_pygame to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from domain.entities import Unit, Weapon
from domain.mechanics import AttackOutcome, resolve_attack
from domain.value_objects import Attributes, CombatStats, Position, ResourcePool


def test_normal_hit():
    """Test normal hit scenario."""
    print("\n=== NORMAL HIT TEST ===")

    weapon = Weapon(
        id="sword",
        name="Sword",
        te_modifier=10,
        ve_modifier=8,
        damage_min=2,
        damage_max=10,
        size_category=2,
        damage_bonus_attributes=["erő"],
    )

    attacker = Unit(
        id="a",
        name="Attacker",
        position=Position(0, 0),
        fp=ResourcePool(20, 20),
        ep=ResourcePool(15, 15),
        attributes=Attributes(strength=18),
        combat_stats=CombatStats(TE=50),
        weapon=weapon,
    )

    defender = Unit(
        id="d",
        name="Defender",
        position=Position(1, 0),
        fp=ResourcePool(20, 20),
        ep=ResourcePool(15, 15),
        combat_stats=CombatStats(VE=60),
    )

    # TÉ: 50 + 10 + 45 = 105, VÉ: 60 → HIT
    result = resolve_attack(
        attacker=attacker,
        defender=defender,
        attack_roll=45,
        base_damage_roll=7,
        weapon_skill_level=2,
    )

    print(f"Outcome: {result.outcome.value}")
    print(f"Hit: {result.hit}")
    print(f"TÉ: {result.all_te}, VÉ: {result.all_ve}")
    print(f"FP damage: {result.damage_to_fp}, EP damage: {result.damage_to_ep}")
    print(f"Mandatory EP: {result.mandatory_ep_loss}")
    print(f"Critical: {result.is_critical}, Overpower: {result.is_overpower}")

    assert result.outcome == AttackOutcome.HIT
    assert result.hit
    assert result.all_te == 105
    assert result.damage_to_fp > 0  # Should deal FP damage

    print("✅ Normal hit test passed")


def test_overpower():
    """Test overpower strike."""
    print("\n=== OVERPOWER TEST ===")

    weapon = Weapon(
        id="sword",
        name="Sword",
        te_modifier=10,
        ve_modifier=8,
        damage_min=2,
        damage_max=10,
        size_category=2,
        damage_bonus_attributes=["erő"],
    )

    attacker = Unit(
        id="a",
        name="Attacker",
        position=Position(0, 0),
        fp=ResourcePool(20, 20),
        ep=ResourcePool(15, 15),
        attributes=Attributes(strength=18),
        combat_stats=CombatStats(TE=50),
        weapon=weapon,
    )

    defender = Unit(
        id="d",
        name="Defender",
        position=Position(1, 0),
        fp=ResourcePool(20, 20),
        ep=ResourcePool(15, 15),
        combat_stats=CombatStats(VE=60),
    )

    # TÉ: 50 + 10 + 88 = 148, VÉ: 60 → 148 > 60 + 50 → OVERPOWER
    result = resolve_attack(
        attacker=attacker,
        defender=defender,
        attack_roll=88,
        base_damage_roll=9,
        weapon_skill_level=2,
    )

    print(f"Outcome: {result.outcome.value}")
    print(f"TÉ: {result.all_te}, VÉ: {result.all_ve}")
    print(f"FP damage: {result.damage_to_fp}, EP damage: {result.damage_to_ep}")
    print(f"Critical: {result.is_critical}, Overpower: {result.is_overpower}")

    assert result.outcome == AttackOutcome.OVERPOWER
    assert result.is_overpower
    assert result.damage_to_ep > 0  # Direct EP damage
    assert result.damage_to_fp == 0  # No FP damage on overpower

    print("✅ Overpower test passed")


def test_critical():
    """Test critical hit."""
    print("\n=== CRITICAL HIT TEST ===")

    weapon = Weapon(
        id="sword",
        name="Sword",
        te_modifier=10,
        ve_modifier=8,
        damage_min=2,
        damage_max=10,
        size_category=2,
        damage_bonus_attributes=["erő"],
    )

    attacker = Unit(
        id="a",
        name="Attacker",
        position=Position(0, 0),
        fp=ResourcePool(20, 20),
        ep=ResourcePool(15, 15),
        attributes=Attributes(strength=18),
        combat_stats=CombatStats(TE=50),
        weapon=weapon,
    )

    defender = Unit(
        id="d",
        name="Defender",
        position=Position(1, 0),
        fp=ResourcePool(20, 20),
        ep=ResourcePool(15, 15),
        combat_stats=CombatStats(VE=60),
    )

    # Roll 96, skill 2 → threshold 95 → CRITICAL
    # TÉ: 50 + 10 + 96 = 156, VÉ: 60
    # 156 > 60 + 50 → Also OVERPOWER (devastating combo!)
    result = resolve_attack(
        attacker=attacker,
        defender=defender,
        attack_roll=96,
        base_damage_roll=6,
        weapon_skill_level=2,
    )

    print(f"Outcome: {result.outcome.value}")
    print(f"TÉ: {result.all_te}, VÉ: {result.all_ve}")
    print(f"FP damage: {result.damage_to_fp}, EP damage: {result.damage_to_ep}")
    print(f"Critical: {result.is_critical}, Overpower: {result.is_overpower}")

    # This is BOTH critical and overpower - a devastating strike!
    assert result.outcome == AttackOutcome.CRITICAL_OVERPOWER
    assert result.is_critical
    assert result.is_overpower
    assert result.damage_to_ep > 0  # CRITICAL_OVERPOWER: Direct EP damage
    assert result.damage_to_fp == 0  # No FP damage for overpower strikes

    print("✅ Critical+Overpower combo test passed")


def test_critical_only():
    """Test pure critical hit (without overpower) - should deal FP damage."""
    print("\n=== PURE CRITICAL HIT TEST ===")

    weapon = Weapon(
        id="sword",
        name="Sword",
        te_modifier=10,
        ve_modifier=8,
        damage_min=2,
        damage_max=10,
        size_category=2,
        damage_bonus_attributes=["erő"],
    )

    attacker = Unit(
        id="a",
        name="Attacker",
        position=Position(0, 0),
        fp=ResourcePool(20, 20),
        ep=ResourcePool(15, 15),
        attributes=Attributes(strength=18),
        combat_stats=CombatStats(TE=50),
        weapon=weapon,
    )

    defender = Unit(
        id="d",
        name="Defender",
        position=Position(1, 0),
        fp=ResourcePool(20, 20),
        ep=ResourcePool(15, 15),
        combat_stats=CombatStats(VE=110),  # High enough VÉ to prevent overpower
    )

    # Roll 97, skill 2 → threshold 95 → CRITICAL
    # TÉ: 50 + 10 + 97 = 157, VÉ: 110
    # 157 NOT > 110 + 50 (160) → Only CRITICAL, not overpower
    result = resolve_attack(
        attacker=attacker,
        defender=defender,
        attack_roll=97,
        base_damage_roll=6,
        weapon_skill_level=2,
    )

    print(f"Outcome: {result.outcome.value}")
    print(f"TÉ: {result.all_te}, VÉ: {result.all_ve}")
    print(f"FP damage: {result.damage_to_fp}, EP damage: {result.damage_to_ep}")
    print(f"Mandatory EP loss: {result.mandatory_ep_loss}")
    print(f"Critical: {result.is_critical}, Overpower: {result.is_overpower}")

    # Pure critical: amplified damage to FP, NOT EP
    assert result.outcome == AttackOutcome.CRITICAL
    assert result.is_critical
    assert not result.is_overpower
    assert result.damage_to_fp > 0  # Goes to FP
    assert result.damage_to_ep == 0  # Not to EP
    assert result.mandatory_ep_loss > 0  # But still has mandatory EP loss

    print("✅ Pure critical hit test passed")


def test_miss():
    """Test miss scenario."""
    print("\n=== MISS TEST ===")

    weapon = Weapon(
        id="sword",
        name="Sword",
        te_modifier=10,
        ve_modifier=8,
        damage_min=2,
        damage_max=10,
        size_category=2,
        damage_bonus_attributes=["erő"],
    )

    attacker = Unit(
        id="a",
        name="Attacker",
        position=Position(0, 0),
        fp=ResourcePool(20, 20),
        ep=ResourcePool(15, 15),
        attributes=Attributes(strength=18),
        combat_stats=CombatStats(TE=50),
        weapon=weapon,
    )

    defender = Unit(
        id="d",
        name="Defender",
        position=Position(1, 0),
        fp=ResourcePool(20, 20),
        ep=ResourcePool(15, 15),
        combat_stats=CombatStats(VE=100),  # High defense
    )

    # TÉ: 50 + 10 + 5 = 65, VÉ: 100 → MISS
    result = resolve_attack(
        attacker=attacker,
        defender=defender,
        attack_roll=5,
        base_damage_roll=7,
        weapon_skill_level=2,
    )

    print(f"Outcome: {result.outcome.value}")
    print(f"TÉ: {result.all_te}, VÉ: {result.all_ve}")
    print(f"FP damage: {result.damage_to_fp}, EP damage: {result.damage_to_ep}")

    assert result.outcome == AttackOutcome.MISS
    assert not result.hit
    assert result.damage_to_fp == 0
    assert result.damage_to_ep == 0

    print("✅ Miss test passed")


if __name__ == "__main__":
    print("🗡️  MAGUS Combat Mechanics Smoke Tests")
    print("=" * 50)

    test_normal_hit()
    test_overpower()
    test_critical()
    test_critical_only()
    test_miss()

    print("\n" + "=" * 50)
    print("✅ All smoke tests passed!")
