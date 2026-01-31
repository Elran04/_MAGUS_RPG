"""Tests for BattleKeyboardHandler."""

from unittest.mock import MagicMock

import pytest
import pygame

from MAGUS_pygame.presentation.screens.game.battle.battle_keyboard_handler import (
    BattleKeyboardHandler,
)


class TestBattleKeyboardHandler:
    """Test keyboard input handling."""

    @pytest.fixture
    def mock_battle_screen(self):
        """Create mock battle screen."""
        screen = MagicMock()
        screen.pause_menu = MagicMock()
        screen.pause_menu.visible = False
        screen.pause_menu.toggle = MagicMock()
        screen.reaction_popup = MagicMock()
        screen.reaction_popup.visible = False
        screen.reaction_popup.hide = MagicMock()
        screen.battle_log_popup = MagicMock()
        screen.battle_log_popup.visible = False
        screen.battle_log_popup.hide = MagicMock()
        screen.weapon_switch_popup = MagicMock()
        screen.weapon_switch_popup.visible = False
        screen.weapon_switch_popup.hide = MagicMock()
        screen.unit_popup = MagicMock()
        screen.unit_popup.visible = False
        screen.unit_popup.hide = MagicMock()
        screen.action_mode = MagicMock()
        screen._end_current_turn = MagicMock()
        screen._cancel_action = MagicMock()
        screen._enter_move_mode = MagicMock()
        screen._enter_attack_mode = MagicMock()
        screen._enter_inspect_mode = MagicMock()
        screen._open_weapon_switch_popup = MagicMock()
        screen._rotate_current_unit = MagicMock()
        return screen

    @pytest.fixture
    def handler(self, mock_battle_screen):
        """Create handler with mock battle screen."""
        return BattleKeyboardHandler(mock_battle_screen)

    def test_init(self, handler):
        """Should initialize with key handlers."""
        assert handler.battle_screen is not None
        assert len(handler._key_handlers) > 0

    def test_escape_closes_reaction_popup(self, handler, mock_battle_screen):
        """ESC should close reaction popup first."""
        mock_battle_screen.reaction_popup.visible = True

        handler.handle_keypress(pygame.K_ESCAPE)

        mock_battle_screen.reaction_popup.hide.assert_called_once()

    def test_escape_closes_battle_log_when_no_reaction(self, handler, mock_battle_screen):
        """ESC should close battle log if reaction popup not visible."""
        mock_battle_screen.battle_log_popup.visible = True

        handler.handle_keypress(pygame.K_ESCAPE)

        mock_battle_screen.battle_log_popup.hide.assert_called_once()

    def test_escape_closes_weapon_switch_when_no_popups(self, handler, mock_battle_screen):
        """ESC should close weapon switch if other popups not visible."""
        mock_battle_screen.weapon_switch_popup.visible = True

        handler.handle_keypress(pygame.K_ESCAPE)

        mock_battle_screen.weapon_switch_popup.hide.assert_called_once()

    def test_escape_closes_unit_popup_when_no_other_popups(self, handler, mock_battle_screen):
        """ESC should close unit popup if other popups not visible."""
        mock_battle_screen.unit_popup.visible = True

        handler.handle_keypress(pygame.K_ESCAPE)

        mock_battle_screen.unit_popup.hide.assert_called_once()

    def test_escape_toggles_pause_menu_when_all_hidden(self, handler, mock_battle_screen):
        """ESC should toggle pause menu if all popups hidden."""
        handler.handle_keypress(pygame.K_ESCAPE)

        mock_battle_screen.pause_menu.toggle.assert_called_once()

    def test_space_ends_turn(self, handler, mock_battle_screen):
        """SPACE should end current turn."""
        handler.handle_keypress(pygame.K_SPACE)

        mock_battle_screen._end_current_turn.assert_called_once()

    def test_return_ends_turn(self, handler, mock_battle_screen):
        """RETURN should end current turn."""
        handler.handle_keypress(pygame.K_RETURN)

        mock_battle_screen._end_current_turn.assert_called_once()

    def test_space_ignored_during_pause(self, handler, mock_battle_screen):
        """SPACE should be ignored if pause menu visible."""
        mock_battle_screen.pause_menu.visible = True

        handler.handle_keypress(pygame.K_SPACE)

        mock_battle_screen._end_current_turn.assert_not_called()

    def test_m_enters_move_mode(self, handler, mock_battle_screen):
        """M should enter move mode when not in move mode."""
        from MAGUS_pygame.presentation.screens.game.battle.battle_action_mode import ActionMode
        mock_battle_screen.action_mode = ActionMode.IDLE

        handler.handle_keypress(pygame.K_m)

        mock_battle_screen._enter_move_mode.assert_called_once()

    def test_a_enters_attack_mode(self, handler, mock_battle_screen):
        """A should enter attack mode when not in attack mode."""
        from MAGUS_pygame.presentation.screens.game.battle.battle_action_mode import ActionMode
        mock_battle_screen.action_mode = ActionMode.IDLE

        handler.handle_keypress(pygame.K_a)

        mock_battle_screen._enter_attack_mode.assert_called_once()

    def test_w_opens_weapon_switch(self, handler, mock_battle_screen):
        """W should open weapon switch popup."""
        handler.handle_keypress(pygame.K_w)

        mock_battle_screen._open_weapon_switch_popup.assert_called_once()

    def test_i_enters_inspect_mode(self, handler, mock_battle_screen):
        """I should enter inspect mode when not in inspect mode."""
        from MAGUS_pygame.presentation.screens.game.battle.battle_action_mode import ActionMode
        mock_battle_screen.action_mode = ActionMode.IDLE

        handler.handle_keypress(pygame.K_i)

        mock_battle_screen._enter_inspect_mode.assert_called_once()

    def test_q_rotates_counterclockwise(self, handler, mock_battle_screen):
        """Q should rotate current unit counter-clockwise."""
        handler.handle_keypress(pygame.K_q)

        mock_battle_screen._rotate_current_unit.assert_called_once_with(-1)

    def test_e_rotates_clockwise(self, handler, mock_battle_screen):
        """E should rotate current unit clockwise."""
        handler.handle_keypress(pygame.K_e)

        mock_battle_screen._rotate_current_unit.assert_called_once_with(1)

    def test_unknown_key_ignored(self, handler, mock_battle_screen):
        """Unknown keys should be ignored."""
        handler.handle_keypress(pygame.K_z)

        mock_battle_screen._end_current_turn.assert_not_called()
        mock_battle_screen._enter_move_mode.assert_not_called()

    def test_m_key_handling(self, handler, mock_battle_screen):
        """M key should call _enter_move_mode or _cancel_action based on mode."""
        handler.handle_keypress(pygame.K_m)
        # Without pause menu blocking, one of these should be called
        assert (mock_battle_screen._cancel_action.called or 
                mock_battle_screen._enter_move_mode.called)

    def test_a_key_handling(self, handler, mock_battle_screen):
        """A key should call _enter_attack_mode or _cancel_action based on mode."""
        handler.handle_keypress(pygame.K_a)
        # Without pause menu blocking, one of these should be called
        assert (mock_battle_screen._cancel_action.called or 
                mock_battle_screen._enter_attack_mode.called)

    def test_i_key_handling(self, handler, mock_battle_screen):
        """I key should call _enter_inspect_mode or _cancel_action based on mode."""
        handler.handle_keypress(pygame.K_i)
        # Without pause menu blocking, one of these should be called
        assert (mock_battle_screen._cancel_action.called or 
                mock_battle_screen._enter_inspect_mode.called)
