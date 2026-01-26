"""
Action panel for battle screen.

Left sidebar with action buttons for combat controls.
"""

import pygame
from config import UI_ACTIVE, UI_BG, UI_BORDER, UI_INACTIVE, UI_TEXT
from logger.logger import get_logger

logger = get_logger(__name__)


class DropdownMenu:
    """Dropdown menu for selecting special attacks."""

    def __init__(self, x: int, y: int, width: int, height: int, label: str):
        """Initialize dropdown menu.

        Args:
            x: X position
            y: Y position
            width: Dropdown width
            height: Item height
            label: Button label
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.height = height
        self.width = width
        self.expanded = False
        self.items = [
            ("Charge", "charge"),
        ]
        self.selected_item = None
        self.hovered_item = None

    def toggle(self) -> None:
        """Toggle dropdown expansion."""
        self.expanded = not self.expanded

    def get_expanded_rect(self) -> pygame.Rect:
        """Get bounding rect when expanded (including all items)."""
        total_height = self.height * (len(self.items) + 1)
        return pygame.Rect(self.rect.x, self.rect.y, self.rect.width, total_height)

    def update_hover(self, mouse_pos: tuple[int, int]) -> None:
        """Update hover state.

        Args:
            mouse_pos: Mouse position (x, y)
        """
        if not self.expanded:
            return

        expanded = self.get_expanded_rect()
        if not expanded.collidepoint(mouse_pos):
            self.hovered_item = None
            return

        # Check which item is hovered (skip button row, start from first item)
        item_y = self.rect.y + self.height
        for i, (label, _) in enumerate(self.items):
            item_rect = pygame.Rect(
                self.rect.x, item_y + i * self.height, self.rect.width, self.height
            )
            if item_rect.collidepoint(mouse_pos):
                self.hovered_item = i
                return

        self.hovered_item = None

    def is_clicked(self, mouse_pos: tuple[int, int]) -> str | None:
        """Check if dropdown or item was clicked.

        Args:
            mouse_pos: Mouse position (x, y)

        Returns:
            Selected item key if item clicked, "toggle" if button clicked, None otherwise
        """
        if self.rect.collidepoint(mouse_pos):
            if not self.expanded:
                return "toggle"
            # If expanded and clicked on button, collapse
            return "toggle"

        if self.expanded:
            expanded = self.get_expanded_rect()
            if expanded.collidepoint(mouse_pos):
                item_y = self.rect.y + self.height
                for i, (_, key) in enumerate(self.items):
                    item_rect = pygame.Rect(
                        self.rect.x, item_y + i * self.height, self.rect.width, self.height
                    )
                    if item_rect.collidepoint(mouse_pos):
                        self.selected_item = key
                        self.expanded = False
                        return key

        return None

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        """Draw the dropdown.

        Args:
            surface: Surface to draw on
            font: Font for text
        """
        # Draw button
        bg_color = UI_ACTIVE if self.expanded else UI_INACTIVE
        border_color = (100, 180, 255) if self.expanded else UI_BORDER
        border_width = 3 if self.expanded else 1

        pygame.draw.rect(surface, bg_color, self.rect)
        pygame.draw.rect(surface, border_color, self.rect, border_width)

        # Draw label with dropdown arrow
        arrow = "▼" if self.expanded else "▶"
        text_color = (255, 255, 255) if self.expanded else UI_TEXT
        label_surface = font.render(f"{self.label} {arrow}", True, text_color)
        label_rect = label_surface.get_rect(center=self.rect.center)
        surface.blit(label_surface, label_rect)

        # Draw items if expanded
        if self.expanded:
            item_y = self.rect.y + self.height
            for i, (item_label, _) in enumerate(self.items):
                item_rect = pygame.Rect(
                    self.rect.x, item_y + i * self.height, self.rect.width, self.height
                )

                # Highlight hovered item
                if self.hovered_item == i:
                    item_bg = (50, 50, 60)
                else:
                    item_bg = (30, 30, 40)

                pygame.draw.rect(surface, item_bg, item_rect)
                pygame.draw.rect(surface, UI_BORDER, item_rect, 1)

                # Draw item label
                item_surface = font.render(item_label, True, UI_TEXT)
                item_label_rect = item_surface.get_rect(center=item_rect.center)
                surface.blit(item_surface, item_label_rect)


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
        self.font_stat = pygame.font.Font(None, 16)

        # Current unit stats
        self.current_unit_name: str | None = None
        self.current_ap = 0
        self.current_ep = 0
        self.current_fp = 0
        self.current_stamina = 0
        self.max_ep = 100
        self.max_fp = 100
        self.max_stamina = 100
        self.current_round = 1

        # Combat log
        self.combat_message: str | None = None
        self.combat_message_timer = 0

        # Buttons
        self.buttons: list[ActionButton] = []
        self.special_attacks_dropdown: DropdownMenu | None = None
        self._create_buttons()

        logger.debug(f"ActionPanel initialized ({width}x{height})")

    def _create_buttons(self) -> None:
        """Create action buttons."""
        padding = 15
        button_width = self.width - 2 * padding
        button_height = 50
        start_y = 130  # Leave space for stats section (round + name + 4 bars)

        actions = [
            ("Move", "M"),
            ("Attack", "A"),
            ("Special", "S"),
            ("Switch Weapon", "W"),
            ("Inspect", "I"),
            ("Rotate CCW", "Q"),
            ("Rotate CW", "E"),
            ("End Turn", "Space"),
        ]

        for i, (label, hotkey) in enumerate(actions):
            y = start_y + i * (button_height + 10)
            button = ActionButton(padding, y, button_width, button_height, label, hotkey)
            self.buttons.append(button)
            # Create special attacks dropdown after "Special" button
            if label == "Special":
                self.special_attacks_dropdown = DropdownMenu(
                    padding, y + button_height + 5, button_width, button_height, "Special Attacks"
                )

    def set_active_mode(self, mode: str, special_active: bool = False) -> None:
        """Set which button should be highlighted as active.

        Args:
            mode: Current action mode ("move", "attack", "idle", etc.)
            special_active: True if a special attack is active (highlights Special)
        """
        mode_map = {
            "move": "Move",
            "attack": "Attack",
            "inspect": "Inspect",
        }

        target_label = "Special" if special_active else mode_map.get(mode, "")
        for button in self.buttons:
            button.active = button.label == target_label

    def set_unit_stats(
        self,
        unit_name: str,
        ap: int,
        ep: int,
        fp: int,
        stamina: int = 0,
        max_ep: int = 100,
        max_fp: int = 100,
        max_stamina: int = 100,
        round_num: int = 1,
    ) -> None:
        """Set current unit stats for display.

        Args:
            unit_name: Unit name
            ap: Action points remaining
            ep: Endurance (physical) current
            fp: Fatigue (stamina) current
            stamina: Stamina current
            max_ep: Maximum EP value
            max_fp: Maximum FP value
            max_stamina: Maximum stamina value
            round_num: Current round number
        """
        self.current_unit_name = unit_name
        self.current_ap = ap
        self.current_ep = ep
        self.current_fp = fp
        self.current_stamina = stamina
        self.max_ep = max_ep
        self.max_fp = max_fp
        self.max_stamina = max_stamina
        self.current_round = round_num

    def set_combat_message(self, message: str | None) -> None:
        """Set combat message to display.

        Args:
            message: Combat message text or None to clear
        """
        self.combat_message = message
        self.combat_message_timer = 600 if message else 0  # 5 seconds at 60fps

    def update_combat_message(self) -> None:
        """Update combat message timer."""
        if self.combat_message_timer > 0:
            self.combat_message_timer -= 1
            if self.combat_message_timer <= 0:
                self.combat_message = None

    def handle_mouse_motion(self, mouse_pos: tuple[int, int]) -> None:
        """Update button hover states.

        Args:
            mouse_pos: Absolute mouse position (x, y)
        """
        for button in self.buttons:
            button.update_hover(mouse_pos)
        if self.special_attacks_dropdown:
            self.special_attacks_dropdown.update_hover(mouse_pos)

    def handle_click(self, mouse_pos: tuple[int, int]) -> str | None:
        """Handle mouse click on panel.

        Args:
            mouse_pos: Absolute mouse position (x, y)

        Returns:
            Action name if button/item clicked, None otherwise
        """
        # Only handle clicks within panel area
        if mouse_pos[0] >= self.width:
            return None

        # Check special attacks dropdown first
        if self.special_attacks_dropdown:
            result = self.special_attacks_dropdown.is_clicked(mouse_pos)
            if result == "toggle":
                self.special_attacks_dropdown.toggle()
                return None
            elif result and result != "toggle":
                logger.debug(f"Special attack selected: {result}")
                return f"special_attack_{result}"

        for button in self.buttons:
            if button.is_clicked(mouse_pos):
                logger.debug(f"Action button clicked: {button.label}")
                action_name = button.label.lower().replace(" ", "_")
                # Don't trigger action for "Special" button, just collapse dropdown
                if action_name == "special":
                    if self.special_attacks_dropdown:
                        self.special_attacks_dropdown.expanded = False
                    return None
                return action_name

        return None

    def _draw_colored_text(self, text: str, center_x: int, y: int, font: pygame.font.Font) -> None:
        """Draw text with color tag support.

        Supports tags: <white>text</white>, <purple>text</purple>, <red>text</red>
        Default color is yellow (255, 220, 100).

        Args:
            text: Text with optional color tags
            center_x: Center x coordinate
            y: Y coordinate
            font: Font to use
        """
        import re

        # Color definitions
        colors = {
            "white": (255, 255, 255),
            "purple": (200, 100, 255),
            "red": (255, 100, 100),
        }
        default_color = (255, 220, 100)

        # Parse color tags and render segments
        x_offset = 0
        segments = re.split(r"(<white>.*?</white>|<purple>.*?</purple>|<red>.*?</red>)", text)

        # Calculate total width first to center properly
        total_width = 0
        for segment in segments:
            if segment:
                temp_text = re.sub(r"<[^>]+>|</[^>]+>", "", segment)
                seg_width = font.size(temp_text)[0]
                total_width += seg_width

        start_x = center_x - total_width // 2
        current_x = start_x

        # Draw each segment
        for segment in segments:
            if not segment:
                continue

            # Check for color tags
            color = default_color
            clean_text = segment
            for color_name, color_val in colors.items():
                tag_pattern = f"<{color_name}>(.*?)</{color_name}>"
                match = re.search(tag_pattern, segment)
                if match:
                    color = color_val
                    clean_text = match.group(1)
                    break

            # Render segment
            seg_surface = font.render(clean_text, True, color)
            seg_rect = seg_surface.get_rect(topleft=(current_x, y))
            self.surface.blit(seg_surface, seg_rect)
            current_x += seg_rect.width

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

        # Draw unit stats (top)
        self._draw_unit_stats()

        # Draw buttons
        for button in self.buttons:
            button.draw(self.surface, self.font_button)

        # Draw special attacks dropdown (below Special button)
        if self.special_attacks_dropdown:
            self.special_attacks_dropdown.draw(self.surface, self.font_button)

        # Draw separator before combat log (static position with space for 4 lines)
        log_y = self.height - 108  # 30 for help + 78 for 4 lines (4*18 + padding)
        separator_y = log_y - 5
        pygame.draw.line(
            self.surface, (80, 80, 90), (10, separator_y), (self.width - 10, separator_y), 1
        )

        # Draw combat message if present
        if self.combat_message:
            msg_lines = self.combat_message.split("\n")
            msg_y = log_y
            for line in msg_lines:
                self._draw_colored_text(line, self.width // 2, msg_y, self.font_small)
                msg_y += 18

        # Draw separator before help text
        help_y = self.height - 30
        separator_y = help_y - 10
        pygame.draw.line(
            self.surface, (80, 80, 90), (10, separator_y), (self.width - 10, separator_y), 1
        )

        # Draw help text at bottom
        help_text = self.font_small.render("ESC - Menu", True, (150, 150, 160))
        help_rect = help_text.get_rect(centerx=self.width // 2, top=help_y)
        self.surface.blit(help_text, help_rect)

        # Blit panel to main screen (at left edge)
        screen.blit(self.surface, (0, 0))

    def _draw_unit_stats(self) -> None:
        """Draw current unit stats at top of panel."""
        x = 10
        y = 5
        line_height = 18

        # Round number
        round_surf = self.font_small.render(f"Round {self.current_round}", True, (200, 200, 100))
        self.surface.blit(round_surf, (x, y))

        y += line_height + 2

        # Unit name and active indicator
        if self.current_unit_name:
            name_surf = self.font_small.render(self.current_unit_name[:22], True, (100, 200, 255))
            self.surface.blit(name_surf, (x, y))
            # Active indicator
            active_surf = self.font_stat.render("<<", True, (100, 255, 100))
            self.surface.blit(active_surf, (self.width - 20, y + 2))

            y += line_height + 2

            # Draw compact bars for stats
            bar_width = 150
            bar_height = 8
            grey = (160, 160, 160)

            # AP - just number, no bar
            ap_text = self.font_stat.render(f"AP: {self.current_ap}", True, grey)
            self.surface.blit(ap_text, (x, y))

            y += line_height

            # FP - yellow bar, grey label
            fp_label = self.font_stat.render("FP", True, grey)
            self.surface.blit(fp_label, (x, y))
            pygame.draw.rect(self.surface, (60, 60, 60), (x + 30, y + 2, bar_width, bar_height))
            if self.current_fp > 0 and self.max_fp > 0:
                fp_fill = int((self.current_fp / self.max_fp) * bar_width)
                pygame.draw.rect(
                    self.surface, (200, 200, 100), (x + 30, y + 2, fp_fill, bar_height)
                )
            # Display value text
            fp_text = self.font_stat.render(f"{self.current_fp}/{self.max_fp}", True, grey)
            self.surface.blit(fp_text, (x + 190, y))

            y += line_height

            # ÉP - red bar, grey label
            ep_label = self.font_stat.render("ÉP", True, grey)
            self.surface.blit(ep_label, (x, y))
            pygame.draw.rect(self.surface, (60, 60, 60), (x + 30, y + 2, bar_width, bar_height))
            if self.current_ep > 0 and self.max_ep > 0:
                ep_fill = int((self.current_ep / self.max_ep) * bar_width)
                pygame.draw.rect(
                    self.surface, (200, 100, 100), (x + 30, y + 2, ep_fill, bar_height)
                )
            # Display value text
            ep_text = self.font_stat.render(f"{self.current_ep}/{self.max_ep}", True, grey)
            self.surface.blit(ep_text, (x + 190, y))

            y += line_height

            # Stamina - green bar, grey label
            stamina_label = self.font_stat.render("STA", True, grey)
            self.surface.blit(stamina_label, (x, y))
            pygame.draw.rect(self.surface, (60, 60, 60), (x + 30, y + 2, bar_width, bar_height))
            if self.current_stamina > 0 and self.max_stamina > 0:
                stamina_fill = int((self.current_stamina / self.max_stamina) * bar_width)
                pygame.draw.rect(
                    self.surface, (150, 200, 100), (x + 30, y + 2, stamina_fill, bar_height)
                )
            # Display value text
            stamina_text = self.font_stat.render(
                f"{self.current_stamina}/{self.max_stamina}", True, grey
            )
            self.surface.blit(stamina_text, (x + 190, y))

            # Draw separator line after stats
            y += line_height + 5
            pygame.draw.line(self.surface, (80, 80, 90), (10, y), (self.width - 10, y), 1)
