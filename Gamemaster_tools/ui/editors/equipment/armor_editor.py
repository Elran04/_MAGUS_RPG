from config.paths import ARMOR_JSON
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTreeWidget,
    QTreeWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from utils.data.json_io import load_json_safe, save_json
from utils.ui.validation import ValidationError, validate_armor


class ArmorEditorQt(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Páncél szerkesztő")
        self.resize(1200, 760)

        # JSON storage
        self._armor_json_path = str(ARMOR_JSON)
        self.armors = self._load_armors()
        self.selected_idx = None
        self.abc_sort_asc = True
        self.sfe_sort_asc = False
        # Avoid premature signal handling before UI is fully built
        self._ui_ready = False

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout()
        central.setLayout(root)

        # Left: tree and actions
        left = QVBoxLayout()
        root.addLayout(left, stretch=1)
        title = QLabel("Páncélok (kategóriák szerint)")
        title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        left.addWidget(title)
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setUniformRowHeights(True)
        self.tree.setAnimated(True)
        self.tree.setSelectionMode(self.tree.SelectionMode.SingleSelection)
        left.addWidget(self.tree, stretch=1)

        btns_row = QHBoxLayout()
        self.btn_new = QPushButton("Új páncél")
        self.btn_new.clicked.connect(self.new_armor)
        self.btn_del = QPushButton("Törlés")
        self.btn_del.clicked.connect(self.delete_armor)
        btns_row.addWidget(self.btn_new)
        btns_row.addWidget(self.btn_del)
        left.addLayout(btns_row)

        sort_row = QHBoxLayout()
        self.btn_sort_abc = QPushButton("ABC ▲")
        self.btn_sort_abc.clicked.connect(self.sort_abc)
        self.btn_sort_sfe = QPushButton("SFÉ ▼")
        self.btn_sort_sfe.clicked.connect(self.sort_sfe)
        sort_row.addWidget(self.btn_sort_abc)
        sort_row.addWidget(self.btn_sort_sfe)
        left.addLayout(sort_row)

        # Right: editor form in a scroll area

        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        form = QWidget()
        form_layout = QGridLayout(form)
        right_layout.addWidget(form)
        root.addWidget(right_container, stretch=2)

        r = 0
        form_layout.addWidget(QLabel("Név:"), r, 0)
        self.inp_name = QLineEdit()
        form_layout.addWidget(self.inp_name, r, 1)
        r += 1

        form_layout.addWidget(QLabel("Azonosító:"), r, 0)
        self.inp_id = QLineEdit()
        form_layout.addWidget(self.inp_id, r, 1)
        r += 1

        form_layout.addWidget(QLabel("Részegységek és SFÉ:"), r, 0)
        r += 1
        parts = [
            "sisak",
            "mellvért",
            "vállvédő",
            "felkarvédő",
            "alkarvédő",
            "kesztyű",
            "combvédő",
            "lábszárvédő",
            "csizma",
        ]
        self.parts_checks = {}
        self.parts_sfe = {}
        part_grid = QGridLayout()
        form_layout.addLayout(part_grid, r, 0, 1, 2)
        for i, part in enumerate(parts):
            chk = QCheckBox(part)
            spn = QSpinBox()
            spn.setRange(0, 99)
            part_grid.addWidget(chk, i, 0)
            part_grid.addWidget(QLabel("SFÉ:"), i, 1)
            part_grid.addWidget(spn, i, 2)
            self.parts_checks[part] = chk
            self.parts_sfe[part] = spn
        r += 1

        form_layout.addWidget(QLabel("SFÉ override-ok (alzónák):"), r, 0)
        r += 1
        self.cmb_main = QComboBox()
        self.cmb_sub = QComboBox()
        self.spn_override = QSpinBox()
        self.spn_override.setRange(0, 99)
        self.btn_add_override = QPushButton("Hozzáadás")
        ov_row = QHBoxLayout()
        ov_row.addWidget(QLabel("Főzóna:"))
        ov_row.addWidget(self.cmb_main)
        ov_row.addWidget(QLabel("Alzóna:"))
        ov_row.addWidget(self.cmb_sub)
        ov_row.addWidget(QLabel("SFÉ:"))
        ov_row.addWidget(self.spn_override)
        ov_row.addWidget(self.btn_add_override)
        form_layout.addLayout(ov_row, r, 0, 1, 2)
        r += 1

        self.override_list = QListWidget()
        form_layout.addWidget(self.override_list, r, 0, 1, 2)
        r += 1
        self.btn_del_override = QPushButton("Kijelölt override törlése")
        self.btn_del_override.clicked.connect(self.delete_selected_override)
        form_layout.addWidget(self.btn_del_override, r, 1)
        r += 1

        # MGT and weight
        form_layout.addWidget(QLabel("MGT:"), r, 0)
        self.spn_mgt = QSpinBox()
        self.spn_mgt.setRange(0, 99)
        form_layout.addWidget(self.spn_mgt, r, 1)
        r += 1

        form_layout.addWidget(QLabel("Súly (kg):"), r, 0)
        self.spn_weight = QDoubleSpinBox()
        self.spn_weight.setRange(0.0, 1000.0)
        self.spn_weight.setDecimals(2)
        form_layout.addWidget(self.spn_weight, r, 1)
        r += 1

        # Armor construction type
        form_layout.addWidget(QLabel("Páncél típusa:"), r, 0)
        self.cmb_armor_type = QComboBox()
        self.cmb_armor_type.addItem("Lemezpáncél", userData="plate")
        self.cmb_armor_type.addItem("Rugalmas fém", userData="flexible_metal")
        self.cmb_armor_type.addItem("Bőr / Textil", userData="leather")
        form_layout.addWidget(self.cmb_armor_type, r, 1)
        r += 1

        # Layer number (for layered armor system)
        form_layout.addWidget(QLabel("Réteg szám:"), r, 0)
        self.spn_layer = QSpinBox()
        self.spn_layer.setRange(1, 3)
        self.spn_layer.setValue(3)
        self.spn_layer.setSuffix(". réteg")
        form_layout.addWidget(self.spn_layer, r, 1)
        r += 1

        # Price
        form_layout.addWidget(QLabel("Ár:"), r, 0, alignment=Qt.AlignmentFlag.AlignTop)
        price_row = QHBoxLayout()

        self.price_spins = {}
        for curr in ["réz", "ezüst", "arany", "mithrill"]:
            price_row.addWidget(QLabel(curr))
            spn = QSpinBox()
            spn.setRange(0, 9999999)
            price_row.addWidget(spn)
            self.price_spins[curr] = spn
        form_layout.addLayout(price_row, r, 1)
        r += 1

        # Description
        form_layout.addWidget(QLabel("Leírás:"), r, 0, alignment=Qt.AlignmentFlag.AlignTop)
        self.txt_desc = QTextEdit()
        form_layout.addWidget(self.txt_desc, r, 1)
        r += 1

        self.btn_save = QPushButton("Mentés")
        form_layout.addWidget(self.btn_save, r, 1)

        # Wiring
        self.btn_add_override.clicked.connect(self.add_override)
        self.cmb_main.currentTextChanged.connect(self._on_main_zone_changed)
        self.btn_save.clicked.connect(self.save_armor)

        self._load_zone_menus()
        self.refresh_list()
        # Now UI is ready; connect selection signal
        self.tree.currentItemChanged.connect(self.on_tree_select)
        self._ui_ready = True

    # JSON helpers (replace JsonManager usage)
    def _load_armors(self):
        return load_json_safe(self._armor_json_path, default=[])

    def _save_armors(self):
        save_json(self._armor_json_path, self.armors)

    # Helpers
    def _load_zone_menus(self):
        from engine.armor_manager import ArmorManager

        self._main_to_sub = ArmorManager.MAIN_ZONES
        self.cmb_main.clear()
        self.cmb_main.addItems(list(self._main_to_sub.keys()))
        self._on_main_zone_changed(self.cmb_main.currentText())

    def _on_main_zone_changed(self, main):
        subs = self._main_to_sub.get(main, []) if hasattr(self, "_main_to_sub") else []
        self.cmb_sub.clear()
        self.cmb_sub.addItems(subs)

    def _price_to_parts(self, price):
        from engine.currency_manager import CurrencyManager

        return CurrencyManager().from_base(int(price or 0))

    def _parts_to_price(self):
        from engine.currency_manager import CurrencyManager

        total = 0
        for curr in ["réz", "ezüst", "arany", "mithrill"]:
            total += CurrencyManager().to_base(self.price_spins[curr].value(), curr)
        return total

    def refresh_list(self):
        """Backward-compatible alias to rebuild the tree view."""
        self._build_tree()

    def _armor_type_label(self, type_key: str) -> str:
        mapping = {
            "plate": "Lemezpáncél",
            "flexible_metal": "Rugalmas fém",
            "leather": "Bőr / Textil",
        }
        return mapping.get(type_key or "leather", "Bőr / Textil")

    def _build_tree(self):
        # Preserve current selection (armor id) if any
        current_id = None
        cur_item = self.tree.currentItem() if hasattr(self, "tree") else None
        if cur_item and cur_item.parent():
            current_id = cur_item.data(0, Qt.ItemDataRole.UserRole)

        self.tree.blockSignals(True)
        self.tree.clear()

        # Prepare category nodes
        categories = {
            "plate": QTreeWidgetItem([self._armor_type_label("plate")]),
            "flexible_metal": QTreeWidgetItem([self._armor_type_label("flexible_metal")]),
            "leather": QTreeWidgetItem([self._armor_type_label("leather")]),
        }
        for key in ["plate", "flexible_metal", "leather"]:
            self.tree.addTopLevelItem(categories[key])

        # Add armors to categories
        for idx, armor in enumerate(self.armors):
            a_type = armor.get("armor_type", "leather")
            node = QTreeWidgetItem([f"{armor.get('name','')} (ID: {armor.get('id','-')})"])
            node.setData(0, Qt.ItemDataRole.UserRole, armor.get("id"))
            categories.get(a_type, categories["leather"]).addChild(node)

        # Expand categories that have content
        for key, cat in categories.items():
            cat.setExpanded(True)

        # Reselect previously selected armor if possible
        if current_id:
            self._select_tree_item_by_id(current_id)
        self.tree.blockSignals(False)

    def _select_tree_item_by_id(self, armor_id: str):
        if not armor_id:
            return
        root_count = self.tree.topLevelItemCount()
        for i in range(root_count):
            cat = self.tree.topLevelItem(i)
            for j in range(cat.childCount()):
                child = cat.child(j)
                if child.data(0, Qt.ItemDataRole.UserRole) == armor_id:
                    self.tree.setCurrentItem(child)
                    cat.setExpanded(True)
                    return

    def _find_armor_index_by_id(self, armor_id: str):
        if not armor_id:
            return None
        for i, a in enumerate(self.armors):
            if a.get("id") == armor_id:
                return i
        return None

    # Sorting
    def sort_abc(self):
        self.armors.sort(key=lambda a: a.get("name", "").lower(), reverse=not self.abc_sort_asc)
        self.abc_sort_asc = not self.abc_sort_asc
        self.btn_sort_abc.setText(f"ABC {'▲' if self.abc_sort_asc else '▼'}")
        self.refresh_list()

    def sort_sfe(self):
        def max_sfe(armor):
            parts = armor.get("parts", {})
            return max(parts.values()) if parts else 0

        self.armors.sort(key=max_sfe, reverse=not self.sfe_sort_asc)
        self.sfe_sort_asc = not self.sfe_sort_asc
        self.btn_sort_sfe.setText(f"SFÉ {'▲' if self.sfe_sort_asc else '▼'}")
        self.refresh_list()

    # Overrides list management
    def add_override(self):
        sub = self.cmb_sub.currentText()
        if not sub:
            QMessageBox.warning(self, "Hiba", "Válassz alzónát és adj meg SFÉ értéket!")
            return
        # check for duplicates by sub
        for i in range(self.override_list.count()):
            it = self.override_list.item(i)
            data = it.data(Qt.ItemDataRole.UserRole)
            if data and data.get("sub") == sub:
                QMessageBox.warning(
                    self, "Hiba", "Ez az alzóna már szerepel az override-ok között!"
                )
                return
        item = {
            "main": self.cmb_main.currentText(),
            "sub": sub,
            "value": int(self.spn_override.value()),
        }
        lw_item = QListWidgetItem(f"{item['sub']} ({item['main']}): {item['value']}")
        lw_item.setData(Qt.ItemDataRole.UserRole, item)
        self.override_list.addItem(lw_item)

    def _load_overrides_to_ui(self, overrides_dict):
        self.override_list.clear()
        # Build from dict of sub->value; infer main by mapping
        from engine.armor_manager import ArmorManager

        for main, subs in ArmorManager.MAIN_ZONES.items():
            for sub in subs:
                if sub in overrides_dict:
                    val = overrides_dict[sub]
                    lw_item = QListWidgetItem(f"{sub} ({main}): {val}")
                    lw_item.setData(
                        Qt.ItemDataRole.UserRole, {"main": main, "sub": sub, "value": val}
                    )
                    self.override_list.addItem(lw_item)

    def _overrides_from_ui(self):
        result = {}
        for i in range(self.override_list.count()):
            data = self.override_list.item(i).data(Qt.ItemDataRole.UserRole)
            if data:
                result[data["sub"]] = data["value"]
        return result

    def delete_selected_override(self):
        row = self.override_list.currentRow()
        if row >= 0:
            self.override_list.takeItem(row)

    # Selection and data binding
    def on_select(self, row):
        if not getattr(self, "_ui_ready", False):
            return
        if row < 0 or row >= len(self.armors):
            self.selected_idx = None
            return
        self.selected_idx = row
        armor = self.armors[row]
        self.inp_name.setText(armor.get("name", ""))
        self.inp_id.setText(armor.get("id", ""))
        # parts
        parts = armor.get("parts", {})
        for part, chk in self.parts_checks.items():
            val = int(parts.get(part, 0))
            chk.setChecked(val > 0)
            self.parts_sfe[part].setValue(val)
        # overrides
        self._load_overrides_to_ui(armor.get("protection_overrides", {}))
        # mgt, weight
        try:
            self.spn_mgt.setValue(int(armor.get("mgt", 0)))
        except (ValueError, TypeError):
            self.spn_mgt.setValue(0)
        try:
            self.spn_weight.setValue(float(armor.get("weight", 0)))
        except (ValueError, TypeError):
            self.spn_weight.setValue(0.0)
        # price
        parts_price = self._price_to_parts(armor.get("price", 0))
        for curr in ["réz", "ezüst", "arany", "mithrill"]:
            self.price_spins[curr].setValue(int(parts_price.get(curr, 0)))
        # description
        self.txt_desc.setPlainText(armor.get("description", ""))
        # armor type
        armor_type = armor.get("armor_type", "leather")
        found = False
        for i in range(self.cmb_armor_type.count()):
            if self.cmb_armor_type.itemData(i) == armor_type:
                self.cmb_armor_type.setCurrentIndex(i)
                found = True
                break
        if not found:
            # fallback to leather
            for i in range(self.cmb_armor_type.count()):
                if self.cmb_armor_type.itemData(i) == "leather":
                    self.cmb_armor_type.setCurrentIndex(i)
                    break
        # layer number
        try:
            self.spn_layer.setValue(int(armor.get("layer", 3)))
        except (ValueError, TypeError):
            self.spn_layer.setValue(3)

    def on_tree_select(self, current, previous):
        if not getattr(self, "_ui_ready", False):
            return
        if current is None:
            self.selected_idx = None
            return
        # Ignore category headers (no parent means top-level)
        if current.parent() is None:
            self.selected_idx = None
            return
        armor_id = current.data(0, Qt.ItemDataRole.UserRole)
        idx = self._find_armor_index_by_id(armor_id)
        if idx is None:
            self.selected_idx = None
            return
        # Populate form from selected armor
        self.on_select(idx)

    def _collect_parts(self):
        result = {}
        for part, chk in self.parts_checks.items():
            if chk.isChecked():
                result[part] = int(self.parts_sfe[part].value())
            else:
                result[part] = 0
        return result

    def save_armor(self):
        # Build armor dict
        armor = {
            "name": self.inp_name.text().strip(),
            "id": self.inp_id.text().strip(),
            "parts": self._collect_parts(),
            "protection_overrides": self._overrides_from_ui(),
            "mgt": int(self.spn_mgt.value()),
            "weight": float(self.spn_weight.value()),
            "price": int(self._parts_to_price()),
            "description": self.txt_desc.toPlainText().strip(),
            "armor_type": self.cmb_armor_type.currentData(),
            "layer": int(self.spn_layer.value()),
        }
        # Validate armor using centralized validator
        try:
            validate_armor(armor)
        except ValidationError:
            QMessageBox.critical(self, "Hiba", "Hiányzó vagy hibás mező!")
            return
        # Determine target index to select after save without being affected by signals
        target_idx = self.selected_idx
        # If nothing is selected but an item with same ID exists, update that instead of appending
        if target_idx is None and armor["id"]:
            for i, a in enumerate(self.armors):
                if a.get("id") == armor["id"]:
                    target_idx = i
                    break

        if target_idx is not None:
            self.armors[target_idx] = armor
        else:
            self.armors.append(armor)
            target_idx = len(self.armors) - 1

        # Persist and refresh tree while blocking selection-change signals
        self._save_armors()
        saved_id = armor.get("id")
        self.tree.blockSignals(True)
        self.refresh_list()
        # Reselect saved armor by id
        if saved_id:
            self._select_tree_item_by_id(saved_id)
        self.tree.blockSignals(False)
        # Update internal selection state and UI fields based on new index
        self.selected_idx = target_idx
        self.on_select(target_idx)
        QMessageBox.information(self, "Mentés", "Páncél mentve!")

    def new_armor(self):
        self.selected_idx = None
        self.inp_name.clear()
        self.inp_id.clear()
        for part in self.parts_checks:
            self.parts_checks[part].setChecked(False)
            self.parts_sfe[part].setValue(0)
        self.override_list.clear()
        self.spn_mgt.setValue(0)
        self.spn_weight.setValue(0.0)
        for curr in ["réz", "ezüst", "arany", "mithrill"]:
            self.price_spins[curr].setValue(0)
        self.txt_desc.clear()
        # Clear tree selection as well
        if hasattr(self, "tree"):
            self.tree.clearSelection()

    def delete_armor(self):
        cur = self.tree.currentItem() if hasattr(self, "tree") else None
        if cur is None or cur.parent() is None:
            QMessageBox.warning(self, "Törlés", "Nincs kiválasztva páncél.")
            return
        armor_id = cur.data(0, Qt.ItemDataRole.UserRole)
        idx = self._find_armor_index_by_id(armor_id)
        if idx is None:
            QMessageBox.warning(self, "Törlés", "A kiválasztott páncél nem található.")
            return
        name = self.armors[idx].get("name", "-")
        answer = QMessageBox.question(
            self,
            "Törlés",
            f"Biztosan törlöd ezt a páncélt?\n{name}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.armors.pop(idx)
            self._save_armors()
            self.refresh_list()
            self.selected_idx = None


if __name__ == "__main__":
    import os as _os
    import sys

    sys.path.insert(
        0, _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..", "..", ".."))
    )
    from utils.ui.dark_mode import apply_dark_mode

    app = QApplication(sys.argv)
    apply_dark_mode(app)
    w = ArmorEditorQt()
    w.show()
    sys.exit(app.exec())
