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
    # Signal for bulk purchases: (item_data, category, quantity)
    bulk_buy_requested = QtCore.Signal(dict, str, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.equipment_data = {}
        self.tab_widget = None
        self.tree_widgets = {}
        # Callback to fetch current currency in base units (for affordability checks)
        self._currency_provider: Callable[[], int] | None = None
        
        self._build_ui()

    def set_currency_provider(self, provider: Callable[[], int]):
        """Provide a callback that returns current currency in base units."""
        self._currency_provider = provider

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
        """Create a grouped tree widget for a category, mimicking the editors' grouping."""
        tree = QtWidgets.QTreeWidget()
        tree.setHeaderLabels(["Név", "Ár"])
        tree.setColumnWidth(0, 300)
        tree.setAlternatingRowColors(True)
        tree.setRootIsDecorated(True)
        tree.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        tree.customContextMenuRequested.connect(
            lambda pos, cat=category: self._show_shop_context_menu(pos, cat)
        )
        tree.itemSelectionChanged.connect(self._on_selection_changed)
        tree.itemDoubleClicked.connect(
            lambda item, col, cat=category: self._on_item_double_clicked(item, cat)
        )

        items = self.equipment_data.get(category, [])

        from engine.currency_manager import CurrencyManager
        currency_manager = CurrencyManager()

        def price_str(price: int) -> str:
            return currency_manager.format(int(price or 0)) + "/db"

        if category == "armor":
            # Group by armor_type with labels similar to editor
            type_labels = {
                "plate": "Lemezpáncél",
                "flexible_metal": "Rugalmas fém",
                "leather": "Bőr / Textil",
            }
            groups: dict[str, QtWidgets.QTreeWidgetItem] = {}
            for tkey, label in type_labels.items():
                root = QtWidgets.QTreeWidgetItem([label, ""])  # header has no price
                root.setFirstColumnSpanned(False)
                tree.addTopLevelItem(root)
                root.setExpanded(True)
                groups[tkey] = root
            for item in items:
                tkey = item.get("armor_type", "leather")
                root = groups.get(tkey, groups["leather"])
                node = QtWidgets.QTreeWidgetItem([
                    item.get("name", "???"), price_str(item.get("price", 0))
                ])
                node.setData(0, QtCore.Qt.ItemDataRole.UserRole, item)
                root.addChild(node)
        elif category == "weapons_and_shields":
            # Group by type -> category like editor
            # Build type order by appearance to keep a stable order
            type_order: list[str] = []
            grouped: dict[str, dict[str, list[dict]]] = {}
            for it in items:
                t = (it.get("type") or "Egyéb").strip()
                c = (it.get("category") or "Egyéb").strip()
                if t not in type_order:
                    type_order.append(t)
                grouped.setdefault(t, {}).setdefault(c, []).append(it)
            for t in type_order:
                type_root = QtWidgets.QTreeWidgetItem([t, ""])  # header
                tree.addTopLevelItem(type_root)
                type_root.setExpanded(True)
                for c in sorted(grouped.get(t, {}).keys()):
                    cat_root = QtWidgets.QTreeWidgetItem([c, ""])  # sub header
                    type_root.addChild(cat_root)
                    cat_root.setExpanded(True)
                    for it in grouped[t][c]:
                        leaf = QtWidgets.QTreeWidgetItem([
                            it.get("name", "???"), price_str(it.get("price", 0))
                        ])
                        leaf.setData(0, QtCore.Qt.ItemDataRole.UserRole, it)
                        cat_root.addChild(leaf)
        elif category == "general":
            # Group by CATEGORIES, with a second level for 'speciális' by subcategory
            CATEGORIES = ["eszköz", "élelem", "tároló", "lőszer", "speciális"]
            cat_map: dict[str, list[dict]] = {cat: [] for cat in CATEGORIES}
            for it in items:
                cat = it.get("category", "eszköz")
                cat_map.setdefault(cat, []).append(it)
            for cat in CATEGORIES:
                root = QtWidgets.QTreeWidgetItem([cat.capitalize(), ""])  # header
                tree.addTopLevelItem(root)
                root.setExpanded(True)
                if cat == "speciális":
                    sub_map: dict[str, list[dict]] = {}
                    for it in cat_map.get(cat, []):
                        sub = it.get("subcategory", "Egyéb")
                        sub_map.setdefault(sub, []).append(it)
                    for sub in sorted(sub_map.keys()):
                        sub_root = QtWidgets.QTreeWidgetItem([sub, ""])  # sub header
                        root.addChild(sub_root)
                        sub_root.setExpanded(True)
                        for it in sub_map[sub]:
                            leaf = QtWidgets.QTreeWidgetItem([
                                it.get("name", "???"), price_str(it.get("price", 0))
                            ])
                            leaf.setData(0, QtCore.Qt.ItemDataRole.UserRole, it)
                            sub_root.addChild(leaf)
                else:
                    for it in cat_map.get(cat, []):
                        leaf = QtWidgets.QTreeWidgetItem([
                            it.get("name", "???"), price_str(it.get("price", 0))
                        ])
                        leaf.setData(0, QtCore.Qt.ItemDataRole.UserRole, it)
                        root.addChild(leaf)
        else:
            # Fallback: flat list
            for item in items:
                name = item.get("name", "???")
                node = QtWidgets.QTreeWidgetItem([name, price_str(item.get("price", 0))])
                node.setData(0, QtCore.Qt.ItemDataRole.UserRole, item)
                tree.addTopLevelItem(node)

        tree.expandAll()
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
        # Enable buy button only if a real item (leaf with data) is selected
        enabled = False
        for tree in self.tree_widgets.values():
            selected = tree.selectedItems()
            if selected:
                data = selected[0].data(0, QtCore.Qt.ItemDataRole.UserRole)
                if isinstance(data, dict):
                    enabled = True
                    break
        self.buy_button.setEnabled(enabled)

    def _on_buy_clicked(self):
        """Handle buy button click."""
        # Find which tree has selection
        for cat_key, tree in self.tree_widgets.items():
            selected = tree.selectedItems()
            if selected:
                item = selected[0]
                item_data = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
                if isinstance(item_data, dict):
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
        if not isinstance(item_data, dict):
            return

        menu = QtWidgets.QMenu(self)
        buy_action = menu.addAction("Vásárlás")

        bulk_action = None
        # Only offer bulk buy for stackable items in General tab
        if category == "general" and bool(item_data.get("stackable", False)):
            bulk_action = menu.addAction("Tömeges vásárlás…")

        action = menu.exec(tree.mapToGlobal(pos))
        if action == buy_action:
            self.buy_requested.emit(item_data, category)
        elif bulk_action is not None and action == bulk_action:
            self._open_bulk_buy_dialog(item_data, category)

    def _open_bulk_buy_dialog(self, item_data: dict[str, Any], category: str):
        """Open a modal dialog to pick quantity and confirm bulk buy with live affordability."""
        from engine.currency_manager import CurrencyManager

        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle(f"Tömeges vásárlás – {item_data.get('name', 'Ismeretlen')}")
        layout = QtWidgets.QVBoxLayout(dlg)

        cm = CurrencyManager()
        price_each = int(item_data.get("price", 0) or 0)

        name_lbl = QtWidgets.QLabel(item_data.get("name", "???"))
        name_lbl.setStyleSheet("font-weight: bold;")
        layout.addWidget(name_lbl)

        form_row = QtWidgets.QHBoxLayout()
        form_row.addWidget(QtWidgets.QLabel("Mennyiség:"))
        qty = QtWidgets.QSpinBox()
        qty.setRange(1, 999)
        qty.setValue(10 if item_data.get("category") == "lőszer" else 1)
        form_row.addWidget(qty)
        form_row.addStretch(1)
        layout.addLayout(form_row)

        total_lbl = QtWidgets.QLabel()
        current_lbl = QtWidgets.QLabel()
        hint = QtWidgets.QLabel("Az OK gomb csak akkor aktív, ha fedezi az összköltséget.")
        hint.setStyleSheet("color: #777; font-size: 10px;")
        layout.addWidget(total_lbl)
        layout.addWidget(current_lbl)
        layout.addWidget(hint)

        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        layout.addWidget(btns)

        ok_btn = btns.button(QtWidgets.QDialogButtonBox.Ok)

        def update_totals():
            q = int(qty.value())
            total = price_each * q
            total_lbl.setText(f"Összesen: {cm.format(total)}")
            cur_val = self._currency_provider() if self._currency_provider else 0
            current_lbl.setText(f"Rendelkezésre álló: {cm.format(cur_val)}")
            ok_btn.setEnabled(cur_val >= total and q > 0)

        qty.valueChanged.connect(update_totals)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)

        update_totals()

        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            q = int(qty.value())
            if q > 0:
                self.bulk_buy_requested.emit(item_data, category, q)
