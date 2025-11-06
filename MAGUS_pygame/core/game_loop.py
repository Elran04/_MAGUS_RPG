"""
Main game loop logic for MAGUS RPG hex-grid combat.
"""

import pygame
from typing import Tuple

from actions.handler import roll_initiative, setup_action_ui
from actions.movement import compute_reachable, find_path, skip_turn
from config import ActionMode
from core.game_setup import setup_game
from core.game_state import GameState
from logger.logger import get_logger
from input.event_handler import process_mouse_click
from rendering.renderer import draw_game_screen, draw_hud, draw_victory_screen
from systems.hex_grid import get_grid_bounds, pixel_to_hex
from ui.unit_info_popup import UnitInfoPopup


logger = get_logger(__name__)


def run_game_loop(screen: pygame.Surface, clock: pygame.time.Clock) -> None:
    """
    Run the main game loop for combat.
    
    Args:
        screen: Pygame display surface
        clock: Pygame clock for timing
    """
    logger.info("=" * 60)
    logger.info("MAGUS RPG combat starting")
    logger.info("=" * 60)
    
    # Get grid bounds
    MIN_Q, MAX_Q, MIN_R, MAX_R = get_grid_bounds()
    grid_bounds = (MIN_Q, MAX_Q, MIN_R, MAX_R)
    
    # Initialize game resources (sprites, units, background)
    warrior, goblin, background = setup_game()
    
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
    
    # Initialize unit info popup
    state.unit_info_popup = UnitInfoPopup()
    
    # Roll initiative to determine who starts
    roll_initiative(state)
    logger.info(
        f"Initiative rolled: {state.active_unit.name if state.active_unit else 'N/A'} starts"
    )
    state.turn_start_pos = state.active_unit.get_position()
    
    # Initial compute for active unit's turn
    compute_reachable(state)
    
    # Overlay font
    overlay_font = pygame.font.SysFont(None, 18)
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                return  # Exit to main menu
            
            # ESC returns to main menu
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                logger.info("ESC pressed - returning to main menu")
                return
            
            # Skip input processing if game is over
            if state.game_over:
                # Allow ESC or click to return to menu after victory
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    if state.game_over:
                        logger.info("Game over - returning to main menu")
                        return
                continue
            
            # Handle keyboard input
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # Space bar skips turn
                    skip_turn(state)
            
            # Handle mouse clicks
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                process_mouse_click(state, mx, my, event.button, grid_bounds)
        
        # Decrement message timer
        if state.message_timer > 0:
            state.message_timer -= 1
        
        # Update path preview based on mouse position
        _update_path_preview(state)
        
        # Render game screen
        draw_game_screen(screen, state, background, grid_bounds, overlay_font)
        
        # Draw UI overlay
        if state.game_over:
            draw_victory_screen(screen, state)
        else:
            draw_hud(screen, state)
        
        # Draw unit info popup if visible
        if state.unit_info_popup and state.unit_info_popup.visible:
            state.unit_info_popup.draw(screen)
        
        pygame.display.flip()
        clock.tick(60)
    
    logger.info("Game loop ended")


def _update_path_preview(state: GameState) -> None:
    """
    Update the path preview based on mouse position and action mode.
    
    Args:
        state: Current game state
    """
    if state.game_over or state.action_mode not in [ActionMode.MOVE, ActionMode.CHARGE]:
        state.preview_path = []
        return
    
    mx, my = pygame.mouse.get_pos()
    hovered_q, hovered_r = pixel_to_hex(mx, my)
    enemy_unit = state.goblin if state.active_unit == state.warrior else state.warrior
    enemy_pos = enemy_unit.get_position()
    
    if state.action_mode == ActionMode.MOVE:
        # Movement path preview
        if (hovered_q, hovered_r) in state.reachable_for_active:
            path = find_path(
                state.turn_start_pos, (hovered_q, hovered_r), blocked={enemy_pos}
            )
            state.preview_path = path
        else:
            state.preview_path = []
    
    elif state.action_mode == ActionMode.CHARGE:
        # Charge path preview - show path to enemy if hovering over valid charge target
        if (hovered_q, hovered_r) in state.charge_targets:
            # Calculate path to best adjacent hex of enemy
            adjacent_hexes = [
                (enemy_pos[0] + 1, enemy_pos[1]),
                (enemy_pos[0] + 1, enemy_pos[1] - 1),
                (enemy_pos[0], enemy_pos[1] - 1),
                (enemy_pos[0] - 1, enemy_pos[1]),
                (enemy_pos[0] - 1, enemy_pos[1] + 1),
                (enemy_pos[0], enemy_pos[1] + 1),
            ]
            
            # Find shortest path among all adjacent hexes
            best_path = None
            best_distance = float("inf")
            start_pos = state.active_unit.get_position()
            
            for adj_q, adj_r in adjacent_hexes:
                path = find_path(start_pos, (adj_q, adj_r), blocked={enemy_pos})
                if path and len(path) > 1:
                    if len(path) < best_distance:
                        best_distance = len(path)
                        best_path = path
            
            state.preview_path = best_path if best_path else []
        else:
            state.preview_path = []
    else:
        state.preview_path = []
