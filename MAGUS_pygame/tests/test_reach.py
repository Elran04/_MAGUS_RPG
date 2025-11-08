"""
Unit tests for weapon reach mechanics.

Tests cover:
- Reach hex calculation with directional rays
- Mandatory EP loss from FP damage
- Attack range validation
"""
import pytest

from domain.entities import Unit, Weapon
from domain.value_objects import Position, ResourcePool, Attributes, CombatStats, Facing
from domain.mechanics.reach import (
    get_weapon_reach,
    compute_reach_hexes,
    can_attack_target,
    calculate_mandatory_ep_loss,
)


# --- Fixtures ---

@pytest.fixture
def basic_unit():
    """Unit at (0,0) facing NE (0)."""
    return Unit(
        id="test",
        name="Test",
        position=Position(0, 0),
        fp=ResourcePool(20, 20),
        ep=ResourcePool(15, 15),
        facing=Facing(0),  # NE
    )


@pytest.fixture
def weapon_size_1():
    """Size 1 weapon (unarmed/dagger)."""
    return Weapon(
        id="dagger",
        name="Dagger",
        size_category=1,
        damage_min=1,
        damage_max=4,
    )


@pytest.fixture
def weapon_size_2():
    """Size 2 weapon (short sword)."""
    return Weapon(
        id="short_sword",
        name="Short Sword",
        size_category=2,
        damage_min=2,
        damage_max=10,
    )


@pytest.fixture
def weapon_size_3():
    """Size 3 weapon (longsword)."""
    return Weapon(
        id="longsword",
        name="Longsword",
        size_category=3,
        damage_min=3,
        damage_max=15,
    )


@pytest.fixture
def weapon_size_4():
    """Size 4 weapon (spear)."""
    return Weapon(
        id="spear",
        name="Spear",
        size_category=4,
        damage_min=4,
        damage_max=18,
    )


@pytest.fixture
def weapon_size_5():
    """Size 5 weapon (pike)."""
    return Weapon(
        id="pike",
        name="Pike",
        size_category=5,
        damage_min=5,
        damage_max=20,
    )


# --- Test Weapon Reach ---

class TestWeaponReach:
    """Test weapon reach retrieval."""
    
    def test_unarmed_reach(self, basic_unit):
        """Unarmed has reach 1."""
        reach = get_weapon_reach(None)
        assert reach == 1
    
    def test_weapon_reach(self, weapon_size_3):
        """Weapon reach comes from size_category."""
        reach = get_weapon_reach(weapon_size_3)
        assert reach == 3
    
    def test_all_weapon_sizes(self, weapon_size_1, weapon_size_2, weapon_size_3, 
                               weapon_size_4, weapon_size_5):
        """All weapon sizes return correct reach."""
        assert get_weapon_reach(weapon_size_1) == 1
        assert get_weapon_reach(weapon_size_2) == 2
        assert get_weapon_reach(weapon_size_3) == 3
        assert get_weapon_reach(weapon_size_4) == 4
        assert get_weapon_reach(weapon_size_5) == 5


# --- Test Reach Hex Calculation ---

class TestReachHexes:
    """Test directional reach hex calculation."""
    
    def test_size_1_reach(self, basic_unit, weapon_size_1):
        """Size 1: F=1, S=0 → forward(1) only → 1 hex."""
        basic_unit.weapon = weapon_size_1
        hexes = compute_reach_hexes(basic_unit)
        
        # Facing 0 (NE): (1, -1)
        assert len(hexes) == 1
        assert (1, -1) in hexes
    
    def test_size_2_reach(self, basic_unit, weapon_size_2):
        """Size 2: F=1, S=1 → forward(1) + left(1) + right(1) → 3 hexes."""
        basic_unit.weapon = weapon_size_2
        hexes = compute_reach_hexes(basic_unit)
        
        # Facing 0 (NE): forward (1,-1), left (0,-1), right (1,0)
        assert len(hexes) == 3
        assert (1, -1) in hexes  # Forward (facing 0)
        assert (0, -1) in hexes  # Left (facing 5)
        assert (1, 0) in hexes   # Right (facing 1)
    
    def test_size_3_reach(self, basic_unit, weapon_size_3):
        """Size 3: F=2, S=1 → forward(1,2) + left(1) + right(1) → 4 hexes."""
        basic_unit.weapon = weapon_size_3
        hexes = compute_reach_hexes(basic_unit)
        
        assert len(hexes) == 4
        # Forward 1 and 2
        assert (1, -1) in hexes
        assert (2, -2) in hexes
        # Left and right at distance 1
        assert (0, -1) in hexes
        assert (1, 0) in hexes
    
    def test_size_4_reach(self, basic_unit, weapon_size_4):
        """Size 4: F=2, S=2 → forward(1,2) + left(1,2) + right(1,2) → 6 hexes."""
        basic_unit.weapon = weapon_size_4
        hexes = compute_reach_hexes(basic_unit)
        
        assert len(hexes) == 6
        # Forward 1 and 2
        assert (1, -1) in hexes
        assert (2, -2) in hexes
        # Left at distance 1 and 2
        assert (0, -1) in hexes
        assert (0, -2) in hexes
        # Right at distance 1 and 2
        assert (1, 0) in hexes
        assert (2, 0) in hexes
    
    def test_size_5_reach(self, basic_unit, weapon_size_5):
        """Size 5: F=3, S=2 → forward(1,2,3) + left(1,2) + right(1,2) → 7 hexes."""
        basic_unit.weapon = weapon_size_5
        hexes = compute_reach_hexes(basic_unit)
        
        assert len(hexes) == 7
        # Forward 1, 2, 3
        assert (1, -1) in hexes
        assert (2, -2) in hexes
        assert (3, -3) in hexes
        # Left and right at 1, 2
        assert (0, -1) in hexes
        assert (0, -2) in hexes
        assert (1, 0) in hexes
        assert (2, 0) in hexes
    
    def test_different_facing(self, basic_unit, weapon_size_2):
        """Test reach hexes change with facing."""
        basic_unit.weapon = weapon_size_2
        basic_unit.facing = Facing(2)  # SE
        hexes = compute_reach_hexes(basic_unit)
        
        # Facing 2 (SE): forward (0,1), left (1,0), right (-1,1)
        assert len(hexes) == 3
        assert (0, 1) in hexes
        assert (1, 0) in hexes
        assert (-1, 1) in hexes
    
    def test_different_position(self, basic_unit, weapon_size_2):
        """Test reach hexes relative to unit position."""
        basic_unit.weapon = weapon_size_2
        basic_unit.position = Position(5, 5)
        hexes = compute_reach_hexes(basic_unit)
        
        # Should be offset by (5, 5)
        assert len(hexes) == 3
        assert (6, 4) in hexes  # (5+1, 5-1)
        assert (5, 4) in hexes  # (5+0, 5-1)
        assert (6, 5) in hexes  # (5+1, 5+0)


# --- Test Attack Target Validation ---

class TestAttackTarget:
    """Test attack target validation."""
    
    def test_can_attack_forward(self, basic_unit, weapon_size_2):
        """Can attack forward hex."""
        basic_unit.weapon = weapon_size_2
        target = Position(1, -1)  # Forward from (0,0) facing NE
        
        assert can_attack_target(basic_unit, target)
    
    def test_can_attack_side(self, basic_unit, weapon_size_2):
        """Can attack side hex."""
        basic_unit.weapon = weapon_size_2
        target = Position(1, 0)  # Right from (0,0) facing NE
        
        assert can_attack_target(basic_unit, target)
    
    def test_cannot_attack_out_of_reach(self, basic_unit, weapon_size_1):
        """Cannot attack hex outside reach."""
        basic_unit.weapon = weapon_size_1
        target = Position(1, 0)  # Side hex, but size 1 has no sides
        
        assert not can_attack_target(basic_unit, target)
    
    def test_cannot_attack_behind(self, basic_unit, weapon_size_2):
        """Cannot attack behind unit."""
        basic_unit.weapon = weapon_size_2
        target = Position(-1, 1)  # Behind (0,0) facing NE
        
        assert not can_attack_target(basic_unit, target)
    
    def test_long_weapon_reach(self, basic_unit, weapon_size_5):
        """Long weapon can attack at distance 3."""
        basic_unit.weapon = weapon_size_5
        target = Position(3, -3)  # Forward distance 3
        
        assert can_attack_target(basic_unit, target)


# --- Test Mandatory EP Loss ---

class TestMandatoryEPLoss:
    """Test mandatory EP loss from FP damage based on reach."""
    
    def test_reach_1_threshold_6(self, weapon_size_1):
        """Reach 1: 6 FP → 1 EP."""
        assert calculate_mandatory_ep_loss(weapon_size_1, 6) == 1
        assert calculate_mandatory_ep_loss(weapon_size_1, 12) == 2
        assert calculate_mandatory_ep_loss(weapon_size_1, 5) == 0  # Below threshold
        assert calculate_mandatory_ep_loss(weapon_size_1, 18) == 3
    
    def test_reach_2_threshold_8(self, weapon_size_2):
        """Reach 2: 8 FP → 1 EP."""
        assert calculate_mandatory_ep_loss(weapon_size_2, 8) == 1
        assert calculate_mandatory_ep_loss(weapon_size_2, 16) == 2
        assert calculate_mandatory_ep_loss(weapon_size_2, 7) == 0
        assert calculate_mandatory_ep_loss(weapon_size_2, 24) == 3
    
    def test_reach_3_threshold_8(self, weapon_size_3):
        """Reach 3: 8 FP → 1 EP (threshold is > 1, not > 2)."""
        assert calculate_mandatory_ep_loss(weapon_size_3, 8) == 1
        assert calculate_mandatory_ep_loss(weapon_size_3, 16) == 2
    
    def test_reach_4_threshold_10(self, weapon_size_4):
        """Reach 4: 10 FP → 1 EP (reach > 3)."""
        assert calculate_mandatory_ep_loss(weapon_size_4, 10) == 1
        assert calculate_mandatory_ep_loss(weapon_size_4, 20) == 2
        assert calculate_mandatory_ep_loss(weapon_size_4, 9) == 0
        assert calculate_mandatory_ep_loss(weapon_size_4, 30) == 3
    
    def test_reach_5_threshold_10(self, weapon_size_5):
        """Reach 5: 10 FP → 1 EP."""
        assert calculate_mandatory_ep_loss(weapon_size_5, 10) == 1
        assert calculate_mandatory_ep_loss(weapon_size_5, 25) == 2
    
    def test_unarmed_threshold_6(self):
        """Unarmed (None weapon): 6 FP → 1 EP."""
        assert calculate_mandatory_ep_loss(None, 6) == 1
        assert calculate_mandatory_ep_loss(None, 12) == 2
    
    def test_zero_damage_no_ep(self, weapon_size_3):
        """Zero FP damage means no EP loss."""
        assert calculate_mandatory_ep_loss(weapon_size_3, 0) == 0
    
    def test_negative_damage_no_ep(self, weapon_size_3):
        """Negative FP damage (shouldn't happen) means no EP loss."""
        assert calculate_mandatory_ep_loss(weapon_size_3, -5) == 0


# --- Edge Cases ---

class TestReachEdgeCases:
    """Test edge cases for reach mechanics."""
    
    def test_facing_wraparound(self, basic_unit, weapon_size_2):
        """Test facing wraparound (5 → 0 → 1)."""
        basic_unit.weapon = weapon_size_2
        basic_unit.facing = Facing(5)  # NW
        hexes = compute_reach_hexes(basic_unit)
        
        # Facing 5: forward (0,-1), left (-1,0), right (1,-1)
        assert len(hexes) == 3
        assert (0, -1) in hexes
        assert (-1, 0) in hexes
        assert (1, -1) in hexes
    
    def test_explicit_weapon_parameter(self, basic_unit, weapon_size_3):
        """Test passing weapon explicitly to compute_reach_hexes."""
        # Unit has no weapon
        basic_unit.weapon = None
        
        # But we pass weapon explicitly
        hexes = compute_reach_hexes(basic_unit, weapon_size_3)
        
        assert len(hexes) == 4  # Size 3 pattern


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
