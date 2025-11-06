"""
Heads-up display (HUD) for MAGUS Pygame.
Shows character stats, health, stamina, mana, and active effects.
"""

from typing import Any, Optional, Tuple
import pygame


class HUD:
    """Manages the game HUD overlay."""

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
        self.color_health = (220, 20, 60)  # Crimson
        self.color_stamina = (50, 205, 50)  # Lime green
        self.color_mana = (30, 144, 255)  # Dodger blue
        self.color_text = (255, 255, 255)  # White
        
        # Layout
        self.padding = 10
        self.bar_height = 20
        self.bar_width = 200

    def draw(self, surface: pygame.Surface, unit_data: Optional[dict[str, Any]] = None) -> None:
        """Draw the HUD.
        
        Args:
            surface: Surface to draw on
            unit_data: Current unit data to display
        """
        if not unit_data:
            return
            
        # Draw character info panel (top-left)
        self._draw_character_panel(surface, unit_data)
        
        # Draw resource bars (top-center)
        self._draw_resource_bars(surface, unit_data)
        
        # Draw active effects (top-right)
        self._draw_active_effects(surface, unit_data)
        
        # Draw turn info (bottom-center)
        self._draw_turn_info(surface, unit_data)

    def _draw_character_panel(self, surface: pygame.Surface, unit_data: dict[str, Any]) -> None:
        """Draw the character information panel.
        
        Args:
            surface: Surface to draw on
            unit_data: Unit data
        """
        x = self.padding
        y = self.padding
        
        # Panel background
        panel_width = 250
        panel_height = 100
        panel_rect = pygame.Rect(x, y, panel_width, panel_height)
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_surface.fill(self.color_bg)
        surface.blit(panel_surface, (x, y))
        
        # Character name
        name = unit_data.get('name', 'Unknown')
        name_text = self.font_large.render(name, True, self.color_text)
        surface.blit(name_text, (x + self.padding, y + self.padding))
        
        # Character level/class
        level = unit_data.get('level', 1)
        char_class = unit_data.get('class', 'Warrior')
        info_text = self.font_small.render(f"Level {level} {char_class}", True, self.color_text)
        surface.blit(info_text, (x + self.padding, y + self.padding + 35))

    def _draw_resource_bars(self, surface: pygame.Surface, unit_data: dict[str, Any]) -> None:
        """Draw health, stamina, and mana bars.
        
        Args:
            surface: Surface to draw on
            unit_data: Unit data
        """
        x = self.screen_width // 2 - self.bar_width // 2
        y = self.padding
        
        # Health bar
        current_hp = unit_data.get('current_hp', 100)
        max_hp = unit_data.get('max_hp', 100)
        self._draw_bar(surface, x, y, current_hp, max_hp, self.color_health, "HP")
        
        # Stamina bar
        current_stamina = unit_data.get('current_stamina', 100)
        max_stamina = unit_data.get('max_stamina', 100)
        self._draw_bar(surface, x, y + 30, current_stamina, max_stamina, self.color_stamina, "Stamina")
        
        # Mana bar (if applicable)
        if 'current_mana' in unit_data:
            current_mana = unit_data.get('current_mana', 0)
            max_mana = unit_data.get('max_mana', 100)
            self._draw_bar(surface, x, y + 60, current_mana, max_mana, self.color_mana, "Mana")

    def _draw_bar(
        self,
        surface: pygame.Surface,
        x: int,
        y: int,
        current: int,
        maximum: int,
        color: Tuple[int, int, int],
        label: str
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

    def _draw_active_effects(self, surface: pygame.Surface, unit_data: dict[str, Any]) -> None:
        """Draw active status effects.
        
        Args:
            surface: Surface to draw on
            unit_data: Unit data
        """
        effects = unit_data.get('active_effects', [])
        if not effects:
            return
            
        x = self.screen_width - 260
        y = self.padding
        
        # Panel background
        panel_height = 30 + len(effects) * 25
        panel_surface = pygame.Surface((250, panel_height), pygame.SRCALPHA)
        panel_surface.fill(self.color_bg)
        surface.blit(panel_surface, (x, y))
        
        # Title
        title_text = self.font_medium.render("Active Effects", True, self.color_text)
        surface.blit(title_text, (x + self.padding, y + self.padding))
        
        # Effects list
        for i, effect in enumerate(effects):
            effect_text = self.font_small.render(f"• {effect}", True, self.color_text)
            surface.blit(effect_text, (x + self.padding, y + 30 + i * 25))

    def _draw_turn_info(self, surface: pygame.Surface, unit_data: dict[str, Any]) -> None:
        """Draw turn and round information.
        
        Args:
            surface: Surface to draw on
            unit_data: Unit data
        """
        round_num = unit_data.get('round', 1)
        current_unit = unit_data.get('current_unit', 'Player')
        
        info = f"Round {round_num} - {current_unit}'s Turn"
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
