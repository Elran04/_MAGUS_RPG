import os
from utils.json_manager import JsonManager
from PySide6.QtWidgets import (
    QWidget, QMainWindow, QApplication, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QLineEdit, QTextEdit, QDoubleSpinBox, QSpinBox, QComboBox,
    QMessageBox, QFormLayout
)
from PySide6.QtCore import Qt


class GeneralEquipmentJsonManager(JsonManager):
    def validate(self, item):
        required = ["id", "name", "description", "weight", "price", "category"]
        for field in required:
            if field not in item or item[field] in (None, ""):
                return False
        cat = item.get("category", "")
        if cat in ["eszköz", "élelem", "speciális"] and "space" not in item:
            return False
        if cat == "tároló" and "capacity" not in item:
            return False
        if cat == "élelem" and ("freshness" not in item or "durability" not in item):
            return False
        return True


GENERAL_JSON = os.path.join(os.path.dirname(__file__), "..", "..", "data", "equipment", "general_equipment.json")


class GeneralEquipmentEditorQt(QMainWindow):
    CATEGORIES = ["eszköz", "élelem", "tároló", "speciális"]
    SPECIAL_SUBCATEGORIES = ["Alkímia"]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Általános felszerelés szerkesztő")
        self.resize(1200, 760)

        self.manager = GeneralEquipmentJsonManager(GENERAL_JSON)
        self.items = self.manager.load()
        self.selected_idx = None

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout()
        central.setLayout(root)

        # Left: tree and actions
        left = QVBoxLayout()
        root.addLayout(left, stretch=1)
        title = QLabel("Felszerelések kategóriák szerint")
        title.setAlignment(Qt.AlignHCenter)
        left.addWidget(title)
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        left.addWidget(self.tree, stretch=1)
        self.tree.currentItemChanged.connect(self.on_tree_select)
        btn_row = QHBoxLayout()
        self.btn_new = QPushButton("Új felszerelés")
        self.btn_new.clicked.connect(self.new_item)
        self.btn_del = QPushButton("Törlés")
        self.btn_del.clicked.connect(self.delete_item)
        btn_row.addWidget(self.btn_new)
        btn_row.addWidget(self.btn_del)
        left.addLayout(btn_row)

        # Right: form
        right = QWidget()
        right_layout = QVBoxLayout(right)
        form = QFormLayout()
        right_layout.addLayout(form)
        root.addWidget(right, stretch=2)

        self.inp_id = QLineEdit()
        form.addRow("Azonosító:", self.inp_id)
        self.inp_name = QLineEdit()
        form.addRow("Név:", self.inp_name)
        self.txt_desc = QTextEdit()
        form.addRow("Leírás:", self.txt_desc)
        self.spn_weight = QDoubleSpinBox()
        self.spn_weight.setRange(0.0, 1000.0)
        self.spn_weight.setDecimals(2)
        form.addRow("Súly (kg):", self.spn_weight)

        # Price
        from engine.currency_manager import CurrencyManager
        self.price_spins = {}
        price_row = QHBoxLayout()
        for curr in ["réz", "ezüst", "arany", "mithrill"]:
            price_row.addWidget(QLabel(curr))
            spn = QSpinBox()
            spn.setRange(0, 9999999)
            price_row.addWidget(spn)
            self.price_spins[curr] = spn
        right_layout.addLayout(price_row)

        # Category and dependent fields
        cat_row = QHBoxLayout()
        cat_row.addWidget(QLabel("Kategória:"))
        self.cmb_category = QComboBox()
        self.cmb_category.addItems(self.CATEGORIES)
        self.cmb_category.currentTextChanged.connect(self.update_category_fields)
        cat_row.addWidget(self.cmb_category)
        right_layout.addLayout(cat_row)

        # Container for dynamic fields
        self.dynamic_container = QWidget()
        self.dynamic_layout = QFormLayout(self.dynamic_container)
        right_layout.addWidget(self.dynamic_container)

        # Save button
        self.btn_save = QPushButton("Mentés")
        self.btn_save.clicked.connect(self.save_item)
        right_layout.addWidget(self.btn_save)

        self.populate_treeview()
        self.update_category_fields(self.cmb_category.currentText())

    # Helpers
    def _price_to_parts(self, price):
        from engine.currency_manager import CurrencyManager
        return CurrencyManager().from_base(int(price or 0))

    def _parts_to_price(self):
        from engine.currency_manager import CurrencyManager
        total = 0
        for curr in ["réz", "ezüst", "arany", "mithrill"]:
            total += CurrencyManager().to_base(self.price_spins[curr].value(), curr)
        return total

    # Tree population
    def populate_treeview(self):
        self.tree.clear()
        cat_map = {cat: [] for cat in self.CATEGORIES}
        for idx, item in enumerate(self.items):
            cat = item.get('category', 'egyéb')
            cat_map.setdefault(cat, []).append((idx, item))
        self._cat_nodes = {}
        for cat in self.CATEGORIES:
            cat_item = QTreeWidgetItem([cat.capitalize()])
            self.tree.addTopLevelItem(cat_item)
            self._cat_nodes[cat] = cat_item
            if cat == "speciális":
                sub_map = {}
                for idx, it in cat_map.get(cat, []):
                    sub = it.get('subcategory', 'Egyéb')
                    sub_map.setdefault(sub, []).append((idx, it))
                for sub in sorted(sub_map.keys()):
                    sub_item = QTreeWidgetItem([sub])
                    cat_item.addChild(sub_item)
                    for idx, it in sub_map[sub]:
                        node = QTreeWidgetItem([it.get('name', '-')])
                        node.setData(0, Qt.UserRole, idx)
                        sub_item.addChild(node)
            else:
                for idx, it in cat_map.get(cat, []):
                    node = QTreeWidgetItem([it.get('name', '-')])
                    node.setData(0, Qt.UserRole, idx)
                    cat_item.addChild(node)
        self.tree.expandAll()

    # Dynamic fields
    def update_category_fields(self, selected_category):
        # Clear existing
        while self.dynamic_layout.rowCount():
            self.dynamic_layout.removeRow(0)
        self.inp_space = None
        self.inp_capacity = None
        self.inp_freshness = None
        self.inp_durability = None
        self.inp_nutritional = None
        self.cmb_subcategory = None

        cat = self.cmb_category.currentText()
        if cat == "speciális":
            self.cmb_subcategory = QComboBox()
            self.cmb_subcategory.addItems(self.SPECIAL_SUBCATEGORIES)
            self.dynamic_layout.addRow("Alkategória:", self.cmb_subcategory)
        if cat in ["eszköz", "élelem", "speciális"]:
            self.inp_space = QSpinBox()
            self.inp_space.setRange(0, 999999)
            self.dynamic_layout.addRow("Helyigény:", self.inp_space)
        if cat == "tároló":
            self.inp_capacity = QSpinBox()
            self.inp_capacity.setRange(0, 999999)
            self.dynamic_layout.addRow("Kapacitás:", self.inp_capacity)
        if cat == "élelem":
            self.inp_freshness = QSpinBox()
            self.inp_freshness.setRange(0, 999999)
            self.dynamic_layout.addRow("Frissesség:", self.inp_freshness)
            self.inp_durability = QSpinBox()
            self.inp_durability.setRange(0, 999999)
            self.dynamic_layout.addRow("Tartósság:", self.inp_durability)
            self.inp_nutritional = QSpinBox()
            self.inp_nutritional.setRange(0, 999999)
            self.dynamic_layout.addRow("Tápérték:", self.inp_nutritional)

    def on_tree_select(self, current, previous):
        if not current:
            return
        idx = current.data(0, Qt.UserRole)
        if idx is None:
            return
        self.selected_idx = int(idx)
        item = self.items[self.selected_idx]
        # Fill fields
        self.inp_id.setText(str(item.get('id', '')))
        self.inp_name.setText(str(item.get('name', '')))
        self.txt_desc.setPlainText(str(item.get('description', '')))
        try:
            self.spn_weight.setValue(float(item.get('weight', 0)))
        except Exception:
            self.spn_weight.setValue(0.0)
        parts_price = self._price_to_parts(item.get('price', 0))
        for curr in ["réz", "ezüst", "arany", "mithrill"]:
            self.price_spins[curr].setValue(int(parts_price.get(curr, 0)))
        # Category and dependent
        cat = item.get('category', '')
        self.cmb_category.setCurrentText(cat)
        # After update_category_fields, set dependent values
        if cat == 'speciális' and 'subcategory' in item and self.cmb_subcategory is not None:
            self.cmb_subcategory.setCurrentText(item.get('subcategory', self.SPECIAL_SUBCATEGORIES[0]))
        if cat in ['eszköz', 'élelem', 'speciális'] and self.inp_space is not None:
            try:
                self.inp_space.setValue(int(item.get('space', 0)))
            except Exception:
                self.inp_space.setValue(0)
        if cat == 'tároló' and self.inp_capacity is not None:
            try:
                self.inp_capacity.setValue(int(item.get('capacity', 0)))
            except Exception:
                self.inp_capacity.setValue(0)
        if cat == 'élelem':
            if self.inp_freshness is not None:
                self.inp_freshness.setValue(int(item.get('freshness', 0)))
            if self.inp_durability is not None:
                self.inp_durability.setValue(int(item.get('durability', 0)))
            if self.inp_nutritional is not None:
                try:
                    self.inp_nutritional.setValue(int(item.get('nutritional_value', 0)))
                except Exception:
                    self.inp_nutritional.setValue(0)

    def save_item(self):
        # Build
        item = {
            'id': self.inp_id.text().strip(),
            'name': self.inp_name.text().strip(),
            'description': self.txt_desc.toPlainText().strip(),
            'weight': float(self.spn_weight.value()),
            'price': int(self._parts_to_price()),
            'category': self.cmb_category.currentText(),
        }
        cat = item['category']
        if cat == 'speciális' and self.cmb_subcategory is not None:
            item['subcategory'] = self.cmb_subcategory.currentText() or self.SPECIAL_SUBCATEGORIES[0]
        if cat in ['eszköz', 'élelem', 'speciális'] and self.inp_space is not None:
            item['space'] = int(self.inp_space.value())
        if cat == 'tároló' and self.inp_capacity is not None:
            item['capacity'] = int(self.inp_capacity.value())
        if cat == 'élelem':
            if self.inp_freshness is not None:
                item['freshness'] = int(self.inp_freshness.value())
            if self.inp_durability is not None:
                item['durability'] = int(self.inp_durability.value())
            if self.inp_nutritional is not None:
                item['nutritional_value'] = int(self.inp_nutritional.value())
        # Validate
        if not self.manager.validate(item):
            QMessageBox.critical(self, "Hiba", "Hiányzó vagy hibás mezők!")
            return
        # Save
        if self.selected_idx is not None:
            self.items[self.selected_idx] = item
        else:
            self.items.append(item)
            self.selected_idx = len(self.items) - 1
        self.manager.save(self.items)
        self.populate_treeview()
        QMessageBox.information(self, "Mentés", "Felszerelés mentve!")

    def new_item(self):
        self.selected_idx = None
        self.inp_id.clear()
        self.inp_name.clear()
        self.txt_desc.clear()
        self.spn_weight.setValue(0.0)
        for curr in ["réz", "ezüst", "arany", "mithrill"]:
            self.price_spins[curr].setValue(0)
        self.cmb_category.setCurrentIndex(0)
        self.update_category_fields(self.cmb_category.currentText())

    def delete_item(self):
        it = self.tree.currentItem()
        if not it:
            return
        idx = it.data(0, Qt.UserRole)
        if idx is None:
            return
        name = self.items[int(idx)].get('name', '-')
        ans = QMessageBox.question(self, "Törlés", f"Biztosan törlöd ezt?\n{name}")
        if ans == QMessageBox.Yes:
            del self.items[int(idx)]
            self.manager.save(self.items)
            self.populate_treeview()
            self.new_item()


if __name__ == "__main__":
    import sys
    import os as _os
    sys.path.insert(0, _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..', '..')))
    from utils.dark_mode import apply_dark_mode
    app = QApplication(sys.argv)
    apply_dark_mode(app)
    w = GeneralEquipmentEditorQt()
    w.show()
    sys.exit(app.exec())
