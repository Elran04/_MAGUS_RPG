"""
Sprite loading and management for the MAGUS pygame game.
"""
import pygame
import math
from config import HEX_SIZE


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
    
    def __init__(self, q, r, sprite):
        """
        Initialize a unit.
        
        Args:
            q, r: hex coordinates
            sprite: pygame.Surface for the unit's sprite
        """
        self.q = q
        self.r = r
        self.sprite = sprite
    
    def move_to(self, q, r):
        """Move the unit to a new hex."""
        self.q = q
        self.r = r
    
    def get_position(self):
        """Get the unit's current hex position."""
        return (self.q, self.r)
