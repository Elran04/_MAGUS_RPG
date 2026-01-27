"""
Unit information popup display - Migrated to new architecture.

Shows detailed unit stats when right-clicking on a unit using new domain entities.
Tab-based UI for organized information display.
"""

import pygame
from config import HEIGHT, UI_ACTIVE, UI_BORDER, UI_INACTIVE, UI_TEXT, WIDTH
from domain.entities import Unit
from domain.mechanics.weapon_wielding import get_wielding_info
from logger.logger import get_logger

from .popup_style import PopupStyle
from .tab_attributes import draw_attributes
from .tab_conditions import draw_conditions
from .tab_equipment import draw_equipment
from .tab_skills import draw_skills
from .tab_stats import draw_combat_stats, draw_health_section
from .tab_weapons import draw_weapons

logger = get_logger(__name__)


class UnitInfoPopup:
    """
    Popup window for displaying detailed unit information with tabs.

    Clean architecture principles:
    - Accepts domain entities (Unit) not raw dicts
    - Pure presentation logic, no game state manipulation
    - Uses domain mechanics for calculations (wielding, stamina)
    """

    def __init__(self, context=None):
        self.visible = False
        self.unit: Unit | None = None
        self.context = context  # Game context for repository access
        self.popup_rect: pygame.Rect | None = None
        self.cached_wield_info = None  # Cache to avoid recalculating every frame
        self.current_tab = "stats"  # "stats", "attributes", "equipment", "skills", "conditions"
        self.tab_buttons = []  # Will store tab button rects
        self.style = PopupStyle()

    def show(self, unit: Unit) -> None:
        """Show popup for the given unit."""
        self.visible = True
        self.unit = unit
        self.current_tab = "stats"  # Reset to first tab
        self.refresh_cached_wield_info()
        logger.debug(f"Showing unit info popup for {unit.name}")

    def hide(self) -> None:
        """Hide the popup."""
        self.visible = False
        self.unit = None
        self.cached_wield_info = None

    def toggle(self, unit: Unit) -> None:
        """Toggle popup visibility for the given unit."""
        if self.visible and self.unit == unit:
            self.hide()
        else:
            self.show(unit)

    def refresh_cached_wield_info(self) -> None:
        """Refresh cached wielding info based on current unit and weapon."""
        if not self.unit or not self.unit.weapon:
            self.cached_wield_info = None
            return

        weapon = self.unit.weapon

        # Only get wielding info if weapon has wield_mode attribute
        # (not all weapons have variable wielding modes)
        if not hasattr(weapon, "wield_mode"):
            self.cached_wield_info = None
            return

        wield_mode = getattr(weapon, "wield_mode", None)
        if not wield_mode:
            self.cached_wield_info = None
            return

        # Get wielding info for weapons with wielding modes
        try:
            self.cached_wield_info = get_wielding_info(
                self.unit,
                weapon,
                wield_mode,
                strength_req=getattr(weapon, "strength_required", 0),
                dex_req=getattr(weapon, "dexterity_required", 0),
            )
        except Exception:
            # If wielding info fails, just skip it
            self.cached_wield_info = None

    def handle_click(self, mx: int, my: int) -> bool:
        """
        Handle click within popup (e.g., tab switching).
        Returns True if click was handled.
        """
        if not self.visible:
            return False

        # Check tab button clicks
        for tab_name, tab_rect in self.tab_buttons:
            if tab_rect.collidepoint(mx, my):
                self.current_tab = tab_name
                logger.debug(f"Switched to tab: {tab_name}")
                return True

        return False

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the popup on screen."""
        if not self.visible or not self.unit:
            return

        # Popup dimensions
        popup_width = self.style.width
        popup_height = self.style.height
        popup_x = (WIDTH - popup_width) // 2
        popup_y = (HEIGHT - popup_height) // 2

        self.popup_rect = pygame.Rect(popup_x, popup_y, popup_width, popup_height)

        # Semi-transparent background overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, self.style.overlay_alpha))
        screen.blit(overlay, (0, 0))

        # Popup background
        pygame.draw.rect(
            screen, self.style.bg_color, self.popup_rect, border_radius=self.style.border_radius
        )
        pygame.draw.rect(
            screen, UI_BORDER, self.popup_rect, width=3, border_radius=self.style.border_radius
        )

        # Draw content
        y_offset = popup_y + 15
        x_left = popup_x + self.style.padding
        x_right = popup_x + popup_width - self.style.padding

        # Title - Unit Name
        title_text = self.style.title_font.render(self.unit.name, True, (255, 215, 0))
        screen.blit(title_text, (x_left, y_offset))
        y_offset += 40

        # Draw tabs
        y_offset = self._draw_tabs(screen, x_left, x_right, y_offset)
        y_offset += self.style.tab_margin_bottom

        # Draw content based on selected tab
        if self.current_tab == "stats":
            y_offset = self._draw_stats_tab(screen, x_left, x_right, y_offset)
        elif self.current_tab == "attributes":
            y_offset = self._draw_attributes_tab(screen, x_left, x_right, y_offset)
        elif self.current_tab == "weapons":
            y_offset = self._draw_weapons_tab(screen, x_left, x_right, y_offset)
        elif self.current_tab == "armor":
            y_offset = self._draw_armor_tab(screen, x_left, x_right, y_offset)
        elif self.current_tab == "skills":
            y_offset = self._draw_skills_tab(screen, x_left, x_right, y_offset)
        elif self.current_tab == "conditions":
            y_offset = self._draw_conditions_tab(screen, x_left, x_right, y_offset)

        # Close instruction
        close_surface = self.style.small_font.render(
            "(Click outside window to close)", True, (150, 150, 150)
        )
        close_rect = close_surface.get_rect()
        close_rect.bottom = popup_y + popup_height - self.style.close_text_bottom_margin
        close_rect.right = popup_x + popup_width - self.style.padding
        screen.blit(close_surface, close_rect)

    def _draw_tabs(self, screen: pygame.Surface, x_left: int, x_right: int, y: int) -> int:
        """Draw tab buttons. Returns new y offset."""
        tabs = [
            ("stats", "Stats"),
            ("attributes", "Attributes"),
            ("weapons", "Weapons"),
            ("armor", "Armor"),
            ("skills", "Skills"),
            ("conditions", "Conditions"),
        ]

        tab_width = (x_right - x_left) // len(tabs)
        self.tab_buttons = []

        for i, (tab_id, tab_label) in enumerate(tabs):
            tab_x = x_left + (i * tab_width)
            tab_rect = pygame.Rect(tab_x, y, tab_width - self.style.tab_gap, self.style.tab_height)
            self.tab_buttons.append((tab_id, tab_rect))

            # Tab background
            is_active = self.current_tab == tab_id
            tab_color = UI_ACTIVE if is_active else UI_INACTIVE
            pygame.draw.rect(screen, tab_color, tab_rect, border_radius=5)
            pygame.draw.rect(screen, UI_BORDER, tab_rect, width=2, border_radius=5)

            # Tab label
            label_text = self.style.small_font.render(tab_label, True, UI_TEXT)
            label_rect = label_text.get_rect(center=tab_rect.center)
            screen.blit(label_text, label_rect)

        return y + self.style.tab_height + self.style.line_gap

    def _draw_stats_tab(self, screen: pygame.Surface, x_left: int, x_right: int, y: int) -> int:
        """Draw stats tab content (Health and Combat). Returns new y offset."""
        # Health/Fatigue Points
        y = draw_health_section(self.unit, screen, self.style, x_left, y)
        y += self.style.section_gap

        # Combat Stats
        y = draw_combat_stats(self.unit, screen, self.style, x_left, y, self.context)
        y += self.style.section_gap

        return y

    def _draw_attributes_tab(self, screen: pygame.Surface, x_left: int, x_right: int, y: int) -> int:
        """Draw attributes tab content (all character properties). Returns new y offset."""
        y = draw_attributes(self.unit, screen, self.style, x_left, y)
        return y

    def _draw_weapons_tab(self, screen: pygame.Surface, x_left: int, x_right: int, y: int) -> int:
        """Draw weapons tab content. Returns new y offset."""
        y = draw_weapons(self.unit, screen, self.style, x_left, x_right, y, self.context)
        return y

    def _draw_armor_tab(self, screen: pygame.Surface, x_left: int, x_right: int, y: int) -> int:
        """Draw armor tab content. Returns new y offset."""
        y = draw_equipment(self.unit, screen, self.style, x_left, x_right, y, self.context)
        return y

    def _draw_skills_tab(self, screen: pygame.Surface, x_left: int, x_right: int, y: int) -> int:
        """Draw skills tab content. Returns new y offset."""
        y = draw_skills(self.unit, screen, self.style, x_left, x_right, y)
        return y

    def _draw_conditions_tab(self, screen: pygame.Surface, x_left: int, x_right: int, y: int) -> int:
        """Draw conditions tab content. Returns new y offset."""
        y = draw_conditions(self.unit, screen, self.style, x_left, y)
        return y

    def is_click_outside(self, mx: int, my: int) -> bool:
        """Check if mouse click is outside the popup area."""
        if not self.visible or not self.popup_rect:
            return False
        return not self.popup_rect.collidepoint(mx, my)
