"""
Action panel for battle screen.

Left sidebar with action buttons for combat controls.
"""

import pygame
from config import SIDEBAR_WIDTH, UI_ACTIVE, UI_BG, UI_BORDER, UI_INACTIVE, UI_TEXT
from logger.logger import get_logger

logger = get_logger(__name__)


class ActionButton:
    """Represents a clickable action button."""

    def __init__(self, x: int, y: int, width: int, height: int, label: str, hotkey: str):
        """Initialize action button.

        Args:
            x: X position
            y: Y position
            width: Button width
            height: Button height
            label: Button text
            hotkey: Keyboard shortcut (e.g., "M", "A")
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.hotkey = hotkey
        self.hovered = False
        self.active = False

    def update_hover(self, mouse_pos: tuple[int, int]) -> None:
        """Update hover state based on mouse position.

        Args:
            mouse_pos: (x, y) mouse coordinates
        """
        self.hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, mouse_pos: tuple[int, int]) -> bool:
        """Check if button was clicked.

        Args:
            mouse_pos: (x, y) mouse coordinates

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
        # Determine color based on state
        if self.active:
            bg_color = UI_ACTIVE
            border_color = (100, 180, 255)
            border_width = 3
        elif self.hovered:
            bg_color = (40, 40, 50)
            border_color = (120, 120, 140)
            border_width = 2
        else:
            bg_color = UI_INACTIVE
            border_color = UI_BORDER
            border_width = 1

        # Draw button background
        pygame.draw.rect(surface, bg_color, self.rect)
        pygame.draw.rect(surface, border_color, self.rect, border_width)

        # Draw label
        text_color = UI_TEXT if not self.active else (255, 255, 255)
        label_surface = font.render(self.label, True, text_color)
        label_rect = label_surface.get_rect(center=self.rect.center)
        surface.blit(label_surface, label_rect)

        # Draw hotkey indicator (small text at bottom-right)
        hotkey_font = pygame.font.Font(None, 18)
        hotkey_surface = hotkey_font.render(f"[{self.hotkey}]", True, (150, 150, 160))
        hotkey_rect = hotkey_surface.get_rect(
            bottomright=(self.rect.right - 5, self.rect.bottom - 3)
        )
        surface.blit(hotkey_surface, hotkey_rect)


class ActionPanel:
    """Left sidebar panel with combat action buttons."""

    def __init__(self, width: int, height: int):
        """Initialize action panel.

        Args:
            width: Panel width (should match SIDEBAR_WIDTH)
            height: Panel height (screen height)
        """
        self.width = width
        self.height = height
        self.surface = pygame.Surface((width, height))

        # Fonts
        self.font_title = pygame.font.Font(None, 28)
        self.font_button = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 18)

        # Buttons
        self.buttons: list[ActionButton] = []
        self._create_buttons()

        logger.debug(f"ActionPanel initialized ({width}x{height})")

    def _create_buttons(self) -> None:
        """Create action buttons."""
        padding = 15
        button_width = self.width - 2 * padding
        button_height = 50
        start_y = 80  # Leave space for title

        actions = [
            ("Move", "M"),
            ("Attack", "A"),
            ("Inspect", "I"),
            ("Rotate CCW", "Q"),
            ("Rotate CW", "E"),
            ("End Turn", "Space"),
        ]

        for i, (label, hotkey) in enumerate(actions):
            y = start_y + i * (button_height + 10)
            button = ActionButton(padding, y, button_width, button_height, label, hotkey)
            self.buttons.append(button)

    def set_active_mode(self, mode: str) -> None:
        """Set which button should be highlighted as active.

        Args:
            mode: Current action mode ("move", "attack", "idle", etc.)
        """
        mode_map = {
            "move": "Move",
            "attack": "Attack",
            "inspect": "Inspect",
        }

        target_label = mode_map.get(mode, "")
        for button in self.buttons:
            button.active = button.label == target_label

    def handle_mouse_motion(self, mouse_pos: tuple[int, int]) -> None:
        """Update button hover states.

        Args:
            mouse_pos: Absolute mouse position (x, y)
        """
        for button in self.buttons:
            button.update_hover(mouse_pos)

    def handle_click(self, mouse_pos: tuple[int, int]) -> str | None:
        """Handle mouse click on panel.

        Args:
            mouse_pos: Absolute mouse position (x, y)

        Returns:
            Action name if button clicked, None otherwise
        """
        # Only handle clicks within panel area
        if mouse_pos[0] >= self.width:
            return None

        for button in self.buttons:
            if button.is_clicked(mouse_pos):
                logger.debug(f"Action button clicked: {button.label}")
                return button.label.lower().replace(" ", "_")

        return None

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the action panel.

        Args:
            screen: Main screen surface to draw on
        """
        # Clear panel surface
        self.surface.fill(UI_BG)

        # Draw border on right edge
        pygame.draw.line(
            self.surface,
            UI_BORDER,
            (self.width - 1, 0),
            (self.width - 1, self.height),
            2,
        )

        # Draw title
        title = self.font_title.render("Actions", True, UI_TEXT)
        title_rect = title.get_rect(centerx=self.width // 2, top=20)
        self.surface.blit(title, title_rect)

        # Draw buttons
        for button in self.buttons:
            button.draw(self.surface, self.font_button)

        # Draw help text at bottom
        help_y = self.height - 60
        help_text = self.font_small.render("ESC - Cancel/Quit", True, (150, 150, 160))
        help_rect = help_text.get_rect(centerx=self.width // 2, top=help_y)
        self.surface.blit(help_text, help_rect)

        # Blit panel to main screen (at left edge)
        screen.blit(self.surface, (0, 0))
