"""Tests for BattlePopupManager."""

from unittest.mock import MagicMock

import pytest

from MAGUS_pygame.presentation.screens.game.battle.battle_popups import (
    BattlePopupManager,
)


class TestBattlePopupManager:
    """Test popup management."""

    @pytest.fixture
    def mock_unit_popup(self):
        """Create mock unit popup."""
        popup = MagicMock()
        popup.visible = False
        popup.show = MagicMock()
        popup.hide = MagicMock()
        popup.handle_click = MagicMock(return_value=True)
        popup.is_click_outside = MagicMock(return_value=False)
        return popup

    @pytest.fixture
    def mock_weapon_switch_popup(self):
        """Create mock weapon switch popup."""
        popup = MagicMock()
        popup.visible = False
        popup.show = MagicMock()
        popup.hide = MagicMock()
        popup.handle_click = MagicMock(return_value=("apply", "main_id", "off_id"))
        popup.is_click_outside = MagicMock(return_value=False)
        return popup

    @pytest.fixture
    def mock_battle_log_popup(self):
        """Create mock battle log popup."""
        popup = MagicMock()
        popup.visible = False
        popup.handle_event = MagicMock(return_value=True)
        return popup

    @pytest.fixture
    def mock_reaction_popup(self):
        """Create mock reaction popup."""
        popup = MagicMock()
        popup.visible = False
        popup.handle_click = MagicMock(return_value="accept")
        popup.is_click_outside = MagicMock(return_value=False)
        return popup

    @pytest.fixture
    def manager(
        self,
        mock_unit_popup,
        mock_weapon_switch_popup,
        mock_battle_log_popup,
        mock_reaction_popup,
    ):
        """Create manager with mock popups."""
        manager = BattlePopupManager()
        manager.set_popups(
            mock_unit_popup,
            mock_weapon_switch_popup,
            mock_battle_log_popup,
            mock_reaction_popup,
        )
        return manager

    def test_init(self):
        """Should initialize with None popups."""
        manager = BattlePopupManager()
        assert manager.unit_popup is None
        assert manager.weapon_switch_popup is None
        assert manager.battle_log_popup is None
        assert manager.reaction_popup is None

    def test_set_popups(
        self,
        mock_unit_popup,
        mock_weapon_switch_popup,
        mock_battle_log_popup,
        mock_reaction_popup,
    ):
        """Should set popup references."""
        manager = BattlePopupManager()
        manager.set_popups(
            mock_unit_popup,
            mock_weapon_switch_popup,
            mock_battle_log_popup,
            mock_reaction_popup,
        )

        assert manager.unit_popup is mock_unit_popup
        assert manager.weapon_switch_popup is mock_weapon_switch_popup
        assert manager.battle_log_popup is mock_battle_log_popup
        assert manager.reaction_popup is mock_reaction_popup

    def test_handle_unit_popup_click_not_visible(
        self, manager, mock_unit_popup
    ):
        """Should return False when unit popup not visible."""
        mock_unit_popup.visible = False

        result = manager.handle_unit_popup_click((100, 100))

        assert result is False

    def test_handle_unit_popup_click_visible_with_handle(
        self, manager, mock_unit_popup
    ):
        """Should handle click when visible and handle_click returns True."""
        mock_unit_popup.visible = True
        mock_unit_popup.handle_click.return_value = True

        result = manager.handle_unit_popup_click((100, 100))

        assert result is True
        mock_unit_popup.handle_click.assert_called_once_with(100, 100)

    def test_handle_unit_popup_click_outside(
        self, manager, mock_unit_popup
    ):
        """Should hide popup when click outside."""
        mock_unit_popup.visible = True
        mock_unit_popup.handle_click.return_value = False
        mock_unit_popup.is_click_outside.return_value = True

        result = manager.handle_unit_popup_click((100, 100))

        assert result is True
        mock_unit_popup.hide.assert_called_once()

    def test_handle_weapon_switch_popup_not_visible(self, manager, mock_weapon_switch_popup):
        """Should return (False, None, None, None) when not visible."""
        mock_weapon_switch_popup.visible = False

        handled, action, main, off = manager.handle_weapon_switch_popup_click((100, 100))

        assert handled is False
        assert action is None
        assert main is None
        assert off is None

    def test_handle_weapon_switch_popup_apply(
        self, manager, mock_weapon_switch_popup
    ):
        """Should handle apply action."""
        mock_weapon_switch_popup.visible = True
        mock_weapon_switch_popup.handle_click.return_value = ("apply", "main", "off")

        handled, action, main, off = manager.handle_weapon_switch_popup_click((100, 100))

        assert handled is True
        assert action == "apply"
        assert main == "main"
        assert off == "off"

    def test_handle_weapon_switch_popup_cancel(
        self, manager, mock_weapon_switch_popup
    ):
        """Should handle cancel action."""
        mock_weapon_switch_popup.visible = True
        mock_weapon_switch_popup.handle_click.return_value = ("cancel", None, None)

        handled, action, main, off = manager.handle_weapon_switch_popup_click((100, 100))

        assert handled is True
        assert action == "cancel"
        mock_weapon_switch_popup.hide.assert_called_once()

    def test_handle_weapon_switch_popup_outside(
        self, manager, mock_weapon_switch_popup
    ):
        """Should handle click outside."""
        mock_weapon_switch_popup.visible = True
        mock_weapon_switch_popup.handle_click.return_value = ("", None, None)
        mock_weapon_switch_popup.is_click_outside.return_value = True

        handled, action, main, off = manager.handle_weapon_switch_popup_click((100, 100))

        assert handled is True
        assert action == "outside"
        mock_weapon_switch_popup.hide.assert_called_once()

    def test_handle_battle_log_click_not_visible(self, manager, mock_battle_log_popup):
        """Should return False when not visible."""
        mock_battle_log_popup.visible = False

        result = manager.handle_battle_log_click(1, (100, 100))

        assert result is False

    def test_handle_battle_log_click_visible(self, manager, mock_battle_log_popup):
        """Should handle click when visible."""
        mock_battle_log_popup.visible = True
        mock_battle_log_popup.handle_event.return_value = True

        result = manager.handle_battle_log_click(1, (100, 100))

        assert result is True

    def test_handle_reaction_popup_click_not_visible(
        self, manager, mock_reaction_popup
    ):
        """Should return False when not visible."""
        mock_reaction_popup.visible = False

        result = manager.handle_reaction_popup_click((100, 100))

        assert result is False

    def test_handle_reaction_popup_click_visible_with_action(
        self, manager, mock_reaction_popup
    ):
        """Should handle click when visible and action occurs."""
        mock_reaction_popup.visible = True
        mock_reaction_popup.handle_click.return_value = "accept"

        result = manager.handle_reaction_popup_click((100, 100))

        assert result is True

    def test_handle_reaction_popup_click_outside(
        self, manager, mock_reaction_popup
    ):
        """Should handle click outside."""
        mock_reaction_popup.visible = True
        mock_reaction_popup.handle_click.return_value = None
        mock_reaction_popup.is_click_outside.return_value = True

        result = manager.handle_reaction_popup_click((100, 100))

        assert result is True
        mock_reaction_popup.handle_click.assert_called()

    def test_show_unit_info(self, manager, mock_unit_popup):
        """Should show unit info popup."""
        unit = MagicMock()
        context = MagicMock()

        manager.show_unit_info(unit, context)

        mock_unit_popup.show.assert_called_once_with(unit)

    def test_show_weapon_switch(self, manager, mock_weapon_switch_popup):
        """Should show weapon switch popup."""
        unit = MagicMock()
        context = MagicMock()

        manager.show_weapon_switch(unit, context)

        mock_weapon_switch_popup.show.assert_called_once_with(unit)

    def test_show_battle_log(self, manager, mock_battle_log_popup):
        """Should show battle log popup."""
        manager.show_battle_log()

        mock_battle_log_popup.show.assert_called_once()

    def test_close_all(
        self, manager, mock_unit_popup, mock_weapon_switch_popup, mock_battle_log_popup, mock_reaction_popup
    ):
        """Should close all popups."""
        # Set popups as visible
        mock_unit_popup.visible = True
        mock_weapon_switch_popup.visible = True
        mock_battle_log_popup.visible = True
        mock_reaction_popup.visible = True

        manager.close_all()

        mock_unit_popup.hide.assert_called_once()
        mock_weapon_switch_popup.hide.assert_called_once()
        mock_battle_log_popup.hide.assert_called_once()
        mock_reaction_popup.hide.assert_called_once()

    def test_any_visible_none_visible(
        self, manager, mock_unit_popup, mock_weapon_switch_popup, mock_battle_log_popup, mock_reaction_popup
    ):
        """Should return False when no popups visible."""
        mock_unit_popup.visible = False
        mock_weapon_switch_popup.visible = False
        mock_battle_log_popup.visible = False
        mock_reaction_popup.visible = False

        result = manager.any_visible()

        assert result is False

    def test_any_visible_one_visible(
        self, manager, mock_unit_popup, mock_weapon_switch_popup, mock_battle_log_popup, mock_reaction_popup
    ):
        """Should return True when at least one popup visible."""
        mock_unit_popup.visible = False
        mock_weapon_switch_popup.visible = True
        mock_battle_log_popup.visible = False
        mock_reaction_popup.visible = False

        result = manager.any_visible()

        assert result is True
