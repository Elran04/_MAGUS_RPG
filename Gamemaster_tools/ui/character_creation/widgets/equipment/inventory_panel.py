"""
Inventory Panel Widget
Displays character's inventory organized by category with sell functionality.
"""

from typing import Any

from PySide6 import QtCore, QtWidgets
from utils.log.logger import get_logger

logger = get_logger(__name__)


class InventoryPanel(QtWidgets.QWidget):
    """Inventory panel showing character's items."""

    # Signal emitted when user wants to sell an item
    # Args: item_id
    sell_requested = QtCore.Signal(str)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.inventory_list: QtWidgets.QListWidget | None = None
        self.sell_button: QtWidgets.QPushButton | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the inventory UI."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Inventory title
        title = QtWidgets.QLabel("Hátizsák")
        title.setStyleSheet("font-weight: bold; font-size: 12px; padding: 4px;")
        layout.addWidget(title)

        # Inventory list
        self.inventory_list = QtWidgets.QListWidget()
        # Use a local variable for type narrowing
        inv = self.inventory_list
        inv.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        inv.customContextMenuRequested.connect(self._show_inventory_context_menu)
        inv.itemSelectionChanged.connect(self._on_selection_changed)
        inv.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(inv, stretch=1)

        # Sell button at bottom
        self.sell_button = QtWidgets.QPushButton("Eladás (1 db, vételáron)")
        sell_btn = self.sell_button
        sell_btn.setEnabled(False)
        sell_btn.clicked.connect(self._on_sell_clicked)
        layout.addWidget(sell_btn)

    def update_inventory(
        self, inventory_by_category: dict[str, list[tuple[str, dict[str, Any]]]]
    ) -> None:
        """
        Update inventory display.

        Args:
            inventory_by_category: Dict mapping category to list of (item_id, item_data) tuples
        """
        from engine.currency_manager import CurrencyManager

        currency_manager = CurrencyManager()

        if not self.inventory_list:
            return
        self.inventory_list.clear()

        # Category display names
        category_names = {
            "armor": "Páncélok",
            "weapons_and_shields": "Fegyverek és pajzsok",
            "general": "Általános felszerelés",
        }

        # Add items by category
        for cat_key in ["armor", "weapons_and_shields", "general"]:
            items = inventory_by_category.get(cat_key, [])

            if items:
                cat_name = category_names.get(cat_key, cat_key)

                # Category header
                header = QtWidgets.QListWidgetItem(f"=== {cat_name} ===")
                header.setFlags(QtCore.Qt.ItemFlag.NoItemFlags)
                font = header.font()
                font.setBold(True)
                header.setFont(font)
                self.inventory_list.addItem(header)

                # Add items
                for item_id, item in items:
                    name = item.get("name", "???")
                    price = item.get("price", 0)
                    sell_price = price  # Full price during character creation
                    price_str = currency_manager.format(price)
                    sell_price_str = currency_manager.format(sell_price)
                    qty = int(item.get("quantity", 1))
                    stackable = bool(item.get("data", {}).get("stackable", False))

                    qty_part = f" x{qty}" if stackable and qty > 1 else ""
                    list_item = QtWidgets.QListWidgetItem(
                        f"  {name}{qty_part} (ár: {price_str}/db, eladható: {sell_price_str}/db)"
                    )
                    list_item.setData(QtCore.Qt.ItemDataRole.UserRole, item_id)
                    self.inventory_list.addItem(list_item)

    def _on_selection_changed(self) -> None:
        """Handle selection change."""
        if not self.inventory_list or not self.sell_button:
            return
        selected = self.inventory_list.selectedItems()

        # Enable sell button only if a sellable item is selected (not header)
        enabled = False
        if selected:
            item = selected[0]
            item_id = item.data(QtCore.Qt.ItemDataRole.UserRole)
            enabled = item_id is not None

        self.sell_button.setEnabled(enabled)

    def _on_sell_clicked(self) -> None:
        """Handle sell button click."""
        if not self.inventory_list:
            return
        selected = self.inventory_list.selectedItems()
        if selected:
            item = selected[0]
            item_id = item.data(QtCore.Qt.ItemDataRole.UserRole)
            if item_id:
                self.sell_requested.emit(item_id)

    def _on_item_double_clicked(self, item: QtWidgets.QListWidgetItem) -> None:
        """Handle double-click on item to sell."""
        item_id = item.data(QtCore.Qt.ItemDataRole.UserRole)
        if item_id:
            self.sell_requested.emit(item_id)

    def _show_inventory_context_menu(self, pos: QtCore.QPoint) -> None:
        """Show context menu for inventory items."""
        if not self.inventory_list:
            return
        item = self.inventory_list.itemAt(pos)
        if not item:
            return

        item_id = item.data(QtCore.Qt.ItemDataRole.UserRole)
        if not item_id:  # Skip headers
            return

        menu = QtWidgets.QMenu(self)
        sell_action = menu.addAction("Eladás (1 db, vételáron)")

        action = menu.exec(self.inventory_list.mapToGlobal(pos))
        if action == sell_action:
            self.sell_requested.emit(item_id)
