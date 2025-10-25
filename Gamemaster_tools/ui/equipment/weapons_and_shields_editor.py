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
    # --- Fő Qt ablak: fegyverek és pajzsok szerkesztője ---
    # A szerkesztő két fő panelből áll: bal oldalon TreeView (lista), jobb oldalon szerkesztő mezők
    # Főbb egységek: setup_treeview, populate_treeview, on_tree_select, build_edit_fields, build_type_fields, mezőkezelés, mentés/törlés logika

    def setup_treeview(self, main_layout):
        """
        Inicializálja a bal oldali TreeView panelt, amely a fegyverek/pajzsok hierarchikus listáját mutatja.
        - TreeView: típus -> kategória -> item
        - Új/Törlés gombok
        - TreeView elem kiválasztásakor: on_tree_select
        """
        left_panel = QVBoxLayout()
        main_layout.addLayout(left_panel, 1)
        left_panel.addWidget(QLabel("Fegyverek és pajzsok listája"))
        self.tree = QTreeView()
        left_panel.addWidget(self.tree)
        from PySide6.QtGui import QStandardItemModel, QStandardItem
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Fegyverek és pajzsok"])
        self.tree.setModel(self.model)
        self.tree.setHeaderHidden(False)
        self.tree.clicked.connect(self.on_tree_select)  # Kiválasztáskor szerkesztő panel frissítése
        self.populate_treeview()  # Lista feltöltése
        btn_new = QPushButton("Új fegyver/pajzs")
        btn_new.clicked.connect(self.new_item)
        left_panel.addWidget(btn_new)
        btn_delete = QPushButton("Törlés")
        btn_delete.clicked.connect(self.delete_item)
        left_panel.addWidget(btn_delete)

    def on_tree_select(self, index: QModelIndex):
        """
        TreeView elem kiválasztásakor betölti az adott item adatait a szerkesztő panelre.
        - Csak leaf node (konkrét fegyver/pajzs) választható ki
        - Kitölti az összes mezőt, típusfüggő mezőket is
        - Frissíti a selected_idx-et
        """
        item = self.model.itemFromIndex(index)
        if item is None or item.parent() is None or item.parent().parent() is None:
            # Csak leaf node lehet (típus->kategória->item)
            return
        idx = item.data()
        if idx is None:
            return
        self.selected_idx = idx
        it = self.items[idx]
        self.fill_fields(it)  # Statikus mezők kitöltése
        self.fields['type'].setCurrentText(it.get('type', self.manager.get_weapon_types()[0]))
        self.build_type_fields(it.get('type', self.manager.get_weapon_types()[0]), item=it)  # Típusfüggő mezők
        self.fields['category'].setCurrentText(it.get('category', ""))

    def populate_treeview(self):
        """
        Feltölti a TreeView-t a fegyverek/pajzsok hierarchiájával:
        - Típus -> Kategória -> Item
        - type_items: {típus: [(kategória, idx, item), ...]}
        - cat_map: {kategória: [(idx, item), ...]}
        - Minden leaf node-hoz beállítja az idx-et, hogy visszakereshető legyen
        """
        self.model.clear()
        self.model.setHorizontalHeaderLabels(["Fegyverek és pajzsok"])
        type_order = self.manager.get_weapon_types()
        type_items = {}
        for idx, item in enumerate(self.items):
            type_val = item.get('type', 'Egyéb')
            cat_val = item.get('category', '') or 'Egyéb'
            type_items.setdefault(type_val, []).append((cat_val, idx, item))
        # Típusok sorrendje: először a manager által definiáltak, majd az egyéb típusok
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
                    leaf.setData(idx)  # index az items listában
                    cat_item.appendRow(leaf)

    # --- Szerkesztő panel (mezőkezelés) logika ---
    def remove_type_fields_from_layout(self):
        """
        Típusfüggő mezők eltávolítása a szerkesztő panelről.
        - Signalokat (pl. QComboBox) lecsatlakoztatja
        - edit_layout-ból eltávolítja a mezőket
        - type_fields dict törlése
        """
        for key, widget in self.type_fields.items():
            if isinstance(widget, QComboBox):
                try:
                    widget.currentTextChanged.disconnect()
                except Exception:
                    pass
            for i in range(self.edit_layout.rowCount()):
                row_widget = self.edit_layout.itemAt(i, QFormLayout.FieldRole)
                if row_widget is not None and row_widget.widget() is widget:
                    self.edit_layout.removeRow(i)
                    break
        self.type_fields = {}
    def set_widget_value(self, widget, value):
        """
        Általános widget értékbeállítás (QLineEdit, QComboBox, QCheckBox, QSpinBox)
        - Hibás érték esetén default érték
        """
        if isinstance(widget, QLineEdit):
            widget.setText(str(value) if value is not None else "")
        elif isinstance(widget, QComboBox):
            widget.setCurrentText(str(value) if value is not None else "")
        elif isinstance(widget, QCheckBox):
            widget.setChecked(bool(value))
        elif isinstance(widget, QSpinBox):
            try:
                widget.setValue(int(value))
            except Exception:
                widget.setValue(0)

    def clear_widget(self, widget):
        """
        Widget értékének törlése/alaphelyzetbe állítása
        """
        if isinstance(widget, QLineEdit):
            widget.clear()
        elif isinstance(widget, QComboBox):
            widget.setCurrentIndex(0)
        elif isinstance(widget, QCheckBox):
            widget.setChecked(False)
        elif isinstance(widget, QSpinBox):
            widget.setValue(0)

    def clear_fields(self):
        """
        Minden szerkesztő mező, checkbox, típusfüggő mező törlése/alaphelyzetbe állítása
        """
        for widget in self.fields.values():
            self.clear_widget(widget)
        for cb in self.damage_type_checks.values():
            cb.setChecked(False)
        for cb in self.damage_bonus_checks.values():
            cb.setChecked(False)
        for widget in self.type_fields.values():
            self.clear_widget(widget)

    def fill_fields(self, it):
        """
        Kitölti a szerkesztő mezőket az adott item adataival.
        - Statikus mezők, ár mezők, damage types, bonus attributes
        - Ár mezők: engine.currency_manager-rel konvertálva
        """
        for key, widget in self.fields.items():
            self.set_widget_value(widget, it.get(key, ""))
        for key in ["can_disarm", "can_break_weapon"]:
            if key in self.fields:
                self.set_widget_value(self.fields[key], it.get(key, False))
        try:
            from engine.currency_manager import CurrencyManager
            price = int(it.get('price', 0))
            price_parts = CurrencyManager().from_base(price)
            for key in self.manager.PRICE_FIELDS:
                curr = key.split('_')[1]
                self.set_widget_value(self.fields[key], price_parts.get(curr, 0))
        except Exception:
            for key in self.manager.PRICE_FIELDS:
                self.set_widget_value(self.fields[key], 0)
        for typ, cb in self.damage_type_checks.items():
            cb.setChecked(typ in it.get('damage_types', []))
        for attr, cb in self.damage_bonus_checks.items():
            cb.setChecked(attr in it.get('damage_bonus_attributes', []))

    def build_type_fields(self, type_value, item=None):
        """
        Típusfüggő mezők dinamikus generálása a szerkesztő panelen.
        - manager.TYPE_FIELD_DEFS alapján
        - Közelharci típusnál: wield_mode QComboBox, 'Változó' esetén extra mezők
        - item paraméterrel kitölti az értékeket
        """
        self.remove_type_fields_from_layout()
        # Típusfüggő QLineEdit mezők
        for label, key in self.manager.TYPE_FIELD_DEFS.get(type_value, []):
            le = QLineEdit()
            self.type_fields[key] = le
            self.edit_layout.addRow(QLabel(label), le)
            if item is not None:
                self.set_widget_value(le, item.get(key, ""))
        # Speciális wield_mode mező (csak közelharci)
        if type_value == "közelharci":
            wield_combo = QComboBox()
            wield_combo.addItems(["Egykezes", "Kétkezes", "Változó"])
            wield_combo.currentTextChanged.connect(self.wield_mode_changed)
            self.type_fields['wield_mode'] = wield_combo
            self.edit_layout.addRow(QLabel("Használati mód:"), wield_combo)
            wield_mode_val = item.get('wield_mode', 'Egykezes') if item is not None else 'Egykezes'
            self.set_widget_value(wield_combo, wield_mode_val)
            # A 'Változó' mezőket mindig létrehozzuk, de csak akkor engedélyezzük, ha a wield_mode 'Változó'
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
                if item is not None:
                    self.set_widget_value(le, item.get(key, ""))
            dual_cb = QCheckBox("Kétkezes harc lehetséges")
            self.type_fields['variable_dual_wield'] = dual_cb
            self.edit_layout.addRow(dual_cb)
            if item is not None:
                self.set_widget_value(dual_cb, item.get('variable_dual_wield', False))
            # Engedélyezés/letiltás az aktuális wield_mode alapján
            enable = wield_mode_val == "Változó"
            for key in [
                "variable_strength_req",
                "variable_dex_req",
                "variable_bonus_KE",
                "variable_bonus_TE",
                "variable_bonus_VE",
                "variable_dual_wield"
            ]:
                if key in self.type_fields:
                    self.type_fields[key].setEnabled(enable)
    def wield_mode_changed(self):
        """
        Ha a wield_mode mező 'Változó' <-> más mód között vált, újragenerálja a típusfüggő mezőket.
        - Csak akkor, ha tényleg változás történt
        """
        # Csak engedélyezzük/letiltjuk a mezőket, nem generáljuk újra őket
        combo = self.type_fields.get('wield_mode')
        if combo is None:
            return
        current = combo.currentText()
        enable = current == "Változó"
        for key in [
            "variable_strength_req",
            "variable_dex_req",
            "variable_bonus_KE",
            "variable_bonus_TE",
            "variable_bonus_VE",
            "variable_dual_wield"
        ]:
            if key in self.type_fields:
                self.type_fields[key].setEnabled(enable)
    def __init__(self):
        """
        Fő ablak inicializálása, manager példány, itemek betöltése, UI felépítése
        """
        super().__init__()
        self.setWindowTitle("Fegyverek és pajzsok szerkesztője")
        self.resize(1100, 700)
        self.manager = WeaponDataManager(WEAPONS_JSON)
        self.items = self.manager.load()
        self.selected_idx = None
        self.init_ui()

    def init_ui(self):
        """
        UI felépítése: fő layout, TreeView panel, szerkesztő panel, mezők, mentés gomb
        """
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout()
        central.setLayout(main_layout)

        # TreeView (lista) panel
        self.setup_treeview(main_layout)

        # Szerkesztő panel új layouttal: QVBoxLayout, legalul Mentés gomb
        self.edit_panel = QWidget()
        editor_vbox = QVBoxLayout()
        self.edit_panel.setLayout(editor_vbox)
        main_layout.addWidget(self.edit_panel, 2)

        # Mezők
        self.fields = {}
        self.edit_layout = QFormLayout()
        # Az edit_layout-ot egy widgetbe csomagoljuk
        edit_fields_widget = QWidget()
        edit_fields_widget.setLayout(self.edit_layout)
        editor_vbox.addWidget(edit_fields_widget)
        self.build_edit_fields()
        # Mentés gomb legalul
        btn_save = QPushButton("Mentés")
        btn_save.clicked.connect(self.save_item)
        editor_vbox.addWidget(btn_save, alignment=Qt.AlignBottom)
        # Típusfüggő mezők generálása induláskor is
        self.update_type_fields(self.fields['type'].currentText())

    def build_edit_fields(self):
        """
        Statikus szerkesztő mezők generálása (egyszer, indításkor)
        - BASE_FIELDS, ár mezők, damage types, bonus attributes, checkboxok
        - Típus/kategória mezők: QComboBox
        - Típusfüggő mezők: csak Qt váz, dinamikusan generálódnak
        """
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
        # Töltsük fel az első típushoz tartozó kategóriákkal, hogy ne legyen üres
        default_type = self.manager.get_weapon_types()[0]
        default_categories = self.manager.get_weapon_categories(default_type)
        self.fields['category'].addItems(default_categories)
        self.edit_layout.addRow(QLabel("Kategória:"), self.fields['category'])
        # Damage types egy sorban, Sebzés típus: label bal oldali oszlopban
        from PySide6.QtWidgets import QGridLayout, QWidget, QSpacerItem, QSizePolicy
        self.damage_type_checks = {}
        damage_grid = QGridLayout()
        damage_grid.setSpacing(4)
        for i, typ in enumerate(self.manager.DAMAGE_TYPES):
            cb = QCheckBox(typ.capitalize())
            cb.setSizePolicy(cb.sizePolicy().horizontalPolicy(), QWidget().sizePolicy().verticalPolicy())
            cb.setStyleSheet("QCheckBox { margin-top: 0px; margin-bottom: 0px; }")
            self.damage_type_checks[typ] = cb
            damage_grid.addWidget(cb, 0, i, alignment=Qt.AlignBottom)
        # Add a horizontal spacer to fill remaining space
        damage_grid.addItem(QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum), 0, len(self.manager.DAMAGE_TYPES))
        damage_grid_widget = QWidget()
        damage_grid_widget.setLayout(damage_grid)
        # Sebzés típus, Sebzés bónusz tulajdonsága, Ár: egy közös grid layoutban, három sorban
        from PySide6.QtWidgets import QGridLayout, QSpacerItem, QSizePolicy
        self.damage_type_checks = {}
        self.damage_bonus_checks = {}
        self.price_fields = {}
        combined_grid = QGridLayout()
        combined_grid.setSpacing(4)
        # Első sor: Sebzés típus
        damage_label = QLabel("Sebzés típus:")
        damage_label.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
        combined_grid.addWidget(damage_label, 0, 0, alignment=Qt.AlignLeft | Qt.AlignBottom)
        for i, typ in enumerate(self.manager.DAMAGE_TYPES):
            cb = QCheckBox(typ.capitalize())
            cb.setSizePolicy(cb.sizePolicy().horizontalPolicy(), QWidget().sizePolicy().verticalPolicy())
            cb.setStyleSheet("QCheckBox { margin-top: 0px; margin-bottom: 0px; }")
            self.damage_type_checks[typ] = cb
            combined_grid.addWidget(cb, 0, i + 1, alignment=Qt.AlignBottom)
        combined_grid.addItem(QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum), 0, len(self.manager.DAMAGE_TYPES) + 1)
        # Második sor: Sebzés bónusz tulajdonsága
        bonus_label = QLabel("Sebzés bónusz tulajdonsága:")
        bonus_label.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
        bonus_label.setMinimumWidth(90)
        combined_grid.addWidget(bonus_label, 1, 0, alignment=Qt.AlignLeft | Qt.AlignBottom)
        for i, attr in enumerate(self.manager.DAMAGE_BONUS_ATTRS):
            cb = QCheckBox(attr.capitalize())
            cb.setStyleSheet("QCheckBox { margin-top: 0px; margin-bottom: 0px; }")
            self.damage_bonus_checks[attr] = cb
            combined_grid.addWidget(cb, 1, i + 1, alignment=Qt.AlignBottom)
        combined_grid.addItem(QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum), 1, len(self.manager.DAMAGE_BONUS_ATTRS) + 1)
        # Harmadik sor: Ár mezők
        price_labels = ["Réz", "Ezüst", "Arany", "Mithrill"]
        price_label = QLabel("Ár:")
        price_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        price_label.setMinimumWidth(40)
        combined_grid.addWidget(price_label, 2, 0, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        from PySide6.QtWidgets import QVBoxLayout
        # Réz
        vbox_copper = QVBoxLayout()
        vbox_copper.setSpacing(2)
        lbl_copper = QLabel(price_labels[0])
        lbl_copper.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
        lbl_copper.setStyleSheet("QLabel { margin-bottom: 2px; }")
        sb_copper = QSpinBox()
        sb_copper.setMaximum(999999)
        sb_copper.setFixedWidth(48)
        self.fields[self.manager.PRICE_FIELDS[0]] = sb_copper
        vbox_copper.addWidget(lbl_copper)
        vbox_copper.addWidget(sb_copper)
        price_widget_copper = QWidget()
        price_widget_copper.setLayout(vbox_copper)
        price_widget_copper.setFixedWidth(60)
        combined_grid.addWidget(price_widget_copper, 2, 1, alignment=Qt.AlignTop)

        # Ezüst
        vbox_silver = QVBoxLayout()
        vbox_silver.setSpacing(2)
        lbl_silver = QLabel(price_labels[1])
        lbl_silver.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
        lbl_silver.setStyleSheet("QLabel { margin-bottom: 2px; }")
        sb_silver = QSpinBox()
        sb_silver.setMaximum(999999)
        sb_silver.setFixedWidth(48)
        self.fields[self.manager.PRICE_FIELDS[1]] = sb_silver
        vbox_silver.addWidget(lbl_silver)
        vbox_silver.addWidget(sb_silver)
        price_widget_silver = QWidget()
        price_widget_silver.setLayout(vbox_silver)
        price_widget_silver.setFixedWidth(60)
        combined_grid.addWidget(price_widget_silver, 2, 2, alignment=Qt.AlignTop)

        # Arany és Mithrill egy cellában, egy sorban
        hbox_gold_mithrill = QHBoxLayout()
        hbox_gold_mithrill.setSpacing(8)
        # Arany
        vbox_gold = QVBoxLayout()
        vbox_gold.setSpacing(2)
        lbl_gold = QLabel(price_labels[2])
        lbl_gold.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
        lbl_gold.setStyleSheet("QLabel { margin-bottom: 2px; }")
        sb_gold = QSpinBox()
        sb_gold.setMaximum(999999)
        sb_gold.setFixedWidth(48)
        self.fields[self.manager.PRICE_FIELDS[2]] = sb_gold
        vbox_gold.addWidget(lbl_gold)
        vbox_gold.addWidget(sb_gold)
        # Mithrill
        vbox_mithrill = QVBoxLayout()
        vbox_mithrill.setSpacing(2)
        lbl_mithrill = QLabel(price_labels[3])
        lbl_mithrill.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
        lbl_mithrill.setStyleSheet("QLabel { margin-bottom: 2px; }")
        sb_mithrill = QSpinBox()
        sb_mithrill.setMaximum(999999)
        sb_mithrill.setFixedWidth(48)
        self.fields[self.manager.PRICE_FIELDS[3]] = sb_mithrill
        vbox_mithrill.addWidget(lbl_mithrill)
        vbox_mithrill.addWidget(sb_mithrill)
        # Arany és Mithrill egymás mellett
        hbox_gold_mithrill.addLayout(vbox_gold)
        hbox_gold_mithrill.addLayout(vbox_mithrill)
        price_widget_gold_mithrill = QWidget()
        price_widget_gold_mithrill.setLayout(hbox_gold_mithrill)
        price_widget_gold_mithrill.setFixedWidth(120)
        combined_grid.addWidget(price_widget_gold_mithrill, 2, 3, alignment=Qt.AlignTop)
        combined_grid_widget = QWidget()
        combined_grid_widget.setLayout(combined_grid)
        self.edit_layout.addRow(combined_grid_widget)
        # Egyéb mezők, checkboxok
        for key in self.manager.CHECKBOX_FIELDS:
            cb = QCheckBox(key.replace('_', ' ').capitalize())
            self.fields[key] = cb
            self.edit_layout.addRow(cb)
        # Típusfüggő mezők (dinamikusan, csak Qt váz)
        self.type_fields = {}

    def update_type_fields(self, type_value):
        """
        Típus mező változásakor:
        - Frissíti a kategória mezőt
        - Újragenerálja a típusfüggő mezőket
        """
        # Frissítsd a kategória mezőt a típus alapján
        categories = self.manager.get_weapon_categories(type_value)
        self.fields['category'].clear()
        self.fields['category'].addItems(categories)
        self.build_type_fields(type_value)

    def new_item(self):
        """
        Új fegyver/pajzs létrehozása:
        - Minden mező törlése
        - Típus/kategória mezők alaphelyzetbe
        - Focus a név mezőre
        """
        self.selected_idx = None
        self.clear_fields()
        self.fields['type'].setCurrentIndex(0)
        self.update_type_fields(self.fields['type'].currentText())
        self.fields['category'].setCurrentIndex(0)
        self.fields['name'].setFocus()

    def save_item(self):
        """
        Aktuális item mentése:
        - Minden mező értékének begyűjtése
        - manager.build_item_from_fields-el item dict generálás
        - Validáció, hibaüzenet
        - Mentés: új vagy meglévő item
        - TreeView frissítése
        """
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
        """
        Kiválasztott item törlése:
        - selected_idx alapján
        - Megerősítő kérdés
        - Mentés, TreeView frissítés, mezők törlése
        """
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = WeaponsAndShieldsEditor()
    win.show()
    sys.exit(app.exec())
