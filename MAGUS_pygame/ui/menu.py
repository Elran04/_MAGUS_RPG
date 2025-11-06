"""
Game menu system for MAGUS Pygame.
Provides main menu, pause menu, and settings.
"""

from typing import Optional, Callable, Tuple
import pygame
from enum import Enum, auto


class MenuState(Enum):
    """Menu states."""
    MAIN_MENU = auto()
    PAUSE_MENU = auto()
    SETTINGS = auto()
    CLOSED = auto()


class MenuItem:
    """Represents a menu item."""

    def __init__(
        self,
        text: str,
        action: Optional[Callable[[], None]] = None,
        enabled: bool = True
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
    """Game menu system."""

    def __init__(self, screen_width: int, screen_height: int) -> None:
        """Initialize the menu.
        
        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.state = MenuState.MAIN_MENU
        
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

    def _create_main_menu(self) -> list[MenuItem]:
        """Create main menu items.
        
        Returns:
            List of menu items
        """
        return [
            MenuItem("New Game", action=lambda: self._start_new_game()),
            MenuItem("Load Game", action=lambda: self._load_game()),
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
                item.action()

    def _update_hover(self, mouse_pos: Tuple[int, int]) -> None:
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

    def _click_at_position(self, mouse_pos: Tuple[int, int]) -> None:
        """Handle click at position.
        
        Args:
            mouse_pos: Mouse position (x, y)
        """
        items = self.get_current_items()
        for item in items:
            if item.is_hovered and item.enabled and item.action:
                item.action()
                break

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the menu.
        
        Args:
            surface: Surface to draw on
        """
        if self.state == MenuState.CLOSED:
            return
            
        # Draw semi-transparent background
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill(self.color_bg)
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

    def _draw_menu_item(
        self,
        surface: pygame.Surface,
        item: MenuItem,
        index: int,
        y: int
    ) -> None:
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

    def open_main_menu(self) -> None:
        """Open the main menu."""
        self.state = MenuState.MAIN_MENU
        self.selected_index = 0

    def open_pause_menu(self) -> None:
        """Open the pause menu."""
        self.state = MenuState.PAUSE_MENU
        self.selected_index = 0

    def close(self) -> None:
        """Close the menu."""
        self.state = MenuState.CLOSED

    def is_open(self) -> bool:
        """Check if menu is open.
        
        Returns:
            True if menu is not closed
        """
        return self.state != MenuState.CLOSED

    # Menu action handlers
    def _start_new_game(self) -> None:
        """Start a new game."""
        self.close()
        # TODO: Implement new game logic

    def _load_game(self) -> None:
        """Load a saved game."""
        # TODO: Implement load game logic
        pass

    def _save_game(self) -> None:
        """Save the current game."""
        # TODO: Implement save game logic
        pass

    def _open_settings(self) -> None:
        """Open settings menu."""
        self.state = MenuState.SETTINGS
        self.selected_index = 0

    def _close_settings(self) -> None:
        """Close settings and return to previous menu."""
        self.state = MenuState.PAUSE_MENU
        self.selected_index = 0

    def _return_to_main_menu(self) -> None:
        """Return to main menu."""
        self.state = MenuState.MAIN_MENU
        self.selected_index = 0

    def _quit_game(self) -> None:
        """Quit the game."""
        pygame.event.post(pygame.event.Event(pygame.QUIT))
