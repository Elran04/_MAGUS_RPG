"""Game Coordinator - High-level game orchestration and state management.

Manages the main game loop, menu navigation, and transitions between game states
(menu, playing, scenario editor, etc.). This is the presentation layer's
orchestration point, coordinating screens and delegating to application services.
"""

import multiprocessing
from typing import TYPE_CHECKING

import pygame
from application.game_context import GameContext
from application.game_flow_service import coordinate_game_flow
from application.quick_combat_service import prepare_quick_combat_battle
from config import HEIGHT, WIDTH
from infrastructure.events.event_bus import EditorEventBus
from logger.logger import get_logger
from presentation.screens.editor.scenario_editor_screen import ScenarioEditorScreen
from presentation.screens.game.battle_screen import BattleScreen
from presentation.screens.game.deployment_screen import DeploymentScreen
from presentation.screens.menu.menu_screen import Menu
from presentation.screens.scenario_setup.scenario_screen import ScenarioScreen

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)


def run_screen_loop(screen_obj, cancel_action: str | None = None, update_method=None) -> str:
    """
    Run the event loop for a screen object until completion.

    Args:
        screen_obj: Screen object with handle_event(), draw(), and get_action() methods
        cancel_action: Action name to return on cancel/back
        update_method: Optional update method to call each frame (e.g., battle_screen.update)

    Returns:
        Final action string ('quit', 'cancelled', or screen-specific action)
    """
    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            screen_obj.handle_event(event)

        # Update if screen has update logic (e.g., battle turn processing)
        if update_method:
            update_method()

        # Draw screen
        screen_obj.draw(pygame.display.get_surface())
        pygame.display.flip()
        clock.tick(60)

        # Check if screen has finished
        action = screen_obj.get_action()
        if action:
            # Treat any non-empty action as an exit signal so screens can return
            # custom outcomes like battle_cancelled or battle_victory_team_a.
            if cancel_action and action == cancel_action:
                return action
            return action

    return "quit"


class GameCoordinator:
    """Orchestrates the main game loop and state transitions."""

    def __init__(self, context: GameContext):
        """Initialize game coordinator.

        Args:
            context: Game context with repositories and factories
        """
        self.context = context
        self.running = True
        self.game_state = "menu"  # menu, playing, scenario_editor, quit
        self.menu: Menu | None = None
        self.scenario_editor: ScenarioEditorScreen | None = None
        self.tool_window_process: multiprocessing.Process | None = None
        self.tool_window_quit_event: multiprocessing.Event | None = None
        self.ui_to_game_queue = None
        self.game_to_ui_queue = None
        self.editor_event_bus: EditorEventBus | None = None
        self.pending_action: str | None = None

    def run(self) -> None:
        """Run the main game loop."""
        logger.info("GameCoordinator starting main loop")

        self.menu = Menu(WIDTH, HEIGHT)
        self.menu.set_loading(True, "Initializing... you can pick a mode")
        self.menu.set_loading(False)  # Backend should be ready by this point
        self.menu.open_main_menu()

        while self.running:
            if self.game_state == "menu":
                self._handle_menu_state()
            elif self.game_state == "playing":
                # This shouldn't happen; _handle_menu_state transitions directly
                self.game_state = "menu"
            elif self.game_state == "scenario_editor":
                self._handle_scenario_editor_state()
            elif self.game_state == "quit":
                self.running = False

            pygame.time.wait(10)  # Prevent busy-waiting

    def _handle_menu_state(self) -> None:
        """Handle menu state and actions."""
        if not self.menu:
            return

        # Draw menu
        self.menu.draw(pygame.display.get_surface())
        pygame.display.flip()

        # Process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                self.game_state = "quit"
            else:
                self.menu.handle_event(event)

        # Check for menu actions
        action = self.menu.get_last_action()
        if not action:
            return

        self.menu.reset_action()

        if action == "new_game":
            logger.info("Starting new game")
            self._run_new_game()
            self.menu.open_main_menu()

        elif action == "quick_combat":
            logger.info("Starting quick combat")
            self._run_quick_combat()
            self.menu.open_main_menu()

        elif action == "load_game":
            logger.info("Load game not yet implemented")

        elif action == "scenario_editor":
            logger.info("Opening Scenario Editor")
            pygame.event.clear()
            self._ensure_tool_window()
            self.scenario_editor = ScenarioEditorScreen(WIDTH, HEIGHT, self.context)
            if self.editor_event_bus:
                self.scenario_editor.set_event_bus(self.editor_event_bus)
            self.game_state = "scenario_editor"

        elif action == "tool_window":
            logger.info("Opening Tool Window")
            self._ensure_tool_window()

        elif action == "quit":
            logger.info("Quit selected from menu")
            self.running = False
            self.game_state = "quit"

    def _handle_scenario_editor_state(self) -> None:
        """Handle scenario editor state."""
        if not self.scenario_editor:
            self.game_state = "menu"
            return

        # Draw scenario editor
        self.scenario_editor.draw(pygame.display.get_surface())
        pygame.display.flip()

        # Process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                self.game_state = "quit"
            else:
                self.scenario_editor.handle_event(event)

        # Check if editor wants to close
        action = self.scenario_editor.get_action()
        if action in ("back", "quit"):
            logger.info("Scenario editor closed")
            self.scenario_editor = None
            self.game_state = "menu"
            self.menu = Menu(WIDTH, HEIGHT)
            self.menu.open_main_menu()
            self._shutdown_tool_window()

    def _run_new_game(self) -> None:
        """Run the full game flow: Scenario -> Deployment -> Battle."""
        try:
            # Create screens
            scenario_screen = ScenarioScreen(WIDTH, HEIGHT, self.context)
            battle_screen = BattleScreen(WIDTH, HEIGHT, None, self.context)

            # Run game flow (application layer); create deployment screen after scenario selected
            result = coordinate_game_flow(
                self.context,
                scenario_screen,
                lambda config: DeploymentScreen(WIDTH, HEIGHT, config, self.context),
                battle_screen,
                run_screen_loop,
            )

            logger.info(f"Game flow completed: {result}")
        except Exception as e:
            logger.error(f"Error during game flow: {e}", exc_info=True)

    def _run_quick_combat(self) -> None:
        """Run quick combat battle."""
        try:
            # Prepare quick combat units and config (application layer)
            team_a_units, team_b_units, config = prepare_quick_combat_battle(self.context)

            # Load background (presentation layer responsibility); scaling handled by BattleScreen
            background = None
            bg_file = config.get("background_file")
            if bg_file:
                background = self.context.sprite_repo.load_background(bg_file)
                if background:
                    logger.info(f"Loaded quick combat background: {bg_file}")

            # Create battle screen (presentation layer)
            from application.battle_service import BattleService

            battle_service = BattleService(
                units=team_a_units + team_b_units,
                equipment_repo=self.context.equipment_repo,
                blocked_hexes=config.get("blocked_hexes"),
            )
            battle_service.set_teams(team_a_units, team_b_units)
            # Enable initiative so turn order is rolled and refreshed each round
            battle_service.enable_initiative()
            battle_service.start_battle()

            battle_screen = BattleScreen(WIDTH, HEIGHT, battle_service, self.context, background)

            # Run battle loop (presentation layer)
            result = run_screen_loop(battle_screen, update_method=battle_screen.update)

            logger.info(f"Quick combat completed: {result}")
        except Exception as e:
            logger.error(f"Error during quick combat: {e}", exc_info=True)

    def _ensure_tool_window(self) -> None:
        """Start the PySide6 tool window if it is not already running."""
        from presentation.desktop.editor_tool_window import run_tool_window

        if self.tool_window_process and self.tool_window_process.is_alive():
            # Ensure game-side bus exists if process is already up
            if not self.editor_event_bus and self.ui_to_game_queue and self.game_to_ui_queue:
                self.editor_event_bus = EditorEventBus(self.ui_to_game_queue, self.game_to_ui_queue)
            logger.info("Tool window already running")
            return

        # Use multiprocessing.Event so it is picklable on Windows spawn start method
        self.tool_window_quit_event = multiprocessing.Event()
        self.ui_to_game_queue = multiprocessing.Queue()
        self.game_to_ui_queue = multiprocessing.Queue()
        self.editor_event_bus = EditorEventBus(self.ui_to_game_queue, self.game_to_ui_queue)

        self.tool_window_process = multiprocessing.Process(
            target=run_tool_window,
            args=(self.tool_window_quit_event, self.ui_to_game_queue, self.game_to_ui_queue),
            daemon=True,
        )
        self.tool_window_process.start()
        logger.info("Tool window launched in separate process")

    def _shutdown_tool_window(self) -> None:
        """Signal the tool window to close and clean up resources."""
        if self.tool_window_quit_event:
            self.tool_window_quit_event.set()

        if self.tool_window_process:
            self.tool_window_process.join(timeout=1.0)
            if self.tool_window_process.is_alive():
                logger.warning("Tool window did not exit cleanly")

        self.tool_window_process = None
        self.tool_window_quit_event = None
        self.editor_event_bus = None
        self.ui_to_game_queue = None
        self.game_to_ui_queue = None
