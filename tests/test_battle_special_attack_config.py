"""Tests for battle special attack configuration module."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from MAGUS_pygame.presentation.screens.game.battle.battle_special_attack_config import (
    SpecialAttackType,
    get_special_attack_config,
    validate_special_attack_entry,
)


class TestSpecialAttackType:
    """Test SpecialAttackType enumeration."""

    def test_enum_values_defined(self):
        """Test that all attack types are defined."""
        assert SpecialAttackType.CHARGE.value == "charge"
        assert SpecialAttackType.DAGGER_COMBO.value == "dagger_combo"
        assert SpecialAttackType.SHIELD_BASH.value == "shield_bash"

    def test_enum_has_three_members(self):
        """Test that exactly three attack types exist."""
        members = list(SpecialAttackType)
        assert len(members) == 3

    def test_enum_names(self):
        """Test enum member names."""
        assert SpecialAttackType.CHARGE.name == "CHARGE"
        assert SpecialAttackType.DAGGER_COMBO.name == "DAGGER_COMBO"
        assert SpecialAttackType.SHIELD_BASH.name == "SHIELD_BASH"


class TestGetSpecialAttackConfig:
    """Test config accessor function."""

    def test_get_charge_config(self):
        """Test retrieving charge attack config."""
        config = get_special_attack_config("charge")
        assert config is not None
        assert "message" in config
        assert "name" in config
        assert "min_skill" in config
        assert "weapon_skill" in config
        assert "validate_weapon" in config

    def test_get_dagger_combo_config(self):
        """Test retrieving dagger combo attack config."""
        config = get_special_attack_config("dagger_combo")
        assert config is not None
        assert "message" in config
        assert "min_skill" in config
        assert "weapon_skill" in config
        assert "validate_weapon" in config

    def test_get_shield_bash_config(self):
        """Test retrieving shield bash attack config."""
        config = get_special_attack_config("shield_bash")
        assert config is not None
        assert "message" in config
        assert "name" in config
        assert "min_skill" in config

    def test_get_unknown_config_returns_none(self):
        """Test that unknown attack ID returns None."""
        config = get_special_attack_config("unknown_attack")
        assert config is None

    def test_get_empty_string_returns_none(self):
        """Test that empty string returns None."""
        config = get_special_attack_config("")
        assert config is None

    def test_config_has_all_required_fields(self):
        """Test that all configs have required fields."""
        for attack_id in ["charge", "dagger_combo", "shield_bash"]:
            config = get_special_attack_config(attack_id)
            assert "message" in config
            assert "name" in config


class TestValidateSpecialAttackEntry:
    """Test attack entry validation function."""

    def setup_method(self):
        """Set up mock battle screen and units."""
        self.battle_screen = Mock()
        self.battle_screen.battle = Mock()
        self.battle_screen.action_executor = Mock()

    def test_validate_victory_check_fails(self):
        """Test validation fails when battle is victory."""
        self.battle_screen.battle.is_victory.return_value = True
        
        is_valid, error_msg = validate_special_attack_entry(
            self.battle_screen, "charge"
        )
        
        assert not is_valid
        assert error_msg
        self.battle_screen.battle.is_victory.assert_called_once()

    def test_validate_no_current_unit(self):
        """Test validation fails when no current unit."""
        self.battle_screen.battle.is_victory.return_value = False
        self.battle_screen.battle.current_unit = None
        
        is_valid, error_msg = validate_special_attack_entry(
            self.battle_screen, "charge"
        )
        
        assert not is_valid
        assert "No active unit" in error_msg

    def test_validate_cannot_attack(self):
        """Test validation fails when unit cannot attack."""
        unit = Mock()
        self.battle_screen.battle.is_victory.return_value = False
        self.battle_screen.battle.current_unit = unit
        self.battle_screen.battle.can_attack.return_value = (False, "No AP")
        
        is_valid, error_msg = validate_special_attack_entry(
            self.battle_screen, "charge"
        )
        
        assert not is_valid
        assert error_msg == "No AP"

    def test_validate_dagger_combo_no_dagger_weapon(self):
        """Test dagger combo validation fails without dagger weapon."""
        unit = Mock()
        unit.weapon = Mock()
        unit.weapon.skill_id = "weaponskill_sword"
        self.battle_screen.battle.is_victory.return_value = False
        self.battle_screen.battle.current_unit = unit
        self.battle_screen.battle.can_attack.return_value = (True, "")
        
        is_valid, error_msg = validate_special_attack_entry(
            self.battle_screen, "dagger_combo"
        )
        
        assert not is_valid
        assert "dagger" in error_msg.lower()

    def test_validate_dagger_combo_no_weapon(self):
        """Test dagger combo validation fails when no weapon equipped."""
        unit = Mock()
        unit.weapon = None
        self.battle_screen.battle.is_victory.return_value = False
        self.battle_screen.battle.current_unit = unit
        self.battle_screen.battle.can_attack.return_value = (True, "")
        
        is_valid, error_msg = validate_special_attack_entry(
            self.battle_screen, "dagger_combo"
        )
        
        assert not is_valid
        assert "dagger" in error_msg.lower()

    def test_validate_dagger_combo_insufficient_skill_level(self):
        """Test dagger combo validation fails with low skill level."""
        unit = Mock()
        unit.weapon = Mock()
        unit.weapon.skill_id = "weaponskill_daggers"
        unit.skills = Mock()
        unit.skills.get_rank.return_value = 2  # Need level 3
        self.battle_screen.battle.is_victory.return_value = False
        self.battle_screen.battle.current_unit = unit
        self.battle_screen.battle.can_attack.return_value = (True, "")
        
        is_valid, error_msg = validate_special_attack_entry(
            self.battle_screen, "dagger_combo"
        )
        
        assert not is_valid
        assert "skill level 3" in error_msg.lower()

    def test_validate_dagger_combo_no_skills_attribute(self):
        """Test dagger combo validation fails when unit has no skills attribute."""
        unit = Mock(spec=[])  # No skills attribute
        unit.weapon = Mock()
        unit.weapon.skill_id = "weaponskill_daggers"
        self.battle_screen.battle.is_victory.return_value = False
        self.battle_screen.battle.current_unit = unit
        self.battle_screen.battle.can_attack.return_value = (True, "")
        
        is_valid, error_msg = validate_special_attack_entry(
            self.battle_screen, "dagger_combo"
        )
        
        assert not is_valid
        assert "skill level 3" in error_msg.lower()

    def test_validate_charge_success(self):
        """Test charge validation succeeds with valid conditions."""
        unit = Mock()
        self.battle_screen.battle.is_victory.return_value = False
        self.battle_screen.battle.current_unit = unit
        self.battle_screen.battle.can_attack.return_value = (True, "")
        
        is_valid, error_msg = validate_special_attack_entry(
            self.battle_screen, "charge"
        )
        
        assert is_valid
        assert error_msg is None

    def test_validate_shield_bash_success(self):
        """Test shield bash validation succeeds with valid conditions."""
        unit = Mock()
        self.battle_screen.battle.is_victory.return_value = False
        self.battle_screen.battle.current_unit = unit
        self.battle_screen.battle.can_attack.return_value = (True, "")
        
        is_valid, error_msg = validate_special_attack_entry(
            self.battle_screen, "shield_bash"
        )
        
        assert is_valid
        assert error_msg is None

    def test_validate_dagger_combo_success(self):
        """Test dagger combo validation succeeds with valid conditions."""
        unit = Mock()
        unit.weapon = Mock()
        unit.weapon.skill_id = "weaponskill_daggers"
        unit.skills = Mock()
        unit.skills.get_rank.return_value = 3
        self.battle_screen.battle.is_victory.return_value = False
        self.battle_screen.battle.current_unit = unit
        self.battle_screen.battle.can_attack.return_value = (True, "")
        
        is_valid, error_msg = validate_special_attack_entry(
            self.battle_screen, "dagger_combo"
        )
        
        assert is_valid
        assert error_msg is None

    def test_validate_unknown_attack_returns_false(self):
        """Test validation returns False for unknown attack type."""
        unit = Mock()
        self.battle_screen.battle.is_victory.return_value = False
        self.battle_screen.battle.current_unit = unit
        self.battle_screen.battle.can_attack.return_value = (True, "")
        
        is_valid, error_msg = validate_special_attack_entry(
            self.battle_screen, "unknown_attack"
        )
        
        assert not is_valid
        assert error_msg

    def test_validate_returns_tuple(self):
        """Test that validation always returns (bool, str|None) tuple."""
        unit = Mock()
        self.battle_screen.battle.is_victory.return_value = False
        self.battle_screen.battle.current_unit = unit
        self.battle_screen.battle.can_attack.return_value = (True, "")
        
        result = validate_special_attack_entry(
            self.battle_screen, "charge"
        )
        
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert result[1] is None or isinstance(result[1], str)

    def test_validate_error_messages_are_informative(self):
        """Test that error messages are descriptive."""
        # Charge without AP
        unit = Mock()
        self.battle_screen.battle.is_victory.return_value = False
        self.battle_screen.battle.current_unit = unit
        self.battle_screen.battle.can_attack.return_value = (False, "Insufficient AP")
        
        is_valid, error_msg = validate_special_attack_entry(
            self.battle_screen, "charge"
        )
        
        assert not is_valid
        assert "AP" in error_msg

    def test_validate_dagger_combo_skill_check_order(self):
        """Test that dagger combo checks weapon before skill level."""
        # If weapon is wrong, should fail before checking skill
        unit = Mock()
        unit.weapon = Mock()
        unit.weapon.skill_id = "weaponskill_sword"
        unit.skills = Mock()
        unit.skills.get_rank.return_value = 2  # Low level
        self.battle_screen.battle.is_victory.return_value = False
        self.battle_screen.battle.current_unit = unit
        self.battle_screen.battle.can_attack.return_value = (True, "")
        
        is_valid, error_msg = validate_special_attack_entry(
            self.battle_screen, "dagger_combo"
        )
        
        # Should fail on weapon, not skill level
        assert not is_valid
        assert "dagger" in error_msg.lower()
        # skill_get_rank should not be called since weapon check failed
        # (Or it might be called, we're just checking the error is about weapon)

    def test_validate_shield_bash_no_special_requirements(self):
        """Test shield bash has minimal requirements."""
        unit = Mock()
        self.battle_screen.battle.is_victory.return_value = False
        self.battle_screen.battle.current_unit = unit
        self.battle_screen.battle.can_attack.return_value = (True, "")
        
        is_valid, error_msg = validate_special_attack_entry(
            self.battle_screen, "shield_bash"
        )
        
        assert is_valid
        # Shield bash should only check generic attack capability
