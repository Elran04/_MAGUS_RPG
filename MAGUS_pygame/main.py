"""
MAGUS RPG - Main entry point (New Clean Architecture).

Complete game flow: Menu -> Scenario Selection -> Deployment -> Battle

For architecture details, see ARCHITECTURE.md
For porting guide, see MIGRATION.md
For quick start, see QUICKSTART.md
"""

import pygame
from application.game_context import GameContext
from application.start_game import start_game
from config import HEIGHT, WIDTH
from logger.logger import get_logger
from presentation.screens.menu_screen import Menu

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
    game_state = "menu"  # menu, playing, quit
    menu = Menu(WIDTH, HEIGHT)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                if game_state == "menu":
                    menu.handle_event(event)

        if game_state == "menu":
            # Draw menu
            menu.draw(screen)
            pygame.display.flip()

            # Check for menu actions
            action = menu.get_last_action()
            if action == "new_game":
                logger.info("Starting new game")
                menu.reset_action()
                menu.close()
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

            elif action == "save_game":
                # TODO: Implement save game
                logger.info("Save game not yet implemented")
                menu.reset_action()

        clock.tick(60)

    # Cleanup
    logger.info("Shutting down...")
    context.shutdown()
    pygame.quit()
    logger.info("Application closed")


if __name__ == "__main__":
    main()
