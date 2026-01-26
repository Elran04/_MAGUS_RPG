"""Tests for directional attack and defense modifiers.

Tests coverage:
- Attacker TÉ bonuses based on attack angle
  - +10 TÉ for back attacks
  - +5 TÉ for diagonal/side attacks (back-left, back-right, front-left, front-right)
  - +0 TÉ for front attacks
- Defender VÉ restrictions based on attack angle
  - Shield VÉ only applies to front attacks
  - Weapon VÉ only applies to front, front-right, front-left attacks
"""

import pytest

from MAGUS_pygame.domain.entities import Unit, Weapon
from MAGUS_pygame.domain.mechanics.attack_resolution import (
    AttackOutcome,
    resolve_attack,
)
from MAGUS_pygame.domain.value_objects import Attributes, CombatStats, Facing, Position, ResourcePool


@pytest.fixture
def weapon():
    """Standard weapon with VÉ modifier."""
    return Weapon(
        id="sword",
        name="Sword",
        te_modifier=10,
        ve_modifier=8,
        damage_min=3,
        damage_max=12,
        size_category=2,
        damage_bonus_attributes=["strength"],
    )


@pytest.fixture
def attacker():
    """Standard attacker at center."""
    return Unit(
        id="att",
        name="Attacker",
        position=Position(0, 0),
        facing=Facing(0),
        fp=ResourcePool(20, 20),
        ep=ResourcePool(15, 15),
        attributes=Attributes(strength=18, dexterity=14),
        combat_stats=CombatStats(TE=50, VE=45),
    )


@pytest.fixture
def defender(weapon):
    """Standard defender at position."""
    return Unit(
        id="def",
        name="Defender",
        position=Position(0, 0),
        facing=Facing(0),
        fp=ResourcePool(20, 20),
        ep=ResourcePool(15, 15),
        attributes=Attributes(strength=14, dexterity=12),
        combat_stats=CombatStats(TE=45, VE=50),
        weapon=weapon,
    )


class TestAttackerDirectionalBonuses:
    """Test TÉ bonuses based on attack direction."""

    def test_back_attack_plus_10_te(self, weapon):
        """Back attack (+3 direction) grants +10 TÉ."""
        # Attacker at direction 3 (back of defender facing 0)
        attacker = Unit(
            id="att",
            name="Attacker",
            position=Position(-1, 1),  # Direction 3 (SW) = back
            facing=Facing(0),
            fp=ResourcePool(20, 20),
            ep=ResourcePool(15, 15),
            attributes=Attributes(strength=18, dexterity=14),
            combat_stats=CombatStats(TE=50, VE=45),
            weapon=weapon,
        )

        defender = Unit(
            id="def",
            name="Defender",
            position=Position(0, 0),
            facing=Facing(0),
            fp=ResourcePool(20, 20),
            ep=ResourcePool(15, 15),
            attributes=Attributes(strength=14, dexterity=12),
            combat_stats=CombatStats(TE=45, VE=50),
        )

        result = resolve_attack(
            attacker=attacker,
            defender=defender,
            attack_roll=50,
            base_damage_roll=5,
            weapon=weapon,
        )

        # Base TÉ: 50 + weapon(10) + roll(50) = 110
        # + back bonus: 10
        # = 120
        assert result.all_te == 120

    def test_back_left_attack_plus_5_te(self, weapon):
        """Back-left attack (direction 4) grants +5 TÉ."""
        attacker = Unit(
            id="att",
            name="Attacker",
            position=Position(-1, 0),  # Direction 4 (W) = back-left
            facing=Facing(1),
            fp=ResourcePool(20, 20),
            ep=ResourcePool(15, 15),
            attributes=Attributes(strength=18, dexterity=14),
            combat_stats=CombatStats(TE=50, VE=45),
            weapon=weapon,
        )

        defender = Unit(
            id="def",
            name="Defender",
            position=Position(0, 0),
            facing=Facing(0),
            fp=ResourcePool(20, 20),
            ep=ResourcePool(15, 15),
            attributes=Attributes(strength=14, dexterity=12),
            combat_stats=CombatStats(TE=45, VE=50),
        )

        result = resolve_attack(
            attacker=attacker,
            defender=defender,
            attack_roll=50,
            base_damage_roll=5,
            weapon=weapon,
        )

        # Base TÉ: 50 + weapon(10) + roll(50) = 110
        # + back-left bonus: 5
        # = 115
        assert result.all_te == 115

    def test_back_right_attack_plus_5_te(self, weapon):
        """Back-right attack (direction 2) grants +5 TÉ."""
        attacker = Unit(
            id="att",
            name="Attacker",
            position=Position(0, 1),  # Direction 2 (SE) = back-right
            facing=Facing(0),
            fp=ResourcePool(20, 20),
            ep=ResourcePool(15, 15),
            attributes=Attributes(strength=18, dexterity=14),
            combat_stats=CombatStats(TE=50, VE=45),
            weapon=weapon,
        )

        defender = Unit(
            id="def",
            name="Defender",
            position=Position(0, 0),
            facing=Facing(0),
            fp=ResourcePool(20, 20),
            ep=ResourcePool(15, 15),
            attributes=Attributes(strength=14, dexterity=12),
            combat_stats=CombatStats(TE=45, VE=50),
        )

        result = resolve_attack(
            attacker=attacker,
            defender=defender,
            attack_roll=50,
            base_damage_roll=5,
            weapon=weapon,
        )

        # Base TÉ: 50 + weapon(10) + roll(50) = 110
        # + back-right bonus: 5
        # = 115
        assert result.all_te == 115

    def test_front_left_attack_plus_5_te(self, weapon):
        """Front-left attack (direction 5) grants +5 TÉ."""
        attacker = Unit(
            id="att",
            name="Attacker",
            position=Position(0, -1),  # Direction 5 (NW) = front-left
            facing=Facing(2),
            fp=ResourcePool(20, 20),
            ep=ResourcePool(15, 15),
            attributes=Attributes(strength=18, dexterity=14),
            combat_stats=CombatStats(TE=50, VE=45),
            weapon=weapon,
        )

        defender = Unit(
            id="def",
            name="Defender",
            position=Position(0, 0),
            facing=Facing(0),
            fp=ResourcePool(20, 20),
            ep=ResourcePool(15, 15),
            attributes=Attributes(strength=14, dexterity=12),
            combat_stats=CombatStats(TE=45, VE=50),
        )

        result = resolve_attack(
            attacker=attacker,
            defender=defender,
            attack_roll=50,
            base_damage_roll=5,
            weapon=weapon,
        )

        # Base TÉ: 50 + weapon(10) + roll(50) = 110
        # + front-left bonus: 5
        # = 115
        assert result.all_te == 115

    def test_front_right_attack_plus_5_te(self, weapon):
        """Front-right attack (direction 1) grants +5 TÉ."""
        attacker = Unit(
            id="att",
            name="Attacker",
            position=Position(1, 0),  # Direction 1 (E) = front-right
            facing=Facing(4),
            fp=ResourcePool(20, 20),
            ep=ResourcePool(15, 15),
            attributes=Attributes(strength=18, dexterity=14),
            combat_stats=CombatStats(TE=50, VE=45),
            weapon=weapon,
        )

        defender = Unit(
            id="def",
            name="Defender",
            position=Position(0, 0),
            facing=Facing(0),
            fp=ResourcePool(20, 20),
            ep=ResourcePool(15, 15),
            attributes=Attributes(strength=14, dexterity=12),
            combat_stats=CombatStats(TE=45, VE=50),
        )

        result = resolve_attack(
            attacker=attacker,
            defender=defender,
            attack_roll=50,
            base_damage_roll=5,
            weapon=weapon,
        )

        # Base TÉ: 50 + weapon(10) + roll(50) = 110
        # + front-right bonus: 5
        # = 115
        assert result.all_te == 115

    def test_front_attack_no_bonus(self, weapon):
        """Front attack (direction 0) grants no TÉ bonus."""
        attacker = Unit(
            id="att",
            name="Attacker",
            position=Position(1, -1),  # Direction 0 (NE) = front
            facing=Facing(3),
            fp=ResourcePool(20, 20),
            ep=ResourcePool(15, 15),
            attributes=Attributes(strength=18, dexterity=14),
            combat_stats=CombatStats(TE=50, VE=45),
            weapon=weapon,
        )

        defender = Unit(
            id="def",
            name="Defender",
            position=Position(0, 0),
            facing=Facing(0),
            fp=ResourcePool(20, 20),
            ep=ResourcePool(15, 15),
            attributes=Attributes(strength=14, dexterity=12),
            combat_stats=CombatStats(TE=45, VE=50),
        )

        result = resolve_attack(
            attacker=attacker,
            defender=defender,
            attack_roll=50,
            base_damage_roll=5,
            weapon=weapon,
        )

        # Base TÉ: 50 + weapon(10) + roll(50) = 110
        # + front bonus: 0
        # = 110
        assert result.all_te == 110


class TestDefenderDirectionalVERestrictions:
    """Test VÉ application restrictions based on attack direction."""

    def test_shield_ve_only_applies_to_front(self, weapon):
        """Shield VÉ bonus only applies to front attacks."""
        attacker_front = Unit(
            id="att1",
            name="Attacker Front",
            position=Position(1, -1),  # Direction 0 = front
            facing=Facing(3),
            fp=ResourcePool(20, 20),
            ep=ResourcePool(15, 15),
            attributes=Attributes(strength=18, dexterity=14),
            combat_stats=CombatStats(TE=60, VE=45),
            weapon=weapon,
        )

        attacker_back = Unit(
            id="att2",
            name="Attacker Back",
            position=Position(-1, 1),  # Direction 3 = back
            facing=Facing(0),
            fp=ResourcePool(20, 20),
            ep=ResourcePool(15, 15),
            attributes=Attributes(strength=18, dexterity=14),
            combat_stats=CombatStats(TE=60, VE=45),
            weapon=weapon,
        )

        defender = Unit(
            id="def",
            name="Defender",
            position=Position(0, 0),
            facing=Facing(0),
            fp=ResourcePool(20, 20),
            ep=ResourcePool(15, 15),
            attributes=Attributes(strength=14, dexterity=12),
            combat_stats=CombatStats(TE=45, VE=50),
        )

        # Front attack with shield
        result_front = resolve_attack(
            attacker=attacker_front,
            defender=defender,
            attack_roll=50,
            base_damage_roll=5,
            weapon=weapon,
            shield_ve=15,  # Shield applied
        )

        # Back attack with same shield
        result_back = resolve_attack(
            attacker=attacker_back,
            defender=defender,
            attack_roll=50,
            base_damage_roll=5,
            weapon=weapon,
            shield_ve=15,  # Shield should NOT apply
        )

        # Front attack VÉ includes shield: 50 + 15 (shield, to block_ve) = 65
        # Back attack VÉ does NOT include shield: 50 = 50
        assert result_front.all_ve > result_back.all_ve

    def test_weapon_ve_applies_only_to_front_angles(self, weapon):
        """Weapon VÉ only applies to front, front-right, front-left attacks."""
        # Attack from front-right (should have weapon VÉ)
        attacker_fr = Unit(
            id="att_fr",
            name="Attacker FR",
            position=Position(1, 0),  # Direction 1 = front-right
            facing=Facing(4),
            fp=ResourcePool(20, 20),
            ep=ResourcePool(15, 15),
            attributes=Attributes(strength=18, dexterity=14),
            combat_stats=CombatStats(TE=60, VE=45),
            weapon=weapon,
        )

        # Attack from back-right (should NOT have weapon VÉ)
        attacker_br = Unit(
            id="att_br",
            name="Attacker BR",
            position=Position(0, 1),  # Direction 2 = back-right
            facing=Facing(0),
            fp=ResourcePool(20, 20),
            ep=ResourcePool(15, 15),
            attributes=Attributes(strength=18, dexterity=14),
            combat_stats=CombatStats(TE=60, VE=45),
            weapon=weapon,
        )

        defender = Unit(
            id="def",
            name="Defender",
            position=Position(0, 0),
            facing=Facing(0),
            fp=ResourcePool(20, 20),
            ep=ResourcePool(15, 15),
            attributes=Attributes(strength=14, dexterity=12),
            combat_stats=CombatStats(TE=45, VE=50),
            weapon=weapon,
        )

        # Front-right attack (weapon VÉ applies)
        result_fr = resolve_attack(
            attacker=attacker_fr,
            defender=defender,
            attack_roll=50,
            base_damage_roll=5,
            weapon=weapon,
        )

        # Back-right attack (weapon VÉ does not apply)
        result_br = resolve_attack(
            attacker=attacker_br,
            defender=defender,
            attack_roll=50,
            base_damage_roll=5,
            weapon=weapon,
        )

        # Front-right should have higher VÉ (includes weapon VÉ)
        # Back-right should have lower VÉ (no weapon VÉ)
        assert result_fr.all_ve > result_br.all_ve
