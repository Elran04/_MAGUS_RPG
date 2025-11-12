"""Equipment Slots Panel - Redesigned for new equipment system.

Displays equipment slots with proper validation and categorization:
- Main hand / Off hand with validation
- Quick access weapon slots (2)
- Armor list with add/remove
- Quick access item slots (2)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from application.game_context import GameContext

# Equipment slot definitions
WEAPON_SLOTS = ["main_hand", "off_hand", "weapon_quick_1", "weapon_quick_2"]
QUICK_ACCESS_SLOTS = ["quick_access_1", "quick_access_2"]


class EquipmentSlotsPanel:
    """Panel displaying equipment slots for a single unit with validation.

    Layout:
    - Main hand (clickable)
    - Off hand (clickable, grayed if invalid)
    - Weapon Quick Access 1 & 2 (clickable)
    - Armor list (scrollable, with add/remove buttons)
    - Quick Access Items 1 & 2 (clickable)
    """

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        font: pygame.font.Font,
        context: GameContext,
        bg_color=(25, 25, 35),
        border_color=(70, 70, 90),
        slot_color=(55, 65, 95),
        slot_disabled=(40, 40, 50),
        slot_hover=(75, 85, 115),
        slot_error=(95, 55, 55),
        text_color=(230, 230, 240),
        text_disabled=(100, 100, 110),
    ) -> None:
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.context = context

        # Colors
        self.bg_color = bg_color
        self.border_color = border_color
        self.slot_color = slot_color
        self.slot_disabled = slot_disabled
        self.slot_hover = slot_hover
        self.slot_error = slot_error
        self.text_color = text_color
        self.text_disabled = text_disabled

        # Equipment state
        # Note: Slots can contain:
        #   - String: single item ID (e.g., "sword_01")
        #   - Dict: item with quantity (e.g., {"id": "arrow", "qty": 20}) for stackable items
        #   - List: for armor slot only
        self.equipment: dict[str, str | dict | list] = {
            "main_hand": "",
            "off_hand": "",
            "weapon_quick_1": "",
            "weapon_quick_2": "",
            "armor": [],  # List of armor piece IDs
            "quick_access_1": "",
            "quick_access_2": "",
        }

        # Validation warnings
        self.warnings: dict[str, str] = {}

        # Selected slot (for highlighting inventory)
        self.selected_slot: str | None = None

        # UI layout
        self.slot_rects: dict[str, pygame.Rect] = {}
        self.armor_list_rect: pygame.Rect | None = None
        self.armor_scroll_offset = 0

        self._layout_slots()

    def _layout_slots(self) -> None:
        """Calculate positions for all slots and buttons."""
        padding = 12
        slot_h = 50
        gap = 8
        x = self.rect.x + padding
        y = self.rect.y + padding
        slot_w = self.rect.width - 2 * padding

        # Section: Weapons
        section_label_h = 30
        y += section_label_h

        # Main hand
        self.slot_rects["main_hand"] = pygame.Rect(x, y, slot_w, slot_h)
        y += slot_h + gap

        # Off hand
        self.slot_rects["off_hand"] = pygame.Rect(x, y, slot_w, slot_h)
        y += slot_h + gap * 2

        # Quick access weapons
        quick_w = (slot_w - gap) // 2
        self.slot_rects["weapon_quick_1"] = pygame.Rect(x, y, quick_w, slot_h)
        self.slot_rects["weapon_quick_2"] = pygame.Rect(x + quick_w + gap, y, quick_w, slot_h)
        y += slot_h + gap * 2

        # Section: Armor
        y += section_label_h
        armor_list_h = 150
        self.armor_list_rect = pygame.Rect(x, y, slot_w, armor_list_h)
        y += armor_list_h + gap

        # No add/remove armor buttons; armor managed by coordinator

        # Section: Quick Access Items
        y += section_label_h
        quick_item_w = (slot_w - gap) // 2
        self.slot_rects["quick_access_1"] = pygame.Rect(x, y, quick_item_w, slot_h)
        self.slot_rects["quick_access_2"] = pygame.Rect(
            x + quick_item_w + gap, y, quick_item_w, slot_h
        )

    def set_initial(self, equipment: dict[str, str | list]) -> None:
        """Set initial equipment state.

        Args:
            equipment: Equipment configuration
        """
        # First, reset all slots to empty (prevents carryover from previous unit)
        self.equipment = {
            "main_hand": "",
            "off_hand": "",
            "weapon_quick_1": "",
            "weapon_quick_2": "",
            "armor": [],
            "quick_access_1": "",
            "quick_access_2": "",
        }

        # Then apply incoming equipment (deep copy to avoid sharing references)
        for key in self.equipment:
            if key in equipment:
                value = equipment[key]
                if isinstance(value, list):
                    self.equipment[key] = value.copy()
                else:
                    self.equipment[key] = value

        self._validate()

    def get_equipment(self) -> dict[str, str | list]:
        """Get current equipment configuration.

        Returns:
            Equipment dictionary with all slots (deep copy)
        """
        # Deep copy to avoid sharing list references
        result = {}
        for key, value in self.equipment.items():
            if isinstance(value, list):
                result[key] = value.copy()
            else:
                result[key] = value
        return result

    def equip_item(self, slot: str, item_id: str, quantity: int = 1) -> tuple[bool, str, str]:
        """Equip an item in a slot with validation and auto-unequip logic.

        Args:
            slot: Slot name (main_hand, off_hand, etc.)
            item_id: Item identifier
            quantity: Quantity to equip (for stackable items)

        Returns:
            Tuple of (success: bool, message: str, auto_unequipped_item: str)
            auto_unequipped_item is the item that was removed from off-hand (if any)
        """
        if slot not in self.equipment:
            return False, "Invalid slot", ""

        validation = self.context.equipment_validation_service
        auto_unequipped = ""  # Track auto-removed off-hand item

        # Validate item compatibility for this slot
        if slot == "off_hand":
            main_hand = self.equipment.get("main_hand")
            # Extract item ID (handle both string and dict formats)
            main_hand_id = None
            if isinstance(main_hand, str):
                main_hand_id = main_hand
            elif isinstance(main_hand, dict):
                main_hand_id = main_hand.get("id")

            result = validation.can_equip_offhand(main_hand_id, item_id)
            if not result.success:
                return False, result.message, ""

        elif slot in ["main_hand", "weapon_quick_1", "weapon_quick_2"]:
            # Verify it's actually a weapon or shield (shields allowed in quick slots)
            is_weapon = (
                validation.is_one_handed_weapon(item_id)
                or validation.is_two_handed_weapon(item_id)
                or validation.is_ranged_weapon(item_id)
            )
            is_shield = validation.is_shield(item_id)

            # Main hand: weapons only
            if slot == "main_hand" and not is_weapon:
                return False, "Not a weapon", ""
            # Quick slots: weapons or shields
            elif slot in ["weapon_quick_1", "weapon_quick_2"] and not (is_weapon or is_shield):
                return False, "Not a weapon or shield", ""

        # Handle armor separately (list)
        if slot == "armor":
            armor_list = self.equipment.get("armor", [])
            if not isinstance(armor_list, list):
                armor_list = []
            armor_list.append(item_id)
            self.equipment["armor"] = armor_list
            self._validate()
            return True, "Armor equipped", ""

        # Auto-unequip logic for main hand
        if slot == "main_hand":
            # Check if new weapon is two-handed/ranged
            if validation.is_two_handed_weapon(item_id) or validation.is_ranged_weapon(item_id):
                # Auto-unequip off-hand and track what was removed
                current_offhand = self.equipment.get("off_hand")
                if current_offhand:
                    if isinstance(current_offhand, str) and current_offhand:
                        auto_unequipped = current_offhand
                    elif isinstance(current_offhand, dict) and current_offhand.get("id"):
                        auto_unequipped = current_offhand.get("id")
                    self.equipment["off_hand"] = ""

        # Set item (with quantity if > 1)
        if quantity > 1:
            self.equipment[slot] = {"id": item_id, "qty": quantity}
        else:
            self.equipment[slot] = item_id

        self._validate()
        return True, "Item equipped", auto_unequipped

    def remove_item(self, slot: str) -> tuple[bool, str, int]:
        """Remove an item from a slot.

        Args:
            slot: Slot name

        Returns:
            Tuple of (success: bool, removed_item_id: str, quantity: int)
        """
        if slot not in self.equipment:
            return False, "", 0

        if slot == "armor":
            # Use remove_last_armor for armor list
            success = self.remove_last_armor()
            # TODO: Track which armor was removed
            return success, "", 0

        # Get current item before clearing
        current = self.equipment.get(slot)
        if current:
            if isinstance(current, str):
                # Simple item
                self.equipment[slot] = ""
                self._validate()
                return True, current, 1
            elif isinstance(current, dict) and current.get("id"):
                # Item with quantity
                item_id = current.get("id")
                qty = current.get("qty", 1)
                self.equipment[slot] = ""
                self._validate()
                return True, item_id, qty

        return False, "", 0

    def remove_last_armor(self) -> bool:
        """Remove the last armor piece from the list.

        Returns:
            True if armor was removed
        """
        armor_list = self.equipment.get("armor", [])
        if isinstance(armor_list, list) and armor_list:
            armor_list.pop()
            self.equipment["armor"] = armor_list
            self._validate()
            return True
        return False

    def _validate(self) -> None:
        """Validate equipment and update warnings."""
        self.warnings = self.context.equipment_validation_service.validate_equipment_slots(
            self.equipment
        )

    def _is_offhand_disabled(self) -> bool:
        """Check if off-hand slot should be disabled."""
        main_hand = self.equipment.get("main_hand")
        if not main_hand:
            return False

        # Extract item ID (handle both string and dict formats)
        main_hand_id = main_hand
        if isinstance(main_hand, dict):
            main_hand_id = main_hand.get("id", "")
        elif not isinstance(main_hand, str):
            return False

        validation_service = self.context.equipment_validation_service
        return validation_service.is_two_handed_weapon(
            main_hand_id
        ) or validation_service.is_ranged_weapon(main_hand_id)

    def get_selected_slot(self) -> str | None:
        """Get currently selected slot.

        Returns:
            Selected slot name or None
        """
        return self.selected_slot

    def handle_event(self, event: pygame.event.Event) -> tuple[bool, str | None]:
        """Handle events.

        Args:
            event: Pygame event

        Returns:
            Tuple of (equipment_changed, slot_clicked)
        """
        equipment_changed = False
        slot_clicked = None

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                # Check weapon/item slots
                for slot, rect in self.slot_rects.items():
                    if rect.collidepoint(event.pos):
                        # Don't allow clicking disabled off-hand
                        if slot == "off_hand" and self._is_offhand_disabled():
                            continue

                        # Select this slot
                        self.selected_slot = slot
                        slot_clicked = slot
                        break

                # Mimic add armor button: clicking armor list area selects armor slot
                if self.armor_list_rect and self.armor_list_rect.collidepoint(event.pos):
                    self.selected_slot = "armor"
                    slot_clicked = "armor"

            elif event.button == 3:  # Right click - remove item
                # Check weapon/item slots
                for slot, rect in self.slot_rects.items():
                    if rect.collidepoint(event.pos):
                        equipment_changed = self.remove_item(slot)
                        break

        # Scroll handling
        if event.type == pygame.MOUSEWHEEL:
            if self.armor_list_rect and self.armor_list_rect.collidepoint(pygame.mouse.get_pos()):
                self.armor_scroll_offset = max(0, self.armor_scroll_offset - event.y * 20)

        return equipment_changed, slot_clicked

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the equipment slots panel.

        Args:
            surface: Surface to draw on
        """
        # Background
        pygame.draw.rect(surface, self.bg_color, self.rect)
        pygame.draw.rect(surface, self.border_color, self.rect, 1)

        y = self.rect.y + 12
        mouse_pos = pygame.mouse.get_pos()

        # === WEAPONS SECTION ===
        section_label = self.font.render("Weapons", True, (200, 200, 255))
        surface.blit(section_label, (self.rect.x + 12, y))

        # Main hand
        self._draw_slot(surface, "main_hand", "Main Hand", mouse_pos)

        # Off hand (may be disabled)
        disabled = self._is_offhand_disabled()
        self._draw_slot(surface, "off_hand", "Off Hand", mouse_pos, disabled=disabled)

        # Quick access weapons
        self._draw_slot(surface, "weapon_quick_1", "Quick 1", mouse_pos)
        self._draw_slot(surface, "weapon_quick_2", "Quick 2", mouse_pos)

        # === ARMOR SECTION ===
        armor_y = self.armor_list_rect.y - 30 if self.armor_list_rect else 0
        section_label = self.font.render("Armor", True, (200, 200, 255))
        surface.blit(section_label, (self.rect.x + 12, armor_y))

        self._draw_armor_list(surface)
        # No add/remove armor button drawing; armor managed by coordinator

        # === QUICK ACCESS ITEMS SECTION ===
        qa_y = self.slot_rects["quick_access_1"].y - 30
        section_label = self.font.render("Quick Access", True, (200, 200, 255))
        surface.blit(section_label, (self.rect.x + 12, qa_y))

        self._draw_slot(surface, "quick_access_1", "Item 1", mouse_pos)
        self._draw_slot(surface, "quick_access_2", "Item 2", mouse_pos)

    def _draw_slot(
        self,
        surface: pygame.Surface,
        slot_name: str,
        display_label: str,
        mouse_pos: tuple[int, int],
        disabled: bool = False,
    ) -> None:
        """Draw a single equipment slot.

        Args:
            surface: Surface to draw on
            slot_name: Slot identifier
            display_label: Display label for the slot
            mouse_pos: Current mouse position
            disabled: Whether the slot is disabled
        """
        rect = self.slot_rects.get(slot_name)
        if not rect:
            return

        # Determine slot color
        has_warning = slot_name in self.warnings
        hover = rect.collidepoint(mouse_pos) and not disabled
        is_selected = slot_name == self.selected_slot

        if disabled:
            color = self.slot_disabled
        elif has_warning:
            color = self.slot_error
        elif hover:
            color = self.slot_hover
        else:
            color = self.slot_color

        # Draw slot
        pygame.draw.rect(surface, color, rect, border_radius=6)

        # Draw selection indicator
        if is_selected:
            pygame.draw.rect(surface, (100, 200, 255), rect, 3, border_radius=6)

        # Draw label
        text_color = self.text_disabled if disabled else self.text_color
        label = self.font.render(display_label, True, text_color)
        surface.blit(label, (rect.x + 8, rect.y + 6))

        # Draw value
        value = self.equipment.get(slot_name, "")
        has_item = False
        display_value = "<empty>"

        if isinstance(value, str) and value:
            # Simple string item ID
            display_value = self.context.get_equipment_name(value, "weapons_and_shields")
            has_item = True
        elif isinstance(value, dict) and value.get("id"):
            # Item with quantity
            item_id = value.get("id")
            qty = value.get("qty", 1)
            item_name = self.context.get_equipment_name(item_id, "general")
            display_value = f"{item_name} x{qty}"
            has_item = True

        value_label = self.font.render(display_value, True, (180, 180, 200))
        surface.blit(value_label, (rect.x + 8, rect.y + 26))

        # Show remove hint on hover if item is equipped
        if has_item and hover and not disabled:
            hint = pygame.font.Font(None, 12).render("Right-click to remove", True, (200, 200, 100))
            surface.blit(hint, (rect.x + 8, rect.y + rect.height - 14))

        # Draw warning if present
        if has_warning:
            warning_text = self.warnings[slot_name]
            warning_label = pygame.font.Font(None, 14).render(warning_text, True, (255, 150, 150))
            surface.blit(warning_label, (rect.x + 8, rect.y + 46))

    def _draw_armor_list(self, surface: pygame.Surface) -> None:
        """Draw the armor list area with conflict highlighting.

        Args:
            surface: Surface to draw on
        """
        if not self.armor_list_rect:
            return

        # Background
        pygame.draw.rect(surface, (30, 30, 40), self.armor_list_rect, border_radius=4)
        pygame.draw.rect(surface, self.border_color, self.armor_list_rect, 1, border_radius=4)

        armor_list = self.equipment.get("armor", [])
        if not isinstance(armor_list, list):
            return

        if not armor_list:
            empty = self.font.render("No armor equipped", True, (120, 120, 130))
            surface.blit(empty, (self.armor_list_rect.x + 10, self.armor_list_rect.y + 10))
            return

        # Check for armor conflicts
        _, _, conflicts = self.context.equipment_validation_service.validate_armor_compatibility(
            armor_list
        )

        # Draw armor pieces
        y = self.armor_list_rect.y + 8 - self.armor_scroll_offset
        for armor_id in armor_list:
            if isinstance(armor_id, str):
                # Look up armor name
                armor_name = self.context.get_equipment_name(armor_id, "armor")

                # Determine color based on conflicts
                has_conflict = armor_id in conflicts
                text_color = (255, 100, 100) if has_conflict else self.text_color

                armor_label = self.font.render(f"• {armor_name}", True, text_color)

                # Only draw if visible
                if self.armor_list_rect.y < y < self.armor_list_rect.bottom:
                    surface.blit(armor_label, (self.armor_list_rect.x + 12, y))

                    # Show conflict details on hover
                    if has_conflict:
                        mouse_pos = pygame.mouse.get_pos()
                        item_rect = pygame.Rect(
                            self.armor_list_rect.x, y, self.armor_list_rect.width, 20
                        )
                        if item_rect.collidepoint(mouse_pos):
                            # Show tooltip with conflict info
                            conflict_list = conflicts[armor_id]
                            zones = ", ".join(
                                [zone for _, zone in conflict_list[:3]]
                            )  # Show first 3
                            tooltip = f"Conflicts: {zones}"
                            tooltip_surf = pygame.font.Font(None, 14).render(
                                tooltip, True, (255, 200, 100)
                            )
                            surface.blit(tooltip_surf, (self.armor_list_rect.x + 12, y + 18))

                y += 22

    # No add/remove armor button drawing; armor managed by coordinator
