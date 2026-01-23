"""
Battle renderer for MAGUS Pygame - Migrated to new architecture.

Handles rendering of the battle scene including:
- Background
- Hex grid
- Units with sprites
- Movement paths
- Highlights and overlays
"""

import pygame
from config import (
    BG_COLOR,
    HEIGHT,
    PATH_DOT_COLOR,
    PATH_DOT_RADIUS,
    PATH_LINE_COLOR,
    PATH_LINE_WIDTH,
    PATH_ZONE_OVERLAP_COLOR,
    PATH_ZONE_OVERLAP_RADIUS,
    WIDTH,
)
from domain.entities import Unit
from domain.value_objects import Position
from infrastructure.rendering.hex_grid import draw_grid, hex_to_pixel
from infrastructure.rendering.sprite_utils import draw_unit_overlays
from logger.logger import get_logger

logger = get_logger(__name__)


class BattleRenderer:
    """
    Renders the battle scene.

    Clean architecture principles:
    - Accepts domain entities (Unit, Position)
    - Pure rendering logic, no game state modification
    - Configurable through constructor
    """

    def __init__(
        self,
        screen: pygame.Surface,
        grid_bounds: tuple[int, int, int, int],
        background: pygame.Surface | None = None,
        x_offset: int = 0,
    ):
        """Initialize the battle renderer.

        Args:
            screen: Main pygame display surface
            grid_bounds: (MIN_Q, MAX_Q, MIN_R, MAX_R) hex grid boundaries
            background: Optional background image
            x_offset: Horizontal offset for rendering (e.g., for left sidebar)
        """
        self.screen = screen
        self.grid_bounds = grid_bounds
        self.background = background
        self.x_offset = x_offset

        # Fonts
        self.overlay_font = pygame.font.SysFont(None, 20)
        self.hud_font = pygame.font.SysFont(None, 32)

        logger.info(f"BattleRenderer initialized with bounds {grid_bounds}, offset={x_offset}")

    def set_background(self, background: pygame.Surface | None) -> None:
        """Set or update the background image.

        Args:
            background: Background surface or None for solid color
        """
        self.background = background

    def clear(self) -> None:
        """Clear the screen with background or solid color."""
        if self.background is not None:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill(BG_COLOR)

    def draw_grid(
        self,
        units: list[Unit],
        reachable_hexes: set[tuple[int, int]] | None = None,
        attackable_hexes: set[tuple[int, int]] | None = None,
        charge_area_hexes: set[tuple[int, int]] | None = None,
        charge_targets: set[tuple[int, int]] | None = None,
        enemy_zone_hexes: set[tuple[int, int]] | None = None,
        highlight_hex: tuple[int, int] | None = None,
        active_unit_hex: tuple[int, int] | None = None,
    ) -> None:
        """Draw the hex grid with units and highlights.

        Args:
            units: List of units to render
            reachable_hexes: Set of (q, r) hexes highlighted for movement
            attackable_hexes: Set of (q, r) hexes highlighted for attacks
            charge_area_hexes: Set of (q, r) hexes for charge movement
            charge_targets: Set of (q, r) hexes with charge targets
            enemy_zone_hexes: Set of (q, r) hexes in enemy zones
            highlight_hex: Single (q, r) hex to highlight (hover)
            active_unit_hex: Single (q, r) hex of active unit (bright highlight)
        """
        # Build sprite positions dict from units
        sprite_positions = {
            (unit.position.q, unit.position.r): unit.sprite
            for unit in units
            if unit.sprite is not None
        }

        MIN_Q, MAX_Q, MIN_R, MAX_R = self.grid_bounds

        draw_grid(
            self.screen,
            MIN_Q,
            MAX_Q,
            MIN_R,
            MAX_R,
            sprite_positions,
            reachable_hexes=reachable_hexes,
            attackable_hexes=attackable_hexes,
            charge_area_hexes=charge_area_hexes,
            charge_targets=charge_targets,
            enemy_zone_hexes=enemy_zone_hexes,
            highlight_hex=highlight_hex,
            active_unit_hex=active_unit_hex,
        )

    def draw_units(self, units: list[Unit], active_unit: Unit | None = None) -> None:
        """Draw unit overlays (name, HP bars, facing).

        Args:
            units: List of units to draw overlays for
            active_unit: Currently active unit to highlight
        """
        for unit in units:
            if unit.is_alive():  # Only draw living units
                draw_unit_overlays(self.screen, unit, self.overlay_font, active_unit)

    def draw_movement_path(self, path: list[Position], enemy_zone: set[tuple[int, int]]) -> None:
        """Draw the movement path with danger highlights.

        Args:
            path: List of Position objects representing the path
            enemy_zone: Set of (q, r) hex coordinates in enemy's zone of control
        """
        if len(path) < 2:
            return

        # Convert path to (q, r) tuples for zone checking
        path_coords = [(pos.q, pos.r) for pos in path]

        # Convert path to pixel coordinates
        pixel_path = [hex_to_pixel(pos.q, pos.r) for pos in path]

        # Draw lines connecting path nodes
        if len(pixel_path) >= 2:
            pygame.draw.lines(self.screen, PATH_LINE_COLOR, False, pixel_path, PATH_LINE_WIDTH)

        # Draw dots at each path node, highlighting zone overlaps
        for i, (hex_pos, (px, py)) in enumerate(zip(path_coords, pixel_path, strict=False)):
            if i == 0:  # Skip starting position
                continue

            # Check if this hex is in the enemy zone
            if hex_pos in enemy_zone:
                # DANGER! Path goes through zone - draw large red circle
                pygame.draw.circle(
                    self.screen, PATH_ZONE_OVERLAP_COLOR, (px, py), PATH_ZONE_OVERLAP_RADIUS
                )
                # Draw inner dot for visibility
                pygame.draw.circle(self.screen, (255, 200, 200), (px, py), PATH_DOT_RADIUS)
            elif i < len(pixel_path) - 1:  # Normal intermediate node (not start or end)
                pygame.draw.circle(self.screen, PATH_DOT_COLOR, (px, py), PATH_DOT_RADIUS)

    def draw_victory_screen(self, winner: Unit, defeated: Unit) -> None:
        """Draw victory screen overlay.

        Args:
            winner: The winning unit
            defeated: The defeated unit
        """
        victory_font = pygame.font.SysFont(None, 64)
        info_font = pygame.font.SysFont(None, 32)

        # Semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # Victory text
        victory_text = victory_font.render(f"{winner.name} Wins!", True, (255, 215, 0))
        victory_rect = victory_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40))
        self.screen.blit(victory_text, victory_rect)

        # Defeated text
        defeated_text = info_font.render(
            f"{defeated.name} has been defeated", True, (200, 200, 200)
        )
        defeated_rect = defeated_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20))
        self.screen.blit(defeated_text, defeated_rect)

        # Instructions
        instruction_text = info_font.render("Close window to exit", True, (150, 150, 150))
        instruction_rect = instruction_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 70))
        self.screen.blit(instruction_text, instruction_rect)

    def draw_hud(
        self,
        round_num: int,
        active_unit: Unit | None,
        action_mode: str = "Normal",
        combat_message: str | None = None,
    ) -> None:
        """Draw the heads-up display.

        Args:
            round_num: Current round number
            active_unit: Currently active unit
            action_mode: Current action mode (Move, Attack, etc.)
            combat_message: Optional combat message (now displayed in action panel)
        """
        # Combat message is now drawn in action panel, this method is kept for compatibility
        pass

    def render_scene(
        self,
        units: list[Unit],
        round_num: int = 1,
        active_unit: Unit | None = None,
        action_mode: str = "Normal",
        movement_path: list[Position] | None = None,
        enemy_zone: set[tuple[int, int]] | None = None,
        reachable_hexes: set[tuple[int, int]] | None = None,
        attackable_hexes: set[tuple[int, int]] | None = None,
        highlight_hex: tuple[int, int] | None = None,
        combat_message: str | None = None,
    ) -> None:
        """Render complete battle scene.

        Convenience method that draws everything in the correct order.

        Args:
            units: List of all units
            round_num: Current round number
            active_unit: Currently active unit
            action_mode: Current action mode
            movement_path: Optional path to render
            enemy_zone: Optional enemy zone hexes
            reachable_hexes: Optional reachable hexes for movement
            attackable_hexes: Optional attackable hexes
            highlight_hex: Optional hex to highlight
            combat_message: Optional combat message
        """
        # Clear screen
        self.clear()

        # Calculate active unit hex
        active_unit_hex = None
        if active_unit:
            active_unit_hex = (active_unit.position.q, active_unit.position.r)

        # Draw grid with highlights
        self.draw_grid(
            units,
            reachable_hexes=reachable_hexes,
            attackable_hexes=attackable_hexes,
            highlight_hex=highlight_hex,
            active_unit_hex=active_unit_hex,
        )

        # Draw movement path if provided
        if movement_path and enemy_zone:
            self.draw_movement_path(movement_path, enemy_zone)

        # Draw unit overlays
        self.draw_units(units, active_unit)

        # Draw HUD
        self.draw_hud(round_num, active_unit, action_mode, combat_message)
