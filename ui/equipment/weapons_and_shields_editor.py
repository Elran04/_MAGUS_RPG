from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QTreeView, QLineEdit, QComboBox, QCheckBox, QPushButton, QMessageBox, QLabel, QSpinBox
)
from PySide6.QtCore import Qt, QAbstractItemModel, QModelIndex
from PySide6.QtGui import QStandardItemModel, QStandardItem
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from utils.weapondata_manager import WeaponDataManager

WEAPONS_JSON = os.path.join(os.path.dirname(__file__), "..", "..", "data", "equipment", "weapons_and_shields.json")

class WeaponsAndShieldsEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fegyverek és pajzsok szerkesztője (Qt)")
        self.resize(1100, 700)
        self.manager = WeaponDataManager(WEAPONS_JSON)
        self.items = self.manager.load()
        self.selected_idx = None
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout()
        central.setLayout(main_layout)

        # Bal oldali lista (TreeView)
        left_panel = QVBoxLayout()
        main_layout.addLayout(left_panel, 1)
        left_panel.addWidget(QLabel("Fegyverek és pajzsok listája"))
        self.tree = QTreeView()
        left_panel.addWidget(self.tree)
        # TreeView modell
        from PySide6.QtGui import QStandardItemModel, QStandardItem
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Fegyverek és pajzsok"])
        self.tree.setModel(self.model)
        self.tree.setHeaderHidden(False)
        self.tree.clicked.connect(self.on_tree_select)
        self.populate_treeview()
        btn_new = QPushButton("Új fegyver/pajzs")
        btn_new.clicked.connect(self.new_item)
        left_panel.addWidget(btn_new)
        btn_delete = QPushButton("Törlés")
        btn_delete.clicked.connect(self.delete_item)
        left_panel.addWidget(btn_delete)

        # Jobb oldali szerkesztő panel
        self.edit_panel = QWidget()
        self.edit_layout = QFormLayout()
        self.edit_panel.setLayout(self.edit_layout)
        main_layout.addWidget(self.edit_panel, 2)

        # Mezők
        self.fields = {}
        self.build_edit_fields()
        btn_save = QPushButton("Mentés")
        btn_save.clicked.connect(self.save_item)
        self.edit_layout.addRow(btn_save)

    def build_edit_fields(self):
        # Csak egyszer generáljuk a fő mezőket, ne töröljük minden új itemnél/kiválasztásnál
        # Alap mezők (kivéve 'type' és 'category')
        for key in self.manager.BASE_FIELDS:
            if key not in ('type', 'category'):
                le = QLineEdit()
                self.fields[key] = le
                self.edit_layout.addRow(QLabel(key.capitalize() + ":"), le)
        # Típus mező (legördülő)
        self.fields['type'] = QComboBox()
        self.fields['type'].addItems(self.manager.get_weapon_types())
        self.fields['type'].currentTextChanged.connect(self.update_type_fields)
        self.edit_layout.addRow(QLabel("Típus:"), self.fields['type'])
        # Kategória mező (legördülő)
        self.fields['category'] = QComboBox()
        self.edit_layout.addRow(QLabel("Kategória:"), self.fields['category'])
        # Damage types
        self.damage_type_checks = {}
        for typ in self.manager.DAMAGE_TYPES:
            cb = QCheckBox(typ.capitalize())
            self.damage_type_checks[typ] = cb
            self.edit_layout.addRow(cb)
        # Damage bonus attributes
        self.damage_bonus_checks = {}
        for attr in self.manager.DAMAGE_BONUS_ATTRS:
            cb = QCheckBox(attr.capitalize())
            self.damage_bonus_checks[attr] = cb
            self.edit_layout.addRow(cb)
        # Ár mezők
        for key in self.manager.PRICE_FIELDS:
            sb = QSpinBox()
            sb.setMaximum(999999)
            self.fields[key] = sb
            self.edit_layout.addRow(QLabel(key.replace('_', ' ').capitalize() + ":"), sb)
        # Egyéb mezők, checkboxok
        for key in self.manager.CHECKBOX_FIELDS:
            cb = QCheckBox(key.replace('_', ' ').capitalize())
            self.fields[key] = cb
            self.edit_layout.addRow(cb)
        # Típusfüggő mezők (dinamikusan, csak Qt váz)
        self.type_fields = {}

    def update_type_fields(self, type_value):
        # Frissítsd a kategória mezőt a típus alapján
        categories = self.manager.get_weapon_categories(type_value)
        self.fields['category'].clear()
        self.fields['category'].addItems(categories)
        # Típusfüggő mezők dinamikus kezelése
        # Először töröld a régieket a layoutból is!
        for key, widget in self.type_fields.items():
            # Megkeressük a widgethez tartozó sort, és eltávolítjuk
            for i in range(self.edit_layout.rowCount()):
                row_widget = self.edit_layout.itemAt(i, self.edit_layout.FieldRole)
                if row_widget is not None and row_widget.widget() is widget:
                    self.edit_layout.removeRow(i)
                    break
            widget.deleteLater()
        self.type_fields = {}
        # Új mezők
        for label, key in self.manager.TYPE_FIELD_DEFS.get(type_value, []):
            le = QLineEdit()
            self.type_fields[key] = le
            self.edit_layout.addRow(QLabel(label), le)
        # Speciális wield_mode mező (csak közelharci)
        if type_value == "közelharci":
            wield_combo = QComboBox()
            wield_combo.addItems(["Egykezes", "Kétkezes", "Változó"])
            wield_combo.currentTextChanged.connect(lambda v: self.update_type_fields(type_value))
            self.type_fields['wield_mode'] = wield_combo
            self.edit_layout.addRow(QLabel("Használati mód:"), wield_combo)
            # Változó extra mezők
            if wield_combo.currentText() == "Változó":
                for label, key in [
                    ("Erő szükséglet:", "variable_strength_req"),
                    ("Ügyesség szükséglet:", "variable_dex_req"),
                    ("Bonus KÉ:", "variable_bonus_KE"),
                    ("Bonus TÉ:", "variable_bonus_TE"),
                    ("Bonus VÉ:", "variable_bonus_VE"),
                ]:
                    le = QLineEdit()
                    self.type_fields[key] = le
                    self.edit_layout.addRow(QLabel(label), le)
                dual_cb = QCheckBox("Kétkezes harc lehetséges")
                self.type_fields['variable_dual_wield'] = dual_cb
                self.edit_layout.addRow(dual_cb)

    def new_item(self):
        self.selected_idx = None
        for key, widget in self.fields.items():
            if isinstance(widget, QLineEdit):
                widget.clear()
            elif isinstance(widget, QComboBox):
                widget.setCurrentIndex(0)
            elif isinstance(widget, QCheckBox):
                widget.setChecked(False)
            elif isinstance(widget, QSpinBox):
                widget.setValue(0)
        for cb in self.damage_type_checks.values():
            cb.setChecked(False)
        for cb in self.damage_bonus_checks.values():
            cb.setChecked(False)
        for key, widget in self.type_fields.items():
            if isinstance(widget, QLineEdit):
                widget.clear()
            elif isinstance(widget, QComboBox):
                widget.setCurrentIndex(0)
            elif isinstance(widget, QCheckBox):
                widget.setChecked(False)
        self.fields['type'].setCurrentIndex(0)
        self.update_type_fields(self.fields['type'].currentText())
        self.fields['category'].setCurrentIndex(0)
        self.fields['name'].setFocus()

    def save_item(self):
        # Collect field values
        fields = {key: widget.text() if isinstance(widget, QLineEdit) else widget.currentText() if isinstance(widget, QComboBox) else widget.isChecked() if isinstance(widget, QCheckBox) else widget.value() if isinstance(widget, QSpinBox) else None for key, widget in self.fields.items()}
        # Damage types and bonus attributes
        fields['damage_types'] = [typ for typ, cb in self.damage_type_checks.items() if cb.isChecked()]
        fields['damage_bonus_attributes'] = [attr for attr, cb in self.damage_bonus_checks.items() if cb.isChecked()]
        # Típusfüggő mezők
        for key, widget in self.type_fields.items():
            if isinstance(widget, QLineEdit):
                fields[key] = widget.text()
            elif isinstance(widget, QComboBox):
                fields[key] = widget.currentText()
            elif isinstance(widget, QCheckBox):
                fields[key] = widget.isChecked()
        # Build item dict using manager logic
        try:
            item = self.manager.build_item_from_fields(fields)
        except Exception as e:
            QMessageBox.critical(self, "Hiba", f"Hibás adat: {e}")
            return
        # Validáció
        if not self.manager.validate(item):
            QMessageBox.critical(self, "Hiba", "Hiányzó vagy hibás mező!")
            return
        # Mentés
        if self.selected_idx is not None:
            self.items[self.selected_idx] = item
        else:
            self.items.append(item)
        self.manager.save(self.items)
        self.populate_treeview()
        QMessageBox.information(self, "Mentés", "Fegyver/pajzs mentve!")

    def delete_item(self):
        # Kiválasztott item törlése
        idx = self.selected_idx
        if idx is None:
            QMessageBox.warning(self, "Törlés", "Nincs kiválasztva fegyver/pajzs.")
            return
        answer = QMessageBox.question(self, "Törlés", f"Biztosan törlöd ezt?\n{self.items[idx]['name']}")
        if answer == QMessageBox.Yes:
            self.items.pop(idx)
            self.manager.save(self.items)
            self.populate_treeview()
            self.new_item()
    def populate_treeview(self):
        # Feltölti a bal oldali TreeView-t a fegyverek/pajzsok listájával
        self.model.clear()
        self.model.setHorizontalHeaderLabels(["Fegyverek és pajzsok"])
        type_order = self.manager.get_weapon_types()
        type_items = {}
        for idx, item in enumerate(self.items):
            type_val = item.get('type', 'Egyéb')
            cat_val = item.get('category', '') or 'Egyéb'
            type_items.setdefault(type_val, []).append((cat_val, idx, item))
        for t in type_order + [t for t in type_items if t not in type_order]:
            if t not in type_items:
                continue
            type_item = QStandardItem(t)
            self.model.appendRow(type_item)
            cat_map = {}
            for cat_val, idx, item in type_items[t]:
                cat_map.setdefault(cat_val, []).append((idx, item))
            for cat_val in sorted(cat_map.keys()):
                cat_item = QStandardItem(cat_val)
                type_item.appendRow(cat_item)
                for idx, item in cat_map[cat_val]:
                    item_text = f"{item['name']} (ID: {item.get('id', '-')})"
                    leaf = QStandardItem(item_text)
                    leaf.setData(idx)
                    cat_item.appendRow(leaf)
    def on_tree_select(self, index: QModelIndex):
        # TreeView elem kiválasztásakor betölti az adott item adatait a szerkesztő panelre
        item = self.model.itemFromIndex(index)
        if item is None or item.parent() is None or item.parent().parent() is None:
            # Csak leaf node lehet
            return
        idx = item.data()
        if idx is None:
            return
        self.selected_idx = idx
        it = self.items[idx]
        # Alap mezők
        for key in self.manager.BASE_FIELDS:
            value = it.get(key, "")
            widget = self.fields[key]
            # Típus és kategória mezők: QComboBox
            if key == "type" and isinstance(widget, QComboBox):
                widget.setCurrentText(str(value))
            elif key == "category" and isinstance(widget, QComboBox):
                widget.setCurrentText(str(value))
            elif isinstance(widget, QLineEdit):
                widget.setText(str(value))
            elif isinstance(widget, QSpinBox):
                try:
                    widget.setValue(int(value))
                except Exception:
                    widget.setValue(0)
            elif isinstance(widget, QCheckBox):
                widget.setChecked(bool(value))
        # Ár mezők
        try:
            from engine.currency_manager import CurrencyManager
            price = int(it.get('price', 0))
            price_parts = CurrencyManager().from_base(price)
            for key in self.manager.PRICE_FIELDS:
                curr = key.split('_')[1]
                self.fields[key].setValue(int(price_parts.get(curr, 0)))
        except Exception:
            for key in self.manager.PRICE_FIELDS:
                self.fields[key].setValue(0)
        # Típus mező
        self.fields['type'].setCurrentText(it.get('type', self.manager.get_weapon_types()[0]))
        self.update_type_fields(it.get('type', self.manager.get_weapon_types()[0]))
        # Kategória mező
        self.fields['category'].setCurrentText(it.get('category', ""))
        # Damage types
        for typ, cb in self.damage_type_checks.items():
            cb.setChecked(typ in it.get('damage_types', []))
        for attr, cb in self.damage_bonus_checks.items():
            cb.setChecked(attr in it.get('damage_bonus_attributes', []))
        # Típusfüggő mezők
        for label, key in self.manager.TYPE_FIELD_DEFS.get(it.get('type', ''), []):
            if key in self.type_fields:
                self.type_fields[key].setText(str(it.get(key, "")))
        # Wield mode
        if 'wield_mode' in self.type_fields:
            self.type_fields['wield_mode'].setCurrentText(it.get('wield_mode', 'Egykezes'))
            if it.get('wield_mode') == "Változó":
                for key in [
                    "variable_strength_req",
                    "variable_dex_req",
                    "variable_bonus_KE",
                    "variable_bonus_TE",
                    "variable_bonus_VE",
                ]:
                    if key in self.type_fields:
                        self.type_fields[key].setText(str(it.get(key, "")))
                if 'variable_dual_wield' in self.type_fields:
                    self.type_fields['variable_dual_wield'].setChecked(bool(it.get('variable_dual_wield', False)))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = WeaponsAndShieldsEditor()
    win.show()
    sys.exit(app.exec())
