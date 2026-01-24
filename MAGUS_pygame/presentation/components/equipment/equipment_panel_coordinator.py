"""Equipment Panel Coordinator.

Coordinates interaction between equipment slots panel and inventory panel.
Handles:
- Slot selection -> inventory highlighting
- Item click -> equip in selected slot
- Auto-unequip logic
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from .equipment_slots_panel import EquipmentSlotsPanel
from .inventory_panel import InventoryPanel

if TYPE_CHECKING:
    from application.game_context import GameContext


class EquipmentPanelCoordinator:
    """Coordinates equipment and inventory panels."""

    def __init__(
        self,
        context: GameContext,
        font: pygame.font.Font,
        title_font: pygame.font.Font,
        screen_width: int,
        screen_height: int,
    ) -> None:
        """Initialize coordinator.

        Args:
            context: Game context
            font: Regular font
            title_font: Title font
            screen_width: Screen width
            screen_height: Screen height
        """
        self.context = context

        # Calculate layout
        padding = 20
        panel_width = (screen_width - 3 * padding) // 2
        panel_height = screen_height - 2 * padding

        # Equipment slots panel (left)
        self.equipment_panel = EquipmentSlotsPanel(
            x=padding,
            y=padding,
            width=panel_width,
            height=panel_height,
            font=font,
            context=context,
        )

        # Inventory panel (right)
        self.inventory_panel = InventoryPanel(
            x=padding * 2 + panel_width,
            y=padding,
            width=panel_width,
            height=panel_height,
            font=font,
            title_font=title_font,
            context=context,
        )

        # Wire up item click callback
        self.inventory_panel.on_item_click = self._on_item_clicked

        # Current inventory tracking (dict format: item_id -> qty)
        self.current_inventory: dict[str, int] = {}

    def set_data(
        self, equipment: dict[str, str | list], inventory: list[dict] | dict[str, int], unit=None
    ) -> None:
        """Set data for both panels, and set unit for validation/highlighting.
        Ensures equipped items are removed from inventory by simulating equip logic."""
        # Store inventory in dict format
        if isinstance(inventory, dict):
            self.current_inventory = inventory.copy()
        else:
            # Convert list format to dict
            self.current_inventory = {}
            for item in inventory:
                if isinstance(item, dict):
                    item_id = item.get("id")
                    qty = item.get("qty", 1)
                    if item_id:
                        self.current_inventory[item_id] = (
                            self.current_inventory.get(item_id, 0) + qty
                        )
                elif isinstance(item, str):
                    self.current_inventory[item] = self.current_inventory.get(item, 0) + 1

        # Clear equipment panel first
        self.equipment_panel.set_initial({})

        # Actually equip items using the same logic as user interaction
        for slot, value in equipment.items():
            if isinstance(value, list):
                # For slots like 'armor' (list of item_ids)
                for item_id in value:
                    if item_id and self.current_inventory.get(item_id, 0) > 0:
                        # Use equip_item to ensure inventory is decremented
                        self.equipment_panel.equip_item(slot, item_id, 1)
                        self.current_inventory[item_id] -= 1
                        if self.current_inventory[item_id] <= 0:
                            del self.current_inventory[item_id]
            elif isinstance(value, str):
                item_id = value
                if item_id and self.current_inventory.get(item_id, 0) > 0:
                    self.equipment_panel.equip_item(slot, item_id, 1)
                    self.current_inventory[item_id] -= 1
                    if self.current_inventory[item_id] <= 0:
                        del self.current_inventory[item_id]

        self.inventory_panel.set_data(self.current_inventory, self.equipment_panel.get_equipment())
        if unit is not None:
            self.inventory_panel.set_unit(unit)

    def _on_item_clicked(self, item_id: str, category: str) -> None:
        """Handle item click from inventory. Enforce Slot enum strictly."""
        import logging

        logger = logging.getLogger(
            "magus_pygame.presentation.components.equipment.equipment_panel_coordinator"
        )
        selected_slot = self.equipment_panel.get_selected_slot()
        if not selected_slot:
            logger.error("[on_item_clicked] No slot selected.")
            return

        # Check if item is in inventory
        if item_id not in self.current_inventory or self.current_inventory[item_id] <= 0:
            logger.error(f"[on_item_clicked] Item {item_id} not in inventory or qty <= 0.")
            return

        # Determine how many items to equip
        qty_to_equip = 1
        if self._is_stackable_ammunition(item_id):
            qty_to_equip = self.current_inventory[item_id]

        # Check if slot already has an item, return it to inventory before equipping
        current_equipment = self.equipment_panel.get_equipment()
        old_item = current_equipment.get(selected_slot)
        if old_item:
            if isinstance(old_item, str):
                self._return_item_to_inventory(old_item)
            elif isinstance(old_item, dict):
                old_id = old_item.get("id")
                old_qty = old_item.get("qty", 1)
                if old_id:
                    self._return_item_to_inventory(old_id, old_qty)

        # Equip the item with validation
        # Always use Slot enum for selected_slot, fail if not possible
        try:
            from domain.value_objects.weapon_type_check import Slot

            slot_enum = (
                Slot(selected_slot) if not isinstance(selected_slot, Slot) else selected_slot
            )
        except Exception as e:
            logger.error(
                f"[on_item_clicked] Invalid slot '{selected_slot}' could not be converted to Slot enum: {e}"
            )
            return
        result = self.equipment_panel.equip_item(slot_enum, item_id, qty_to_equip)
        if not result.success:
            from logger.logger import get_logger

            logger = get_logger(__name__)
            logger.info(f"Cannot equip {item_id} in {selected_slot}: {result.message}")
            return
        qty_to_remove = qty_to_equip
        self.current_inventory[item_id] -= qty_to_remove
        if self.current_inventory[item_id] <= 0:
            del self.current_inventory[item_id]
        if result.details:
            self._return_item_to_inventory(result.details)
        self.inventory_panel.set_data(self.current_inventory, self.equipment_panel.get_equipment())

    def get_current_inventory(self) -> dict[str, int]:
        """Get current inventory items.

        Returns:
            Dictionary mapping item_id to quantity
        """
        return self.current_inventory.copy()

    def get_equipment(self) -> dict[str, str | list]:
        """Get current equipment configuration.

        Returns:
            Equipment dictionary
        """
        return self.equipment_panel.get_equipment()

    def _return_item_to_inventory(self, item_id: str, quantity: int = 1) -> None:
        """Return an item to inventory when unequipped.

        Args:
            item_id: Item identifier
            quantity: Quantity to return
        """
        if item_id:
            self.current_inventory[item_id] = self.current_inventory.get(item_id, 0) + quantity

    def _is_stackable_ammunition(self, item_id: str) -> bool:
        """Check if item is stackable ammunition (lőszer category).

        Args:
            item_id: Item identifier

        Returns:
            True if item is stackable ammunition
        """
        repo = self.context.equipment_validation_service.equipment_repo

        # Check general equipment for ammunition
        general_items = repo.load_general_equipment()
        for item in general_items:
            if item.get("id") == item_id:
                category = item.get("category", "").lower()
                stackable = item.get("stackable", False)
                # Check for "lőszer" category and stackable flag
                return category == "lőszer" and stackable

        return False

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle events for both panels, including armor equip/remove by clicking/hovering."""
        # --- Armor slot hover/click logic ---
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Left click: add armor
            if event.button == 1:
                for slot, rect in self.equipment_panel.slot_rects.items():
                    if slot == "armor" and rect.collidepoint(event.pos):
                        mouse_pos = pygame.mouse.get_pos()
                        armor_items = self.inventory_panel.items.get("armor", [])
                        armor_rect = self.inventory_panel.category_rects.get("armor")
                        if armor_rect and armor_rect.collidepoint(mouse_pos):
                            y = (
                                mouse_pos[1]
                                - armor_rect.y
                                - 30
                                + self.inventory_panel.scroll_offsets["armor"]
                            )
                            idx = y // 22
                            if 0 <= idx < len(armor_items):
                                item_id, qty = armor_items[idx]
                                result = self.inventory_panel._is_item_eligible(item_id, "armor")
                                if result.success and qty > 0:
                                    self.current_inventory[item_id] -= 1
                                    if self.current_inventory[item_id] <= 0:
                                        del self.current_inventory[item_id]
                                    self.equipment_panel.equip_item("armor", item_id, 1)
                                    self.inventory_panel.set_data(
                                        self.current_inventory, self.equipment_panel.get_equipment()
                                    )
                                    return True
            # Right click: remove equipped item (armor or other slots)
            elif event.button == 3:
                # Remove specific armor item if right-clicked in armor list area
                armor_rect = self.equipment_panel.armor_list_rect
                if armor_rect and armor_rect.collidepoint(event.pos):
                    armor_list = self.equipment_panel.equipment.get("armor", [])
                    if isinstance(armor_list, list) and armor_list:
                        # Calculate which armor item is clicked
                        y = (
                            event.pos[1]
                            - armor_rect.y
                            + self.equipment_panel.armor_scroll_offset
                            - 8
                        )
                        idx = y // 22
                        if 0 <= idx < len(armor_list):
                            removed_id = armor_list[idx]
                            # Remove the specific armor item
                            armor_list.pop(idx)
                            self.equipment_panel.equipment["armor"] = armor_list
                            self.equipment_panel._validate()
                            self._return_item_to_inventory(removed_id)
                            self.inventory_panel.set_data(
                                self.current_inventory, self.equipment_panel.get_equipment()
                            )
                            return True
                # Handle right-click unequip for other slots
                for slot, rect in self.equipment_panel.slot_rects.items():
                    if slot != "armor" and rect.collidepoint(event.pos):
                        # Remove item from this slot
                        success, removed_id, qty = self.equipment_panel.remove_item(slot)
                        if success and removed_id:
                            self._return_item_to_inventory(removed_id, qty)
                            self.inventory_panel.set_data(
                                self.current_inventory, self.equipment_panel.get_equipment()
                            )
                            return True

        # Equipment panel (other slots)
        equipment_changed, slot_clicked = self.equipment_panel.handle_event(event)
        if slot_clicked:
            self.inventory_panel.set_selected_slot(slot_clicked)
            return True
        if equipment_changed:
            self.inventory_panel.set_data(
                self.current_inventory, self.equipment_panel.get_equipment()
            )
            return True

        # Inventory panel
        handled, item_id, category = self.inventory_panel.handle_event(event)
        if handled and item_id:
            return True
        return handled

    def draw(self, surface: pygame.Surface) -> None:
        """Draw both panels.

        Args:
            surface: Surface to draw on
        """
        self.equipment_panel.draw(surface)
        self.inventory_panel.draw(surface)
