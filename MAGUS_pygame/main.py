"""
MAGUS RPG - Main game loop for the hex-grid turn-based game.
"""
import pygame
from config import WIDTH, HEIGHT, BG_COLOR
from hex_grid import get_grid_bounds, pixel_to_hex, draw_grid
from sprite_manager import load_and_mask_sprite, Unit

# Initialize pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("MAGUS Hexgrid Turn-Based Demo")
clock = pygame.time.Clock()

# Get grid bounds
MIN_Q, MAX_Q, MIN_R, MAX_R = get_grid_bounds()

# Load warrior sprite and create unit
warrior_sprite = load_and_mask_sprite("warrior_sprite_selfmade.jpg")
warrior = Unit(3, 3, warrior_sprite)

def main():
    """Main game loop."""
    running = True
    turn = 0  # 0: Player, 1: Enemy (example)
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Move warrior on left mouse click
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                q, r = pixel_to_hex(mx, my)
                # Only move if the clicked hex is on the grid
                if MIN_Q <= q < MAX_Q and MIN_R <= r < MAX_R:
                    warrior.move_to(q, r)
            
            # Example: right click to advance turn
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                turn = (turn + 1) % 2

        # Clear screen
        screen.fill(BG_COLOR)
        
        # Draw grid with warrior
        sprite_positions = {warrior.get_position(): warrior.sprite}
        draw_grid(screen, MIN_Q, MAX_Q, MIN_R, MAX_R, sprite_positions)

        # Draw turn info
        font = pygame.font.SysFont(None, 36)
        text = font.render(f"Turn: {'Player' if turn == 0 else 'Enemy'}", True, (255, 255, 255))
        screen.blit(text, (10, 10))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()