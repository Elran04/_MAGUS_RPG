"""
MAGUS RPG - Main entry point with menu system.
"""

import pygame

from config import HEIGHT, WIDTH
from core.game_loop import run_game_loop
from logger.logger import get_logger
from ui.menu import Menu

# Logger initialization
logger = get_logger(__name__)

# Initialize pygame
logger.info("Pygame initialization")
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("MAGUS RPG - Hex-Grid Turn-Based Combat")
clock = pygame.time.Clock()


def main() -> None:
    """Main application loop with menu system."""
    logger.info("=" * 60)
    logger.info("MAGUS RPG starting")
    logger.info("=" * 60)
    
    # Initialize menu
    menu = Menu(WIDTH, HEIGHT)
    menu.open_main_menu()
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Let menu handle events
            if menu.is_open():
                menu.handle_event(event)
        
        # Check if an action was selected from the menu
        if not menu.is_open():
            action = menu.get_last_action()
            
            if action == "new_game":
                logger.info("Starting new game from menu")
                menu.reset_action()
                run_game_loop(screen, clock)
                # After game ends, reopen menu
                menu.open_main_menu()
            
            elif action == "load_game":
                logger.info("Load game not yet implemented")
                menu.reset_action()
                menu.open_main_menu()
            
            elif action is None:
                # Menu was closed without action (shouldn't happen normally)
                menu.open_main_menu()
        
        # Clear screen
        screen.fill((0, 0, 0))
        
        # Draw menu if open
        if menu.is_open():
            menu.draw(screen)
        
        pygame.display.flip()
        clock.tick(60)
    
    logger.info("Application closing, shutting down pygame")
    pygame.quit()


if __name__ == "__main__":
    main()
