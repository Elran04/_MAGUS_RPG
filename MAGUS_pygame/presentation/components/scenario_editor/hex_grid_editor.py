"""Hex Grid Editor - Interactive hex grid for scenario editing."""

from __future__ import annotations

import math

import pygame
from config import HEX_BORDER, HEX_SIZE
from infrastructure.rendering.hex_grid import draw_hex, get_grid_bounds, hex_to_pixel, pixel_to_hex
from logger.logger import get_logger

logger = get_logger(__name__)


class HexGridEditor:
    """Renders and handles interaction with hex grid."""

    def __init__(self, hex_size: int | None = None):
        self.hex_size = hex_size if hex_size is not None else HEX_SIZE

        # Colors
        self.color_team_a = (100, 150, 255, 140)  # Blue
        self.color_team_b = (255, 100, 100, 140)  # Red
        self.color_obstacle = (80, 80, 80, 180)  # Gray
        self.color_hex_border = (100, 100, 120)

        # Fonts
        self.font_small = pygame.font.Font(None, 24)

    def get_hex_at_pixel(self, x: int, y: int) -> tuple[int, int]:
        """Convert pixel coordinates to hex coordinates."""
        return pixel_to_hex(x, y)

    def is_hex_in_bounds(self, q: int, r: int, grid_bounds: dict) -> bool:
        """Check if hex is within scenario grid bounds."""
        min_q = grid_bounds.get("min_q", -8)
        max_q = grid_bounds.get("max_q", 8)
        min_r = grid_bounds.get("min_r", -8)
        max_r = grid_bounds.get("max_r", 8)
        return min_q <= q <= max_q and min_r <= r <= max_r

    def draw(self, surface: pygame.Surface, scenario_data: dict) -> None:
        """Draw hex grid with zones and obstacles."""
        if not scenario_data:
            return

        # Use the game grid bounds, but limit to the play area's usable grid that battle draws.
        # Battle renders to the play surface (PLAY_AREA_WIDTH x screen_height) with the same
        # hex_size and center offset, so we reuse get_grid_bounds but then clamp to the
        # play area's dimensions to avoid showing hexes the battle view will never render.
        from config import HEIGHT, PLAY_AREA_WIDTH

        min_q, max_q, min_r, max_r = get_grid_bounds()
        screen_w, screen_h = surface.get_size()

        # Adjust bounds so that only hexes that would appear inside the battle play area
        # are drawn in the editor. This keeps coordinates consistent between editor and battle.
        # We filter by pixel position against PLAY_AREA_WIDTH rather than full window width.
        max_play_x = PLAY_AREA_WIDTH

        # Extract zone data
        team_a_zones = set(
            (z["q"], z["r"]) for z in scenario_data.get("spawn_zones", {}).get("team_a", [])
        )
        team_b_zones = set(
            (z["q"], z["r"]) for z in scenario_data.get("spawn_zones", {}).get("team_b", [])
        )
        obstacles = set((o["q"], o["r"]) for o in scenario_data.get("obstacles", []))

        # Create overlay surface for transparent zone colors
        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)

        # Draw hexes
        margin = self.hex_size * 2

        for q in range(min_q, max_q + 1):
            for r in range(min_r, max_r + 1):
                cx, cy = hex_to_pixel(q, r)

                # Skip if outside play area width or off-screen vertically
                if cx < -margin or cx > max_play_x + margin:
                    continue
                if cy < -margin or cy > screen_h + margin:
                    continue

                # Draw hex border using game's method
                draw_hex(surface, HEX_BORDER, (cx, cy), self.hex_size, border=2)

                # Get corner points for filled overlays
                corners = self._get_hex_corners(cx, cy)

                # Draw zone overlays
                if (q, r) in team_a_zones:
                    pygame.draw.polygon(overlay, self.color_team_a, corners, 0)

                if (q, r) in team_b_zones:
                    pygame.draw.polygon(overlay, self.color_team_b, corners, 0)

                if (q, r) in obstacles:
                    pygame.draw.polygon(overlay, self.color_obstacle, corners, 0)

        # Blit overlay with all transparent zones
        surface.blit(overlay, (0, 0))

        # Draw obstacle markers on top
        for q, r in obstacles:
            cx, cy = hex_to_pixel(q, r)
            if -margin < cx < screen_w + margin and -margin < cy < screen_h + margin:
                # Draw X for obstacle
                mark_size = self.hex_size // 3
                pygame.draw.line(
                    surface,
                    (200, 200, 200),
                    (cx - mark_size, cy - mark_size),
                    (cx + mark_size, cy + mark_size),
                    3,
                )
                pygame.draw.line(
                    surface,
                    (200, 200, 200),
                    (cx - mark_size, cy + mark_size),
                    (cx + mark_size, cy - mark_size),
                    3,
                )

    def _get_hex_corners(self, cx: int, cy: int) -> list[tuple[int, int]]:
        """Get hex corner points for pointy-top hex."""
        corners = []
        for i in range(6):
            angle = math.pi / 180 * (60 * i - 30)  # Match game's hex orientation
            x = cx + self.hex_size * math.cos(angle)
            y = cy + self.hex_size * math.sin(angle)
            corners.append((int(x), int(y)))
        return corners
