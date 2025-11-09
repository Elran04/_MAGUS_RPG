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
    ArmorSystem,
)


# --- Fixtures ---

@pytest.fixture
def leather_armor():
    """Basic leather armor covering chest (mellvért)."""
    return ArmorPiece(
        id="leather_vest",
        name="Leather Vest",
        parts={"mellvért": 3},
        mgt=1,
        layer=3,
    )


@pytest.fixture
def chain_mail():
    """Medium chainmail covering chest (mellvért)."""
    return ArmorPiece(
        id="chainmail",
        name="Chainmail",
        parts={"mellvért": 8},
        mgt=3,
        layer=2,
    )


@pytest.fixture
def steel_helmet():
    """Steel helmet covering head (sisak)."""
    return ArmorPiece(
        id="steel_helmet",
        name="Steel Helmet",
        parts={"sisak": 5},
        mgt=1,
        layer=1,
    )


@pytest.fixture
def plate_armor():
    """Heavy plate armor covering chest (mellvért)."""
    return ArmorPiece(
        id="plate",
        name="Plate Armor",
        parts={"mellvért": 12},
        mgt=5,
        layer=1,
    )


# --- Test ArmorPiece ---

class TestArmorPiece:
    """Test ArmorPiece entity."""
    
    def test_armor_creation(self):
        """Armor piece initializes correctly."""
        armor = ArmorPiece(
            id="test",
            name="Test Armor",
            parts={"mellvért": 5},
            mgt=2,
            layer=3,
        )
        
        assert armor.id == "test"
        assert armor.name == "Test Armor"
        assert armor.get_sfé("mellvért") == 5
        assert armor.get_mgt() == 2
        # Not covering other zones
        assert armor.get_sfé("sisak") == 0
    
    def test_armor_defaults(self):
        """Armor uses default values."""
        armor = ArmorPiece(id="test", name="Test", parts={"mellvért": 3})
        
        assert armor.mgt == 0
        assert armor.get_sfé("mellvért") == 3
    
    def test_armor_fully_functional_initially(self, chain_mail):
        """Current SFÉ equals base SFÉ initially."""
        assert chain_mail.get_sfé("mellvért") == 8


# --- Test Armor Degradation ---

class TestArmorDegradation:
    """Test armor degradation mechanics."""
    
    def test_degrade_reduces_sfe(self, chain_mail):
        """Degrading armor reduces current SFÉ."""
        original_sfe = chain_mail.get_sfé("mellvért")
        chain_mail.degrade_zone("mellvért", 1)
        
        assert chain_mail.get_sfé("mellvért") == original_sfe - 1
    
    def test_degrade_custom_amount(self, chain_mail):
        """Can degrade by custom amount."""
        chain_mail.degrade_zone("mellvért", 3)
        
        assert chain_mail.get_sfé("mellvért") == max(0, 8 - 3)
    
    def test_degrade_cannot_go_negative(self, leather_armor):
        """Degrading armor cannot make SFÉ negative."""
        leather_armor.degrade_zone("mellvért", 10)  # Degrade more than max
        
        assert leather_armor.get_sfé("mellvért") == 0
    
    def test_multiple_degrades(self, chain_mail):
        """Multiple degradations accumulate."""
        chain_mail.degrade_zone("mellvért", 1)
        chain_mail.degrade_zone("mellvért", 1)
        chain_mail.degrade_zone("mellvért", 1)
        
        assert chain_mail.get_sfé("mellvért") == 5
    
    def test_zero_sfe_zone_is_zero(self, leather_armor):
        """Zero SFÉ zone returns 0."""
        # Not covering head on leather armor
        assert leather_armor.get_sfé("sisak") == 0


# --- Test Armor Repair ---

# (Repair mechanics are not part of the new model; omitted.)


# --- Test Total Absorption ---

class TestZoneAggregation:
    """Test zone-based SFÉ aggregation with ArmorSystem."""

    def test_single_zone_sfe(self, chain_mail):
        system = ArmorSystem([chain_mail])
        assert system.get_sfe_for_hit("mellvért") == chain_mail.get_sfé("mellvért")

    def test_multiple_layers_same_zone(self, chain_mail, leather_armor):
        leather_armor.layer = 4  # inner layer
        system = ArmorSystem([chain_mail, leather_armor])
        expected = chain_mail.get_sfé("mellvért") + leather_armor.get_sfé("mellvért")
        assert system.get_sfe_for_hit("mellvért") == expected

    def test_zone_without_coverage(self, steel_helmet, leather_armor):
        system = ArmorSystem([steel_helmet, leather_armor])
        # No leg coverage in fixtures
        assert system.get_sfe_for_hit("lábszárvédő") == 0

    def test_degrade_outermost_only(self, chain_mail, leather_armor):
        leather_armor.layer = 4
        system = ArmorSystem([chain_mail, leather_armor])
        before = system.get_sfe_for_hit("mellvért")
        system.reduce_sfe("mellvért", 1)
        after = system.get_sfe_for_hit("mellvért")
        # Only chain_mail degraded (outermost by lower layer index)
        assert after == before - 1

    def test_degrade_no_effect_if_uncovered(self, chain_mail):
        system = ArmorSystem([chain_mail])
        before = system.get_sfe_for_hit("felkarvédő")  # not covered
        system.reduce_sfe("felkarvédő", 2)
        after = system.get_sfe_for_hit("felkarvédő")
        assert before == after == 0


# --- Test MGT Calculation ---

class TestMGTCalculation:
    """Test movement penalty (MGT) calculation via ArmorSystem."""

    def test_total_mgt_single(self, chain_mail):
        system = ArmorSystem([chain_mail])
        assert system.get_total_mgt() == chain_mail.mgt

    def test_total_mgt_multiple(self, leather_armor, steel_helmet, plate_armor):
        system = ArmorSystem([leather_armor, steel_helmet, plate_armor])
        expected = leather_armor.mgt + steel_helmet.mgt + plate_armor.mgt
        assert system.get_total_mgt() == expected

    def test_total_mgt_empty(self):
        system = ArmorSystem([])
        assert system.get_total_mgt() == 0


# --- Test Overpower Degradation ---

class TestTargetedDegradation:
    """Test zone-specific degradation (outermost layer only)."""

    def test_reduce_sfe_outermost_layer(self, chain_mail, leather_armor):
        leather_armor.layer = 5
        system = ArmorSystem([chain_mail, leather_armor])
        before_chain = chain_mail.current_parts.get("mellvért", 0)
        system.reduce_sfe("mellvért", 2)
        after_chain = chain_mail.current_parts.get("mellvért", 0)
        assert after_chain == max(0, before_chain - 2)

    def test_reduce_sfe_no_coverage(self, steel_helmet):
        system = ArmorSystem([steel_helmet])
        before = system.get_sfe_for_hit("mellvért")
        system.reduce_sfe("mellvért", 3)
        after = system.get_sfe_for_hit("mellvért")
        assert before == after == 0


# --- Edge Cases ---

class TestArmorEdgeCases:
    """Test edge cases for armor mechanics."""
    
    def test_armor_with_zero_sfe_zone(self):
        """Armor can have 0 base SFÉ on a zone."""
        cloth = ArmorPiece(id="cloth", name="Cloth", parts={"mellvért": 0})
        
        assert cloth.get_sfé("mellvért") == 0
    
    def test_armor_with_zero_mgt(self, leather_armor):
        """Armor can have 0 MGT (light armor)."""
        light = ArmorPiece(id="light", name="Light", parts={"mellvért": 2}, mgt=0)
        
        assert light.mgt == 0
    
    def test_high_sfe_armor(self):
        """Very high SFÉ armor works correctly."""
        super_armor = ArmorPiece(id="super", name="Super Armor", parts={"mellvért": 20}, mgt=10)
        super_armor.degrade_zone("mellvért", 5)
        assert super_armor.get_sfé("mellvért") == 15


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
