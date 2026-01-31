"""Tests for SpecialAttackRegistry."""

from unittest.mock import MagicMock, call

import pytest

from MAGUS_pygame.presentation.screens.game.battle.battle_special_attack_execution import (
    SpecialAttackRegistry,
)


class TestSpecialAttackRegistry:
    """Test special attack registration and execution."""

    @pytest.fixture
    def mock_battle_service(self):
        """Create mock battle service."""
        service = MagicMock()
        service.validate_charge_target = MagicMock(return_value=(True, ""))
        service.validate_attack_combination_target = MagicMock(return_value=(True, ""))
        service.validate_shield_bash_target = MagicMock(return_value=(True, ""))
        return service

    @pytest.fixture
    def mock_action_executor(self):
        """Create mock action executor."""
        executor = MagicMock()
        executor.show_message = MagicMock()
        executor._execute_charge = MagicMock()
        executor._execute_dagger_combo = MagicMock()
        executor._execute_shield_bash = MagicMock()
        return executor

    @pytest.fixture
    def registry(self, mock_battle_service, mock_action_executor):
        """Create registry with mocks."""
        return SpecialAttackRegistry(mock_battle_service, mock_action_executor)

    def test_init_registers_default_attacks(self, registry):
        """Default attacks should be registered."""
        assert registry.is_registered("charge")
        assert registry.is_registered("dagger_combo")
        assert registry.is_registered("shield_bash")

    def test_get_all_ids(self, registry):
        """Should return all registered attack IDs."""
        ids = registry.get_all_ids()
        assert "charge" in ids
        assert "dagger_combo" in ids
        assert "shield_bash" in ids
        assert len(ids) == 3

    def test_register_new_attack(self, registry):
        """Should register new attack."""
        validate_fn = MagicMock(return_value=(True, ""))
        execute_fn = MagicMock()

        registry.register("test_attack", validate_fn, execute_fn)

        assert registry.is_registered("test_attack")
        assert "test_attack" in registry.get_all_ids()

    def test_is_registered_returns_true_for_registered(self, registry):
        """Should return True for registered attacks."""
        assert registry.is_registered("charge")

    def test_is_registered_returns_false_for_unregistered(self, registry):
        """Should return False for unregistered attacks."""
        assert not registry.is_registered("nonexistent")

    def test_validate_and_execute_success(self, registry, mock_action_executor):
        """Should execute attack on validation success."""
        unit = MagicMock()
        target_pos = MagicMock()

        result = registry.validate_and_execute("charge", unit, target_pos)

        assert result is True
        mock_action_executor.execute_charge.assert_called_once_with(target_pos)

    def test_validate_and_execute_validation_fails(
        self, registry, mock_battle_service, mock_action_executor
    ):
        """Should show error message on validation failure."""
        mock_battle_service.validate_charge_target.return_value = (
            False,
            "Not in range",
        )
        unit = MagicMock()
        target_pos = MagicMock()

        result = registry.validate_and_execute("charge", unit, target_pos)

        assert result is False
        mock_action_executor.show_message.assert_called_once_with("Not in range")
        mock_action_executor._execute_charge.assert_not_called()

    def test_validate_and_execute_unknown_attack(
        self, registry, mock_action_executor
    ):
        """Should return False for unknown attack."""
        unit = MagicMock()
        target_pos = MagicMock()

        result = registry.validate_and_execute("unknown", unit, target_pos)

        assert result is False
        mock_action_executor.show_message.assert_not_called()

    def test_validate_and_execute_dagger_combo(self, registry, mock_action_executor):
        """Should execute dagger combo attack."""
        unit = MagicMock()
        target_pos = MagicMock()

        result = registry.validate_and_execute("dagger_combo", unit, target_pos)

        assert result is True
        mock_action_executor.execute_attack_combination.assert_called_once_with(
            target_pos
        )

    def test_validate_and_execute_shield_bash(self, registry, mock_action_executor):
        """Should execute shield bash attack."""
        unit = MagicMock()
        target_pos = MagicMock()

        result = registry.validate_and_execute("shield_bash", unit, target_pos)

        assert result is True
        mock_action_executor.execute_shield_bash.assert_called_once_with(target_pos)

    def test_register_replaces_existing(self, registry):
        """Should replace existing attack on re-register."""
        new_validate = MagicMock(return_value=(True, ""))
        new_execute = MagicMock()

        registry.register("charge", new_validate, new_execute)

        unit = MagicMock()
        target_pos = MagicMock()
        registry.validate_and_execute("charge", unit, target_pos)

        new_execute.assert_called_once_with(target_pos)

    def test_multiple_attacks_registered(self, registry):
        """Should support multiple custom attacks."""
        validate1 = MagicMock(return_value=(True, ""))
        execute1 = MagicMock()
        validate2 = MagicMock(return_value=(True, ""))
        execute2 = MagicMock()

        registry.register("attack1", validate1, execute1)
        registry.register("attack2", validate2, execute2)

        assert len(registry.get_all_ids()) == 5  # 3 default + 2 new
        assert registry.is_registered("attack1")
        assert registry.is_registered("attack2")
