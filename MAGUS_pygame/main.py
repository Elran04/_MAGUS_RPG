"""
MAGUS RPG - Main game loop for the hex-grid turn-based game.
"""
import os
import pygame
from config import (
    WIDTH,
    HEIGHT,
    BG_COLOR,
)
from hex_grid import get_grid_bounds, pixel_to_hex, draw_grid
from sprite_manager import load_and_mask_sprite, Unit, draw_unit_overlays
from character_loader import load_character_json
from action_handling import setup_action_ui, draw_action_ui, process_action_button_click
from movement_handling import (
    compute_reachable,
    compute_attackable,
    apply_move_if_valid,
    handle_attack_click,
    skip_turn,
    roll_initiative,
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

# Try to attach demo combat stats from repo characters/*.json
try:
    warrior_json = load_character_json("Teszt.json")
    warrior.name = warrior_json.get("Név", "Warrior")
    warrior.set_combat(warrior_json.get("Harci értékek", {}))
except Exception:
    pass

try:
    goblin_json = load_character_json("Teszt_Goblin.json")
    goblin.name = goblin_json.get("Név", "Goblin")
    goblin.set_combat(goblin_json.get("Harci értékek", {}))
except Exception:
    pass

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
        active_unit=None,
        action_mode="move",
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
                        _ = apply_move_if_valid(state, q, r)
                    else:  # attack mode
                        _ = handle_attack_click(state, q, r)

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

        # Overlays for each unit
        draw_unit_overlays(screen, state.warrior, overlay_font)
        draw_unit_overlays(screen, state.goblin, overlay_font)

        # Draw turn/action info and action buttons
        info_font = pygame.font.SysFont(None, 32)
        # Show round, active unit name and their initiative roll
        active_name = state.active_unit.name if state.active_unit else "Unknown"
        active_init = state.initiative_rolls.get(active_name, 0)
        acted_count = len(state.units_acted_this_round)
        text = info_font.render(
            f"Round {state.round} ({acted_count}/2) | Active: {active_name} (Init: {active_init}) | {state.action_mode.title()}",
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