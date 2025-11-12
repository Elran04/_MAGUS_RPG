"""
Dropdown component for pygame UI.

Custom dropdown menu for selecting items from a list with keyboard and mouse support.
"""

import pygame
from config import DEJAVU_FONT_PATH
from logger.logger import get_logger

logger = get_logger(__name__)


class Dropdown:
    """Custom dropdown menu component.

    Features:
    - Mouse click to open/close
    - Arrow keys to navigate when open
    - Keyboard support (up/down to cycle through options)
    - Visual feedback for hover and selection
    """

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        options: list[str],
        default_index: int = 0,
        label: str = "",
    ):
        """Initialize dropdown.

        Args:
            x: X position
            y: Y position
            width: Dropdown width
            height: Dropdown button height
            options: List of option strings
            default_index: Initially selected option index
            label: Optional label text shown before dropdown
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.options = options
        self.selected_index = default_index
        self.label = label

        # State
        self.is_open = False
        self.hovered_index = -1

        # Layout
        self.max_visible_items = 8
        self.item_height = height
        self.dropdown_height = min(len(options), self.max_visible_items) * self.item_height

        # Fonts
        self.font = pygame.font.Font(DEJAVU_FONT_PATH, 20)
        self.font_small = pygame.font.Font(DEJAVU_FONT_PATH, 16)

        # Colors
        self.color_bg = (50, 50, 70)
        self.color_bg_open = (40, 40, 60)
        self.color_hover = (70, 70, 90)
        self.color_selected = (60, 80, 100)
        self.color_text = (255, 255, 255)
        self.color_border = (100, 100, 120)
        self.color_label = (200, 200, 200)

        logger.debug(f"Dropdown created at ({x}, {y}) with {len(options)} options")

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle input event.

        Args:
            event: Pygame event

        Returns:
            True if selection changed
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                mouse_pos = event.pos

                # Check if clicking main button
                if self.rect.collidepoint(mouse_pos):
                    self.is_open = not self.is_open
                    return False

                # Check if clicking dropdown item
                if self.is_open:
                    dropdown_rect = pygame.Rect(
                        self.rect.x,
                        self.rect.y + self.rect.height,
                        self.rect.width,
                        self.dropdown_height,
                    )

                    if dropdown_rect.collidepoint(mouse_pos):
                        # Calculate which item was clicked
                        relative_y = mouse_pos[1] - (self.rect.y + self.rect.height)
                        clicked_index = int(relative_y / self.item_height)

                        if 0 <= clicked_index < len(self.options):
                            old_index = self.selected_index
                            self.selected_index = clicked_index
                            self.is_open = False
                            return old_index != self.selected_index
                    else:
                        # Clicked outside - close dropdown
                        self.is_open = False

        elif event.type == pygame.MOUSEMOTION:
            if self.is_open:
                mouse_pos = event.pos
                dropdown_rect = pygame.Rect(
                    self.rect.x,
                    self.rect.y + self.rect.height,
                    self.rect.width,
                    self.dropdown_height,
                )

                if dropdown_rect.collidepoint(mouse_pos):
                    relative_y = mouse_pos[1] - (self.rect.y + self.rect.height)
                    self.hovered_index = int(relative_y / self.item_height)
                else:
                    self.hovered_index = -1

        elif event.type == pygame.KEYDOWN:
            if self.is_open:
                if event.key == pygame.K_UP:
                    self.selected_index = (self.selected_index - 1) % len(self.options)
                    return True
                elif event.key == pygame.K_DOWN:
                    self.selected_index = (self.selected_index + 1) % len(self.options)
                    return True
                elif (
                    event.key == pygame.K_RETURN
                    or event.key == pygame.K_SPACE
                    or event.key == pygame.K_ESCAPE
                ):
                    self.is_open = False
                    return False

        return False

    def cycle(self, direction: int) -> bool:
        """Cycle through options even when closed.

        Args:
            direction: -1 for previous, 1 for next

        Returns:
            True if selection changed
        """
        if not self.options:
            return False

        old_index = self.selected_index
        self.selected_index = (self.selected_index + direction) % len(self.options)
        return old_index != self.selected_index

    def set_options(self, options: list[str], reset_selection: bool = True) -> None:
        """Update dropdown options.

        Args:
            options: New list of options
            reset_selection: Whether to reset selection to 0
        """
        self.options = options
        self.dropdown_height = min(len(options), self.max_visible_items) * self.item_height

        if reset_selection or self.selected_index >= len(options):
            self.selected_index = 0 if options else -1

        self.is_open = False

    def get_selected(self) -> str | None:
        """Get currently selected option.

        Returns:
            Selected option string or None
        """
        if 0 <= self.selected_index < len(self.options):
            return self.options[self.selected_index]
        return None

    def get_selected_index(self) -> int:
        """Get currently selected option index.

        Returns:
            Selected index
        """
        return self.selected_index

    def draw(self, surface: pygame.Surface) -> None:
        """Draw dropdown.

        Args:
            surface: Surface to draw on
        """
        # Draw label if present
        if self.label:
            label_surf = self.font_small.render(self.label, True, self.color_label)
            surface.blit(label_surf, (self.rect.x, self.rect.y - 25))

        # Draw main button
        button_color = self.color_bg_open if self.is_open else self.color_bg
        pygame.draw.rect(surface, button_color, self.rect)
        pygame.draw.rect(surface, self.color_border, self.rect, 2)

        # Draw selected text
        if 0 <= self.selected_index < len(self.options):
            selected_text = self.options[self.selected_index]
            # Truncate if too long
            if len(selected_text) > 30:
                selected_text = selected_text[:27] + "..."

            text_surf = self.font.render(selected_text, True, self.color_text)
            text_rect = text_surf.get_rect(midleft=(self.rect.x + 10, self.rect.centery))
            surface.blit(text_surf, text_rect)

        # Draw dropdown arrow
        arrow = "▲" if self.is_open else "▼"
        arrow_surf = self.font.render(arrow, True, self.color_text)
        arrow_rect = arrow_surf.get_rect(midright=(self.rect.right - 10, self.rect.centery))
        surface.blit(arrow_surf, arrow_rect)

        # Draw dropdown list if open
        if self.is_open:
            self._draw_dropdown_list(surface)

    def _draw_dropdown_list(self, surface: pygame.Surface) -> None:
        """Draw the expanded dropdown list.

        Args:
            surface: Surface to draw on
        """
        list_y = self.rect.y + self.rect.height

        # Draw background
        list_rect = pygame.Rect(self.rect.x, list_y, self.rect.width, self.dropdown_height)
        pygame.draw.rect(surface, self.color_bg_open, list_rect)
        pygame.draw.rect(surface, self.color_border, list_rect, 2)

        # Draw items
        visible_items = min(len(self.options), self.max_visible_items)

        for i in range(visible_items):
            item_y = list_y + i * self.item_height
            item_rect = pygame.Rect(self.rect.x, item_y, self.rect.width, self.item_height)

            # Highlight selected or hovered
            if i == self.selected_index:
                pygame.draw.rect(surface, self.color_selected, item_rect)
            elif i == self.hovered_index:
                pygame.draw.rect(surface, self.color_hover, item_rect)

            # Draw item text
            item_text = self.options[i]
            if len(item_text) > 30:
                item_text = item_text[:27] + "..."

            text_surf = self.font.render(item_text, True, self.color_text)
            text_rect = text_surf.get_rect(midleft=(item_rect.x + 10, item_rect.centery))
            surface.blit(text_surf, text_rect)

        # Show scroll indicator if more items
        if len(self.options) > self.max_visible_items:
            scroll_text = f"... +{len(self.options) - self.max_visible_items} more"
            scroll_surf = self.font_small.render(scroll_text, True, self.color_label)
            surface.blit(scroll_surf, (self.rect.x + 10, list_y + self.dropdown_height - 20))
