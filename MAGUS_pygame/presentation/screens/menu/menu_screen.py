"""
Game menu system for MAGUS Pygame - Migrated to new architecture.

Provides main menu, pause menu, and settings using clean separation of concerns.
"""

from collections.abc import Callable
from enum import Enum, auto

import pygame
from config import MENU_BACKGROUND
from logger.logger import get_logger

logger = get_logger(__name__)


class MenuState(Enum):
    """Menu states."""

    MAIN_MENU = auto()
    PAUSE_MENU = auto()
    SETTINGS = auto()
    CLOSED = auto()


class MenuItem:
    """Represents a menu item."""

    def __init__(
        self, text: str, action: Callable[[], None] | None = None, enabled: bool = True
    ) -> None:
        """Initialize a menu item.

        Args:
            text: Display text
            action: Callback when selected
            enabled: Whether item can be selected
        """
        self.text = text
        self.action = action
        self.enabled = enabled
        self.is_hovered = False


class Menu:
    """
    Game menu system.

    Handles:
    - Main menu (new game, load, settings, quit)
    - Pause menu (resume, save, settings, main menu)
    - Settings menu (placeholder for future settings)

    Clean architecture principles:
    - Pure UI logic, no game state manipulation
    - Actions are callbacks that higher layer handles
    - Self-contained rendering and input handling
    """

    def __init__(self, screen_width: int, screen_height: int) -> None:
        """Initialize the menu.

        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.state = MenuState.MAIN_MENU

        # Track last selected action (for application layer to handle)
        self.last_action: str | None = None

        # Track previous state for proper back navigation
        self.previous_state: MenuState | None = None

        # Load background image
        self.background_image = self._load_background()

        # Fonts
        self.font_title = pygame.font.Font(None, 64)
        self.font_menu = pygame.font.Font(None, 40)

        # Colors
        self.color_bg = (0, 0, 0, 200)  # Semi-transparent black
        self.color_title = (255, 215, 0)  # Gold
        self.color_text = (255, 255, 255)  # White
        self.color_hover = (255, 215, 0)  # Gold
        self.color_disabled = (128, 128, 128)  # Gray

        # Menu items
        self.main_menu_items = self._create_main_menu()
        self.pause_menu_items = self._create_pause_menu()
        self.settings_items = self._create_settings_menu()

        self.selected_index = 0

        logger.info("Menu system initialized")

    def _load_background(self) -> pygame.Surface | None:
        """Load and scale the background image.

        Returns:
            Scaled background surface or None if loading fails
        """
        try:
            # Load image using centralized path from config
            background = pygame.image.load(str(MENU_BACKGROUND)).convert()

            # Scale to screen size while maintaining aspect ratio
            bg_width, bg_height = background.get_size()
            screen_ratio = self.screen_width / self.screen_height
            bg_ratio = bg_width / bg_height

            if bg_ratio > screen_ratio:
                # Background is wider - scale to screen height
                new_height = self.screen_height
                new_width = int(bg_width * (new_height / bg_height))
            else:
                # Background is taller - scale to screen width
                new_width = self.screen_width
                new_height = int(bg_height * (new_width / bg_width))

            background = pygame.transform.scale(background, (new_width, new_height))

            # Center the background if it's larger than screen
            if new_width > self.screen_width or new_height > self.screen_height:
                x_offset = (new_width - self.screen_width) // 2
                y_offset = (new_height - self.screen_height) // 2
                background = background.subsurface(
                    pygame.Rect(x_offset, y_offset, self.screen_width, self.screen_height)
                )

            logger.debug("Menu background loaded successfully")
            return background
        except Exception as e:
            logger.warning(f"Could not load menu background image: {e}")
            return None

    def _create_main_menu(self) -> list[MenuItem]:
        """Create main menu items.

        Returns:
            List of menu items
        """
        return [
            MenuItem("New Game", action=lambda: self._start_new_game()),
            MenuItem("Quick Combat", action=lambda: self._start_quick_combat()),
            MenuItem("Load Game", action=lambda: self._load_game()),
            MenuItem("Scenario Editor", action=lambda: self._open_scenario_editor()),
            MenuItem("Settings", action=lambda: self._open_settings()),
            MenuItem("Quit", action=lambda: self._quit_game()),
        ]

    def _create_pause_menu(self) -> list[MenuItem]:
        """Create pause menu items.

        Returns:
            List of menu items
        """
        return [
            MenuItem("Resume", action=lambda: self.close()),
            MenuItem("Settings", action=lambda: self._open_settings()),
            MenuItem("Save Game", action=lambda: self._save_game()),
            MenuItem("Main Menu", action=lambda: self._return_to_main_menu()),
        ]

    def _create_settings_menu(self) -> list[MenuItem]:
        """Create settings menu items.

        Returns:
            List of menu items
        """
        return [
            MenuItem("Graphics Settings", enabled=False),
            MenuItem("Audio Settings", enabled=False),
            MenuItem("Controls", enabled=False),
            MenuItem("Back", action=lambda: self._close_settings()),
        ]

    def get_current_items(self) -> list[MenuItem]:
        """Get items for current menu state.

        Returns:
            List of current menu items
        """
        if self.state == MenuState.MAIN_MENU:
            return self.main_menu_items
        elif self.state == MenuState.PAUSE_MENU:
            return self.pause_menu_items
        elif self.state == MenuState.SETTINGS:
            return self.settings_items
        return []

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle input events.

        Args:
            event: Pygame event
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self._move_selection(-1)
            elif event.key == pygame.K_DOWN:
                self._move_selection(1)
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                self._select_current_item()
            elif event.key == pygame.K_ESCAPE:
                if self.state == MenuState.PAUSE_MENU:
                    self.close()
                elif self.state == MenuState.SETTINGS:
                    self._close_settings()

        elif event.type == pygame.MOUSEMOTION:
            self._update_hover(event.pos)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                self._click_at_position(event.pos)

    def _move_selection(self, direction: int) -> None:
        """Move menu selection.

        Args:
            direction: -1 for up, 1 for down
        """
        items = self.get_current_items()
        if not items:
            return

        self.selected_index += direction
        self.selected_index = max(0, min(len(items) - 1, self.selected_index))

        # Skip disabled items
        if not items[self.selected_index].enabled:
            self._move_selection(direction)

    def _select_current_item(self) -> None:
        """Select the currently highlighted item."""
        items = self.get_current_items()
        if 0 <= self.selected_index < len(items):
            item = items[self.selected_index]
            if item.enabled and item.action:
                logger.debug(f"Menu item selected: {item.text}")
                item.action()

    def _update_hover(self, mouse_pos: tuple[int, int]) -> None:
        """Update hover state based on mouse position.

        Args:
            mouse_pos: Mouse position (x, y)
        """
        items = self.get_current_items()
        start_y = self.screen_height // 2 - (len(items) * 50) // 2

        for i, item in enumerate(items):
            item_y = start_y + i * 60
            item.is_hovered = (
                self.screen_width // 2 - 150 <= mouse_pos[0] <= self.screen_width // 2 + 150
                and item_y <= mouse_pos[1] <= item_y + 50
            )
            # Update selected index when hovering over enabled items
            if item.is_hovered and item.enabled:
                self.selected_index = i

    def _click_at_position(self, mouse_pos: tuple[int, int]) -> None:
        """Handle click at position.

        Args:
            mouse_pos: Mouse position (x, y)
        """
        items = self.get_current_items()
        for item in items:
            if item.is_hovered and item.enabled and item.action:
                logger.debug(f"Menu item clicked: {item.text}")
                item.action()
                break

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the menu.

        Args:
            surface: Surface to draw on
        """
        if self.state == MenuState.CLOSED:
            return

        # Draw background image if available
        if self.background_image:
            surface.blit(self.background_image, (0, 0))
        else:
            # Fallback to black background
            surface.fill((0, 0, 0))

        # Draw semi-transparent overlay for better text readability
        if self.state == MenuState.PAUSE_MENU:
            # Darker overlay for pause menu
            overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
            overlay.fill(self.color_bg)
            surface.blit(overlay, (0, 0))
        else:
            # Light overlay for main menu to keep background visible
            overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))  # Light semi-transparent black
            surface.blit(overlay, (0, 0))

        # Draw title
        title_text = "MAGUS RPG"
        if self.state == MenuState.PAUSE_MENU:
            title_text = "PAUSED"
        elif self.state == MenuState.SETTINGS:
            title_text = "SETTINGS"

        title_surface = self.font_title.render(title_text, True, self.color_title)
        title_rect = title_surface.get_rect(center=(self.screen_width // 2, 100))
        surface.blit(title_surface, title_rect)

        # Draw menu items
        items = self.get_current_items()
        start_y = self.screen_height // 2 - (len(items) * 50) // 2

        for i, item in enumerate(items):
            self._draw_menu_item(surface, item, i, start_y + i * 60)

    def _draw_menu_item(self, surface: pygame.Surface, item: MenuItem, index: int, y: int) -> None:
        """Draw a single menu item.

        Args:
            surface: Surface to draw on
            item: Menu item to draw
            index: Item index
            y: Y position
        """
        # Determine color
        if not item.enabled:
            color = self.color_disabled
        elif item.is_hovered or index == self.selected_index:
            color = self.color_hover
        else:
            color = self.color_text

        # Render text
        text_surface = self.font_menu.render(item.text, True, color)
        text_rect = text_surface.get_rect(center=(self.screen_width // 2, y))

        # Draw selection indicator
        if index == self.selected_index:
            indicator = self.font_menu.render(">", True, self.color_hover)
            surface.blit(indicator, (text_rect.left - 40, y - text_surface.get_height() // 2))

        surface.blit(text_surface, text_rect)

    # Public API methods

    def open_main_menu(self) -> None:
        """Open the main menu."""
        self.state = MenuState.MAIN_MENU
        self.selected_index = 0
        logger.info("Opened main menu")

    def open_pause_menu(self) -> None:
        """Open the pause menu."""
        self.state = MenuState.PAUSE_MENU
        self.selected_index = 0
        logger.info("Opened pause menu")

    def close(self) -> None:
        """Close the menu."""
        self.state = MenuState.CLOSED
        logger.info("Closed menu")

    def reset_action(self) -> None:
        """Reset the last action."""
        self.last_action = None

    def is_open(self) -> bool:
        """Check if menu is open.

        Returns:
            True if menu is not closed
        """
        return self.state != MenuState.CLOSED

    def get_last_action(self) -> str | None:
        """Get the last selected action.

        Application layer should check this to handle menu selections.

        Returns:
            Last action string or None
        """
        return self.last_action

    # Menu action handlers (emit events to application layer)

    def _start_new_game(self) -> None:
        """Start a new game."""
        self.last_action = "new_game"
        logger.info("New game requested")

    def _start_quick_combat(self) -> None:
        """Start quick combat with hardcoded units."""
        self.last_action = "quick_combat"
        logger.info("Quick combat requested")

    def _load_game(self) -> None:
        """Load a saved game."""
        self.last_action = "load_game"
        logger.info("Load game requested")
        # TODO: Implement load game logic in application layer

    def _open_scenario_editor(self) -> None:
        """Open the scenario editor screen."""
        self.last_action = "scenario_editor"
        logger.info("Scenario editor requested")

    def _save_game(self) -> None:
        """Save the current game."""
        self.last_action = "save_game"
        logger.info("Save game requested")
        # TODO: Implement save game logic in application layer

    def _open_settings(self) -> None:
        """Open settings menu."""
        self.previous_state = self.state
        self.state = MenuState.SETTINGS
        self.selected_index = 0
        logger.debug("Settings menu opened")

    def _close_settings(self) -> None:
        """Close settings and return to previous menu."""
        # Return to whichever menu opened settings
        if self.previous_state:
            self.state = self.previous_state
            self.previous_state = None
        else:
            # Fallback to main menu if no previous state tracked
            self.state = MenuState.MAIN_MENU
        self.selected_index = 0
        logger.debug("Settings menu closed")

    def _return_to_main_menu(self) -> None:
        """Return to main menu."""
        self.state = MenuState.MAIN_MENU
        self.selected_index = 0
        logger.info("Returned to main menu")

    def _quit_game(self) -> None:
        """Quit the game."""
        logger.info("Quit game requested")
        pygame.event.post(pygame.event.Event(pygame.QUIT))
