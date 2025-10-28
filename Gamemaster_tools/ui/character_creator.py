from PySide6 import QtWidgets, QtCore
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.class_db_manager import ClassDBManager
from utils.character_storage import save_character
from data.race.race_list import ALL_RACES
from data.race.race_age_stat_modifiers import AGE_LIMITS
from engine.character import generate_character, is_valid_character, GENDER_RESTRICTIONS, RACE_RESTRICTIONS

class CharacterWizardQt(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Karakteralkotás varázsló")
        self.resize(600, 600)
        self.class_db = ClassDBManager()
        self.data = {}
        self.step = 0
        self.specializations = ["Nincs"]
        self.init_ui()
        self.show_step()

    def init_ui(self):
        self.layout = QtWidgets.QVBoxLayout(self)
        self.step_widget = QtWidgets.QWidget(self)
        self.step_layout = QtWidgets.QVBoxLayout(self.step_widget)
        self.layout.addWidget(self.step_widget)
        self.btn_frame = QtWidgets.QHBoxLayout()
        self.layout.addLayout(self.btn_frame)
        self.back_btn = QtWidgets.QPushButton("Vissza")
        self.next_btn = QtWidgets.QPushButton("Következő")
        self.back_btn.clicked.connect(self.prev_step)
        self.next_btn.clicked.connect(self.next_step)
        self.btn_frame.addWidget(self.back_btn)
        self.btn_frame.addWidget(self.next_btn)

    def show_step(self):
        for i in reversed(range(self.step_layout.count())):
            widget = self.step_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        if self.step == 0:
            self.show_basic_data()
            self.back_btn.setEnabled(False)
            self.next_btn.setText("Következő")
        elif self.step == 1:
            self.show_specialization()
            self.back_btn.setEnabled(True)
            self.next_btn.setText("Következő")
        elif self.step == 2:
            self.show_skills()
            self.back_btn.setEnabled(True)
            self.next_btn.setText("Következő")
        elif self.step == 3:
            self.show_equipment()
            self.back_btn.setEnabled(True)
            self.next_btn.setText("Következő")
        elif self.step == 4:
            self.show_summary()
            self.back_btn.setEnabled(True)
            self.next_btn.setText("Mentés")

    def show_basic_data(self):
        self.name_edit = QtWidgets.QLineEdit()
        self.gender_combo = QtWidgets.QComboBox()
        self.gender_combo.addItems(["Férfi", "Nő"])
        self.age_edit = QtWidgets.QLineEdit()
        self.race_combo = QtWidgets.QComboBox()
        self.race_combo.addItems(ALL_RACES)
        self.class_combo = QtWidgets.QComboBox()
        self.result_label = QtWidgets.QLabel("")
        self.age_limits_label = QtWidgets.QLabel("")
        self.step_layout.addWidget(QtWidgets.QLabel("Név:"))
        self.step_layout.addWidget(self.name_edit)
        self.step_layout.addWidget(QtWidgets.QLabel("Nem:"))
        self.step_layout.addWidget(self.gender_combo)
        self.step_layout.addWidget(QtWidgets.QLabel("Kor:"))
        self.step_layout.addWidget(self.age_edit)
        self.step_layout.addWidget(self.age_limits_label)
        self.step_layout.addWidget(QtWidgets.QLabel("Faj:"))
        self.step_layout.addWidget(self.race_combo)
        self.step_layout.addWidget(QtWidgets.QLabel("Kaszt:"))
        self.step_layout.addWidget(self.class_combo)
        self.step_layout.addWidget(self.result_label)
        self.race_combo.currentTextChanged.connect(self.update_age_limits)
        self.race_combo.currentTextChanged.connect(self.update_class_options)
        self.gender_combo.currentTextChanged.connect(self.update_class_options)
        self.update_age_limits()
        self.update_class_options()

    def update_age_limits(self):
        race = self.race_combo.currentText()
        limits = AGE_LIMITS.get(race, (13, 100))
        self.age_limits_label.setText(f"Engedélyezett kor: {limits[0]} - {limits[1]}")

    def update_class_options(self):
        race = self.race_combo.currentText()
        gender = self.gender_combo.currentText()
        restricted_by_gender = GENDER_RESTRICTIONS.get(gender, set())
        restricted_by_race = RACE_RESTRICTIONS.get(race, set())
        all_classes = [name for _, name in self.class_db.list_classes()]
        allowed_classes = [k for k in all_classes if k not in restricted_by_gender and k not in restricted_by_race]
        self.class_combo.clear()
        self.class_combo.addItems(allowed_classes)

    def validate_basic_data(self):
        name = self.name_edit.text()
        gender = self.gender_combo.currentText()
        age = self.age_edit.text()
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
        self.data = {
            "Név": name,
            "Nem": gender,
            "Kor": age,
            "Faj": race,
            "Kaszt": klass
        }
        return True

    def show_specialization(self):
        # Load specializations for selected class
        selected_class_id = None
        for class_id, class_name in self.class_db.list_classes():
            if class_name == self.data.get("Kaszt"):
                selected_class_id = class_id
                break
        
        self.selected_class_id = selected_class_id  # Store for base class description loading
        self.specializations = ["Nincs"]
        self.spec_data = {}  # Map spec name to spec data
        if selected_class_id:
            try:
                specs = self.class_db.list_specialisations(selected_class_id)
                for spec in specs:
                    spec_name = spec["specialisation_name"]
                    self.specializations.append(spec_name)
                    self.spec_data[spec_name] = spec
            except Exception:
                pass
        
        self.spec_combo = QtWidgets.QComboBox()
        self.spec_combo.addItems(self.specializations)
        self.spec_combo.currentTextChanged.connect(self.load_specialization_description)
        
        # Use QTextBrowser for markdown rendering
        self.spec_desc = QtWidgets.QTextBrowser()
        self.spec_desc.setOpenExternalLinks(False)
        self.spec_desc.setPlaceholderText("Válassz egy specializációt a leírás megtekintéséhez...")
        
        self.step_layout.addWidget(QtWidgets.QLabel("Specializáció:"))
        self.step_layout.addWidget(self.spec_combo)
        self.step_layout.addWidget(QtWidgets.QLabel("Leírás:"))
        self.step_layout.addWidget(self.spec_desc)
        
        # Load initial description if default selection is not "Nincs"
        self.load_specialization_description(self.spec_combo.currentText())
    
    def load_specialization_description(self, spec_name):
        """Load specialization description from .md file"""
        if spec_name == "Nincs" or not spec_name:
            # Load base class description instead
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
        
        # Build path to description file: data/Class/descriptions/
        # __file__ is at Gamemaster_tools/ui/character_creator.py
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        desc_path = os.path.join(base_path, 'data', 'Class', 'descriptions', desc_file)
        
        if os.path.exists(desc_path):
            try:
                with open(desc_path, 'r', encoding='utf-8') as f:
                    markdown_content = f.read()
                    # Render as markdown
                    self.spec_desc.setMarkdown(markdown_content)
            except Exception as e:
                self.spec_desc.setPlainText(f"Hiba a leírás betöltésekor:\n{e}")
        else:
            self.spec_desc.setPlainText(f"A leírás fájl nem található:\n{desc_file}")
    
    def load_base_class_description(self):
        """Load base class description when no specialization is selected"""
        if not self.selected_class_id:
            self.spec_desc.clear()
            self.spec_desc.setPlaceholderText("Nincs kaszt kiválasztva.")
            return
        
        # Get class details including description filename
        try:
            class_details = self.class_db.get_class_details(self.selected_class_id)
            desc_file = class_details.get("class_description_file", "")
            
            if not desc_file:
                # Fallback: try using class_id.md
                desc_file = f"{self.selected_class_id}.md"
            
            # Build path to description file: data/Class/descriptions/
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            desc_path = os.path.join(base_path, 'data', 'Class', 'descriptions', desc_file)
            
            if os.path.exists(desc_path):
                try:
                    with open(desc_path, 'r', encoding='utf-8') as f:
                        markdown_content = f.read()
                        # Render as markdown
                        self.spec_desc.setMarkdown(markdown_content)
                except Exception as e:
                    self.spec_desc.setPlainText(f"Hiba a leírás betöltésekor:\n{e}")
            else:
                self.spec_desc.setPlainText(f"Nincs leírás fájl a {self.data.get('Kaszt')} kaszthoz.\n(Keresett fájl: {desc_file})")
        except Exception as e:
            self.spec_desc.setPlainText(f"Hiba a kaszt részletek betöltésekor:\n{e}")

    def show_skills(self):
        self.step_layout.addWidget(QtWidgets.QLabel("Képzettségek szerkesztése (később)"))

    def show_equipment(self):
        self.step_layout.addWidget(QtWidgets.QLabel("Felszerelések szerkesztése (később)"))

    def show_summary(self):
        summary = "\n".join(f"{k}: {v}" for k, v in self.data.items())
        self.step_layout.addWidget(QtWidgets.QLabel("Karakter összegzés"))
        self.step_layout.addWidget(QtWidgets.QLabel(summary))

    def next_step(self):
        if self.step == 0:
            if not self.validate_basic_data():
                return
        elif self.step == 1:
            self.data["Specializáció"] = self.spec_combo.currentText()
            self.data["Spec_leírás"] = self.spec_desc.toPlainText().strip()
        self.step += 1
        if self.step > 4:
            self.finish()
        else:
            self.show_step()

    def prev_step(self):
        if self.step > 0:
            self.step -= 1
            self.show_step()

    def finish(self):
        char = generate_character(
            self.data["Név"], self.data["Nem"], self.data["Kor"], self.data["Faj"], self.data["Kaszt"]
        )
        # Save character to JSON file
        filename = f"{self.data['Név'].replace(' ', '_')}.json"
        save_character(char, filename)
        
        # Itt bővíthető a char a specializációval, képzettségekkel, felszereléssel
        self.accept()
        # Optionally show summary or pass char to another window
        QtWidgets.QMessageBox.information(
            self, 
            "Karakter létrehozva", 
            f"Sikeres karaktergenerálás!\nMentve: characters/{filename}"
        )

if __name__ == "__main__":
    import sys
    from utils.dark_mode import apply_dark_mode
    
    app = QtWidgets.QApplication(sys.argv)
    apply_dark_mode(app)
    
    wizard = CharacterWizardQt()
    wizard.exec()
