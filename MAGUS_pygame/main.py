"""
MAGUS RPG - Main entry point (New Clean Architecture).

Complete game flow: Menu -> Scenario Selection -> Deployment -> Battle

For architecture details, see ARCHITECTURE.md
For porting guide, see MIGRATION.md
For quick start, see QUICKSTART.md
"""

import multiprocessing

import pygame
from application.game_context import GameContext
from application.game_flow_service import start_game
from config import HEIGHT, WIDTH
from logger.logger import get_logger
from presentation.desktop.editor_tool_window import run_tool_window
from presentation.screens.editor.scenario_editor_screen import ScenarioEditorScreen
from presentation.screens.menu.menu_screen import Menu

logger = get_logger(__name__)


def main() -> None:
    """Main application entry point."""
    logger.info("=" * 60)
    logger.info("MAGUS RPG - Starting Game")
    logger.info("=" * 60)

    # Initialize pygame
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("MAGUS RPG")
    clock = pygame.time.Clock()

    # Initialize application context
    context = GameContext()

    # Main game loop
    running = True
    game_state = "menu"  # menu, playing, scenario_editor, quit
    menu = Menu(WIDTH, HEIGHT)
    scenario_editor: ScenarioEditorScreen | None = None
    tool_window_process = None
    tool_window_quit_event = None
    # Shared queues for editor communication
    ui_to_game_queue = None
    game_to_ui_queue = None

    while running:
        # Process events based on game state
        if game_state == "menu":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    menu.handle_event(event)

            # Draw menu
            menu.draw(screen)
            pygame.display.flip()

            # Check for menu actions (only if menu is still open)
            action = menu.get_last_action()
            if action == "new_game":
                logger.info("Starting new game")
                menu.reset_action()
                game_state = "playing"

                # Start game (runs until completion or quit)
                start_game(context, screen, clock)

                # Return to menu after game ends
                game_state = "menu"
                menu.open_main_menu()
                logger.info("Returned to main menu")

            elif action == "load_game":
                # TODO: Implement load game
                logger.info("Load game not yet implemented")
                menu.reset_action()
            elif action == "scenario_editor":
                logger.info("Opening Scenario Editor - menu action received")
                menu.reset_action()

                # Clear any pending events
                pygame.event.clear()

                scenario_editor = ScenarioEditorScreen(WIDTH, HEIGHT, context)
                game_state = "scenario_editor"
                logger.info(f"Scenario Editor created, game_state is now: {game_state}")

                # Launch PySide6 tool window in a separate process
                if tool_window_process is None or not tool_window_process.is_alive():
                    # Create shared queues for inter-process communication
                    ui_to_game_queue = multiprocessing.Queue()
                    game_to_ui_queue = multiprocessing.Queue()

                    # Create event bus instance for game process
                    from infrastructure.events.event_bus import EditorEventBus

                    event_bus = EditorEventBus(ui_to_game_queue, game_to_ui_queue)
                    scenario_editor.set_event_bus(event_bus)

                    tool_window_quit_event = multiprocessing.Event()
                    tool_window_process = multiprocessing.Process(
                        target=run_tool_window,
                        args=(tool_window_quit_event, ui_to_game_queue, game_to_ui_queue),
                        daemon=True,
                    )
                    tool_window_process.start()
                    logger.info("Editor Tool Window launched in separate process")

        elif game_state == "scenario_editor":
            if scenario_editor is None:
                # Safety fallback
                game_state = "menu"
            else:
                events = pygame.event.get()
                for event in events:
                    if event.type == pygame.QUIT:
                        running = False
                    else:
                        scenario_editor.handle_event(event)
                # Process any external tool window events
                scenario_editor.process_external_events()

                scenario_editor.draw(screen)
                pygame.display.flip()
                if scenario_editor.is_done():
                    logger.info("Scenario Editor closed, returning to menu")
                    # Request PySide6 tool window to close
                    if tool_window_quit_event:
                        tool_window_quit_event.set()
                    if tool_window_process and tool_window_process.is_alive():
                        tool_window_process.join(timeout=1.0)
                        if tool_window_process.is_alive():
                            tool_window_process.terminate()
                    game_state = "menu"
                    menu.open_main_menu()
                    scenario_editor = None
                    tool_window_process = None
                    tool_window_quit_event = None
                    ui_to_game_queue = None
                    game_to_ui_queue = None
        # Save game action handled only in menu state

        clock.tick(60)

    # Cleanup
    logger.info("Shutting down...")
    context.shutdown()
    pygame.quit()
    logger.info("Application closed")


if __name__ == "__main__":
    main()
