"""Tests for menu_screen Menu behavior."""

import pygame
import pytest

from MAGUS_pygame.presentation.screens.menu.menu_screen import Menu, MenuItem, MenuState


@pytest.fixture(scope="module", autouse=True)
def pygame_setup():
    """Initialize pygame for menu tests."""
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


@pytest.fixture
def menu():
    """Create a Menu instance for testing."""
    return Menu(800, 600)


class TestMenuLoadingBehavior:
    """Tests for loading state behavior."""

    def test_handle_event_ignored_when_loading(self, menu):
        """Input should be ignored while loading is true."""
        menu.is_loading = True
        menu.selected_index = 0

        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
        menu.handle_event(event)

        assert menu.get_last_action() is None


class TestMenuSelection:
    """Tests for menu selection logic."""

    def test_move_selection_skips_disabled_items(self, menu):
        """Selection should skip disabled items when moving."""
        menu.main_menu_items = [
            MenuItem("Disabled", enabled=False),
            MenuItem("Enabled", enabled=True),
        ]
        menu.state = MenuState.MAIN_MENU
        menu.selected_index = 0

        menu._move_selection(1)

        assert menu.selected_index == 1

    def test_move_selection_all_disabled_no_recursion(self, menu):
        """Selection should not recurse infinitely if all items are disabled."""
        menu.settings_items = [
            MenuItem("Disabled 1", enabled=False),
            MenuItem("Disabled 2", enabled=False),
        ]
        menu.state = MenuState.SETTINGS
        menu.selected_index = 0

        menu._move_selection(1)

        assert menu.selected_index == 0


class TestMenuQuitAction:
    """Tests for quit action handling."""

    def test_quit_game_sets_last_action(self, menu):
        """Quit should set last_action so coordinator can handle it."""
        menu._quit_game()
        assert menu.get_last_action() == "quit"
