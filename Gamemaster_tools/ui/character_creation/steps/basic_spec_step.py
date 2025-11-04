import os
import sys
from pathlib import Path
from typing import Any

from PySide6 import QtCore, QtWidgets

# Ensure Gamemaster_tools root on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from engine.race_manager import RaceManager
from engine.restrictions_manager import GENDER_RESTRICTIONS, is_class_allowed
from utils.data.class_db_manager import ClassDBManager
from config.paths import DATA_DIR, CLASSES_DESCRIPTIONS_DIR

# Initialize race manager using centralized data directory
_race_manager = RaceManager(DATA_DIR)
_race_manager.load_all()


class BasicSpecStepWidget(QtWidgets.QWidget):
    """Left: basic data; Right: specialization selection & description.
    Provides validate() and getters to return state to the wizard.
    """

    def __init__(self, base_dir: str, class_db: ClassDBManager | None = None):
        super().__init__()
        self.BASE_DIR = base_dir
        self.class_db = class_db or ClassDBManager()

        self.specializations = ["Nincs"]
        self.spec_data: dict[str, Any] = {}
        self.selected_class_id = None

        self._build_ui()
        self._wire()
        self._initial_fill()

    # --- UI construction ---
    def _build_ui(self):
        hlayout = QtWidgets.QHBoxLayout(self)
        hlayout.setContentsMargins(0, 0, 0, 0)
        hlayout.setSpacing(16)

        # Left form
        left = QtWidgets.QWidget()
        self.left_form = QtWidgets.QFormLayout(left)
        self.left_form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.left_form.setVerticalSpacing(10)  # Control spacing between rows

        self.name_edit = QtWidgets.QLineEdit()
        self.gender_combo = QtWidgets.QComboBox()
        self.gender_combo.addItems(["Férfi", "Nő"])
        self.age_edit = QtWidgets.QLineEdit()
        # Get race names from RaceManager
        race_names = _race_manager.get_race_names()
        self.race_combo = QtWidgets.QComboBox()
        self.race_combo.addItems(race_names)

        # Class tree view instead of combo box
        self.class_tree = QtWidgets.QTreeWidget()
        self.class_tree.setHeaderHidden(True)
        self.class_tree.setMaximumHeight(200)
        self.class_tree.setAlternatingRowColors(True)

        self.result_label = QtWidgets.QLabel("")
        self.result_label.setStyleSheet("color:#c33;")
        self.age_limits_label = QtWidgets.QLabel("")
        self.age_limits_label.setStyleSheet(
            "color:#888; font-size:9pt; font-style:italic; margin-top: 2px; margin-bottom: 2px;"
        )

        self.left_form.addRow("Név:", self.name_edit)
        self.left_form.addRow("Nem:", self.gender_combo)
        self.left_form.addRow("Kor:", self.age_edit)

        # Add age limits as a compact info row (no label, just widget)
        age_limits_container = QtWidgets.QWidget()
        age_limits_container.setMaximumHeight(20)
        age_limits_layout = QtWidgets.QHBoxLayout(age_limits_container)
        age_limits_layout.setContentsMargins(0, 0, 0, 0)
        age_limits_layout.addWidget(self.age_limits_label)
        self.left_form.addRow("", age_limits_container)

        self.left_form.addRow("Faj:", self.race_combo)
        self.left_form.addRow("Kaszt:", self.class_tree)
        self.left_form.addRow("", self.result_label)

        # Right panel
        right = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(QtWidgets.QLabel("Specializáció:"))
        self.spec_combo = QtWidgets.QComboBox()
        self.spec_combo.currentTextChanged.connect(self.load_specialization_description)
        right_layout.addWidget(self.spec_combo)
        right_layout.addWidget(QtWidgets.QLabel("Leírás:"))
        self.spec_desc = QtWidgets.QTextBrowser()
        self.spec_desc.setOpenExternalLinks(False)
        self.spec_desc.setPlaceholderText("Válassz egy specializációt a leírás megtekintéséhez...")
        right_layout.addWidget(self.spec_desc, stretch=1)

        hlayout.addWidget(left, stretch=1)
        hlayout.addWidget(right, stretch=2)

    def _wire(self):
        self.race_combo.currentTextChanged.connect(self.update_age_limits)
        self.race_combo.currentTextChanged.connect(self.update_class_options)
        self.gender_combo.currentTextChanged.connect(self.update_class_options)
        self.class_tree.itemSelectionChanged.connect(
            self.populate_specializations_for_selected_class
        )

    def _initial_fill(self):
        self.update_age_limits()
        self.update_class_options()

    # --- Behavior ---
    def update_age_limits(self):
        race_name = self.race_combo.currentText()
        # Convert race name to ID
        race_id = race_name.lower().replace(" ", "_")
        race_id = race_id.replace("á", "a").replace("é", "e").replace("ö", "o")
        race_id = race_id.replace("ő", "o").replace("ü", "u").replace("ű", "u").replace("í", "i")

        race = _race_manager.get_race(race_id)
        if race:
            limits = (race.age.min, race.age.max)
        else:
            limits = (13, 100)  # Fallback
        self.age_limits_label.setText(f"Engedélyezett kor: {limits[0]} - {limits[1]}")

    def update_class_options(self):
        race_name = self.race_combo.currentText()
        gender = self.gender_combo.currentText()
        # resolve race id and object
        race_id = race_name.lower().replace(" ", "_")
        race_id = race_id.replace("á", "a").replace("é", "e").replace("ö", "o")
        race_id = race_id.replace("ő", "o").replace("ü", "u").replace("ű", "u").replace("í", "i")
        race_obj = _race_manager.get_race(race_id)

        classes = list(self.class_db.list_classes())  # (id, name)
        name_set = {name for (_cid, name) in classes}
        id_to_name = {cid: name for (cid, name) in classes}
        # Normalize allowed list from JSON (it may contain class IDs or names)
        allowed_by_race = set()
        if race_obj:
            for token in race_obj.class_restrictions.allowed_classes:
                if token in name_set:
                    allowed_by_race.add(token)
                elif token in id_to_name:
                    allowed_by_race.add(id_to_name[token])
        if not allowed_by_race:
            allowed_by_race = set(name_set)
        restricted_by_gender = set(GENDER_RESTRICTIONS.get(gender, set()))

        allowed = [
            (cid, name)
            for (cid, name) in classes
            if name in allowed_by_race and name not in restricted_by_gender
        ]

        # Remember current selection
        current_class = None
        selected_items = self.class_tree.selectedItems()
        if selected_items:
            current_class = selected_items[0].text(0)

        # Clear and rebuild tree
        self.class_tree.blockSignals(True)
        self.class_tree.clear()

        # Group classes by category (you can customize this categorization)
        categories: dict[str, list[tuple[str, str]]] = {
            "Harcos": [],
            "Szerencsevadász": [],
            "Harcművész": [],
            "Pap": [],
            "Varázshasználó": [],
            "Egyéb": [],
        }

        # Categorize classes (customize based on your class structure)
        warrior_classes = {
            "Harcos",
            "Lovag",
            "Gladiátor",
            "Barbár",
            "Amazon",
            "Fejvadász",
            "Bajvívó",
        }
        magic_classes = {"Varázsló", "Tűzvarázsló", "Boszorkány", "Boszorkánymester"}
        rogue_classes = {"Tolvaj", "Bárd"}
        martial_classes = {"Harcművész", "Kardművész"}
        priest_classes = {"Pap", "Szerzetes", "Paplovag", "Sámán"}

        for cid, name in sorted(allowed, key=lambda x: x[1]):
            if name in warrior_classes:
                categories["Harcos"].append((cid, name))
            elif name in magic_classes:
                categories["Varázshasználó"].append((cid, name))
            elif name in rogue_classes:
                categories["Szerencsevadász"].append((cid, name))
            elif name in martial_classes:
                categories["Harcművész"].append((cid, name))
            elif name in priest_classes:
                categories["Pap"].append((cid, name))
            else:
                categories["Egyéb"].append((cid, name))

        # Build tree structure
        for category_name, class_list in categories.items():
            if not class_list:
                continue

            if len(class_list) == 1:
                # If only one class in category, don't create parent node
                cid, name = class_list[0]
                item = QtWidgets.QTreeWidgetItem(self.class_tree)
                item.setText(0, name)
                item.setData(0, QtCore.Qt.ItemDataRole.UserRole, cid)
                if name == current_class:
                    self.class_tree.setCurrentItem(item)
            else:
                # Create category parent
                parent = QtWidgets.QTreeWidgetItem(self.class_tree)
                parent.setText(0, category_name)
                parent.setData(0, QtCore.Qt.ItemDataRole.UserRole, None)  # Category has no ID
                parent.setFlags(parent.flags() & ~QtCore.Qt.ItemFlag.ItemIsSelectable)

                for cid, name in class_list:
                    item = QtWidgets.QTreeWidgetItem(parent)
                    item.setText(0, name)
                    item.setData(0, QtCore.Qt.ItemDataRole.UserRole, cid)
                    if name == current_class:
                        self.class_tree.setCurrentItem(item)

                parent.setExpanded(True)

        # If no selection was restored and we have items, select the first leaf
        if not self.class_tree.selectedItems() and self.class_tree.topLevelItemCount() > 0:
            first_item = self.class_tree.topLevelItem(0)
            # If it has children, select first child; otherwise select it
            if first_item and first_item.childCount() > 0:
                first_child = first_item.child(0)
                if first_child:
                    self.class_tree.setCurrentItem(first_child)
            elif first_item:
                self.class_tree.setCurrentItem(first_item)

        self.class_tree.blockSignals(False)
        self.populate_specializations_for_selected_class()

    def populate_specializations_for_selected_class(self):
        selected_items = self.class_tree.selectedItems()
        if not selected_items:
            self.selected_class_id = None
            self.specializations = ["Nincs"]
            self.spec_data = {}
            self.spec_combo.blockSignals(True)
            self.spec_combo.clear()
            self.spec_combo.addItems(self.specializations)
            self.spec_combo.blockSignals(False)
            return

        selected_item = selected_items[0]
        sel_name = selected_item.text(0)
        self.selected_class_id = selected_item.data(0, QtCore.Qt.ItemDataRole.UserRole)

        # If selected item is a category (no UserRole data), do nothing
        if self.selected_class_id is None:
            return

        self.specializations = ["Nincs"]
        self.spec_data = {}
        if self.selected_class_id:
            try:
                specs = self.class_db.list_specialisations(self.selected_class_id)
                for spec in specs:
                    spec_name = spec["specialisation_name"]
                    self.specializations.append(spec_name)
                    self.spec_data[spec_name] = spec
            except Exception:
                pass
        self.spec_combo.blockSignals(True)
        self.spec_combo.clear()
        self.spec_combo.addItems(self.specializations)
        self.spec_combo.blockSignals(False)
        self.load_specialization_description(self.spec_combo.currentText())

    def load_specialization_description(self, spec_name):
        if spec_name == "Nincs" or not spec_name:
            self.load_base_class_description()
            return
        spec_info = self.spec_data.get(spec_name)
        if not spec_info:
            self.spec_desc.clear()
            return
        desc_file = spec_info.get("specialisation_description", "")
        if not desc_file:
            self.spec_desc.setPlainText("Nincs leírás fájl megadva ehhez a specializációhoz.")
            return
        desc_path = (Path(CLASSES_DESCRIPTIONS_DIR) / desc_file)
        if desc_path.exists():
            try:
                with open(desc_path, encoding="utf-8") as f:
                    self.spec_desc.setMarkdown(f.read())
            except Exception as e:
                self.spec_desc.setPlainText(f"Hiba a leírás betöltésekor:\n{e}")
        else:
            self.spec_desc.setPlainText(f"A leírás fájl nem található:\n{desc_file}")

    def load_base_class_description(self):
        if not self.selected_class_id:
            self.spec_desc.clear()
            self.spec_desc.setPlaceholderText("Nincs kaszt kiválasztva.")
            return
        try:
            class_details = self.class_db.get_class_details(self.selected_class_id)
            desc_file = class_details.get("class_description_file", "")
            if not desc_file:
                desc_file = f"{self.selected_class_id}.md"
            desc_path = (Path(CLASSES_DESCRIPTIONS_DIR) / desc_file)
            if desc_path.exists():
                try:
                    with open(desc_path, encoding="utf-8") as f:
                        self.spec_desc.setMarkdown(f.read())
                except Exception as e:
                    self.spec_desc.setPlainText(f"Hiba a leírás betöltésekor:\n{e}")
            else:
                self.spec_desc.setPlainText(
                    f"Nincs leírás fájl a {self.get_data().get('Kaszt')} kaszthoz.\n(Keresett fájl: {desc_file})"
                )
        except Exception as e:
            self.spec_desc.setPlainText(f"Hiba a kaszt részletek betöltésekor:\n{e}")

    # --- Data & validation ---
    def validate_basic_data(self) -> bool:
        name = self.name_edit.text().strip()
        gender = self.gender_combo.currentText()
        age = self.age_edit.text().strip()
        race = self.race_combo.currentText()

        # Get selected class from tree
        selected_items = self.class_tree.selectedItems()
        klass = selected_items[0].text(0) if selected_items else ""

        if not name:
            self.result_label.setText("Adj meg egy nevet!")
            return False
        if not age:
            self.result_label.setText("Add meg a karakter korát!")
            return False
        # Validate against gender and race-allowed list
        race_id = race.lower().replace(" ", "_")
        race_id = race_id.replace("á", "a").replace("é", "e").replace("ö", "o")
        race_id = race_id.replace("ő", "o").replace("ü", "u").replace("ű", "u").replace("í", "i")
        race_obj = _race_manager.get_race(race_id)
        # Normalize allowed list to names for validation
        allowed_for_race = None
        if race_obj:
            classes = list(self.class_db.list_classes())
            name_set = {name for (_cid, name) in classes}
            id_to_name = {cid: name for (cid, name) in classes}
            allowed_names = []
            for token in race_obj.class_restrictions.allowed_classes:
                if token in name_set:
                    allowed_names.append(token)
                elif token in id_to_name:
                    allowed_names.append(id_to_name[token])
            allowed_for_race = allowed_names if allowed_names else None
        if not is_class_allowed(gender, klass, allowed_for_race):
            self.result_label.setText(
                f"A(z) {race.lower()} {gender.lower()} nem lehet {klass.lower()}!"
            )
            return False
        try:
            age_int = int(age)
        except ValueError:
            self.result_label.setText("A kor csak szám lehet.")
            return False

        # Get race age limits from RaceManager
        race_id = race.lower().replace(" ", "_")
        race_id = race_id.replace("á", "a").replace("é", "e").replace("ö", "o")
        race_id = race_id.replace("ő", "o").replace("ü", "u").replace("ű", "u").replace("í", "i")

        race_obj = _race_manager.get_race(race_id)
        if race_obj:
            limits = (race_obj.age.min, race_obj.age.max)
        else:
            limits = (13, 100)

        if age_int < limits[0] or age_int > limits[1]:
            self.result_label.setText(
                f"A(z) {race} kora {limits[0]} és {limits[1]} között kell legyen."
            )
            return False
        self.result_label.setText("")
        return True

    def get_data(self) -> dict:
        selected_items = self.class_tree.selectedItems()
        selected_class = selected_items[0].text(0) if selected_items else ""

        data = {
            "Név": self.name_edit.text().strip(),
            "Nem": self.gender_combo.currentText(),
            "Kor": self.age_edit.text().strip(),
            "Faj": self.race_combo.currentText(),
            "Kaszt": selected_class,
            "Specializáció": self.spec_combo.currentText(),
            "Spec_leírás": self.spec_desc.toPlainText().strip(),
        }
        return data

    def get_selected_class_id(self):
        return self.selected_class_id

    def get_spec_data(self):
        return self.spec_data

    # --- Prefill from existing data ---
    def set_data(self, data: dict):
        """Prefill the form from a provided data dict produced by get_data().

        Keys used: Név, Nem, Kor, Faj, Kaszt, Specializáció.
        """
        if not data:
            return
        # Basic fields
        name = data.get("Név")
        if name:
            self.name_edit.setText(str(name))
        gender = data.get("Nem")
        if gender and gender in [
            self.gender_combo.itemText(i) for i in range(self.gender_combo.count())
        ]:
            self.gender_combo.setCurrentText(gender)
        race = data.get("Faj")
        if race and race in [self.race_combo.itemText(i) for i in range(self.race_combo.count())]:
            self.race_combo.setCurrentText(race)
        age = data.get("Kor")
        if age is not None:
            self.age_edit.setText(str(age))

        # Ensure class options reflect current race/gender
        self.update_class_options()

        # Class selection - search for the class in the tree
        klass = data.get("Kaszt")
        if klass:
            # Search through tree items
            found = False
            for i in range(self.class_tree.topLevelItemCount()):
                top_item = self.class_tree.topLevelItem(i)
                if not top_item:
                    continue
                # Check if top-level item matches
                if top_item.text(0) == klass:
                    self.class_tree.setCurrentItem(top_item)
                    found = True
                    break
                # Check children
                for j in range(top_item.childCount()):
                    child_item = top_item.child(j)
                    if child_item and child_item.text(0) == klass:
                        self.class_tree.setCurrentItem(child_item)
                        found = True
                        break
                if found:
                    break

        # Populate specs for the selected class and set selection
        self.populate_specializations_for_selected_class()
        spec = data.get("Specializáció")
        if spec and spec in [self.spec_combo.itemText(i) for i in range(self.spec_combo.count())]:
            self.spec_combo.setCurrentText(spec)
        else:
            # Default to "Nincs" if not provided or missing
            if self.spec_combo.findText("Nincs") != -1:
                self.spec_combo.setCurrentText("Nincs")
