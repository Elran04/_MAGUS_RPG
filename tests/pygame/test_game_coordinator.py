"""Tests for GameCoordinator state management and transitions."""

import pytest
from unittest.mock import MagicMock, patch

from MAGUS_pygame.application.game_context import GameContext
from MAGUS_pygame.presentation.game_coordinator import GameState, GameCoordinator


@pytest.fixture
def mock_context():
    """Create a mock GameContext."""
    context = MagicMock(spec=GameContext)
    return context


@pytest.fixture
def coordinator(mock_context):
    """Create a GameCoordinator instance for testing."""
    return GameCoordinator(mock_context)


class TestGameCoordinatorInitialization:
    """Test GameCoordinator initialization."""

    def test_coordinator_initializes_with_menu_state(self, coordinator):
        """Test that GameCoordinator starts in MENU state."""
        assert coordinator.game_state == GameState.MENU

    def test_coordinator_initializes_running(self, coordinator):
        """Test that GameCoordinator starts with running=True."""
        assert coordinator.running is True

    def test_coordinator_initializes_empty_screens(self, coordinator):
        """Test that screens are None on initialization."""
        assert coordinator.menu is None
        assert coordinator.scenario_editor is None

    def test_coordinator_initializes_tool_window_fields_none(self, coordinator):
        """Test that tool window fields are None on initialization."""
        assert coordinator.tool_window_process is None
        assert coordinator.tool_window_quit_event is None
        assert coordinator.ui_to_game_queue is None
        assert coordinator.game_to_ui_queue is None
        assert coordinator.editor_event_bus is None

    def test_coordinator_stores_context(self, coordinator, mock_context):
        """Test that coordinator stores the context reference."""
        assert coordinator.context is mock_context


class TestGameStateEnum:
    """Test GameState enum values."""

    def test_game_state_enum_values(self):
        """Test that GameState has expected values."""
        assert GameState.MENU.value == "menu"
        assert GameState.SCENARIO_EDITOR.value == "scenario_editor"
        assert GameState.QUIT.value == "quit"

    def test_game_state_enum_members(self):
        """Test that GameState has exactly 3 members."""
        members = list(GameState)
        assert len(members) == 3

    def test_game_state_enum_comparison(self):
        """Test enum value comparisons."""
        assert GameState.MENU != GameState.SCENARIO_EDITOR
        assert GameState.MENU != GameState.QUIT
        assert GameState.SCENARIO_EDITOR != GameState.QUIT


class TestGameCoordinatorStateTransitions:
    """Test state transitions in GameCoordinator."""

    def test_can_set_game_state_to_scenario_editor(self, coordinator):
        """Test setting game state to SCENARIO_EDITOR."""
        coordinator.game_state = GameState.SCENARIO_EDITOR
        assert coordinator.game_state == GameState.SCENARIO_EDITOR

    def test_can_set_game_state_to_quit(self, coordinator):
        """Test setting game state to QUIT."""
        coordinator.game_state = GameState.QUIT
        assert coordinator.game_state == GameState.QUIT

    def test_can_reset_to_menu_state(self, coordinator):
        """Test resetting to MENU state."""
        coordinator.game_state = GameState.SCENARIO_EDITOR
        coordinator.game_state = GameState.MENU
        assert coordinator.game_state == GameState.MENU


class TestHandleMenuStateValidation:
    """Test _handle_menu_state method structure."""

    def test_handle_menu_state_returns_early_if_no_menu(self, coordinator):
        """Test that _handle_menu_state handles None menu gracefully."""
        coordinator.menu = None
        # Should not raise an exception
        coordinator._handle_menu_state()

    def test_handle_menu_state_exists(self, coordinator):
        """Test that _handle_menu_state method exists and is callable."""
        assert callable(coordinator._handle_menu_state)

    def test_handle_scenario_editor_state_exists(self, coordinator):
        """Test that _handle_scenario_editor_state method exists."""
        assert callable(coordinator._handle_scenario_editor_state)


class TestToolWindowManagement:
    """Test tool window initialization and shutdown."""

    def test_shutdown_tool_window_with_no_process(self, coordinator):
        """Test shutdown when tool window process is None."""
        coordinator.tool_window_process = None
        # Should not raise an exception
        coordinator._shutdown_tool_window()

    def test_shutdown_tool_window_clears_all_fields(self, coordinator):
        """Test that shutdown clears all tool window related fields."""
        # Setup some mock values
        coordinator.tool_window_process = MagicMock()
        coordinator.tool_window_quit_event = MagicMock()
        coordinator.ui_to_game_queue = MagicMock()
        coordinator.game_to_ui_queue = MagicMock()
        coordinator.editor_event_bus = MagicMock()

        # Shutdown
        coordinator._shutdown_tool_window()

        # All fields should be None
        assert coordinator.tool_window_process is None
        assert coordinator.tool_window_quit_event is None
        assert coordinator.ui_to_game_queue is None
        assert coordinator.game_to_ui_queue is None
        assert coordinator.editor_event_bus is None


class TestRunNewGameValidation:
    """Test _run_new_game method structure."""

    def test_run_new_game_method_exists(self, coordinator):
        """Test that _run_new_game method exists and is callable."""
        assert callable(coordinator._run_new_game)


class TestRunQuickCombatValidation:
    """Test _run_quick_combat method structure."""

    def test_run_quick_combat_method_exists(self, coordinator):
        """Test that _run_quick_combat method exists and is callable."""
        assert callable(coordinator._run_quick_combat)


class TestMenuStateErrorHandling:
    """Test error handling in menu state."""

    def test_menu_state_has_quit_action_in_enum(self):
        """Test that quit action uses proper state."""
        # Verify the enum value for quit state
        assert GameState.QUIT.value == "quit"


class TestCoordinatorAttributes:
    """Test GameCoordinator attribute types and initialization."""

    def test_coordinator_has_context_attribute(self, coordinator):
        """Test that coordinator has context attribute."""
        assert hasattr(coordinator, "context")

    def test_coordinator_has_running_flag(self, coordinator):
        """Test that coordinator has running flag."""
        assert hasattr(coordinator, "running")
        assert isinstance(coordinator.running, bool)

    def test_coordinator_has_game_state(self, coordinator):
        """Test that coordinator has game_state attribute."""
        assert hasattr(coordinator, "game_state")

    def test_coordinator_has_menu_attribute(self, coordinator):
        """Test that coordinator has menu attribute."""
        assert hasattr(coordinator, "menu")

    def test_coordinator_has_scenario_editor_attribute(self, coordinator):
        """Test that coordinator has scenario_editor attribute."""
        assert hasattr(coordinator, "scenario_editor")


class TestRunScreenLoopImport:
    """Test that run_screen_loop is available and has correct signature."""

    def test_run_screen_loop_is_callable(self):
        """Test that run_screen_loop function is importable."""
        from MAGUS_pygame.presentation.game_coordinator import run_screen_loop

        assert callable(run_screen_loop)

    def test_run_screen_loop_has_correct_signature(self):
        """Test that run_screen_loop has expected parameters."""
        from MAGUS_pygame.presentation.game_coordinator import run_screen_loop
        import inspect

        sig = inspect.signature(run_screen_loop)
        params = list(sig.parameters.keys())
        # Should have at least screen_obj, cancel_action, update_method
        assert "screen_obj" in params
        assert "cancel_action" in params
        assert "update_method" in params
