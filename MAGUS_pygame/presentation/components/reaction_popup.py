"""
Reaction popup for accepting or declining reactions during battle.

Reactions include:
- Shield bash (triggered after defender blocks)
- Opportunity attacks (triggered after miss/parry/friendly fire)
"""

from typing import Callable, Optional

import pygame
from config import HEIGHT, UI_ACTIVE, UI_BORDER, UI_INACTIVE, UI_TEXT, WIDTH
from logger.logger import get_logger

logger = get_logger(__name__)


class ReactionButton:
    """Represents a clickable reaction button (Accept/Decline)."""

    def __init__(self, x: int, y: int, width: int, height: int, label: str, action: str):
        """Initialize reaction button.

        Args:
            x: X position
            y: Y position
            width: Button width
            height: Button height
            label: Display text (e.g., "Accept" or "Decline")
            action: Action identifier ("accept" or "decline")
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.action = action
        self.hovered = False

    def update_hover(self, mouse_pos: tuple[int, int]) -> None:
        """Update hover state based on mouse position."""
        self.hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, mouse_pos: tuple[int, int]) -> bool:
        """Check if button was clicked."""
        return self.rect.collidepoint(mouse_pos)

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        """Draw the button.

        Args:
            surface: Pygame surface to draw on
            font: Font for button text
        """
        # Determine color based on state
        if self.hovered:
            bg_color = (100, 140, 100) if self.action == "accept" else (140, 100, 100)
            border_color = (150, 200, 150) if self.action == "accept" else (200, 150, 150)
            border_width = 2
        else:
            bg_color = (60, 100, 60) if self.action == "accept" else (100, 60, 60)
            border_color = UI_BORDER
            border_width = 1

        # Draw button background
        pygame.draw.rect(surface, bg_color, self.rect, border_radius=5)
        pygame.draw.rect(surface, border_color, self.rect, border_width, border_radius=5)

        # Draw text
        text_surface = font.render(self.label, True, UI_TEXT)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)


class ReactionPopup:
    """Popup for accepting/declining a reaction during combat.

    Appears when a unit triggers a reaction (shield bash, opportunity attack).
    Player can accept or decline with mouse or keyboard (Y/N keys).
    """

    def __init__(self, screen_width: int, screen_height: int):
        """Initialize reaction popup.

        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.visible = False

        # Popup dimensions and position
        self.popup_width = 400
        self.popup_height = 200
        self.popup_x = (screen_width - self.popup_width) // 2
        self.popup_y = (screen_height - self.popup_height) // 2
        self.popup_rect = pygame.Rect(self.popup_x, self.popup_y, self.popup_width, self.popup_height)

        # Content
        self.title = "Reaction"
        self.description = ""
        self.reaction_data: dict = {}  # Store reaction info (type, attacker, defender, etc.)

        # Buttons
        button_width = 80
        button_height = 40
        button_spacing = 20
        button_y = self.popup_y + self.popup_height - 60

        accept_x = self.popup_x + (self.popup_width // 2) - button_width - button_spacing // 2
        decline_x = self.popup_x + (self.popup_width // 2) + button_spacing // 2

        self.accept_button = ReactionButton(accept_x, button_y, button_width, button_height, "Accept", "accept")
        self.decline_button = ReactionButton(decline_x, button_y, button_width, button_height, "Decline", "decline")

        # Result callback
        self.on_reaction_result: Optional[Callable[[bool], None]] = None  # Called with (accepted: bool)

    def show(
        self,
        reaction_type: str,
        description: str,
        reaction_data: Optional[dict] = None,
        on_result: Optional[Callable[[bool], None]] = None,
    ) -> None:
        """Show the reaction popup.

        Args:
            reaction_type: Type of reaction (e.g., "shield_bash", "opportunity_attack")
            description: Description text to display
            reaction_data: Optional dict with reaction details (attacker, defender, etc.)
            on_result: Optional callback(accepted: bool) to call when reaction is resolved
        """
        self.title = f"{reaction_type.replace('_', ' ').title()} Reaction"
        self.description = description
        self.reaction_data = reaction_data or {}
        self.on_reaction_result = on_result
        self.visible = True
        logger.debug(f"Showing reaction popup: {self.title} - {self.description}")

    def hide(self) -> None:
        """Hide the reaction popup."""
        self.visible = False
        self.reaction_data = {}
        self.on_reaction_result = None

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle events for the popup.

        Args:
            event: Pygame event

        Returns:
            True if event was handled, False otherwise
        """
        if not self.visible:
            return False

        # Handle keyboard input (Y = accept, N = decline)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_y:
                self._resolve_reaction(True)
                return True
            elif event.key == pygame.K_n:
                self._resolve_reaction(False)
                return True

        return False

    def handle_click(self, mouse_pos: tuple[int, int]) -> Optional[str]:
        """Handle mouse click on popup buttons.

        Args:
            mouse_pos: Mouse position (x, y)

        Returns:
            Action string ("accept" or "decline"), or None if click was outside buttons
        """
        if not self.visible:
            return None

        self.accept_button.update_hover(mouse_pos)
        self.decline_button.update_hover(mouse_pos)

        if self.accept_button.is_clicked(mouse_pos):
            self._resolve_reaction(True)
            return "accept"
        elif self.decline_button.is_clicked(mouse_pos):
            self._resolve_reaction(False)
            return "decline"

        return None

    def _resolve_reaction(self, accepted: bool) -> None:
        """Resolve the reaction and call the callback.

        Args:
            accepted: Whether the reaction was accepted
        """
        if self.on_reaction_result:
            self.on_reaction_result(accepted)
        self.hide()

    def is_click_outside(self, mouse_pos: tuple[int, int]) -> bool:
        """Check if click is outside the popup.

        Args:
            mouse_pos: Mouse position (x, y)

        Returns:
            True if click is outside the popup area
        """
        if not self.visible:
            return False
        return not self.popup_rect.collidepoint(mouse_pos)

    def handle_mouse_motion(self, mouse_pos: tuple[int, int]) -> None:
        """Update button hover states based on mouse position.

        Args:
            mouse_pos: Mouse position (x, y)
        """
        if not self.visible:
            return

        self.accept_button.update_hover(mouse_pos)
        self.decline_button.update_hover(mouse_pos)

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, small_font: pygame.font.Font) -> None:
        """Draw the reaction popup.

        Args:
            surface: Pygame surface to draw on
            font: Font for title and description
            small_font: Font for button text
        """
        if not self.visible:
            return

        # Draw semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))

        # Draw popup background
        pygame.draw.rect(surface, UI_ACTIVE, self.popup_rect, border_radius=8)
        pygame.draw.rect(surface, UI_BORDER, self.popup_rect, 2, border_radius=8)

        # Draw title
        title_surface = font.render(self.title, True, UI_TEXT)
        title_rect = title_surface.get_rect(
            center=(self.popup_rect.centerx, self.popup_y + 20)
        )
        surface.blit(title_surface, title_rect)

        # Draw description (with text wrapping if needed)
        self._draw_wrapped_text(surface, small_font, self.description, self.popup_y + 60)

        # Draw buttons
        self.accept_button.draw(surface, small_font)
        self.decline_button.draw(surface, small_font)

        # Draw keyboard hints
        hint_y = self.popup_y + self.popup_height - 15
        hint_surface = small_font.render("Y/N for keyboard, Click for mouse", True, (150, 150, 150))
        hint_rect = hint_surface.get_rect(center=(self.popup_rect.centerx, hint_y))
        surface.blit(hint_surface, hint_rect)

    def _draw_wrapped_text(
        self, surface: pygame.Surface, font: pygame.font.Font, text: str, start_y: int, max_width: int = 360
    ) -> None:
        """Draw text with word wrapping.

        Args:
            surface: Pygame surface to draw on
            font: Font to use
            text: Text to draw
            start_y: Starting Y position
            max_width: Maximum width before wrapping
        """
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            test_surface = font.render(test_line, True, UI_TEXT)
            if test_surface.get_width() <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

        # Draw each line
        y = start_y
        for line in lines:
            line_surface = font.render(line, True, UI_TEXT)
            line_rect = line_surface.get_rect(center=(self.popup_rect.centerx, y))
            surface.blit(line_surface, line_rect)
            y += 25
