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
    """Draw a single hex at pos (center) with given size."""
    points = _hex_points(pos, size)
    pygame.draw.polygon(surface, color, points)
    pygame.draw.polygon(surface, HEX_BORDER, points, border)


def draw_grid(
    screen,
    min_q,
    max_q,
    min_r,
    max_r,
    sprite_positions=None,
    reachable_hexes=None,
    highlight_hex=None,
):
    """
    Draw the hex grid and any sprites at their positions.

    Args:
        screen: pygame screen surface
        min_q, max_q, min_r, max_r: grid bounds
        sprite_positions: dict of {(q, r): sprite_surface} to draw
        reachable_hexes: set of (q, r) within movement range
        highlight_hex: (q, r) hex to draw as hovered
    """
    margin = HEX_SIZE * 2
    for q in range(min_q, max_q):
        for r in range(min_r, max_r):
            px, py = hex_to_pixel(q, r)
            if -margin < px < WIDTH + margin and -margin < py < HEIGHT + margin:
                # Base hex tile
                draw_hex(screen, HEX_COLOR, (px, py), HEX_SIZE)

                # Compute polygon points once
                points = _hex_points((px, py), HEX_SIZE)

                # Under-sprite overlays: reachable and hover fills
                if reachable_hexes and (q, r) in reachable_hexes:
                    pygame.draw.polygon(screen, REACHABLE_TINT, points, 0)
                if highlight_hex is not None and (q, r) == highlight_hex:
                    pygame.draw.polygon(screen, HOVER_TINT, points, 0)

                # Sprites on top of fills
                if sprite_positions and (q, r) in sprite_positions:
                    sprite = sprite_positions[(q, r)]
                    rect = sprite.get_rect(center=(px, py))
                    screen.blit(sprite, rect)

                # On-top overlay: hover border only (no fill)
                if highlight_hex is not None and (q, r) == highlight_hex:
                    pygame.draw.polygon(
                        screen, HIGHLIGHT_COLOR, points, HIGHLIGHT_BORDER_WIDTH
                    )
