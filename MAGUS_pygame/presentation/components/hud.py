"""
Heads-up display (HUD) for MAGUS Pygame - Migrated to new architecture.

Shows character stats, health, stamina, and active effects using new domain entities.
"""

import pygame
from domain.entities import Unit
from domain.mechanics import Stamina
from logger.logger import get_logger

logger = get_logger(__name__)


class HUD:
    """
    Manages the game HUD overlay.

    Clean architecture principles:
    - Accepts domain entities (Unit) not raw dicts
    - Pure presentation logic, no game state manipulation
    - Self-contained rendering
    """

    def __init__(self, screen_width: int, screen_height: int) -> None:
        """Initialize the HUD.

        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
        """
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Fonts
        self.font_large = pygame.font.Font(None, 32)
        self.font_medium = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 18)

        # Colors
        self.color_bg = (0, 0, 0, 180)  # Semi-transparent black
        self.color_health = (220, 20, 60)  # Crimson (EP)
        self.color_fatigue = (100, 149, 237)  # Cornflower blue (FP)
        self.color_stamina = (50, 205, 50)  # Lime green
        self.color_mana = (138, 43, 226)  # Blue violet
        self.color_text = (255, 255, 255)  # White

        # Layout
        self.padding = 10
        self.bar_height = 20
        self.bar_width = 200

        logger.debug("HUD initialized")

    def draw(
        self,
        surface: pygame.Surface,
        unit: Unit | None = None,
        round_num: int = 1,
        action_points: int | None = None,
    ) -> None:
        """Draw the HUD.

        Args:
            surface: Surface to draw on
            unit: Current active unit to display
            round_num: Current round number
            action_points: Optional action points remaining for current unit
        """
        if not unit:
            return

        # Draw character info panel (top-left)
        self._draw_character_panel(surface, unit, action_points)

        # Draw resource bars (top-center)
        self._draw_resource_bars(surface, unit)

        # Draw active effects (top-right) - placeholder for future conditions system
        # self._draw_active_effects(surface, unit)

        # Draw turn info (bottom-center)
        self._draw_turn_info(surface, unit, round_num)

    def _draw_character_panel(
        self, surface: pygame.Surface, unit: Unit, action_points: int | None = None
    ) -> None:
        """Draw the character information panel.

        Args:
            surface: Surface to draw on
            unit: Unit to display
            action_points: Optional action points remaining
        """
        x = self.padding
        y = self.padding

        # Panel background
        panel_width = 250
        panel_height = 120 if action_points is not None else 100
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_surface.fill(self.color_bg)
        surface.blit(panel_surface, (x, y))

        # Character name
        name_text = self.font_large.render(unit.name, True, self.color_text)
        surface.blit(name_text, (x + self.padding, y + self.padding))

        # Combat stats summary
        stats_text = self.font_small.render(
            f"KÉ:{unit.combat_stats.KE} TÉ:{unit.combat_stats.TE} VÉ:{unit.combat_stats.VE}",
            True,
            self.color_text,
        )
        surface.blit(stats_text, (x + self.padding, y + self.padding + 35))

        # Position info
        pos_text = self.font_small.render(f"Position: {unit.position}", True, (180, 180, 180))
        surface.blit(pos_text, (x + self.padding, y + self.padding + 55))

        # Action points (if provided)
        if action_points is not None:
            ap_color = (
                (255, 215, 0)
                if action_points > 5
                else (255, 100, 100) if action_points > 0 else (128, 128, 128)
            )
            ap_text = self.font_medium.render(f"AP: {action_points}", True, ap_color)
            surface.blit(ap_text, (x + self.padding, y + self.padding + 80))

    def _draw_resource_bars(self, surface: pygame.Surface, unit: Unit) -> None:
        """Draw health (EP), fatigue (FP), and stamina bars.

        Args:
            surface: Surface to draw on
            unit: Unit to display
        """
        x = self.screen_width // 2 - self.bar_width // 2
        y = self.padding

        # EP bar (Health/Életerő Pont)
        self._draw_bar(
            surface, x, y, unit.ep.current, unit.ep.maximum, self.color_health, "ÉP (Health)"
        )

        # FP bar (Fájdalomtűrés Pont - Pain Tolerance Points)
        # FP is damaged before ÉP in combat (see attack_resolution.py)
        self._draw_bar(
            surface,
            x,
            y + 30,
            unit.fp.current,
            unit.fp.maximum,
            self.color_fatigue,
            "FP (Pain Tolerance)",
        )

        # Stamina bar (independent system based on Állóképesség/Endurance)
        # See domain/mechanics/stamina.py for details
        if hasattr(unit.attributes, "endurance"):
            stamina = Stamina.from_attribute(unit.attributes.endurance)
            # TODO: Unit needs to track current stamina as separate attribute
            # For now using max as placeholder until stamina tracking is implemented
            stamina.current_stamina = stamina.max_stamina
            percentage, state = stamina.get_state()

            self._draw_bar(
                surface,
                x,
                y + 60,
                stamina.current_stamina,
                stamina.max_stamina,
                self.color_stamina,
                f"Stamina ({state.value})",
            )

    def _draw_bar(
        self,
        surface: pygame.Surface,
        x: int,
        y: int,
        current: int,
        maximum: int,
        color: tuple[int, int, int],
        label: str,
    ) -> None:
        """Draw a resource bar.

        Args:
            surface: Surface to draw on
            x: X position
            y: Y position
            current: Current value
            maximum: Maximum value
            color: Bar color
            label: Bar label
        """
        # Background
        bg_rect = pygame.Rect(x, y, self.bar_width, self.bar_height)
        pygame.draw.rect(surface, (50, 50, 50), bg_rect)

        # Fill
        if maximum > 0:
            fill_width = int(self.bar_width * (current / maximum))
            fill_rect = pygame.Rect(x, y, fill_width, self.bar_height)
            pygame.draw.rect(surface, color, fill_rect)

        # Border
        pygame.draw.rect(surface, self.color_text, bg_rect, 2)

        # Text
        text = self.font_small.render(f"{label}: {current}/{maximum}", True, self.color_text)
        text_rect = text.get_rect(center=(x + self.bar_width // 2, y + self.bar_height // 2))
        surface.blit(text, text_rect)

    def _draw_turn_info(self, surface: pygame.Surface, unit: Unit, round_num: int) -> None:
        """Draw turn and round information.

        Args:
            surface: Surface to draw on
            unit: Current active unit
            round_num: Current round number
        """
        info = f"Round {round_num} - {unit.name}'s Turn"
        text = self.font_medium.render(info, True, self.color_text)

        # Center at bottom
        x = self.screen_width // 2 - text.get_width() // 2
        y = self.screen_height - 50

        # Background
        bg_rect = pygame.Rect(x - 10, y - 5, text.get_width() + 20, text.get_height() + 10)
        bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        bg_surface.fill(self.color_bg)
        surface.blit(bg_surface, (bg_rect.x, bg_rect.y))

        # Text
        surface.blit(text, (x, y))

    def draw_tooltip(self, surface: pygame.Surface, text: str, x: int, y: int) -> None:
        """Draw a tooltip at the specified position.

        Args:
            surface: Surface to draw on
            text: Tooltip text
            x: X position
            y: Y position
        """
        # Render text
        text_surface = self.font_small.render(text, True, self.color_text)

        # Background
        padding = 5
        bg_width = text_surface.get_width() + padding * 2
        bg_height = text_surface.get_height() + padding * 2
        bg_surface = pygame.Surface((bg_width, bg_height), pygame.SRCALPHA)
        bg_surface.fill(self.color_bg)

        # Draw
        surface.blit(bg_surface, (x, y))
        surface.blit(text_surface, (x + padding, y + padding))
