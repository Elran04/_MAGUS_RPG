"""
Pause menu overlay for battle screen.

Displayed when ESC is pressed during combat.
"""

import pygame
from config import UI_ACTIVE, UI_BG, UI_BORDER, UI_TEXT
from logger.logger import get_logger

logger = get_logger(__name__)


class PauseMenuButton:
    """Represents a button in the pause menu."""

    def __init__(self, x: int, y: int, width: int, height: int, label: str, action: str):
        """Initialize pause menu button.

        Args:
            x: X position
            y: Y position
            width: Button width
            height: Button height
            label: Button text
            action: Action identifier ("continue", "exit_to_menu")
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.action = action
        self.hovered = False

    def update_hover(self, mouse_pos: tuple[int, int]) -> None:
        """Update hover state.

        Args:
            mouse_pos: Mouse position (x, y)
        """
        self.hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, mouse_pos: tuple[int, int]) -> bool:
        """Check if button was clicked.

        Args:
            mouse_pos: Mouse position (x, y)

        Returns:
            True if clicked
        """
        return self.rect.collidepoint(mouse_pos)

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        """Draw the button.

        Args:
            surface: Surface to draw on
            font: Font for text
        """
        # Button colors
        if self.hovered:
            bg_color = UI_ACTIVE
            border_color = (120, 180, 255)
            border_width = 3
        else:
            bg_color = (50, 50, 60)
            border_color = UI_BORDER
            border_width = 2

        # Draw button
        pygame.draw.rect(surface, bg_color, self.rect)
        pygame.draw.rect(surface, border_color, self.rect, border_width)

        # Draw label
        text_color = (255, 255, 255) if self.hovered else UI_TEXT
        text_surface = font.render(self.label, True, text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)


class PauseMenu:
    """In-game pause menu overlay."""

    def __init__(self, screen_width: int, screen_height: int):
        """Initialize pause menu.

        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.visible = False

        # Fonts
        self.font_title = pygame.font.Font(None, 64)
        self.font_button = pygame.font.Font(None, 32)
        self.font_hint = pygame.font.Font(None, 20)

        # Menu panel dimensions
        self.panel_width = 400
        self.panel_height = 300
        self.panel_x = (screen_width - self.panel_width) // 2
        self.panel_y = (screen_height - self.panel_height) // 2

        # Buttons
        self.buttons: list[PauseMenuButton] = []
        self._create_buttons()

        logger.debug("PauseMenu initialized")

    def _create_buttons(self) -> None:
        """Create menu buttons."""
        button_width = 300
        button_height = 60
        button_x = self.panel_x + (self.panel_width - button_width) // 2
        start_y = self.panel_y + 100

        # Continue button
        continue_btn = PauseMenuButton(
            button_x, start_y, button_width, button_height, "Continue", "continue"
        )
        self.buttons.append(continue_btn)

        # Exit to menu button
        exit_btn = PauseMenuButton(
            button_x,
            start_y + button_height + 20,
            button_width,
            button_height,
            "Exit to Main Menu",
            "exit_to_menu",
        )
        self.buttons.append(exit_btn)

    def show(self) -> None:
        """Show the pause menu."""
        self.visible = True
        logger.debug("Pause menu opened")

    def hide(self) -> None:
        """Hide the pause menu."""
        self.visible = False
        logger.debug("Pause menu closed")

    def toggle(self) -> None:
        """Toggle pause menu visibility."""
        self.visible = not self.visible
        if self.visible:
            logger.debug("Pause menu opened")
        else:
            logger.debug("Pause menu closed")

    def handle_mouse_motion(self, mouse_pos: tuple[int, int]) -> None:
        """Update button hover states.

        Args:
            mouse_pos: Mouse position (x, y)
        """
        if not self.visible:
            return

        for button in self.buttons:
            button.update_hover(mouse_pos)

    def handle_click(self, mouse_pos: tuple[int, int]) -> str | None:
        """Handle mouse click on pause menu.

        Args:
            mouse_pos: Mouse position (x, y)

        Returns:
            Action identifier if button clicked ("continue", "exit_to_menu"), None otherwise
        """
        if not self.visible:
            return None

        for button in self.buttons:
            if button.is_clicked(mouse_pos):
                logger.debug(f"Pause menu button clicked: {button.action}")
                return button.action

        return None

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the pause menu overlay.

        Args:
            surface: Surface to draw on
        """
        if not self.visible:
            return

        # Semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        # Menu panel background
        panel_surface = pygame.Surface((self.panel_width, self.panel_height), pygame.SRCALPHA)
        panel_surface.fill((*UI_BG, 240))
        surface.blit(panel_surface, (self.panel_x, self.panel_y))

        # Panel border
        panel_rect = pygame.Rect(self.panel_x, self.panel_y, self.panel_width, self.panel_height)
        pygame.draw.rect(surface, UI_BORDER, panel_rect, 3)

        # Title
        title = self.font_title.render("PAUSED", True, UI_TEXT)
        title_rect = title.get_rect(centerx=self.screen_width // 2, top=self.panel_y + 20)
        surface.blit(title, title_rect)

        # Buttons
        for button in self.buttons:
            button.draw(surface, self.font_button)

        # Hint text
        hint = self.font_hint.render("Press ESC to continue", True, (150, 150, 160))
        hint_rect = hint.get_rect(
            centerx=self.screen_width // 2, bottom=self.panel_y + self.panel_height - 20
        )
        surface.blit(hint, hint_rect)
