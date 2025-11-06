"""
Rendering utilities for game visuals and UI.
"""

import pygame
from actions.action_handling import draw_action_ui  # Direct import to avoid circular dependency
from config import (
    BG_COLOR,
    HEIGHT,
    PATH_DOT_COLOR,
    PATH_DOT_RADIUS,
    PATH_LINE_COLOR,
    PATH_LINE_WIDTH,
    PATH_ZONE_OVERLAP_COLOR,
    PATH_ZONE_OVERLAP_RADIUS,
    WIDTH,
    ActionMode,
)
from core.game_state import GameState
from systems.hex_grid import draw_grid, hex_to_pixel, pixel_to_hex

from rendering.sprite_manager import draw_unit_overlays


def draw_movement_path(
    screen: pygame.Surface, path: list[tuple[int, int]], enemy_zone: set[tuple[int, int]]
) -> None:
    """
    Draw the movement path as lines connecting hex centers with dots at each hex.
    Highlights path nodes that pass through enemy zone of control in red.

    Args:
        screen: Main pygame display surface
        path: List of (q, r) hex coordinates representing the path
        enemy_zone: Set of (q, r) hex coordinates in enemy's zone of control
    """
    if len(path) < 2:
        return

    # Convert path to pixel coordinates
    pixel_path = [hex_to_pixel(q, r) for q, r in path]

    # Draw lines connecting path nodes
    if len(pixel_path) >= 2:
        pygame.draw.lines(screen, PATH_LINE_COLOR, False, pixel_path, PATH_LINE_WIDTH)

    # Draw dots at each path node, highlighting zone overlaps
    for i, (hex_pos, (px, py)) in enumerate(zip(path, pixel_path)):
        if i == 0:  # Skip starting position
            continue

        # Check if this hex is in the enemy zone
        if hex_pos in enemy_zone:
            # DANGER! Path goes through zone - draw large red circle
            pygame.draw.circle(screen, PATH_ZONE_OVERLAP_COLOR, (px, py), PATH_ZONE_OVERLAP_RADIUS)
            # Draw inner dot for visibility
            pygame.draw.circle(screen, (255, 200, 200), (px, py), PATH_DOT_RADIUS)
        elif i < len(pixel_path) - 1:  # Normal intermediate node (not start or end)
            pygame.draw.circle(screen, PATH_DOT_COLOR, (px, py), PATH_DOT_RADIUS)


def draw_game_screen(
    screen: pygame.Surface,
    state: GameState,
    background: pygame.Surface | None,
    grid_bounds: tuple,
    overlay_font: pygame.font.Font,
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
        reachable_hexes=(
            state.reachable_for_active if state.action_mode == ActionMode.MOVE else None
        ),
        attackable_hexes=(
            state.attackable_for_active if state.action_mode == ActionMode.ATTACK else None
        ),
        charge_area_hexes=(
            state.reachable_for_active if state.action_mode == ActionMode.CHARGE else None
        ),
        charge_targets=state.charge_targets if state.action_mode == ActionMode.CHARGE else None,
        enemy_zone_hexes=(
            state.enemy_zone_hexes
            if state.action_mode in [ActionMode.MOVE, ActionMode.CHARGE]
            else None
        ),
        highlight_hex=(hovered_q, hovered_r),
    )

    # Draw path preview if available (for both MOVE and CHARGE modes)
    if state.preview_path and state.action_mode == ActionMode.MOVE:
        draw_movement_path(screen, state.preview_path, state.enemy_zone_hexes)
    elif state.preview_path and state.action_mode == ActionMode.CHARGE:
        # For charge, also compute enemy zone to show danger
        enemy_unit = state.goblin if state.active_unit == state.warrior else state.warrior
        enemy_pos = enemy_unit.get_position()
        from systems.reach import compute_reach_hexes

        enemy_zone = compute_reach_hexes(
            enemy_pos[0], enemy_pos[1], enemy_unit.facing, enemy_unit.size_category
        )
        draw_movement_path(screen, state.preview_path, enemy_zone)

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

    # Draw combat message if present
    if state.combat_message and state.message_timer > 0:
        message_font = pygame.font.SysFont(None, 36)
        message_text = message_font.render(state.combat_message, True, (255, 220, 0))
        message_rect = message_text.get_rect(center=(WIDTH // 2, 60))

        # Semi-transparent background for message
        padding = 10
        bg_rect = pygame.Rect(
            message_rect.x - padding,
            message_rect.y - padding,
            message_rect.width + 2 * padding,
            message_rect.height + 2 * padding,
        )
        bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        bg_surface.fill((0, 0, 0, 180))
        screen.blit(bg_surface, bg_rect)

        screen.blit(message_text, message_rect)

    # Draw action buttons
    draw_action_ui(screen, state.ui_state, state.action_mode, state.active_unit)
