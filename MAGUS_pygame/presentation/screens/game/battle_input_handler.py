"""
Input handling for battle screen.

Processes keyboard and mouse events, translating them into game actions.
"""

import pygame
from config import SIDEBAR_WIDTH
from infrastructure.rendering.hex_grid import get_grid_bounds, pixel_to_hex
from logger.logger import get_logger

logger = get_logger(__name__)


class BattleInputHandler:
    """Handles all input processing for battle screen."""

    def __init__(self):
        """Initialize input handler."""
        self.hovered_hex: tuple[int, int] | None = None

    def translate_mouse_to_play_area(self, mouse_pos: tuple[int, int]) -> tuple[int, int]:
        """Translate screen mouse coordinates to play area coordinates.

        Args:
            mouse_pos: Mouse position in screen coordinates

        Returns:
            Mouse position in play area coordinates (offset by sidebar)
        """
        return (mouse_pos[0] - SIDEBAR_WIDTH, mouse_pos[1])

    def update_hovered_hex(self, mouse_pos: tuple[int, int]) -> tuple[int, int] | None:
        """Update hovered hex from mouse position.

        Args:
            mouse_pos: Mouse position (x, y) in screen coordinates

        Returns:
            Updated hovered hex (q, r) or None
        """
        # Translate to play area coordinates
        play_pos = self.translate_mouse_to_play_area(mouse_pos)
        q, r = pixel_to_hex(*play_pos)
        min_q, max_q, min_r, max_r = get_grid_bounds()

        if min_q <= q < max_q and min_r <= r < max_r:
            self.hovered_hex = (q, r)
            return self.hovered_hex
        else:
            self.hovered_hex = None
            return None

    def is_click_in_play_area(self, mouse_pos: tuple[int, int]) -> bool:
        """Check if mouse click is in play area (not on sidebar).

        Args:
            mouse_pos: Mouse position in screen coordinates

        Returns:
            True if click is in play area
        """
        return mouse_pos[0] >= SIDEBAR_WIDTH
