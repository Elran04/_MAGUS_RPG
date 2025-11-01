"""
Sprite loading and visual rendering for the MAGUS pygame game.
"""

import math

import pygame
from config import HEX_SIZE, UI_BORDER, UI_TEXT
from systems.hex_grid import hex_to_pixel


def draw_facing_indicator(screen: pygame.Surface, unit, px: int, py: int):
    """
    Draw a small triangle on the sprite indicating facing direction.

    Args:
        screen: pygame surface to draw on
        unit: Unit with facing property (0-5)
        px, py: pixel position of the unit
    """
    # Triangle size
    triangle_size = HEX_SIZE * 0.4

    # Calculate angle based on facing (0-5)
    # For pointy-top hexagons, flat edges are at 0°, 60°, 120°, 180°, 240°, 300°
    # Facing 0 = North (0° = right, so -90° + 30° = -60° for top-right edge)
    # We want: 0=N, 1=NE, 2=SE, 3=S, 4=SW, 5=NW
    # Start at -90° (top) and add 30° to point at sides instead of vertices
    angle_degrees = -90 + 30 + (unit.facing * 60)
    angle_rad = math.radians(angle_degrees)

    # Triangle points (small triangle pointing in facing direction)
    # Base of triangle at center, point extends outward
    tip_distance = triangle_size
    base_width = triangle_size * 0.4

    # Tip of triangle (pointing in facing direction)
    tip_x = px + tip_distance * math.cos(angle_rad)
    tip_y = py + tip_distance * math.sin(angle_rad)

    # Base corners (perpendicular to facing direction)
    perp_angle = angle_rad + math.pi / 2
    base1_x = px + base_width * math.cos(perp_angle)
    base1_y = py + base_width * math.sin(perp_angle)
    base2_x = px - base_width * math.cos(perp_angle)
    base2_y = py - base_width * math.sin(perp_angle)

    points = [(tip_x, tip_y), (base1_x, base1_y), (base2_x, base2_y)]

    # Draw triangle with outline
    pygame.draw.polygon(screen, (255, 255, 100), points)  # Yellow fill
    pygame.draw.polygon(screen, (200, 200, 50), points, width=2)  # Darker outline


def load_and_mask_sprite(filepath):
    """
    Load a sprite image and mask it to a hex shape.

    Args:
        filepath: path to the image file

    Returns:
        pygame.Surface with the masked sprite
    """
    # Load the sprite
    sprite_orig = pygame.image.load(filepath).convert_alpha()

    # Scale to fit inside the hex's bounding circle
    sprite_size = int(HEX_SIZE * 2)
    sprite = pygame.transform.smoothscale(sprite_orig, (sprite_size, sprite_size))

    # Create a hex mask surface
    hex_mask = pygame.Surface((sprite_size, sprite_size), pygame.SRCALPHA)
    center = (sprite_size // 2, sprite_size // 2)
    points = []
    for i in range(6):
        angle = math.pi / 180 * (60 * i - 30)
        x = center[0] + HEX_SIZE * math.cos(angle)
        y = center[1] + HEX_SIZE * math.sin(angle)
        points.append((x, y))
    pygame.draw.polygon(hex_mask, (255, 255, 255, 255), points)

    # Apply mask to the sprite
    sprite_masked = sprite.copy()
    sprite_masked.blit(hex_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    return sprite_masked


def draw_unit_overlays(screen: pygame.Surface, unit, font: pygame.font.Font):
    """Draw the unit's name and FP/ÉP bars near the sprite.

    - Name: above the sprite
    - Bars: at the feet (near bottom of the hex)
    - Facing indicator: small triangle on the sprite
    """
    px, py = hex_to_pixel(*unit.get_position())

    # Draw facing direction indicator
    draw_facing_indicator(screen, unit, px, py)

    # Name above
    if unit.name:
        name_surf = font.render(unit.name, True, UI_TEXT)
        name_rect = name_surf.get_rect(center=(px, int(py - 1.1 * HEX_SIZE)))
        screen.blit(name_surf, name_rect)

    # Bars at the feet (near bottom of hex)
    bar_width = int(1.6 * HEX_SIZE)
    bar_height = 12
    spacing = 4
    # Bottom of hex is roughly py + HEX_SIZE; keep bars inside by stacking upward
    start_y = int(py + HEX_SIZE - (2 * bar_height + spacing + 2))
    x_left = px - bar_width // 2

    def draw_bar(y_top, current_val, max_val, fill_color):
        # Track background
        pygame.draw.rect(
            screen, (40, 40, 48), (x_left, y_top, bar_width, bar_height), border_radius=3
        )
        # Filled portion
        if max_val > 0:
            fill_w = int(bar_width * max(0, min(1, current_val / max_val)))
        else:
            fill_w = 0
        if fill_w > 0:
            pygame.draw.rect(
                screen, fill_color, (x_left, y_top, fill_w, bar_height), border_radius=3
            )
        # Border
        pygame.draw.rect(
            screen, UI_BORDER, (x_left, y_top, bar_width, bar_height), width=1, border_radius=3
        )

    # FP (yellow) then ÉP (red)
    current_fp = getattr(unit, "current_fp", unit.FP)
    current_ep = getattr(unit, "current_ep", unit.EP)
    # Draw bars
    draw_bar(start_y, current_fp, unit.FP, (235, 200, 50))
    draw_bar(start_y + bar_height + spacing, current_ep, unit.EP, (200, 60, 60))

    # Numeric values centered on bars (cur/max)
    def blit_value(text: str, y_top: int):
        # Render with shadow for contrast
        txt = font.render(text, True, (255, 255, 255))
        shadow = font.render(text, True, (0, 0, 0))
        # Center horizontally on the bar
        tx = px - txt.get_width() // 2
        # Center vertically on the bar
        ty = int(y_top + bar_height // 2 - txt.get_height() // 2)
        screen.blit(shadow, (tx + 1, ty + 1))
        screen.blit(txt, (tx, ty))

    blit_value(f"{current_fp}/{unit.FP}", start_y)
    blit_value(f"{current_ep}/{unit.EP}", start_y + bar_height + spacing)
