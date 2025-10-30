from PySide6 import QtWidgets, QtCore
import os
import sys

# Ensure Gamemaster_tools root on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from utils.class_db_manager import ClassDBManager
from data.race.race_list import ALL_RACES
from data.race.race_age_stat_modifiers import AGE_LIMITS
from engine.character import is_valid_character, GENDER_RESTRICTIONS, RACE_RESTRICTIONS


class BasicSpecStepWidget(QtWidgets.QWidget):
    """Left: basic data; Right: specialization selection & description.
    Provides validate() and getters to return state to the wizard.
    """

    def __init__(self, base_dir: str, class_db: ClassDBManager | None = None):
        super().__init__()
        self.BASE_DIR = base_dir
        self.class_db = class_db or ClassDBManager()

        self.specializations = ["Nincs"]
        self.spec_data = {}
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
        self.gender_combo = QtWidgets.QComboBox(); self.gender_combo.addItems(["Férfi", "Nő"])
        self.age_edit = QtWidgets.QLineEdit()
        self.race_combo = QtWidgets.QComboBox(); self.race_combo.addItems(ALL_RACES)
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
        self.class_combo.currentTextChanged.connect(self.populate_specializations_for_selected_class)

    def _initial_fill(self):
        self.update_age_limits()
        self.update_class_options()

    # --- Behavior ---
    def update_age_limits(self):
        race = self.race_combo.currentText()
        limits = AGE_LIMITS.get(race, (13, 100))
        self.age_limits_label.setText(f"Engedélyezett kor: {limits[0]} - {limits[1]}")

    def update_class_options(self):
        race = self.race_combo.currentText()
        gender = self.gender_combo.currentText()
        restricted_by_gender = GENDER_RESTRICTIONS.get(gender, set())
        restricted_by_race = RACE_RESTRICTIONS.get(race, set())
        classes = list(self.class_db.list_classes())
        allowed = [name for (_cid, name) in classes if name not in restricted_by_gender and name not in restricted_by_race]
        current_class = self.class_combo.currentText() if self.class_combo.count() > 0 else None
        self.class_combo.blockSignals(True)
        self.class_combo.clear()
        self.class_combo.addItems(allowed)
        if current_class in allowed:
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
        desc_path = os.path.join(self.BASE_DIR, 'data', 'Class', 'descriptions', desc_file)
        if os.path.exists(desc_path):
            try:
                with open(desc_path, 'r', encoding='utf-8') as f:
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
            desc_path = os.path.join(self.BASE_DIR, 'data', 'Class', 'descriptions', desc_file)
            if os.path.exists(desc_path):
                try:
                    with open(desc_path, 'r', encoding='utf-8') as f:
                        self.spec_desc.setMarkdown(f.read())
                except Exception as e:
                    self.spec_desc.setPlainText(f"Hiba a leírás betöltésekor:\n{e}")
            else:
                self.spec_desc.setPlainText(f"Nincs leírás fájl a {self.get_data().get('Kaszt')} kaszthoz.\n(Keresett fájl: {desc_file})")
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
        if not is_valid_character(gender, race, klass):
            self.result_label.setText(f"A(z) {race.lower()} {gender.lower()} nem lehet {klass.lower()}!")
            return False
        try:
            age_int = int(age)
        except ValueError:
            self.result_label.setText("A kor csak szám lehet.")
            return False
        limits = AGE_LIMITS.get(race, (13, 100))
        if age_int < limits[0] or age_int > limits[1]:
            self.result_label.setText(f"A(z) {race} kora {limits[0]} és {limits[1]} között kell legyen.")
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
