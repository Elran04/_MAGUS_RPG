"""
Unit tests for armor mechanics.

Tests cover:
- Armor absorption calculation
- Armor degradation on overpower
- MGT (movement penalty) calculation
- Armor repair mechanics
"""
import pytest

from domain.mechanics.armor import (
    ArmorPiece,
    calculate_total_armor_absorption,
    calculate_total_mgt,
    apply_overpower_degradation,
)


# --- Fixtures ---

@pytest.fixture
def leather_armor():
    """Basic leather armor."""
    return ArmorPiece(
        id="leather_vest",
        name="Leather Vest",
        sfe=3,
        mgt=1,
        location="torso",
    )


@pytest.fixture
def chain_mail():
    """Medium chainmail armor."""
    return ArmorPiece(
        id="chainmail",
        name="Chainmail",
        sfe=8,
        mgt=3,
        location="torso",
    )


@pytest.fixture
def steel_helmet():
    """Steel helmet."""
    return ArmorPiece(
        id="steel_helmet",
        name="Steel Helmet",
        sfe=5,
        mgt=1,
        location="head",
    )


@pytest.fixture
def plate_armor():
    """Heavy plate armor."""
    return ArmorPiece(
        id="plate",
        name="Plate Armor",
        sfe=12,
        mgt=5,
        location="torso",
    )


# --- Test ArmorPiece ---

class TestArmorPiece:
    """Test ArmorPiece entity."""
    
    def test_armor_creation(self):
        """Armor piece initializes correctly."""
        armor = ArmorPiece(
            id="test",
            name="Test Armor",
            sfe=5,
            mgt=2,
            location="torso",
        )
        
        assert armor.id == "test"
        assert armor.name == "Test Armor"
        assert armor.sfe == 5
        assert armor.current_sfe == 5  # Initialized to base
        assert armor.mgt == 2
        assert armor.location == "torso"
    
    def test_armor_defaults(self):
        """Armor uses default values."""
        armor = ArmorPiece(id="test", name="Test", sfe=3)
        
        assert armor.mgt == 0
        assert armor.location == "torso"
    
    def test_armor_not_broken_initially(self, leather_armor):
        """New armor is not broken."""
        assert not leather_armor.is_broken()
    
    def test_armor_fully_functional_initially(self, chain_mail):
        """Current SFÉ equals base SFÉ initially."""
        assert chain_mail.current_sfe == chain_mail.sfe


# --- Test Armor Degradation ---

class TestArmorDegradation:
    """Test armor degradation mechanics."""
    
    def test_degrade_reduces_sfe(self, chain_mail):
        """Degrading armor reduces current SFÉ."""
        original_sfe = chain_mail.current_sfe
        chain_mail.degrade()
        
        assert chain_mail.current_sfe == original_sfe - 1
    
    def test_degrade_custom_amount(self, chain_mail):
        """Can degrade by custom amount."""
        chain_mail.degrade(3)
        
        assert chain_mail.current_sfe == chain_mail.sfe - 3
    
    def test_degrade_cannot_go_negative(self, leather_armor):
        """Degrading armor cannot make SFÉ negative."""
        leather_armor.degrade(10)  # Degrade more than max
        
        assert leather_armor.current_sfe == 0
        assert leather_armor.is_broken()
    
    def test_multiple_degrades(self, chain_mail):
        """Multiple degradations accumulate."""
        chain_mail.degrade(1)
        chain_mail.degrade(1)
        chain_mail.degrade(1)
        
        assert chain_mail.current_sfe == chain_mail.sfe - 3
    
    def test_broken_armor_has_zero_sfe(self, leather_armor):
        """Broken armor has 0 SFÉ."""
        leather_armor.current_sfe = 0
        
        assert leather_armor.is_broken()
        assert leather_armor.current_sfe == 0


# --- Test Armor Repair ---

class TestArmorRepair:
    """Test armor repair mechanics."""
    
    def test_partial_repair(self, chain_mail):
        """Partial repair restores some SFÉ."""
        chain_mail.degrade(5)
        chain_mail.repair(2)
        
        assert chain_mail.current_sfe == chain_mail.sfe - 3
    
    def test_full_repair(self, chain_mail):
        """Full repair restores to base SFÉ."""
        chain_mail.degrade(5)
        chain_mail.repair()  # No amount = full repair
        
        assert chain_mail.current_sfe == chain_mail.sfe
        assert not chain_mail.is_broken()
    
    def test_repair_cannot_exceed_base(self, leather_armor):
        """Repair cannot exceed base SFÉ."""
        leather_armor.degrade(1)
        leather_armor.repair(10)  # Try to over-repair
        
        assert leather_armor.current_sfe == leather_armor.sfe
    
    def test_repair_broken_armor(self, leather_armor):
        """Can repair broken armor."""
        leather_armor.current_sfe = 0
        assert leather_armor.is_broken()
        
        leather_armor.repair()
        
        assert not leather_armor.is_broken()
        assert leather_armor.current_sfe == leather_armor.sfe


# --- Test Total Absorption ---

class TestTotalAbsorption:
    """Test total armor absorption calculation."""
    
    def test_single_armor_piece(self, chain_mail):
        """Single armor piece absorption."""
        total = calculate_total_armor_absorption([chain_mail])
        
        assert total == chain_mail.current_sfe
    
    def test_multiple_armor_pieces(self, leather_armor, steel_helmet):
        """Multiple armor pieces sum together."""
        total = calculate_total_armor_absorption([leather_armor, steel_helmet])
        
        assert total == leather_armor.current_sfe + steel_helmet.current_sfe
    
    def test_degraded_armor_absorbs_less(self, chain_mail, steel_helmet):
        """Degraded armor provides less absorption."""
        chain_mail.degrade(3)
        
        total = calculate_total_armor_absorption([chain_mail, steel_helmet])
        
        expected = (chain_mail.sfe - 3) + steel_helmet.current_sfe
        assert total == expected
    
    def test_broken_armor_no_absorption(self, leather_armor, steel_helmet):
        """Broken armor provides no absorption."""
        leather_armor.current_sfe = 0
        
        total = calculate_total_armor_absorption([leather_armor, steel_helmet])
        
        assert total == steel_helmet.current_sfe  # Only helmet counts
    
    def test_empty_armor_list(self):
        """Empty armor list returns 0."""
        total = calculate_total_armor_absorption([])
        
        assert total == 0
    
    def test_all_broken_armor(self, leather_armor, steel_helmet):
        """All broken armor returns 0."""
        leather_armor.current_sfe = 0
        steel_helmet.current_sfe = 0
        
        total = calculate_total_armor_absorption([leather_armor, steel_helmet])
        
        assert total == 0


# --- Test MGT Calculation ---

class TestMGTCalculation:
    """Test movement penalty (MGT) calculation."""
    
    def test_single_armor_mgt(self, chain_mail):
        """Single armor piece MGT."""
        total = calculate_total_mgt([chain_mail])
        
        assert total == chain_mail.mgt
    
    def test_multiple_armor_mgt(self, leather_armor, steel_helmet, plate_armor):
        """Multiple armor pieces MGT sums."""
        total = calculate_total_mgt([leather_armor, steel_helmet, plate_armor])
        
        expected = leather_armor.mgt + steel_helmet.mgt + plate_armor.mgt
        assert total == expected
    
    def test_no_armor_no_mgt(self):
        """No armor means no MGT."""
        total = calculate_total_mgt([])
        
        assert total == 0
    
    def test_light_armor_low_mgt(self, leather_armor):
        """Light armor has low MGT."""
        assert leather_armor.mgt <= 2
    
    def test_heavy_armor_high_mgt(self, plate_armor):
        """Heavy armor has high MGT."""
        assert plate_armor.mgt >= 5


# --- Test Overpower Degradation ---

class TestOverpowerDegradation:
    """Test armor degradation on overpower strikes."""
    
    def test_overpower_degrades_all_armor(self, leather_armor, steel_helmet):
        """Overpower degrades all armor pieces by 1."""
        armor_list = [leather_armor, steel_helmet]
        
        original_leather = leather_armor.current_sfe
        original_helmet = steel_helmet.current_sfe
        
        apply_overpower_degradation(armor_list)
        
        assert leather_armor.current_sfe == original_leather - 1
        assert steel_helmet.current_sfe == original_helmet - 1
    
    def test_overpower_skips_broken_armor(self, leather_armor, steel_helmet):
        """Overpower doesn't degrade already broken armor."""
        leather_armor.current_sfe = 0
        armor_list = [leather_armor, steel_helmet]
        
        apply_overpower_degradation(armor_list)
        
        assert leather_armor.current_sfe == 0  # Still 0
        assert steel_helmet.current_sfe == steel_helmet.sfe - 1
    
    def test_overpower_empty_list(self):
        """Overpower on empty list doesn't crash."""
        apply_overpower_degradation([])  # Should not raise
    
    def test_overpower_can_break_armor(self, leather_armor):
        """Overpower can reduce armor to broken state."""
        leather_armor.current_sfe = 1
        armor_list = [leather_armor]
        
        apply_overpower_degradation(armor_list)
        
        assert leather_armor.is_broken()
    
    def test_multiple_overpowers(self, chain_mail):
        """Multiple overpower strikes degrade further."""
        armor_list = [chain_mail]
        
        apply_overpower_degradation(armor_list)
        apply_overpower_degradation(armor_list)
        apply_overpower_degradation(armor_list)
        
        assert chain_mail.current_sfe == chain_mail.sfe - 3


# --- Edge Cases ---

class TestArmorEdgeCases:
    """Test edge cases for armor mechanics."""
    
    def test_armor_with_zero_sfe(self):
        """Armor can have 0 base SFÉ (cloth)."""
        cloth = ArmorPiece(id="cloth", name="Cloth", sfe=0)
        
        assert cloth.current_sfe == 0
        assert cloth.is_broken()
    
    def test_armor_with_zero_mgt(self, leather_armor):
        """Armor can have 0 MGT (light armor)."""
        light = ArmorPiece(id="light", name="Light", sfe=2, mgt=0)
        
        assert light.mgt == 0
    
    def test_high_sfe_armor(self):
        """Very high SFÉ armor works correctly."""
        super_armor = ArmorPiece(id="super", name="Super Armor", sfe=20, mgt=10)
        
        super_armor.degrade(5)
        assert super_armor.current_sfe == 15
        assert not super_armor.is_broken()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
