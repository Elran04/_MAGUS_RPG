"""Equipment Panel Coordinator.

Coordinates interaction between equipment slots panel and inventory panel.
Handles:
- Slot selection -> inventory highlighting
- Item click -> equip in selected slot
- Auto-unequip logic
"""

from __future__ import annotations

import pygame
from typing import TYPE_CHECKING

from .equipment_slots_panel import EquipmentSlotsPanel
from .inventory_panel import InventoryPanel

if TYPE_CHECKING:
    from application.game_context import GameContext


class EquipmentPanelCoordinator:
    """Coordinates equipment and inventory panels."""

    def __init__(
        self,
        context: "GameContext",
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

    def set_data(self, equipment: dict[str, str | list], inventory: list[dict] | dict[str, int]) -> None:
        """Set data for both panels.
        
        Args:
            equipment: Current equipment configuration
            inventory: Inventory items (list of dicts or dict mapping id->qty)
        """
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
                        self.current_inventory[item_id] = self.current_inventory.get(item_id, 0) + qty
                elif isinstance(item, str):
                    self.current_inventory[item] = self.current_inventory.get(item, 0) + 1
        
        self.equipment_panel.set_initial(equipment)
        self.inventory_panel.set_data(self.current_inventory, equipment)

    def _on_item_clicked(self, item_id: str, category: str) -> None:
        """Handle item click from inventory.
        
        Args:
            item_id: Item identifier
            category: Item category
        """
        selected_slot = self.equipment_panel.get_selected_slot()
        if not selected_slot:
            return
        
        # Check if item is in inventory
        if item_id not in self.current_inventory or self.current_inventory[item_id] <= 0:
            return
        
        # Determine how many items to equip
        # For stackable ammunition ("lőszer" category), move entire stack
        qty_to_equip = 1
        if self._is_stackable_ammunition(item_id):
            qty_to_equip = self.current_inventory[item_id]
        
        # Equip the item with validation
        success, message, auto_unequipped = self.equipment_panel.equip_item(selected_slot, item_id, qty_to_equip)
        
        if not success:
            # Log the reason for failure
            from logger.logger import get_logger
            logger = get_logger(__name__)
            logger.info(f"Cannot equip {item_id} in {selected_slot}: {message}")
            return
        
        # Remove items from inventory
        qty_to_remove = qty_to_equip
        
        # Remove item(s) from inventory
        self.current_inventory[item_id] -= qty_to_remove
        if self.current_inventory[item_id] <= 0:
            del self.current_inventory[item_id]
        
        # Return auto-unequipped item to inventory (if any)
        if auto_unequipped:
            self._return_item_to_inventory(auto_unequipped)
        
        # Update inventory panel with new equipment state
        self.inventory_panel.set_data(
            self.current_inventory,
            self.equipment_panel.get_equipment()
        )

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
        """Handle events for both panels.
        
        Args:
            event: Pygame event
            
        Returns:
            True if event was handled
        """
        # Check for right-click removal before passing to equipment panel
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            # Check if right-click is on a slot
            for slot, rect in self.equipment_panel.slot_rects.items():
                if rect.collidepoint(event.pos):
                    # Get current item before removal
                    current_equipment = self.equipment_panel.get_equipment()
                    current_item = current_equipment.get(slot)
                    
                    # Check if slot has an item (can be string or dict)
                    has_item = False
                    if isinstance(current_item, str) and current_item:
                        has_item = True
                    elif isinstance(current_item, dict) and current_item.get("id"):
                        has_item = True
                    
                    if has_item:
                        # Remove the item
                        success, removed_id, qty = self.equipment_panel.remove_item(slot)
                        
                        if success and removed_id:
                            # Return item(s) to inventory with quantity
                            self._return_item_to_inventory(removed_id, qty)
                            
                            # Update inventory panel
                            self.inventory_panel.set_data(
                                self.current_inventory,
                                self.equipment_panel.get_equipment()
                            )
                            return True
        
        # Equipment panel
        equipment_changed, slot_clicked = self.equipment_panel.handle_event(event)
        
        if slot_clicked:
            # Update inventory highlighting
            self.inventory_panel.set_selected_slot(slot_clicked)
            return True
        
        if equipment_changed:
            # Update inventory panel
            self.inventory_panel.set_data(
                self.current_inventory,
                self.equipment_panel.get_equipment()
            )
            return True
        
        # Inventory panel
        handled, item_id, category = self.inventory_panel.handle_event(event)
        if handled and item_id:
            # Item was clicked and equipped - trigger persistence
            return True
        return handled

    def draw(self, surface: pygame.Surface) -> None:
        """Draw both panels.
        
        Args:
            surface: Surface to draw on
        """
        self.equipment_panel.draw(surface)
        self.inventory_panel.draw(surface)
