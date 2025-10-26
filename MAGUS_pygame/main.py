"""
MAGUS RPG - Main game loop for the hex-grid turn-based game.
"""
import pygame
from config import WIDTH, HEIGHT, ActionMode
from systems.hex_grid import get_grid_bounds
from actions.action_handling import setup_action_ui, roll_initiative
from actions.action_movement import compute_reachable
from core.game_state import GameState
from core.game_setup import setup_game
from input.event_handler import process_mouse_click
from rendering.renderer import draw_game_screen, draw_victory_screen, draw_hud

# Initialize pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("MAGUS Hexgrid Turn-Based Demo")
clock = pygame.time.Clock()

# Get grid bounds
MIN_Q, MAX_Q, MIN_R, MAX_R = get_grid_bounds()

# Initialize game resources (sprites, units, background)
warrior, goblin, background = setup_game()

def main():
    """Main game loop."""
    running = True
    
    # Initialize game state
    state = GameState(
        turn=0,
        active_unit=None,
        action_mode=ActionMode.MOVE,
        turn_start_pos=warrior.get_position(),
        reachable_for_active=set(),
        attackable_for_active=set(),
        ui_state=setup_action_ui(),
        warrior=warrior,
        goblin=goblin,
    )
    

    # Roll initiative to determine who starts
    roll_initiative(state)
    state.turn_start_pos = state.active_unit.get_position()
    
    # Initial compute for active unit's turn
    compute_reachable(state)

    # Overlay font
    overlay_font = pygame.font.SysFont(None, 18)
    
    # Grid bounds for event handling
    grid_bounds = (MIN_Q, MAX_Q, MIN_R, MAX_R)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Skip input processing if game is over
            if state.game_over:
                continue

            # Handle mouse clicks
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                process_mouse_click(state, mx, my, event.button, grid_bounds)

        # Render game screen
        draw_game_screen(screen, state, background, grid_bounds, overlay_font)

        # Draw UI overlay
        if state.game_over:
            draw_victory_screen(screen, state)
        else:
            draw_hud(screen, state)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()