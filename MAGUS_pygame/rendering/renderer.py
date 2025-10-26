"""
Rendering utilities for game visuals and UI.
"""
import pygame
from typing import Optional
from config import WIDTH, HEIGHT, BG_COLOR, ActionMode
from core.game_state import GameState
from systems.hex_grid import pixel_to_hex, draw_grid
from rendering.sprite_manager import draw_unit_overlays
from actions.action_handling import draw_action_ui  # Direct import to avoid circular dependency


def draw_game_screen(
    screen: pygame.Surface,
    state: GameState,
    background: Optional[pygame.Surface],
    grid_bounds: tuple,
    overlay_font: pygame.font.Font
) -> None:
    """
    Draw the main game screen with background, grid, units, and overlays.
    
    Args:
        screen: Main pygame display surface
        state: Current game state
        background: Background image (None for solid color)
        grid_bounds: (MIN_Q, MAX_Q, MIN_R, MAX_R) boundaries
        overlay_font: Font for unit overlays
    """
    MIN_Q, MAX_Q, MIN_R, MAX_R = grid_bounds
    
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
        reachable_hexes=state.reachable_for_active if state.action_mode == ActionMode.MOVE else None,
        attackable_hexes=state.attackable_for_active if state.action_mode == ActionMode.ATTACK else None,
        highlight_hex=(hovered_q, hovered_r),
    )

    # Overlays for each unit
    draw_unit_overlays(screen, state.warrior, overlay_font)
    draw_unit_overlays(screen, state.goblin, overlay_font)


def draw_victory_screen(screen: pygame.Surface, state: GameState) -> None:
    """
    Draw victory screen overlay when game is over.
    
    Args:
        screen: Main pygame display surface
        state: Current game state (must have game_over=True)
    """
    victory_font = pygame.font.SysFont(None, 64)
    info_font = pygame.font.SysFont(None, 32)
    
    # Semi-transparent overlay
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    
    # Victory text
    victory_text = victory_font.render(f"{state.winner.name} Wins!", True, (255, 215, 0))
    victory_rect = victory_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40))
    screen.blit(victory_text, victory_rect)
    
    # Defeated text
    defeated_name = state.warrior.name if state.winner == state.goblin else state.goblin.name
    defeated_text = info_font.render(f"{defeated_name} has been defeated", True, (200, 200, 200))
    defeated_rect = defeated_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20))
    screen.blit(defeated_text, defeated_rect)
    
    # Instructions
    instruction_text = info_font.render("Close window to exit", True, (150, 150, 150))
    instruction_rect = instruction_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 70))
    screen.blit(instruction_text, instruction_rect)


def draw_hud(screen: pygame.Surface, state: GameState) -> None:
    """
    Draw the heads-up display with round info, active unit, initiative, AP, and action mode.
    
    Args:
        screen: Main pygame display surface
        state: Current game state
    """
    info_font = pygame.font.SysFont(None, 32)
    
    # Show round, active unit name and their initiative roll
    active_name = state.active_unit.name if state.active_unit else "Unknown"
    active_init = state.initiative_rolls.get(active_name, 0)
    acted_count = len(state.units_acted_this_round)
    ap_current = state.active_unit.current_action_points if state.active_unit else 0
    ap_max = state.active_unit.max_action_points if state.active_unit else 0
    
    text = info_font.render(
        f"Round {state.round} ({acted_count}/2) | Active: {active_name} (Init: {active_init}) | AP: {ap_current}/{ap_max} | {state.action_mode.title()}",
        True,
        (255, 255, 255),
    )
    screen.blit(text, (10, 10))
    
    # Draw action buttons
    draw_action_ui(screen, state.ui_state, state.action_mode)
