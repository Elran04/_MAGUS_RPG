"""
MAGUS RPG - Main entry point (New Clean Architecture).

This is a minimal test entry point to verify the new architecture works.
Full game features will be incrementally reimplemented.

For architecture details, see ARCHITECTURE.md
For porting guide, see MIGRATION.md
For quick start, see QUICKSTART.md
"""

import pygame

from config import WIDTH, HEIGHT
from logger.logger import get_logger
from application.game_context import GameContext
from domain.value_objects import Position, Facing
from presentation.test_screen import TestScreen

logger = get_logger(__name__)


def main() -> None:
    """Main application entry point."""
    logger.info("=" * 60)
    logger.info("MAGUS RPG - New Architecture Test")
    logger.info("=" * 60)
    
    # Initialize pygame
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("MAGUS RPG - Architecture Test")
    clock = pygame.time.Clock()
    
    # Initialize application context
    context = GameContext()
    
    # Create test screen
    test_screen = TestScreen(WIDTH, HEIGHT)
    
    # Create a test unit
    logger.info("Creating test unit...")
    test_unit = context.unit_factory.create_unit(
        character_filename="Warri.json",
        position=Position(q=0, r=0),
        facing=Facing(0)
    )
    
    if test_unit:
        # Load sprite for the unit
        sprite = context.sprite_repo.load_character_sprite("warrior.png")
        if sprite:
            test_unit.sprite = sprite
        
        test_screen.set_test_unit(test_unit)
        logger.info("Test unit created successfully")
    else:
        logger.error("Failed to create test unit")
    
    # Main loop
    running = True
    while running and test_screen.is_running():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                test_screen.handle_event(event)
        
        # Draw
        test_screen.draw(screen)
        pygame.display.flip()
        clock.tick(60)
    
    # Cleanup
    logger.info("Shutting down...")
    context.shutdown()
    pygame.quit()
    logger.info("Application closed")


if __name__ == "__main__":
    main()
