"""
Sprite utilities for loading, masking, and rendering visual elements.

Migrated from old_system/rendering/sprite_manager.py with clean architecture principles.
"""

import math

import pygame
from config import HEX_SIZE, UI_BORDER, UI_TEXT
from domain.entities import Unit
from domain.value_objects import Position
from infrastructure.rendering.hex_grid import hex_to_pixel
from logger.logger import get_logger

logger = get_logger(__name__)


def load_and_mask_sprite(filepath: str) -> pygame.Surface:
    """
    Load a sprite image and mask it to a hex shape.

    Args:
        filepath: path to the image file

    Returns:
        pygame.Surface with the masked sprite
    """
    try:
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

        logger.debug(f"Loaded and masked sprite: {filepath}")
        return sprite_masked
    except Exception as e:
        logger.error(f"Failed to load sprite {filepath}: {e}")
        # Return a fallback surface
        sprite_size = int(HEX_SIZE * 2)
        fallback = pygame.Surface((sprite_size, sprite_size), pygame.SRCALPHA)
        fallback.fill((255, 0, 255, 128))  # Magenta to indicate missing sprite
        return fallback


def draw_facing_indicator(screen: pygame.Surface, unit: Unit, px: int, py: int) -> None:
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
    angle_degrees = -90 + 30 + (unit.facing.direction * 60)
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


def draw_unit_overlays(
    screen: pygame.Surface, unit: Unit, font: pygame.font.Font, active_unit: Unit | None = None
) -> None:
    """
    Draw the unit's name and FP/ÉP bars near the sprite.

    Uses domain entity (Unit) instead of raw dict.

    - Name: above the sprite
    - Bars: at the feet (near bottom of the hex)
    - Facing indicator: small triangle on the sprite

    Args:
        screen: pygame surface to draw on
        unit: Unit entity to render overlays for
        font: pygame font for text rendering
        active_unit: Currently active unit (for reference, hex highlighted separately)
    """
    px, py = hex_to_pixel(unit.position.q, unit.position.r)

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

    def draw_bar(y_top: int, current_val: int, max_val: int, fill_color: tuple):
        """Helper to draw a single resource bar."""
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

    # FP (yellow) then ÉP (red) - use domain entity's ResourcePool
    current_fp = unit.fp.current
    max_fp = unit.fp.maximum
    current_ep = unit.ep.current
    max_ep = unit.ep.maximum

    # Draw bars
    draw_bar(start_y, current_fp, max_fp, (235, 200, 50))
    draw_bar(start_y + bar_height + spacing, current_ep, max_ep, (200, 60, 60))

    # Numeric values centered on bars (cur/max)
    def blit_value(text: str, y_top: int):
        """Helper to render text with shadow on bar."""
        # Render with shadow for contrast
        txt = font.render(text, True, (255, 255, 255))
        shadow = font.render(text, True, (0, 0, 0))
        # Center horizontally on the bar
        tx = px - txt.get_width() // 2
        # Center vertically on the bar
        ty = int(y_top + bar_height // 2 - txt.get_height() // 2)
        screen.blit(shadow, (tx + 1, ty + 1))
        screen.blit(txt, (tx, ty))

    blit_value(f"{current_fp}/{max_fp}", start_y)
    blit_value(f"{current_ep}/{max_ep}", start_y + bar_height + spacing)


def draw_hex_highlight(
    screen: pygame.Surface, position: Position, color: tuple[int, int, int, int], alpha: int = 100
) -> None:
    """
    Draw a highlighted hex at the given position.

    Args:
        screen: pygame surface to draw on
        position: Hex position to highlight
        color: RGB or RGBA color tuple
        alpha: Alpha transparency (0-255)
    """
    px, py = hex_to_pixel(position.q, position.r)

    # Create hex points
    points = []
    for i in range(6):
        angle = math.pi / 180 * (60 * i - 30)
        x = px + HEX_SIZE * math.cos(angle)
        y = py + HEX_SIZE * math.sin(angle)
        points.append((x, y))

    # Draw filled hex with alpha
    if len(color) == 3:
        color = (*color, alpha)

    # Create surface for alpha blending
    hex_surf = pygame.Surface((int(HEX_SIZE * 2.5), int(HEX_SIZE * 2.5)), pygame.SRCALPHA)
    offset_x = int(HEX_SIZE * 1.25)
    offset_y = int(HEX_SIZE * 1.25)

    adjusted_points = [(x - px + offset_x, y - py + offset_y) for x, y in points]
    pygame.draw.polygon(hex_surf, color, adjusted_points)

    screen.blit(hex_surf, (px - offset_x, py - offset_y))
