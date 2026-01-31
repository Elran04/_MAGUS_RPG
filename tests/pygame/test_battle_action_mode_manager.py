"""Tests for BattleActionModeManager."""

from unittest.mock import MagicMock

import pytest

from MAGUS_pygame.presentation.screens.game.battle.battle_action_mode_manager import (
    BattleActionModeManager,
)
from MAGUS_pygame.presentation.screens.game.battle.battle_action_mode import ActionMode


class TestBattleActionModeManager:
    """Test action mode management and entry logic."""

    @pytest.fixture
    def mock_battle_screen(self):
        """Create mock battle screen."""
        screen = MagicMock()
        screen.battle = MagicMock()
        screen.battle.is_victory = MagicMock(return_value=False)
        screen.battle.can_move = MagicMock(return_value=(True, ""))
        screen.battle.can_attack = MagicMock(return_value=(True, ""))
        screen.battle.current_unit = MagicMock()
        screen.battle.current_unit.weapon = MagicMock()
        screen.battle.current_unit.weapon.skill_id = "weaponskill_swords"
        screen.battle.current_unit.skills = MagicMock()
        screen.action_executor = MagicMock()
        screen.action_mode = ActionMode.IDLE
        screen.selected_unit = None
        screen.movement_path = None
        screen._active_special_attack = None
        return screen

    @pytest.fixture
    def manager(self, mock_battle_screen):
        """Create manager with mock battle screen."""
        return BattleActionModeManager(mock_battle_screen)

    def test_init(self, manager):
        """Should initialize with battle screen reference."""
        assert manager.battle_screen is not None

    def test_enter_move_mode_success(self, manager, mock_battle_screen):
        """Should enter move mode when validation passes."""
        manager.enter_move_mode()

        # Check that action_mode was set to MOVE (check the actual object attribute was assigned)
        assert mock_battle_screen.action_mode.value == ActionMode.MOVE.value
        assert mock_battle_screen.selected_unit is not None

    def test_enter_move_mode_cannot_move(self, manager, mock_battle_screen):
        """Should show error when can_move fails."""
        mock_battle_screen.battle.can_move.return_value = (False, "No movement available")

        manager.enter_move_mode()

        mock_battle_screen.action_executor.show_message.assert_called_with("No movement available")
        assert mock_battle_screen.action_mode == ActionMode.IDLE

    def test_enter_move_mode_clears_special_attack(self, manager, mock_battle_screen):
        """Should clear active special attack when entering move mode."""
        mock_battle_screen._active_special_attack = "charge"

        manager.enter_move_mode()

        assert mock_battle_screen._active_special_attack is None

    def test_enter_move_mode_during_victory(self, manager, mock_battle_screen):
        """Should not enter move mode during victory."""
        mock_battle_screen.battle.is_victory.return_value = True

        manager.enter_move_mode()

        assert mock_battle_screen.action_mode == ActionMode.IDLE

    def test_enter_attack_mode_success(self, manager, mock_battle_screen):
        """Should enter attack mode when validation passes."""
        manager.enter_attack_mode()

        assert mock_battle_screen.action_mode.value == ActionMode.ATTACK.value
        assert mock_battle_screen.selected_unit is not None

    def test_enter_attack_mode_cannot_attack(self, manager, mock_battle_screen):
        """Should show error when can_attack fails."""
        mock_battle_screen.battle.can_attack.return_value = (False, "No weapon equipped")

        manager.enter_attack_mode()

        mock_battle_screen.action_executor.show_message.assert_called_with("No weapon equipped")
        assert mock_battle_screen.action_mode == ActionMode.IDLE

    def test_enter_charge_mode_success(self, manager, mock_battle_screen):
        """Should enter charge mode when validation passes."""
        manager.enter_charge_mode()

        assert mock_battle_screen.action_mode.value == ActionMode.ATTACK.value
        assert mock_battle_screen._active_special_attack == "charge"
        mock_battle_screen.action_executor.show_message.assert_called()

    def test_enter_charge_mode_no_unit(self, manager, mock_battle_screen):
        """Should show error when no current unit."""
        mock_battle_screen.battle.current_unit = None

        manager.enter_charge_mode()

        mock_battle_screen.action_executor.show_message.assert_called_with("No active unit")

    def test_enter_dagger_combo_mode_success(self, manager, mock_battle_screen):
        """Should enter dagger combo mode when unit has dagger skill."""
        mock_battle_screen.battle.current_unit.weapon.skill_id = "weaponskill_daggers"
        mock_battle_screen.battle.current_unit.skills.get_rank.return_value = 3

        manager.enter_dagger_combo_mode()

        assert mock_battle_screen.action_mode.value == ActionMode.ATTACK.value
        assert mock_battle_screen._active_special_attack == "dagger_combo"

    def test_enter_dagger_combo_mode_no_dagger(self, manager, mock_battle_screen):
        """Should show error when unit doesn't have dagger."""
        mock_battle_screen.battle.current_unit.weapon.skill_id = "weaponskill_swords"

        manager.enter_dagger_combo_mode()

        mock_battle_screen.action_executor.show_message.assert_called_with(
            "Attack combination requires a dagger"
        )

    def test_enter_dagger_combo_mode_insufficient_skill(self, manager, mock_battle_screen):
        """Should show error when dagger skill below 3."""
        mock_battle_screen.battle.current_unit.weapon.skill_id = "weaponskill_daggers"
        mock_battle_screen.battle.current_unit.skills.get_rank.return_value = 2

        manager.enter_dagger_combo_mode()

        mock_battle_screen.action_executor.show_message.assert_called_with(
            "Attack combination requires dagger skill level 3+"
        )

    def test_enter_shield_bash_mode_success(self, manager, mock_battle_screen):
        """Should enter shield bash mode when validation passes."""
        manager.enter_shield_bash_mode()

        assert mock_battle_screen.action_mode.value == ActionMode.ATTACK.value
        assert mock_battle_screen._active_special_attack == "shield_bash"

    def test_enter_shield_bash_mode_cannot_attack(self, manager, mock_battle_screen):
        """Should show error when can_attack fails."""
        mock_battle_screen.battle.can_attack.return_value = (False, "No weapon")

        manager.enter_shield_bash_mode()

        mock_battle_screen.action_executor.show_message.assert_called_with("Cannot use shield bash: No weapon")

    def test_enter_inspect_mode(self, manager, mock_battle_screen):
        """Should enter inspect mode."""
        manager.enter_inspect_mode()

        assert mock_battle_screen.action_mode.value == ActionMode.INSPECT.value
        assert mock_battle_screen.selected_unit is None
        assert mock_battle_screen._active_special_attack is None

    def test_cancel_action(self, manager, mock_battle_screen):
        """Should cancel action and return to idle."""
        mock_battle_screen.action_mode = ActionMode.ATTACK
        mock_battle_screen.selected_unit = MagicMock()
        mock_battle_screen.movement_path = [MagicMock()]
        mock_battle_screen._active_special_attack = "charge"

        manager.cancel_action()

        assert mock_battle_screen.action_mode.value == ActionMode.IDLE.value
        assert mock_battle_screen.selected_unit is None
        assert mock_battle_screen.movement_path is None
        assert mock_battle_screen._active_special_attack is None

    def test_mode_transitions(self, manager, mock_battle_screen):
        """Should handle mode transitions correctly."""
        # Start in idle
        assert mock_battle_screen.action_mode.value == ActionMode.IDLE.value

        # Enter move mode
        manager.enter_move_mode()
        assert mock_battle_screen.action_mode.value == ActionMode.MOVE.value

        # Cancel and return to idle
        manager.cancel_action()
        assert mock_battle_screen.action_mode.value == ActionMode.IDLE.value

        # Enter attack mode
        manager.enter_attack_mode()
        assert mock_battle_screen.action_mode.value == ActionMode.ATTACK.value

        # Cancel
        manager.cancel_action()
        assert mock_battle_screen.action_mode.value == ActionMode.IDLE.value
