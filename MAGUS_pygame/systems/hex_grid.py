"""
Hex grid logic and rendering for the MAGUS pygame game.
"""
import pygame
import math
from config import (
    WIDTH,
    HEIGHT,
    HEX_SIZE,
    HEX_COLOR,
    HEX_BORDER,
    HIGHLIGHT_COLOR,
    HIGHLIGHT_BORDER_WIDTH,
    REACHABLE_TINT,
    HOVER_TINT,
    ATTACKABLE_TINT,
    CHARGE_AREA_TINT,
    CHARGE_TINT,
    ENEMY_ZONE_TINT,
)


def get_grid_bounds():
    """Calculate grid bounds to fill the screen."""
    hex_width = HEX_SIZE * math.sqrt(3)
    vert_spacing = HEX_SIZE * 1.5
    # Use a wide enough range to cover the screen
    min_q = -int(WIDTH // hex_width)
    max_q = int(WIDTH // hex_width) * 2
    min_r = -int(HEIGHT // vert_spacing)
    max_r = int(HEIGHT // vert_spacing) * 2
    return min_q, max_q, min_r, max_r


def hex_to_pixel(q, r):
    """Convert hex coordinates to pixel coordinates (pointy-topped)."""
    x = HEX_SIZE * math.sqrt(3) * (q + r / 2)
    y = HEX_SIZE * 3 / 2 * r
    return int(x), int(y)


def pixel_to_hex(x, y):
    """Convert pixel coordinates to hex coordinates (inverse of hex_to_pixel)."""
    q = (x / (HEX_SIZE * math.sqrt(3)) - y / (HEX_SIZE * 3 / 2) / 2)
    r = y / (HEX_SIZE * 3 / 2)
    # Round to nearest hex
    rq = round(q)
    rr = round(r)
    return rq, rr


def hex_distance(q1, r1, q2, r2):
    """Compute distance between two axial hex coordinates.
    Uses cube coordinates (x=q, z=r, y=-x-z) and Chebyshev distance.
    """
    x1, z1, y1 = q1, r1, -q1 - r1
    x2, z2, y2 = q2, r2, -q2 - r2
    return max(abs(x1 - x2), abs(y1 - y2), abs(z1 - z2))


def hexes_in_range(q0, r0, rng):
    """Return a set of axial hexes within range rng from (q0, r0)."""
    result = set()
    for dq in range(-rng, rng + 1):
        dr_min = max(-rng, -dq - rng)
        dr_max = min(rng, -dq + rng)
        for dr in range(dr_min, dr_max + 1):
            result.add((q0 + dq, r0 + dr))
    return result


def _hex_points(center, size):
    """Return the list of 6 vertex points for a hex at center with given size."""
    points = []
    for i in range(6):
        angle = math.pi / 180 * (60 * i - 30)
        x = center[0] + size * math.cos(angle)
        y = center[1] + size * math.sin(angle)
        points.append((x, y))
    return points


def draw_hex(surface, color, pos, size, border=2):
    """Draw a single hex border at pos (center) with given size.
    The interior is left transparent so backgrounds remain visible.
    """
    points = _hex_points(pos, size)
    # No fill: leave interior transparent to reveal background
    pygame.draw.polygon(surface, HEX_BORDER, points, border)


def draw_grid(
    screen,
    min_q,
    max_q,
    min_r,
    max_r,
    sprite_positions=None,
    reachable_hexes=None,
    attackable_hexes=None,
    charge_area_hexes=None,
    charge_targets=None,
    enemy_zone_hexes=None,
    highlight_hex=None,
):
    """
    Draw the hex grid and any sprites at their positions.

    Args:
        screen: pygame screen surface
        min_q, max_q, min_r, max_r: grid bounds
        sprite_positions: dict of {(q, r): sprite_surface} to draw
        reachable_hexes: set of (q, r) within movement range
        attackable_hexes: set of (q, r) within attack range
        charge_area_hexes: set of (q, r) in chargeable range (4+ hexes away)
        charge_targets: set of (q, r) valid for charge attacks (enemy positions)
        enemy_zone_hexes: set of (q, r) in enemy's zone of control
        highlight_hex: (q, r) hex to draw as hovered
    """
    margin = HEX_SIZE * 2
    # Draw semi-transparent overlays onto a separate surface for correct alpha blending
    overlay_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    # Pass 1: draw base hex borders and accumulate overlay fills
    for q in range(min_q, max_q):
        for r in range(min_r, max_r):
            px, py = hex_to_pixel(q, r)
            if -margin < px < WIDTH + margin and -margin < py < HEIGHT + margin:
                # Base hex border (interior transparent)
                draw_hex(screen, HEX_COLOR, (px, py), HEX_SIZE)

                # Compute polygon points once
                points = _hex_points((px, py), HEX_SIZE)

                # Accumulate semi-transparent fills
                if reachable_hexes and (q, r) in reachable_hexes:
                    pygame.draw.polygon(overlay_surface, REACHABLE_TINT, points, 0)
                if enemy_zone_hexes and (q, r) in enemy_zone_hexes:
                    pygame.draw.polygon(overlay_surface, ENEMY_ZONE_TINT, points, 0)
                if attackable_hexes and (q, r) in attackable_hexes:
                    pygame.draw.polygon(overlay_surface, ATTACKABLE_TINT, points, 0)
                if charge_area_hexes and (q, r) in charge_area_hexes:
                    pygame.draw.polygon(overlay_surface, CHARGE_AREA_TINT, points, 0)
                if charge_targets and (q, r) in charge_targets:
                    pygame.draw.polygon(overlay_surface, CHARGE_TINT, points, 0)
                if highlight_hex is not None and (q, r) == highlight_hex:
                    pygame.draw.polygon(overlay_surface, HOVER_TINT, points, 0)

    # Blit accumulated overlays once (under sprites)
    screen.blit(overlay_surface, (0, 0))

    # Pass 2: draw sprites above overlays
    if sprite_positions:
        for (sq, sr), sprite in sprite_positions.items():
            spx, spy = hex_to_pixel(sq, sr)
            if -margin < spx < WIDTH + margin and -margin < spy < HEIGHT + margin:
                rect = sprite.get_rect(center=(spx, spy))
                screen.blit(sprite, rect)

    # On-top overlay: hover border only (no fill)
    if highlight_hex is not None:
        hq, hr = highlight_hex
        hpx, hpy = hex_to_pixel(hq, hr)
        if -margin < hpx < WIDTH + margin and -margin < hpy < HEIGHT + margin:
            hpoints = _hex_points((hpx, hpy), HEX_SIZE)
            pygame.draw.polygon(screen, HIGHLIGHT_COLOR, hpoints, HIGHLIGHT_BORDER_WIDTH)
