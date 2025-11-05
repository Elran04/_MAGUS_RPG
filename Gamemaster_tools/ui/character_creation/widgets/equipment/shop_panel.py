"""
Shop Panel Widget
Displays equipment categories in tabs with tree view and buy functionality.
"""

from typing import Any, Callable

from PySide6 import QtCore, QtWidgets

from utils.log.logger import get_logger

logger = get_logger(__name__)


class ShopPanel(QtWidgets.QWidget):
    """Shop panel with categorized equipment tabs."""

    # Signal emitted when user wants to buy an item
    # Args: (item_data, category)
    buy_requested = QtCore.Signal(dict, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.equipment_data = {}
        self.tab_widget = None
        self.tree_widgets = {}
        
        self._build_ui()

    def _build_ui(self):
        """Build the shop UI with tabs."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Shop title
        title = QtWidgets.QLabel("Felszerelés bolt")
        title.setStyleSheet("font-weight: bold; font-size: 12px; padding: 4px;")
        layout.addWidget(title)
        
        # Tab widget for categories
        self.tab_widget = QtWidgets.QTabWidget()
        layout.addWidget(self.tab_widget, stretch=1)
        
        # Buy button at bottom
        self.buy_button = QtWidgets.QPushButton("Vásárlás")
        self.buy_button.setEnabled(False)
        self.buy_button.clicked.connect(self._on_buy_clicked)
        layout.addWidget(self.buy_button)

    def load_equipment(self, equipment_data: dict[str, list[dict[str, Any]]]):
        """
        Load equipment data into shop tabs.
        
        Args:
            equipment_data: Dict with 'armor', 'weapons_and_shields', 'general' keys
        """
        self.equipment_data = equipment_data
        
        # Clear existing tabs
        self.tab_widget.clear()
        self.tree_widgets.clear()
        
        # Create tabs for each category
        categories = [
            ("armor", "Páncélok"),
            ("weapons_and_shields", "Fegyverek és pajzsok"),
            ("general", "Általános felszerelés")
        ]
        
        for cat_key, cat_name in categories:
            tree = self._create_category_tree(cat_key, cat_name)
            self.tab_widget.addTab(tree, cat_name)
            self.tree_widgets[cat_key] = tree

    def _create_category_tree(self, category: str, category_name: str) -> QtWidgets.QTreeWidget:
        """Create a tree widget for a category."""
        tree = QtWidgets.QTreeWidget()
        tree.setHeaderLabels(["Név", "Ár"])
        tree.setColumnWidth(0, 300)
        tree.setAlternatingRowColors(True)
        tree.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        tree.customContextMenuRequested.connect(
            lambda pos, cat=category: self._show_shop_context_menu(pos, cat)
        )
        tree.itemSelectionChanged.connect(self._on_selection_changed)
        tree.itemDoubleClicked.connect(
            lambda item, col, cat=category: self._on_item_double_clicked(item, cat)
        )
        
        # Populate with items
        items = self.equipment_data.get(category, [])
        for item in items:
            self._add_item_to_tree(tree, item)
            
        return tree

    def _add_item_to_tree(self, tree: QtWidgets.QTreeWidget, item: dict[str, Any]):
        """Add an item to the tree."""
        from engine.currency_manager import CurrencyManager
        
        currency_manager = CurrencyManager()
        name = item.get("name", "???")
        price = item.get("price", 0)
        price_str = currency_manager.format(price) + "/db"
        
        tree_item = QtWidgets.QTreeWidgetItem([name, price_str])
        tree_item.setData(0, QtCore.Qt.ItemDataRole.UserRole, item)
        tree.addTopLevelItem(tree_item)

    def _on_selection_changed(self):
        """Handle selection change in any tree."""
        # Enable buy button if something is selected
        has_selection = False
        for tree in self.tree_widgets.values():
            if tree.selectedItems():
                has_selection = True
                break
        
        self.buy_button.setEnabled(has_selection)

    def _on_buy_clicked(self):
        """Handle buy button click."""
        # Find which tree has selection
        for cat_key, tree in self.tree_widgets.items():
            selected = tree.selectedItems()
            if selected:
                item = selected[0]
                item_data = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
                if item_data:
                    self.buy_requested.emit(item_data, cat_key)
                break

    def _on_item_double_clicked(self, item: QtWidgets.QTreeWidgetItem, category: str):
        """Handle double-click on item to buy."""
        item_data = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if item_data:
            self.buy_requested.emit(item_data, category)

    def _show_shop_context_menu(self, pos: QtCore.QPoint, category: str):
        """Show context menu for shop items."""
        tree = self.tree_widgets.get(category)
        if not tree:
            return
            
        item = tree.itemAt(pos)
        if not item:
            return
            
        item_data = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if not item_data:
            return
            
        menu = QtWidgets.QMenu(self)
        buy_action = menu.addAction("Vásárlás")
        
        action = menu.exec(tree.mapToGlobal(pos))
        if action == buy_action:
            self.buy_requested.emit(item_data, category)
