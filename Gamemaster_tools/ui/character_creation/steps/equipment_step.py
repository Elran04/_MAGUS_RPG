"""
Equipment Step
Handles equipment selection and purchase during character creation.
Coordinator for equipment widgets and services.
"""

from collections.abc import Callable
from typing import Any

from PySide6 import QtCore, QtWidgets
from utils.log.logger import get_logger

from ui.character_creation.services.equipment_loader import EquipmentLoader
from ui.character_creation.services.equipment_service import EquipmentService
from ui.character_creation.widgets.equipment import (
    CurrencyWidget,
    InventoryPanel,
    ShopPanel,
)

logger = get_logger(__name__)


class EquipmentStepWidget(QtWidgets.QWidget):
    """
    Equipment selection and purchase interface.
    Coordinates shop, inventory, and currency widgets with equipment services.
    """

    def __init__(
        self,
        get_character_data: Callable[[], dict[str, Any]],
        get_class_id: Callable[[], str | None],
    ):
        super().__init__()
        self.get_character_data = get_character_data
        self.get_class_id = get_class_id

        # Initialize-once guard: compute and populate only on first entry
        # Subsequent visits to this step will preserve state until editor restart
        self._initialized: bool = False

        # Services
        self.equipment_loader = EquipmentLoader()
        self.equipment_service = EquipmentService()

        # Widgets (created in _build_ui)
        self.shop_panel: ShopPanel | None = None
        self.inventory_panel: InventoryPanel | None = None
        self.currency_widget: CurrencyWidget | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the UI with shop (left) and inventory + currency (right)."""
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(4)

        # Compact title and info
        title = QtWidgets.QLabel("Felszerelés beszerzése")
        title.setStyleSheet("font-weight: bold; font-size: 13px; padding: 2px;")
        main_layout.addWidget(title, stretch=0)

        info = QtWidgets.QLabel(
            "Kezdő felszerelésed már a hátizsákodban van. Vásárolhatsz vagy eladhatsz tárgyakat."
        )
        info.setWordWrap(True)
        info.setStyleSheet("font-size: 10px; color: #666; padding: 2px;")
        main_layout.addWidget(info, stretch=0)

        # Splitter: Shop (left) | Inventory + Currency (right)
        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)

        # Left panel: Shop
        self.shop_panel = ShopPanel()
        self.shop_panel.buy_requested.connect(self._on_buy_item)
        self.shop_panel.bulk_buy_requested.connect(self._on_bulk_buy_item)
        # Provide currency so the shop can validate affordability in dialogs
        self.shop_panel.set_currency_provider(lambda: self.equipment_service.currency_base)
        splitter.addWidget(self.shop_panel)

        # Right panel: Inventory and Currency (vertical layout)
        right_panel = self._build_right_panel()
        splitter.addWidget(right_panel)

        splitter.setSizes([700, 300])  # Shop takes more space
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)

        # Give splitter maximum stretch so it fills remaining space
        main_layout.addWidget(splitter, stretch=1)

    def _build_right_panel(self) -> QtWidgets.QWidget:
        """Build the right panel with inventory (top) and currency (bottom)."""
        panel = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Inventory panel (takes most space)
        self.inventory_panel = InventoryPanel()
        self.inventory_panel.sell_requested.connect(self._on_sell_item)
        layout.addWidget(self.inventory_panel, stretch=1)

        # Currency widget (fixed size at bottom)
        self.currency_widget = CurrencyWidget()
        layout.addWidget(self.currency_widget, stretch=0)

        return panel

    def refresh(self) -> None:
        """Populate shop and starting inventory only once; preserve thereafter."""
        logger.info("Equipment step refresh() called")

        if not self._initialized:
            # Load equipment catalog once
            equipment_data = self.equipment_loader.load_all_equipment()
            if self.shop_panel is not None:
                self.shop_panel.load_equipment(equipment_data)

            # Ensure clean initial state
            self.equipment_service.inventory.clear()
            self.equipment_service.currency_base = 0

            data = self.get_character_data() or {}

            # Get class/spec from the wizard (locked earlier in flow)
            class_id = self.get_class_id()
            spec_id = data.get("Specializáció")

            logger.info(
                f"initializing equipment step - class_id={class_id}, spec_id={spec_id}, data.keys={list(data.keys())}"
            )

            if class_id:
                self._load_starting_equipment(class_id, spec_id)
            else:
                logger.warning("class_id is None, cannot load starting equipment")

            # Mark as initialized to preserve state on subsequent visits
            self._initialized = True

        # Always refresh displays to reflect current state
        self._update_displays()

    def _load_starting_equipment(self, class_id: str, spec_id: str | None) -> None:
        """Load starting equipment and currency from database."""
        starting_items, starting_currency_gold = self.equipment_loader.load_starting_equipment(
            str(class_id), spec_id
        )

        # Set starting currency
        if starting_currency_gold:
            self.equipment_service.set_currency(starting_currency_gold)

        # Add starting items to inventory
        for item_info in starting_items:
            item_type = item_info["type"]
            item_id = item_info["id"]

            # Find the item data
            item_data = self.equipment_loader.find_item_by_id(item_type, item_id)
            if item_data:
                # Map database type to category
                category_map = {
                    "armor": "armor",
                    "weaponandshield": "weapons_and_shields",
                    "general": "general",
                }
                category = category_map.get(item_type, "general")
                self.equipment_service.add_starting_item(item_data, category)
            else:
                logger.warning(f"Starting item not found: {item_type}/{item_id}")

    def _on_buy_item(self, item_data: dict[str, Any], category: str) -> None:
        """Handle buy item request from shop (single unit)."""
        success = self.equipment_service.buy_item(item_data, category)
        if success:
            self._update_displays()
        else:
            # Show error message
            QtWidgets.QMessageBox.warning(
                self,
                "Nincs elég pénz",
                f"Nem elég a pénzed a {item_data.get('name', '???')} megvásárlásához.",
            )

    def _on_bulk_buy_item(self, item_data: dict[str, Any], category: str, quantity: int) -> None:
        """Handle bulk buy request from shop (multiple units)."""
        success = self.equipment_service.buy_item_bulk(item_data, category, quantity)
        if success:
            self._update_displays()
        else:
            QtWidgets.QMessageBox.warning(
                self,
                "Nincs elég pénz",
                (
                    f"Nem elég a pénzed a {quantity}× {item_data.get('name', '???')} megvásárlásához."
                ),
            )

    def _on_sell_item(self, item_id: str) -> None:
        """Handle sell item request from inventory."""
        success = self.equipment_service.sell_item(item_id)
        if success:
            self._update_displays()

    def _update_displays(self) -> None:
        """Update all display widgets."""
        # Update currency
        if self.currency_widget is not None:
            self.currency_widget.set_currency(self.equipment_service.currency_base)

        # Update inventory
        inventory_by_category = self.equipment_service.get_inventory_by_category()
        if self.inventory_panel is not None:
            self.inventory_panel.update_inventory(inventory_by_category)

    def validate(self) -> bool:
        """Validate that the step is complete."""
        # Equipment step is always valid (optional purchases)
        return True

    def get_data(self) -> dict[str, Any]:
        """Get equipment data for character save."""
        return {"Felszerelés": self.equipment_service.get_export_data()}
