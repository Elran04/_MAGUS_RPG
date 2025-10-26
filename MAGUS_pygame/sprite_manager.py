"""
Sprite loading and management for the MAGUS pygame game.
"""
import pygame
import math
from config import HEX_SIZE, UI_BORDER, UI_TEXT
from hex_grid import hex_to_pixel


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
        angle = math.pi/180 * (60 * i - 30)
        x = center[0] + HEX_SIZE * math.cos(angle)
        y = center[1] + HEX_SIZE * math.sin(angle)
        points.append((x, y))
    pygame.draw.polygon(hex_mask, (255, 255, 255, 255), points)
    
    # Apply mask to the sprite
    sprite_masked = sprite.copy()
    sprite_masked.blit(hex_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    
    return sprite_masked


class Unit:
    """Represents a game unit on the hex grid."""
    
    def __init__(self, q, r, sprite, name: str | None = None, combat: dict | None = None):
        """
        Initialize a unit.
        
        Args:
            q, r: hex coordinates
            sprite: pygame.Surface for the unit's sprite
            name: optional display name
            combat: optional dict of combat values (e.g., from character JSON 'Harci értékek')
        """
        self.q = q
        self.r = r
        self.sprite = sprite
        self.name = name or ""
        self.combat = combat or {}
    
    def move_to(self, q, r):
        """Move the unit to a new hex."""
        self.q = q
        self.r = r
    
    def get_position(self):
        """Get the unit's current hex position."""
        return (self.q, self.r)

    # Convenience getters for common combat values (fallback to 0)
    @property
    def FP(self) -> int:
        return int(self.combat.get("FP", 0))

    @property
    def EP(self) -> int:
        return int(self.combat.get("ÉP", 0))

    @property
    def KE(self) -> int:
        return int(self.combat.get("KÉ", 0))

    @property
    def TE(self) -> int:
        return int(self.combat.get("TÉ", 0))

    @property
    def VE(self) -> int:
        return int(self.combat.get("VÉ", 0))

    @property
    def CE(self) -> int:
        return int(self.combat.get("CÉ", 0))

    def set_combat(self, combat: dict):
        self.combat = combat or {}
        # Initialize current EP to max EP if not already set
        if not hasattr(self, "current_ep") or self.current_ep is None:
            try:
                self.current_ep = int(self.combat.get("ÉP", 0))
            except Exception:
                self.current_ep = 0
        # Initialize current FP to max FP if not already set
        if not hasattr(self, "current_fp") or self.current_fp is None:
            try:
                self.current_fp = int(self.combat.get("FP", 0))
            except Exception:
                self.current_fp = 0


def draw_unit_overlays(screen: pygame.Surface, unit: Unit, font: pygame.font.Font):
    """Draw the unit's name and FP/ÉP bars near the sprite.

    - Name: above the sprite
    - Bars: at the feet (near bottom of the hex)
    """
    px, py = hex_to_pixel(*unit.get_position())

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
        pygame.draw.rect(screen, (40, 40, 48), (x_left, y_top, bar_width, bar_height), border_radius=3)
        # Filled portion
        if max_val > 0:
            fill_w = int(bar_width * max(0, min(1, current_val / max_val)))
        else:
            fill_w = 0
        if fill_w > 0:
            pygame.draw.rect(screen, fill_color, (x_left, y_top, fill_w, bar_height), border_radius=3)
        # Border
        pygame.draw.rect(screen, UI_BORDER, (x_left, y_top, bar_width, bar_height), width=1, border_radius=3)

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
