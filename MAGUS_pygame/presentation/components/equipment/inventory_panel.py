"""Inventory Panel - Updated for new equipment system.

Shows available items categorized by type with eligibility highlighting.
Supports clicking items to equip them in selected slot.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import pygame
from logger.logger import get_logger

if TYPE_CHECKING:
    from application.game_context import GameContext

logger = get_logger(__name__)
# Item categories
CATEGORY_WEAPONS = "weapons_shields"
CATEGORY_ARMOR = "armor"
CATEGORY_GENERAL = "general"


class InventoryPanel:
    def set_unit(self, unit) -> None:
        """Set the current unit for validation/highlighting only."""
        self.unit = unit

    """Displays inventory items with eligibility highlighting.

    Features:
    - Categorized item display (weapons, armor, general)
    - Highlight eligible items in green when slot selected
    - Click item to equip in selected slot
    - Scrollable lists
    """

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        font: pygame.font.Font,
        title_font: pygame.font.Font,
        context: GameContext,
        bg_color=(25, 25, 35),
        border_color=(70, 70, 90),
        text_color=(230, 230, 240),
        highlight_color=(100, 200, 100),
        invalid_color=(200, 80, 80),
    ) -> None:
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.title_font = title_font
        self.context = context

        # Colors
        self.bg_color = bg_color
        self.border_color = border_color
        self.text_color = text_color
        self.highlight_color = highlight_color
        self.invalid_color = invalid_color

        # Inventory data
        self.items: dict[str, list[tuple[str, int]]] = {
            CATEGORY_WEAPONS: [],
            CATEGORY_ARMOR: [],
            CATEGORY_GENERAL: [],
        }

        # Current equipment state (for eligibility checking)
        self.current_equipment: dict[str, str | list] = {}

        # Selected slot (for highlighting eligible items)
        self.selected_slot: str | None = None

        # Scroll offsets per category
        self.scroll_offsets: dict[str, int] = {
            CATEGORY_WEAPONS: 0,
            CATEGORY_ARMOR: 0,
            CATEGORY_GENERAL: 0,
        }

        # Layout
        self.category_rects: dict[str, pygame.Rect] = {}
        self._layout()

        # Item click callback
        self.on_item_click: Callable[[str, str], None] | None = None

        # Category cache to avoid repeated lookups
        self._category_cache: dict[str, str] = {}

        # Selected wield mode for variable wield mode weapons
        self.selected_wield_mode: str | None = None  # 'one_handed' or 'two_handed'

    def _layout(self) -> None:
        """Calculate layout for category sections."""
        section_h = (self.rect.height - 60) // 3
        x = self.rect.x + 10
        y = self.rect.y + 40
        w = self.rect.width - 20

        self.category_rects[CATEGORY_WEAPONS] = pygame.Rect(x, y, w, section_h)
        y += section_h + 10

        self.category_rects[CATEGORY_ARMOR] = pygame.Rect(x, y, w, section_h)
        y += section_h + 10

        self.category_rects[CATEGORY_GENERAL] = pygame.Rect(x, y, w, section_h)

    def set_data(
        self, inventory_items: list[dict] | dict[str, int], equipment: dict[str, str | list]
    ) -> None:
        """Set inventory items and current equipment (unit is set separately for validation)."""
        self.current_equipment = equipment

        # Categorize items
        self.items = {
            CATEGORY_WEAPONS: [],
            CATEGORY_ARMOR: [],
            CATEGORY_GENERAL: [],
        }

        # Handle different inventory formats
        if isinstance(inventory_items, dict):
            # Format: {item_id: qty}
            # Need to look up category from repository
            for item_id, qty in inventory_items.items():
                if not item_id:
                    continue

                # Try to determine category from equipment repository
                category = self._get_item_category(item_id)

                # Map categories
                if category in ["weapons_and_shields", "weapon", "shield"]:
                    self.items[CATEGORY_WEAPONS].append((item_id, qty))
                elif category == "armor":
                    self.items[CATEGORY_ARMOR].append((item_id, qty))
                else:
                    self.items[CATEGORY_GENERAL].append((item_id, qty))
        else:
            # Format: list of dicts
            for item in inventory_items:
                if isinstance(item, str):
                    # Handle legacy format: list of item IDs
                    item_id = item
                    category = self._get_item_category(item_id)
                    qty = 1
                else:
                    # Handle dict format
                    item_id = item.get("id")
                    category = item.get("category", "general")
                    qty = item.get("qty", 1)

                if not item_id:
                    continue

                # Map categories
                if category in ["weapons_and_shields", "weapon", "shield"]:
                    self.items[CATEGORY_WEAPONS].append((item_id, qty))
                elif category == "armor":
                    self.items[CATEGORY_ARMOR].append((item_id, qty))
                else:
                    self.items[CATEGORY_GENERAL].append((item_id, qty))

    def set_selected_slot(self, slot: str | None) -> None:
        """Set the currently selected equipment slot for highlighting. Enforce Slot enum strictly."""
        if slot is not None:
            try:
                from domain.value_objects.weapon_type_check import Slot

                if not isinstance(slot, Slot):
                    self.selected_slot = Slot(slot)
                else:
                    self.selected_slot = slot
            except Exception:
                self.selected_slot = None
        else:
            self.selected_slot = None

    def show_wield_mode_dropdown(self, item_id: str) -> None:
        """Show dropdown for variable wield mode weapons."""
        repo = self.context.equipment_repo
        weapon = repo.find_weapon_by_id(item_id)
        if not weapon or weapon.get("wield_mode", "") != "variable":
            self.selected_wield_mode = None
            return
        # UI code to show dropdown (pseudo-code, replace with your UI framework)
        # Example: self.selected_wield_mode = user_selection_from_dropdown(["one_handed", "two_handed"])
        # For now, default to two_handed
        self.selected_wield_mode = "two_handed"

    def _get_item_category(self, item_id: str) -> str:
        """Determine item category from repository.

        Args:
            item_id: Item identifier

        Returns:
            Category string
        """
        # Check cache first
        if item_id in self._category_cache:
            return self._category_cache[item_id]

        repo = self.context.equipment_validation_service.equipment_repo
        category = "general"

        # Check weapons (load all and search without logging each miss)
        weapons = repo.load_weapons()
        if any(w.get("id") == item_id for w in weapons):
            category = "weapons_and_shields"
        else:
            # Check armor
            armor_list = repo.load_armor()
            if any(a.get("id") == item_id for a in armor_list):
                category = "armor"
            else:
                # Check general
                general = repo.load_general_equipment()
                if any(g.get("id") == item_id for g in general):
                    category = "general"

        # Cache the result
        self._category_cache[item_id] = category
        return category

    def _is_item_eligible(self, item_id: str, category: str, weapon: dict | None = None):
        from application.equipment_validation_service import ValidationResult

        if not self.selected_slot:
            return ValidationResult(False, "No slot selected")
        unit = getattr(self, "unit", None)
        slot = self.selected_slot
        selected_wield_mode = self.selected_wield_mode

        # Always use Slot enum for slot, fail if not possible
        try:
            from domain.value_objects.weapon_type_check import Slot

            slot_enum = Slot(slot) if not isinstance(slot, Slot) else slot
        except Exception as e:
            logger.error(
                f"[_is_item_eligible] Invalid slot '{slot}' could not be converted to Slot enum: {e}"
            )
            return ValidationResult(False, "Invalid slot")

        weapon_slots = [Slot.MAIN_HAND, Slot.OFF_HAND, Slot.WEAPON_QUICK_1, Slot.WEAPON_QUICK_2]
        # Normalize category for weapon slots
        normalized_category = category
        if category == "weapons_shields":
            normalized_category = "weapons_and_shields"
        if slot_enum in weapon_slots:
            if normalized_category not in ["weapons_and_shields", "weapon", "shield"]:
                return ValidationResult(False, "Not a weapon")
        if slot_enum in [Slot.QUICK_ACCESS_1, Slot.QUICK_ACCESS_2]:
            if normalized_category != "general":
                return ValidationResult(False, "Not a general item")

        return self.context.equipment_validation_service.is_item_eligible(
            unit, slot_enum, item_id, selected_wield_mode
        )

    def handle_event(self, event: pygame.event.Event) -> tuple[bool, str | None, str | None]:
        """Handle events.

        Args:
            event: Pygame event

        Returns:
            Tuple of (handled, item_id, category) - item_id is set if item was clicked
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Check which category was clicked
            for category, rect in self.category_rects.items():
                if rect.collidepoint(event.pos):
                    # Find which item was clicked
                    items = self.items.get(category, [])
                    if not items:
                        continue

                    # Calculate item position
                    item_y = rect.y + 30 - self.scroll_offsets[category]
                    item_h = 22

                    for item_id, qty in items:
                        item_rect = pygame.Rect(rect.x, item_y, rect.width, item_h)
                        if item_rect.collidepoint(event.pos):
                            # Check if item is eligible before allowing click
                            result = self._is_item_eligible(item_id, category)
                            if result.success:
                                # Item clicked and eligible
                                if self.on_item_click:
                                    self.on_item_click(item_id, category)
                                return True, item_id, category
                            else:
                                # Item clicked but not eligible - just ignore
                                return True, None, None
                        item_y += item_h

        # Scroll handling
        if event.type == pygame.MOUSEWHEEL:
            for category, rect in self.category_rects.items():
                if rect.collidepoint(pygame.mouse.get_pos()):
                    self.scroll_offsets[category] = max(
                        0, self.scroll_offsets[category] - event.y * 20
                    )
                    return True, None, None

        return False, None, None

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the inventory panel.

        Args:
            surface: Surface to draw on
        """
        # Background
        pygame.draw.rect(surface, self.bg_color, self.rect)
        pygame.draw.rect(surface, self.border_color, self.rect, 1)

        # Title
        title = self.title_font.render("Inventory", True, self.text_color)
        surface.blit(title, (self.rect.x + 10, self.rect.y + 10))

        # Draw each category
        self._draw_category(surface, CATEGORY_WEAPONS, "Weapons & Shields")
        self._draw_category(surface, CATEGORY_ARMOR, "Armor")
        self._draw_category(surface, CATEGORY_GENERAL, "General Items")

    def _draw_category(self, surface: pygame.Surface, category: str, title: str) -> None:
        """Draw a category section.

        Args:
            surface: Surface to draw on
            category: Category identifier
            title: Display title
        """
        rect = self.category_rects.get(category)
        if not rect:
            return

        # Section background
        pygame.draw.rect(surface, (30, 30, 40), rect, border_radius=4)
        pygame.draw.rect(surface, self.border_color, rect, 1, border_radius=4)

        # Section title
        title_surf = self.font.render(title, True, (200, 200, 255))
        surface.blit(title_surf, (rect.x + 8, rect.y + 6))

        # Items
        items = self.items.get(category, [])
        if not items:
            empty = self.font.render("(empty)", True, (120, 120, 130))
            surface.blit(empty, (rect.x + 12, rect.y + 32))
            return

        # Create clipping surface for scrolling
        content_rect = pygame.Rect(rect.x, rect.y + 30, rect.width, rect.height - 30)
        clip_surface = surface.subsurface(content_rect)

        y = -self.scroll_offsets[category]
        mouse_pos = pygame.mouse.get_pos()

        # Cache for weapon lookups
        weapon_cache = {}

        # Determine which slot is currently selected and use it for eligibility
        selected_slot = self.selected_slot
        for item_id, qty in items:
            # Only lookup weapon if in weapons category
            weapon = None
            if category == CATEGORY_WEAPONS:
                if item_id in weapon_cache:
                    weapon = weapon_cache[item_id]
                else:
                    weapon = self.context.equipment_repo.find_weapon_by_id(item_id)
                    weapon_cache[item_id] = weapon
            # Patch: If selected_slot is not a weapon slot, but we're drawing weapons, use MAIN_HAND as default for eligibility
            slot_for_eligibility = selected_slot
            if category == CATEGORY_WEAPONS and selected_slot is None:
                try:
                    from domain.value_objects.weapon_type_check import Slot

                    slot_for_eligibility = Slot.MAIN_HAND
                except Exception:
                    slot_for_eligibility = "main_hand"
            # Patch: Temporarily override self.selected_slot for eligibility check
            orig_selected_slot = self.selected_slot
            self.selected_slot = slot_for_eligibility
            result = self._is_item_eligible(item_id, category, weapon)
            self.selected_slot = orig_selected_slot

            # Determine color
            if self.selected_slot and result.success:
                color = self.highlight_color
            elif self.selected_slot and not result.success:
                color = self.invalid_color
            else:
                color = self.text_color

            # Get item name (convert internal category to repository category)
            repo_category = category
            if category == CATEGORY_WEAPONS:
                repo_category = "weapons_and_shields"
            elif category == CATEGORY_ARMOR:
                repo_category = "armor"
            else:
                repo_category = "general"

            item_name = self.context.get_equipment_name(item_id, repo_category)
            if qty > 1:
                display_text = f"• {item_name} x{qty}"
            else:
                display_text = f"• {item_name}"

            # --- Wield mode hint logic ---
            wield_mode_hint = ""
            unit = getattr(self, "unit", None)
            if category == CATEGORY_WEAPONS and weapon:
                wield_mode_hint = self.context.equipment_validation_service.get_wield_mode_hint(
                    unit, item_id, weapon
                )
            # --- End wield mode hint logic ---

            if wield_mode_hint:
                display_text += f" {wield_mode_hint}"

            # Check hover
            item_rect = pygame.Rect(0, y, content_rect.width, 22)
            hover = item_rect.collidepoint(
                mouse_pos[0] - content_rect.x, mouse_pos[1] - content_rect.y
            )

            # Draw background on hover
            if hover and 0 <= y < content_rect.height:
                hover_rect = pygame.Rect(2, y, content_rect.width - 4, 20)
                pygame.draw.rect(clip_surface, (50, 50, 60), hover_rect, border_radius=3)

            # Draw item text
            if 0 <= y < content_rect.height:
                item_surf = self.font.render(display_text, True, color)
                clip_surface.blit(item_surf, (8, y + 2))

            y += 22
