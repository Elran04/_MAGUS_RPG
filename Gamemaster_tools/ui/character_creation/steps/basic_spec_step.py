import os
import sys
from pathlib import Path
from typing import Any

from PySide6 import QtCore, QtWidgets

# Ensure Gamemaster_tools root on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from engine.race_manager import RaceManager
from engine.restrictions import GENDER_RESTRICTIONS, is_class_allowed
from utils.class_db_manager import ClassDBManager

# Initialize race manager
_data_dir = Path(__file__).resolve().parent.parent.parent.parent / "data"
_race_manager = RaceManager(_data_dir)
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

        self.name_edit = QtWidgets.QLineEdit()
        self.gender_combo = QtWidgets.QComboBox()
        self.gender_combo.addItems(["Férfi", "Nő"])
        self.age_edit = QtWidgets.QLineEdit()
        # Get race names from RaceManager
        race_names = _race_manager.get_race_names()
        self.race_combo = QtWidgets.QComboBox()
        self.race_combo.addItems(race_names)
        self.class_combo = QtWidgets.QComboBox()
        self.result_label = QtWidgets.QLabel("")
        self.result_label.setStyleSheet("color:#c33;")
        self.age_limits_label = QtWidgets.QLabel("")

        self.left_form.addRow("Név:", self.name_edit)
        self.left_form.addRow("Nem:", self.gender_combo)
        self.left_form.addRow("Kor:", self.age_edit)
        self.left_form.addRow("Korhatár:", self.age_limits_label)
        self.left_form.addRow("Faj:", self.race_combo)
        self.left_form.addRow("Kaszt:", self.class_combo)
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
        self.class_combo.currentTextChanged.connect(
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
            name
            for (_cid, name) in classes
            if name in allowed_by_race and name not in restricted_by_gender
        ]
        current_class = self.class_combo.currentText() if self.class_combo.count() > 0 else None
        self.class_combo.blockSignals(True)
        self.class_combo.clear()
        self.class_combo.addItems(sorted(allowed))
        if current_class and current_class in allowed:
            self.class_combo.setCurrentText(current_class)
        self.class_combo.blockSignals(False)
        self.populate_specializations_for_selected_class()

    def populate_specializations_for_selected_class(self):
        sel_name = self.class_combo.currentText()
        self.selected_class_id = None
        for class_id, class_name in self.class_db.list_classes():
            if class_name == sel_name:
                self.selected_class_id = class_id
                break
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
        desc_path = os.path.join(self.BASE_DIR, "data", "Class", "descriptions", desc_file)
        if os.path.exists(desc_path):
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
            desc_path = os.path.join(self.BASE_DIR, "data", "Class", "descriptions", desc_file)
            if os.path.exists(desc_path):
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
        klass = self.class_combo.currentText()
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
        data = {
            "Név": self.name_edit.text().strip(),
            "Nem": self.gender_combo.currentText(),
            "Kor": self.age_edit.text().strip(),
            "Faj": self.race_combo.currentText(),
            "Kaszt": self.class_combo.currentText(),
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

        # Class selection
        klass = data.get("Kaszt")
        if klass and klass in [
            self.class_combo.itemText(i) for i in range(self.class_combo.count())
        ]:
            self.class_combo.setCurrentText(klass)

        # Populate specs for the selected class and set selection
        self.populate_specializations_for_selected_class()
        spec = data.get("Specializáció")
        if spec and spec in [self.spec_combo.itemText(i) for i in range(self.spec_combo.count())]:
            self.spec_combo.setCurrentText(spec)
        else:
            # Default to "Nincs" if not provided or missing
            if self.spec_combo.findText("Nincs") != -1:
                self.spec_combo.setCurrentText("Nincs")
