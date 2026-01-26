"""Tests for attack angle detection."""

import pytest

from MAGUS_pygame.domain.entities import Unit, Weapon
from MAGUS_pygame.domain.mechanics.attack_angle import (
    AttackAngle,
    get_attack_angle,
    is_attack_from_back,
    is_attack_from_back_left,
    is_attack_from_back_right,
    is_attack_from_front,
    is_attack_from_front_left,
    is_attack_from_front_right,
)
from MAGUS_pygame.domain.value_objects import Attributes, CombatStats, Facing, Position, ResourcePool


@pytest.fixture
def weapon():
    return Weapon(
        id="sword",
        name="Sword",
        te_modifier=5,
        ve_modifier=5,
        damage_min=2,
        damage_max=8,
        size_category=2,
    )


@pytest.fixture
def defender(weapon):
    """Defender at center (0,0) facing direction 0 (NE)."""
    return Unit(
        id="defender",
        name="Defender",
        position=Position(0, 0),
        facing=Facing(0),
        fp=ResourcePool(40, 40),
        ep=ResourcePool(30, 30),
        attributes=Attributes(strength=14, dexterity=12, endurance=10),
        combat_stats=CombatStats(TE=50, VE=55),
        weapon=weapon,
    )


class TestAttackFromFront:
    """Attack from in front of defender."""

    def test_0_direct_front(self, defender, weapon):
        """Attacker at facing 0 relative to defender facing 0 = FRONT (0)."""
        attacker = Unit(
            id="att1",
            name="Attacker",
            position=Position(1, -1),  # Direction 0 (NE)
            facing=Facing(3),
            fp=ResourcePool(40, 40),
            ep=ResourcePool(30, 30),
            attributes=Attributes(strength=14, dexterity=12, endurance=10),
            combat_stats=CombatStats(TE=50, VE=55),
            weapon=weapon,
        )
        angle = get_attack_angle(attacker, defender)
        assert angle == AttackAngle.FRONT
        assert angle.value == 0
        assert is_attack_from_front(attacker, defender)

    def test_1_front_right(self, defender, weapon):
        """Attacker at +1 direction = FRONT_RIGHT (1)."""
        attacker = Unit(
            id="att2",
            name="Attacker",
            position=Position(1, 0),  # Direction 1 (E)
            facing=Facing(4),
            fp=ResourcePool(40, 40),
            ep=ResourcePool(30, 30),
            attributes=Attributes(strength=14, dexterity=12, endurance=10),
            combat_stats=CombatStats(TE=50, VE=55),
            weapon=weapon,
        )
        angle = get_attack_angle(attacker, defender)
        assert angle == AttackAngle.FRONT_RIGHT
        assert angle.value == 1
        assert is_attack_from_front_right(attacker, defender)

    def test_5_front_left(self, defender, weapon):
        """Attacker at -1 direction (wraps to 5) = FRONT_LEFT (5)."""
        attacker = Unit(
            id="att3",
            name="Attacker",
            position=Position(0, -1),  # Direction 5 (NW)
            facing=Facing(2),
            fp=ResourcePool(40, 40),
            ep=ResourcePool(30, 30),
            attributes=Attributes(strength=14, dexterity=12, endurance=10),
            combat_stats=CombatStats(TE=50, VE=55),
            weapon=weapon,
        )
        angle = get_attack_angle(attacker, defender)
        assert angle == AttackAngle.FRONT_LEFT
        assert angle.value == 5
        assert is_attack_from_front_left(attacker, defender)


class TestAllSixDirections:
    """Test all 6 attack angle directions."""

    def test_2_back_right(self, defender, weapon):
        """Attacker at +2 direction = BACK_RIGHT (2)."""
        attacker = Unit(
            id="att",
            name="Attacker",
            position=Position(0, 1),  # Direction 2 (SE)
            facing=Facing(0),
            fp=ResourcePool(40, 40),
            ep=ResourcePool(30, 30),
            attributes=Attributes(strength=14, dexterity=12, endurance=10),
            combat_stats=CombatStats(TE=50, VE=55),
            weapon=weapon,
        )
        angle = get_attack_angle(attacker, defender)
        assert angle == AttackAngle.BACK_RIGHT
        assert angle.value == 2
        assert is_attack_from_back_right(attacker, defender)

    def test_3_direct_back(self, defender, weapon):
        """Attacker at opposite direction (+3) = BACK (3)."""
        attacker = Unit(
            id="att",
            name="Attacker",
            position=Position(-1, 1),  # Direction 3 (SW), opposite of facing 0
            facing=Facing(0),
            fp=ResourcePool(40, 40),
            ep=ResourcePool(30, 30),
            attributes=Attributes(strength=14, dexterity=12, endurance=10),
            combat_stats=CombatStats(TE=50, VE=55),
            weapon=weapon,
        )
        angle = get_attack_angle(attacker, defender)
        assert angle == AttackAngle.BACK
        assert angle.value == 3
        assert is_attack_from_back(attacker, defender)

    def test_4_back_left(self, defender, weapon):
        """Attacker at +4 direction = BACK_LEFT (4)."""
        attacker = Unit(
            id="att",
            name="Attacker",
            position=Position(-1, 0),  # Direction 4 (W)
            facing=Facing(1),
            fp=ResourcePool(40, 40),
            ep=ResourcePool(30, 30),
            attributes=Attributes(strength=14, dexterity=12, endurance=10),
            combat_stats=CombatStats(TE=50, VE=55),
            weapon=weapon,
        )
        angle = get_attack_angle(attacker, defender)
        assert angle == AttackAngle.BACK_LEFT
        assert angle.value == 4
        assert is_attack_from_back_left(attacker, defender)


class TestDifferentDefenderFacings:
    """Test attacks with defender facing different directions."""

    def test_defender_facing_1_front_attack(self, weapon):
        """Defender facing 1 (E), attacker at bearing 1 = FRONT (0)."""
        defender = Unit(
            id="defender",
            name="Defender",
            position=Position(0, 0),
            facing=Facing(1),  # Facing E
            fp=ResourcePool(40, 40),
            ep=ResourcePool(30, 30),
            attributes=Attributes(strength=14, dexterity=12, endurance=10),
            combat_stats=CombatStats(TE=50, VE=55),
            weapon=weapon,
        )

        # Attack from direction 1 (E) = FRONT
        attacker = Unit(
            id="att",
            name="Attacker",
            position=Position(1, 0),
            facing=Facing(0),
            fp=ResourcePool(40, 40),
            ep=ResourcePool(30, 30),
            attributes=Attributes(strength=14, dexterity=12, endurance=10),
            combat_stats=CombatStats(TE=50, VE=55),
            weapon=weapon,
        )
        assert get_attack_angle(attacker, defender) == AttackAngle.FRONT

    def test_defender_facing_3_back_attack(self, weapon):
        """Defender facing 3 (SW), attacker at bearing 0 (opposite) = BACK (3)."""
        defender = Unit(
            id="defender",
            name="Defender",
            position=Position(0, 0),
            facing=Facing(3),  # Facing SW
            fp=ResourcePool(40, 40),
            ep=ResourcePool(30, 30),
            attributes=Attributes(strength=14, dexterity=12, endurance=10),
            combat_stats=CombatStats(TE=50, VE=55),
            weapon=weapon,
        )

        # Attack from direction 0 (NE, opposite of SW) = BACK
        attacker = Unit(
            id="att",
            name="Attacker",
            position=Position(1, -1),
            facing=Facing(0),
            fp=ResourcePool(40, 40),
            ep=ResourcePool(30, 30),
            attributes=Attributes(strength=14, dexterity=12, endurance=10),
            combat_stats=CombatStats(TE=50, VE=55),
            weapon=weapon,
        )
        assert get_attack_angle(attacker, defender) == AttackAngle.BACK

    def test_defender_facing_2_front_right_attack(self, weapon):
        """Defender facing 2 (SE), attacker at bearing 3 (relative +1) = FRONT_RIGHT (1)."""
        defender = Unit(
            id="defender",
            name="Defender",
            position=Position(0, 0),
            facing=Facing(2),  # Facing SE
            fp=ResourcePool(40, 40),
            ep=ResourcePool(30, 30),
            attributes=Attributes(strength=14, dexterity=12, endurance=10),
            combat_stats=CombatStats(TE=50, VE=55),
            weapon=weapon,
        )

        # Attack from direction 3 (SW) = relative direction 1 = FRONT_RIGHT
        attacker = Unit(
            id="att",
            name="Attacker",
            position=Position(-1, 1),
            facing=Facing(0),
            fp=ResourcePool(40, 40),
            ep=ResourcePool(30, 30),
            attributes=Attributes(strength=14, dexterity=12, endurance=10),
            combat_stats=CombatStats(TE=50, VE=55),
            weapon=weapon,
        )
        assert get_attack_angle(attacker, defender) == AttackAngle.FRONT_RIGHT
