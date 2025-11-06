"""
Camera system for managing viewport and scrolling in MAGUS Pygame.
"""

from typing import Tuple
import pygame


class Camera:
    """Manages the game camera/viewport for scrolling and positioning."""

    def __init__(self, width: int, height: int, world_width: int, world_height: int) -> None:
        """Initialize the camera.
        
        Args:
            width: Viewport width in pixels
            height: Viewport height in pixels
            world_width: Total world width in pixels
            world_height: Total world height in pixels
        """
        self.width = width
        self.height = height
        self.world_width = world_width
        self.world_height = world_height
        
        # Camera position (top-left corner)
        self.x = 0.0
        self.y = 0.0
        
        # Scroll speed
        self.scroll_speed = 5.0
        
        # Zoom level (1.0 = normal)
        self.zoom = 1.0
        self.min_zoom = 0.5
        self.max_zoom = 2.0

    def apply(self, entity_rect: pygame.Rect) -> pygame.Rect:
        """Apply camera offset to an entity's rect.
        
        Args:
            entity_rect: The entity's world-space rectangle
            
        Returns:
            The screen-space rectangle
        """
        return entity_rect.move(-int(self.x), -int(self.y))

    def apply_pos(self, pos: Tuple[float, float]) -> Tuple[int, int]:
        """Apply camera offset to a position.
        
        Args:
            pos: World-space position (x, y)
            
        Returns:
            Screen-space position (x, y)
        """
        return (int(pos[0] - self.x), int(pos[1] - self.y))

    def update(self, target_x: float, target_y: float) -> None:
        """Update camera to follow a target position.
        
        Args:
            target_x: Target world x coordinate
            target_y: Target world y coordinate
        """
        # Center camera on target
        self.x = target_x - self.width / 2
        self.y = target_y - self.height / 2
        
        # Keep camera within world bounds
        self.x = max(0, min(self.x, self.world_width - self.width))
        self.y = max(0, min(self.y, self.world_height - self.height))

    def scroll(self, dx: float, dy: float) -> None:
        """Manually scroll the camera.
        
        Args:
            dx: Horizontal scroll amount
            dy: Vertical scroll amount
        """
        self.x += dx
        self.y += dy
        
        # Keep camera within world bounds
        self.x = max(0, min(self.x, self.world_width - self.width))
        self.y = max(0, min(self.y, self.world_height - self.height))

    def set_zoom(self, zoom: float) -> None:
        """Set the camera zoom level.
        
        Args:
            zoom: New zoom level (clamped to min/max)
        """
        self.zoom = max(self.min_zoom, min(zoom, self.max_zoom))

    def screen_to_world(self, screen_x: int, screen_y: int) -> Tuple[int, int]:
        """Convert screen coordinates to world coordinates.
        
        Args:
            screen_x: Screen x coordinate
            screen_y: Screen y coordinate
            
        Returns:
            World coordinates (x, y)
        """
        world_x = int(screen_x + self.x)
        world_y = int(screen_y + self.y)
        return (world_x, world_y)
