"""
Hex Grid Utilities - Coordinate conversion, distance calculation, and rendering.

Supports camera transformations for future zoom/pan features.
"""

import math

import pygame
from config import (
    ATTACKABLE_TINT,
    CHARGE_AREA_TINT,
    CHARGE_TINT,
    ENEMY_ZONE_TINT,
    HEIGHT,
    HEX_BORDER,
    HEX_SIZE,
    HIGHLIGHT_BORDER_WIDTH,
    HIGHLIGHT_COLOR,
    HOVER_TINT,
    REACHABLE_TINT,
    WIDTH,
)
from config import (
    HEX_COLOR as HEX_COLOR_OUTLINE,
)

# Grid origin offset (can be modified by camera)
HEX_OFFSET_X = WIDTH // 2
HEX_OFFSET_Y = HEIGHT // 2


def get_grid_bounds() -> tuple[int, int, int, int]:
    """Calculate grid bounds to fill the screen.

    Returns:
        (min_q, max_q, min_r, max_r) tuple
    """
    hex_width = HEX_SIZE * math.sqrt(3)
    vert_spacing = HEX_SIZE * 1.5
    # Use a wide enough range to cover the screen
    min_q = -int(WIDTH // hex_width)
    max_q = int(WIDTH // hex_width) * 2
    min_r = -int(HEIGHT // vert_spacing)
    max_r = int(HEIGHT // vert_spacing) * 2
    return min_q, max_q, min_r, max_r


def get_adjacent_hexes(q: int, r: int) -> list[tuple[int, int]]:
    """Get all 6 adjacent hex coordinates.

    Args:
        q, r: Center hex coordinates

    Returns:
        List of 6 adjacent hex coordinates in facing order (0-5)
    """
    # Hex neighbor offsets in facing order
    neighbors = [
        (1, -1),  # 0: NE
        (1, 0),  # 1: E
        (0, 1),  # 2: SE
        (-1, 1),  # 3: SW
        (-1, 0),  # 4: W
        (0, -1),  # 5: NW
    ]
    return [(q + dq, r + dr) for dq, dr in neighbors]


def calculate_facing_to_hex(from_q: int, from_r: int, to_q: int, to_r: int) -> int | None:
    """Calculate facing direction from one hex to an adjacent hex.

    Hex directions (pointy-top):
    - 0: NE (top-right)
    - 1: E (right)
    - 2: SE (bottom-right)
    - 3: SW (bottom-left)
    - 4: W (left)
    - 5: NW (top-left)

    Args:
        from_q, from_r: Starting hex coordinates
        to_q, to_r: Target hex coordinates (should be adjacent)

    Returns:
        Facing direction (0-5) or None if not adjacent
    """
    # Calculate direction vector
    dq = to_q - from_q
    dr = to_r - from_r

    # Map direction vectors to facing values
    # Based on HEX_DIRECTIONS in reach.py
    direction_map = {
        (1, -1): 0,  # NE
        (1, 0): 1,  # E
        (0, 1): 2,  # SE
        (-1, 1): 3,  # SW
        (-1, 0): 4,  # W
        (0, -1): 5,  # NW
    }

    return direction_map.get((dq, dr))


def hex_to_pixel(q: int, r: int) -> tuple[int, int]:
    """Convert hex coordinates to pixel coordinates (pointy-topped).

    Args:
        q: Hex Q coordinate
        r: Hex R coordinate

    Returns:
        (x, y) pixel coordinates
    """
    x = HEX_SIZE * math.sqrt(3) * (q + r / 2) + HEX_OFFSET_X
    y = HEX_SIZE * 3 / 2 * r + HEX_OFFSET_Y
    return int(x), int(y)


def pixel_to_hex(x: int, y: int) -> tuple[int, int]:
    """Convert pixel coordinates to hex coordinates (inverse of hex_to_pixel).

    Args:
        x: Pixel x coordinate
        y: Pixel y coordinate

    Returns:
        (q, r) hex coordinates
    """
    x_adj = x - HEX_OFFSET_X
    y_adj = y - HEX_OFFSET_Y

    q = x_adj / (HEX_SIZE * math.sqrt(3)) - y_adj / (HEX_SIZE * 3 / 2) / 2
    r = y_adj / (HEX_SIZE * 3 / 2)

    # Round to nearest hex
    rq = round(q)
    rr = round(r)
    return rq, rr


def hex_distance(q1: int, r1: int, q2: int, r2: int) -> int:
    """Compute distance between two axial hex coordinates.

    Uses cube coordinates (x=q, z=r, y=-x-z) and Chebyshev distance.

    Args:
        q1, r1: First hex coordinates
        q2, r2: Second hex coordinates

    Returns:
        Distance in hexes
    """
    x1, z1, y1 = q1, r1, -q1 - r1
    x2, z2, y2 = q2, r2, -q2 - r2
    return max(abs(x1 - x2), abs(y1 - y2), abs(z1 - z2))


def hexes_in_range(q0: int, r0: int, rng: int) -> set[tuple[int, int]]:
    """Return a set of axial hexes within range from (q0, r0).

    Args:
        q0, r0: Center hex coordinates
        rng: Range radius

    Returns:
        Set of (q, r) tuples within range
    """
    result = set()
    for dq in range(-rng, rng + 1):
        dr_min = max(-rng, -dq - rng)
        dr_max = min(rng, -dq + rng)
        for dr in range(dr_min, dr_max + 1):
            result.add((q0 + dq, r0 + dr))
    return result


def _hex_points(center: tuple[int, int], size: int) -> list[tuple[float, float]]:
    """Return the list of 6 vertex points for a hex at center with given size.

    Args:
        center: (x, y) pixel center of hex
        size: Hex size

    Returns:
        List of 6 vertex points
    """
    points = []
    for i in range(6):
        angle = math.pi / 180 * (60 * i - 30)
        x = center[0] + size * math.cos(angle)
        y = center[1] + size * math.sin(angle)
        points.append((x, y))
    return points


def draw_hex(
    surface: pygame.Surface,
    color: tuple[int, int, int],
    pos: tuple[int, int],
    size: int,
    border: int = 2,
) -> None:
    """Draw a single hex border at pos (center) with given size.

    The interior is left transparent so backgrounds remain visible.

    Args:
        surface: Surface to draw on
        color: Border color
        pos: (x, y) center position
        size: Hex size
        border: Border width
    """
    points = _hex_points(pos, size)
    pygame.draw.polygon(surface, color, points, border)


def draw_hex_outline(
    surface: pygame.Surface,
    x: int,
    y: int,
    color: tuple[int, int, int] = HEX_COLOR_OUTLINE,
    width: int = 2,
) -> None:
    """Draw a hex outline at pixel position.

    Args:
        surface: Surface to draw on
        x, y: Pixel coordinates
        color: Outline color
        width: Line width
    """
    points = _hex_points((x, y), HEX_SIZE)
    pygame.draw.polygon(surface, color, points, width)


def draw_grid(
    screen: pygame.Surface,
    min_q: int,
    max_q: int,
    min_r: int,
    max_r: int,
    sprite_positions: dict[tuple[int, int], pygame.Surface] | None = None,
    reachable_hexes: set[tuple[int, int]] | None = None,
    attackable_hexes: set[tuple[int, int]] | None = None,
    charge_area_hexes: set[tuple[int, int]] | None = None,
    charge_targets: set[tuple[int, int]] | None = None,
    enemy_zone_hexes: set[tuple[int, int]] | None = None,
    highlight_hex: tuple[int, int] | None = None,
) -> None:
    """Draw the hex grid and any sprites at their positions.

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
                draw_hex(screen, HEX_BORDER, (px, py), HEX_SIZE)

                # Compute polygon points once
                points = _hex_points((px, py), HEX_SIZE)

                # Accumulate semi-transparent fills (order matters - later = on top)
                # 1. Base ranges (movement/charge area)
                if reachable_hexes and (q, r) in reachable_hexes:
                    pygame.draw.polygon(overlay_surface, REACHABLE_TINT, points, 0)
                if charge_area_hexes and (q, r) in charge_area_hexes:
                    pygame.draw.polygon(overlay_surface, CHARGE_AREA_TINT, points, 0)
                # 2. Attack ranges
                if attackable_hexes and (q, r) in attackable_hexes:
                    pygame.draw.polygon(overlay_surface, ATTACKABLE_TINT, points, 0)
                if charge_targets and (q, r) in charge_targets:
                    pygame.draw.polygon(overlay_surface, CHARGE_TINT, points, 0)
                # 3. Enemy zone (rendered on top so it's visible as warning)
                if enemy_zone_hexes and (q, r) in enemy_zone_hexes:
                    pygame.draw.polygon(overlay_surface, ENEMY_ZONE_TINT, points, 0)
                # 4. Hover highlight (always on top)
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
