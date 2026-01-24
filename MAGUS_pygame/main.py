"""
MAGUS RPG - Main entry point (Clean Architecture).

Complete game flow: Menu -> Scenario Selection -> Deployment -> Battle

For architecture details, see docs/ARCHITECTURE.md
For setup and run, see docs/DEVELOPER_GUIDE.md
For porting legacy features, see docs/archive/MIGRATION.md
"""

import threading

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

    # Initialize pygame
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("MAGUS RPG")

    # Initialize context on background thread (non-blocking)
    context: GameContext | None = None
    context_ready = threading.Event()

    def init_context() -> None:
        nonlocal context
        context = GameContext()
        context_ready.set()

    context_thread = threading.Thread(target=init_context, daemon=True)
    context_thread.start()

    # Wait for context to be ready
    context_ready.wait()
    if context is None:
        logger.error("Failed to initialize game context")
        return

    logger.info("Game context initialized, starting coordinator")

    # Delegate to game coordinator
    coordinator = GameCoordinator(context)
    coordinator.run()

    logger.info("Game coordinator finished, exiting")
    pygame.quit()


if __name__ == "__main__":
    main()
