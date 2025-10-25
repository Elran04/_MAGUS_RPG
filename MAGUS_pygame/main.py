"""
MAGUS RPG - Main game loop for the hex-grid turn-based game.
"""
import os
import pygame
from config import WIDTH, HEIGHT, BG_COLOR, MOVEMENT_RANGE
from hex_grid import get_grid_bounds, pixel_to_hex, draw_grid, hex_distance, hexes_in_range
from sprite_manager import load_and_mask_sprite, Unit

# Initialize pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("MAGUS Hexgrid Turn-Based Demo")
clock = pygame.time.Clock()

# Get grid bounds
MIN_Q, MAX_Q, MIN_R, MAX_R = get_grid_bounds()

# Load warrior sprite and create unit
# Build a robust relative path to the sprites folder
SPRITES_DIR = os.path.join(os.path.dirname(__file__), "sprites")
warrior_sprite = load_and_mask_sprite(os.path.join(SPRITES_DIR, "warrior_sprite_selfmade.jpg"))
goblin_sprite = load_and_mask_sprite(os.path.join(SPRITES_DIR, "goblin.png"))
warrior = Unit(3, 3, warrior_sprite)
goblin = Unit(6, 3, goblin_sprite)

def main():
    """Main game loop."""
    running = True
    turn = 0  # 0: Player, 1: Enemy
    
    # Track turn start position and compute reachable hexes once per turn
    turn_start_pos = warrior.get_position()  # Initial position for player turn
    reachable_for_active = hexes_in_range(turn_start_pos[0], turn_start_pos[1], MOVEMENT_RANGE)
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Left click: move the unit whose turn it is (within range only)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                q, r = pixel_to_hex(mx, my)
                # Only move if the clicked hex is on the grid and reachable from turn start
                if MIN_Q <= q < MAX_Q and MIN_R <= r < MAX_R:
                    if (q, r) in reachable_for_active:
                        if turn == 0:
                            warrior.move_to(q, r)
                        else:
                            goblin.move_to(q, r)
                        # After moving, automatically advance turn
                        turn = (turn + 1) % 2
                        # Compute new reachable area from the new unit's starting position
                        turn_start_pos = warrior.get_position() if turn == 0 else goblin.get_position()
                        reachable_for_active = hexes_in_range(turn_start_pos[0], turn_start_pos[1], MOVEMENT_RANGE)
            
            # Right click to skip turn without moving
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                turn = (turn + 1) % 2
                # Compute reachable from new active unit's current position
                turn_start_pos = warrior.get_position() if turn == 0 else goblin.get_position()
                reachable_for_active = hexes_in_range(turn_start_pos[0], turn_start_pos[1], MOVEMENT_RANGE)

        # Clear screen
        screen.fill(BG_COLOR)

        # Determine hovered hex under the mouse
        mx, my = pygame.mouse.get_pos()
        hovered_q, hovered_r = pixel_to_hex(mx, my)

        # Draw grid with both units, reachable highlights, and hovered hex
        sprite_positions = {
            warrior.get_position(): warrior.sprite,
            goblin.get_position(): goblin.sprite,
        }
        draw_grid(
            screen,
            MIN_Q,
            MAX_Q,
            MIN_R,
            MAX_R,
            sprite_positions,
            reachable_hexes=reachable_for_active,
            highlight_hex=(hovered_q, hovered_r),
        )

        # Draw turn info
        font = pygame.font.SysFont(None, 36)
        text = font.render(f"Turn: {'Player' if turn == 0 else 'Enemy'}", True, (255, 255, 255))
        screen.blit(text, (10, 10))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()