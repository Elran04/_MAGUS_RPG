"""
Hex grid logic and rendering for the MAGUS pygame game.
"""
import pygame
import math
from config import WIDTH, HEIGHT, HEX_SIZE, HEX_COLOR, HEX_BORDER, HIGHLIGHT_COLOR, HIGHLIGHT_BORDER_WIDTH


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
    x = HEX_SIZE * math.sqrt(3) * (q + r/2)
    y = HEX_SIZE * 3/2 * r
    return int(x), int(y)


def pixel_to_hex(x, y):
    """Convert pixel coordinates to hex coordinates (inverse of hex_to_pixel)."""
    q = (x / (HEX_SIZE * math.sqrt(3)) - y / (HEX_SIZE * 3/2) / 2)
    r = y / (HEX_SIZE * 3/2)
    # Round to nearest hex
    rq = round(q)
    rr = round(r)
    return rq, rr


def _hex_points(center, size):
    """Return the list of 6 vertex points for a hex at center with given size."""
    points = []
    for i in range(6):
        angle = math.pi/180 * (60 * i - 30)
        x = center[0] + size * math.cos(angle)
        y = center[1] + size * math.sin(angle)
        points.append((x, y))
    return points


def draw_hex(surface, color, pos, size, border=2):
    """Draw a single hex at pos (center) with given size."""
    points = _hex_points(pos, size)
    pygame.draw.polygon(surface, color, points)
    pygame.draw.polygon(surface, HEX_BORDER, points, border)


def draw_grid(screen, min_q, max_q, min_r, max_r, sprite_positions=None, highlight_hex=None):
    """
    Draw the hex grid and any sprites at their positions.
    
    Args:
        screen: pygame screen surface
        min_q, max_q, min_r, max_r: grid bounds
        sprite_positions: dict of {(q, r): sprite_surface} to draw
    """
    margin = HEX_SIZE * 2
    for q in range(min_q, max_q):
        for r in range(min_r, max_r):
            px, py = hex_to_pixel(q, r)
            if -margin < px < WIDTH + margin and -margin < py < HEIGHT + margin:
                draw_hex(screen, HEX_COLOR, (px, py), HEX_SIZE)
                
                # Highlight hovered hex with a thicker yellow border
                if highlight_hex is not None and (q, r) == highlight_hex:
                    points = _hex_points((px, py), HEX_SIZE)
                    pygame.draw.polygon(screen, HIGHLIGHT_COLOR, points, HIGHLIGHT_BORDER_WIDTH)
                
                # Draw sprites at their positions
                if sprite_positions and (q, r) in sprite_positions:
                    sprite = sprite_positions[(q, r)]
                    rect = sprite.get_rect(center=(px, py))
                    screen.blit(sprite, rect)
