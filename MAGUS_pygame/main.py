"""
MAGUS RPG - Main entry point (Clean Architecture).

Complete game flow: Menu -> Scenario Selection -> Deployment -> Battle

For architecture details, see docs/ARCHITECTURE.md
For setup and run, see docs/DEVELOPER_GUIDE.md
For porting legacy features, see docs/archive/MIGRATION.md
"""

import pygame
from application.game_context import GameContext
from config import HEIGHT, WIDTH
from logger.logger import get_logger
from presentation.game_coordinator import GameCoordinator

logger = get_logger(__name__)


def main() -> None:
    """Main application entry point - thin bootstrap."""
    logger.info("=" * 60)
    logger.info("MAGUS RPG - Starting Game")
    logger.info("=" * 60)

    # Initialize pygame first
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("MAGUS RPG")

    # Initialize game context (fast operation: repositories are lazy-loaded)
    try:
        logger.info("Initializing game context...")
        context = GameContext()
        logger.info("Game context initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize game context: {e}", exc_info=True)
        pygame.quit()
        return

    # Delegate to game coordinator
    try:
        coordinator = GameCoordinator(context)
        coordinator.run()
    except Exception as e:
        logger.error(f"Fatal error in game coordinator: {e}", exc_info=True)
    finally:
        # Graceful cleanup
        if hasattr(context, "shutdown"):
            context.shutdown()
        logger.info("Game coordinator finished, exiting")
        pygame.quit()


if __name__ == "__main__":
    main()
