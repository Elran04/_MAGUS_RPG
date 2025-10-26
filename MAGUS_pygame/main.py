"""
MAGUS RPG - Main game loop for the hex-grid turn-based game.
"""
import os
import pygame
from config import (
    WIDTH,
    HEIGHT,
    BG_COLOR,
    MOVEMENT_RANGE,
    ATTACK_RANGE,
    UI_BG,
    UI_BORDER,
    UI_TEXT,
    UI_ACTIVE,
    UI_INACTIVE,
)
from hex_grid import get_grid_bounds, pixel_to_hex, draw_grid, hex_distance, hexes_in_range
from sprite_manager import load_and_mask_sprite, Unit
from action_handling import setup_action_ui, draw_action_ui, process_action_button_click
from movement_handling import (
    compute_reachable,
    compute_attackable,
    apply_move_if_valid,
    handle_attack_click,
    skip_turn,
)
from game_state import GameState

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
warrior_sprite = load_and_mask_sprite(os.path.join(SPRITES_DIR, "warrior.png"))
goblin_sprite = load_and_mask_sprite(os.path.join(SPRITES_DIR, "goblin.png"))
warrior = Unit(3, 3, warrior_sprite)
goblin = Unit(6, 3, goblin_sprite)

# Load background image and scale to window size
try:
    _bg_img = pygame.image.load(os.path.join(SPRITES_DIR, "grass_bg.jpg")).convert()
    background = pygame.transform.smoothscale(_bg_img, (WIDTH, HEIGHT))
except Exception:
    background = None

def main():
    """Main game loop."""
    running = True
    # Initialize game state
    state = GameState(
        turn=0,
        action_mode="move",
        turn_start_pos=warrior.get_position(),
        reachable_for_active=set(),
        attackable_for_active=set(),
        ui_state=setup_action_ui(),
        warrior=warrior,
        goblin=goblin,
    )

    # Initial compute for player turn
    compute_reachable(state)
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Left click: interact with UI or perform action based on current mode
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                # Buttons first
                clicked_mode = process_action_button_click(mx, my, state.ui_state)
                if clicked_mode == "move":
                    state.action_mode = "move"
                    compute_reachable(state)
                    state.attackable_for_active = set()
                    continue
                elif clicked_mode == "attack":
                    state.action_mode = "attack"
                    state.reachable_for_active = set()
                    compute_attackable(state)
                    continue

                q, r = pixel_to_hex(mx, my)
                # Only act if the clicked hex is on the grid
                if MIN_Q <= q < MAX_Q and MIN_R <= r < MAX_R:
                    if state.action_mode == "move":
                        did_move = apply_move_if_valid(state, q, r)
                        # On success, state is already advanced and recomputed
                    else:  # attack mode
                        did_attack = handle_attack_click(state, q, r)
                        # On success, state is already advanced and recomputed
            
            # Right click to skip turn without moving
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                skip_turn(state)

        # Draw background (image if available, else solid color)
        if background is not None:
            screen.blit(background, (0, 0))
        else:
            screen.fill(BG_COLOR)

        # Determine hovered hex under the mouse
        mx, my = pygame.mouse.get_pos()
        hovered_q, hovered_r = pixel_to_hex(mx, my)

        # Draw grid with both units, reachable highlights, and hovered hex
        sprite_positions = {
            state.warrior.get_position(): state.warrior.sprite,
            state.goblin.get_position(): state.goblin.sprite,
        }
        draw_grid(
            screen,
            MIN_Q,
            MAX_Q,
            MIN_R,
            MAX_R,
            sprite_positions,
            reachable_hexes=state.reachable_for_active if state.action_mode == "move" else None,
            attackable_hexes=state.attackable_for_active if state.action_mode == "attack" else None,
            highlight_hex=(hovered_q, hovered_r),
        )

        # Draw turn/action info and action buttons
        info_font = pygame.font.SysFont(None, 32)
        text = info_font.render(
            f"Turn: {'Player' if state.turn == 0 else 'Enemy'}  Action: {state.action_mode.title()}",
            True,
            (255, 255, 255),
        )
        screen.blit(text, (10, 10))

        # Buttons
        draw_action_ui(screen, state.ui_state, state.action_mode)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()