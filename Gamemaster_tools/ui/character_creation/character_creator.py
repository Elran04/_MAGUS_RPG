from PySide6 import QtWidgets, QtCore
import sys
import os
import sqlite3
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.class_db_manager import ClassDBManager
from utils.character_storage import save_character
from utils.placeholder_manager import PlaceholderManager
from data.race.race_list import ALL_RACES
from data.race.race_age_stat_modifiers import AGE_LIMITS
from engine.character import generate_character, is_valid_character, GENDER_RESTRICTIONS, RACE_RESTRICTIONS

# Base directory for data paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


class PlaceholderResolutionDialog(QtWidgets.QDialog):
    """Dialog for choosing which skill to use for a placeholder"""
    
    def __init__(self, parent, placeholder_id, resolutions):
        super().__init__(parent)
        self.placeholder_id = placeholder_id
        self.resolutions = resolutions
        self.chosen_skill_id = None
        
        self.setWindowTitle("Helyfoglaló képzettség feloldása")
        self.setModal(True)
        self.resize(500, 400)
        
        layout = QtWidgets.QVBoxLayout(self)
        
        # Header
        header_text = f"<b>Válassz egy képzettséget a(z) '{placeholder_id}' helyfoglaló helyére:</b>"
        header_label = QtWidgets.QLabel(header_text)
        header_label.setWordWrap(True)
        layout.addWidget(header_label)
        
        # List of available skills
        self.skill_list = QtWidgets.QListWidget()
        self.skill_list.doubleClicked.connect(self.on_accept)
        
        for res in resolutions:
            display_name = f"{res['skill_name']}"
            if res['parameter']:
                display_name += f" ({res['parameter']})"
            if res['resolution_category']:
                display_name += f" [{res['resolution_category']}]"
            
            item = QtWidgets.QListWidgetItem(display_name)
            item.setData(QtCore.Qt.UserRole, res['target_skill_id'])
            self.skill_list.addItem(item)
        
        layout.addWidget(self.skill_list)
        
        # Buttons
        btn_layout = QtWidgets.QHBoxLayout()
        btn_ok = QtWidgets.QPushButton("Kiválaszt")
        btn_ok.clicked.connect(self.on_accept)
        btn_cancel = QtWidgets.QPushButton("Mégsem")
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
    
    def on_accept(self):
        """Handle OK button or double-click"""
        current_item = self.skill_list.currentItem()
        if current_item:
            self.chosen_skill_id = current_item.data(QtCore.Qt.UserRole)
            self.accept()
        else:
            QtWidgets.QMessageBox.warning(self, "Nincs kiválasztva", "Válassz egy képzettséget a listából!")
    
    def get_chosen_skill(self):
        """Return the chosen skill ID"""
        return self.chosen_skill_id

class CharacterWizardQt(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Karakteralkotás varázsló")
        # Larger window to show class and specialization side-by-side
        self.resize(1000, 700)
        self.class_db = ClassDBManager()
        self.placeholder_mgr = PlaceholderManager()
        self.data = {}
        self.step = 0
        self.specializations = ["Nincs"]
        self.spec_data = {}
        self.selected_class_id = None
        self.placeholder_choices = {}  # Store user's placeholder resolutions
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
            # Merged step: basic data + specialization
            self.show_basic_and_specialization()
            self.back_btn.setEnabled(False)
            self.next_btn.setText("Következő")
        elif self.step == 1:
            self.show_skills()
            self.back_btn.setEnabled(True)
            self.next_btn.setText("Következő")
        elif self.step == 2:
            self.show_equipment()
            self.back_btn.setEnabled(True)
            self.next_btn.setText("Következő")
        elif self.step == 3:
            self.show_summary()
            self.back_btn.setEnabled(True)
            self.next_btn.setText("Mentés")

    def show_basic_and_specialization(self):
        """Show a merged step with basic data on the left and specialization on the right"""
        container = QtWidgets.QWidget()
        hlayout = QtWidgets.QHBoxLayout(container)
        hlayout.setContentsMargins(0, 0, 0, 0)
        hlayout.setSpacing(16)

        # Left pane: Basic data
        left = QtWidgets.QWidget()
        left_form = QtWidgets.QFormLayout(left)
        left_form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight)

        self.name_edit = QtWidgets.QLineEdit()
        self.gender_combo = QtWidgets.QComboBox(); self.gender_combo.addItems(["Férfi", "Nő"])
        self.age_edit = QtWidgets.QLineEdit()
        self.race_combo = QtWidgets.QComboBox(); self.race_combo.addItems(ALL_RACES)
        self.class_combo = QtWidgets.QComboBox()
        self.result_label = QtWidgets.QLabel("")
        self.result_label.setStyleSheet("color:#c33;")
        self.age_limits_label = QtWidgets.QLabel("")

        left_form.addRow("Név:", self.name_edit)
        left_form.addRow("Nem:", self.gender_combo)
        left_form.addRow("Kor:", self.age_edit)
        left_form.addRow("Korhatár:", self.age_limits_label)
        left_form.addRow("Faj:", self.race_combo)
        left_form.addRow("Kaszt:", self.class_combo)
        left_form.addRow("", self.result_label)

        # Right pane: Specialization selection and description
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

        self.step_layout.addWidget(container)

        # Wire changes
        self.race_combo.currentTextChanged.connect(self.update_age_limits)
        self.race_combo.currentTextChanged.connect(self.update_class_options)
        self.gender_combo.currentTextChanged.connect(self.update_class_options)

        # Initial fills
        self.update_age_limits()
        self.update_class_options()

    def update_age_limits(self):
        race = self.race_combo.currentText()
        limits = AGE_LIMITS.get(race, (13, 100))
        self.age_limits_label.setText(f"Engedélyezett kor: {limits[0]} - {limits[1]}")

    def update_class_options(self):
        """Populate class options based on race/gender restrictions and refresh specs."""
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
        # Try keep previous selection if still allowed
        if current_class in allowed:
            self.class_combo.setCurrentText(current_class)
        self.class_combo.blockSignals(False)

        # After classes updated, repopulate specs for selected class
        self.populate_specializations_for_selected_class()

        # React to direct user change too
        self.class_combo.currentTextChanged.connect(self.populate_specializations_for_selected_class)

    def populate_specializations_for_selected_class(self):
        """Fill specialization combo based on selected class and load description."""
        sel_name = self.class_combo.currentText()
        self.selected_class_id = None
        for class_id, class_name in self.class_db.list_classes():
            if class_name == sel_name:
                self.selected_class_id = class_id
                break

        # Default spec list
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

        # Update combo
        self.spec_combo.blockSignals(True)
        self.spec_combo.clear()
        self.spec_combo.addItems(self.specializations)
        self.spec_combo.blockSignals(False)

        # Load description for current selection (or base class if "Nincs")
        self.load_specialization_description(self.spec_combo.currentText())

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

    # Removed standalone specialization step; merged into step 0
    
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
        """Show class/spec skills with KP information"""
        container = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header with KP information
        header = QtWidgets.QWidget()
        header_layout = QtWidgets.QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 10)
        
        # Get KP values from character data
        kp_alap = self.data.get("Képzettségpontok", {}).get("Alap", 0)
        kp_szinten = self.data.get("Képzettségpontok", {}).get("Szintenként", 0)
        total_kp = kp_alap + kp_szinten  # Level 1, so just base + per-level
        
        info_label = QtWidgets.QLabel(
            f"<b>Képzettségpontok:</b> Alap: {kp_alap} + Szintenként: {kp_szinten} = <b>{total_kp} KP</b> az 1. szinten"
        )
        info_label.setStyleSheet("font-size: 12pt; padding: 8px; background-color: rgba(100,100,120,50); border-radius: 4px;")
        header_layout.addWidget(info_label)
        header_layout.addStretch()
        
        main_layout.addWidget(header)
        
        # Skills table
        main_layout.addWidget(QtWidgets.QLabel("Kaszt/Specializáció képzettségei:"))
        
        self.skills_table = QtWidgets.QTableWidget()
        self.skills_table.setColumnCount(5)
        self.skills_table.setHorizontalHeaderLabels(["Képzettség", "Szint", "%", "KP költség", "Forrás"])
        self.skills_table.horizontalHeader().setStretchLastSection(False)
        self.skills_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.skills_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.skills_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.skills_table.doubleClicked.connect(self.on_skill_double_click)
        
        main_layout.addWidget(self.skills_table)
        
        # Button bar for placeholder resolution
        btn_bar = QtWidgets.QHBoxLayout()
        self.btn_resolve_placeholder = QtWidgets.QPushButton("🔧 Helyfoglaló feloldása")
        self.btn_resolve_placeholder.clicked.connect(self.resolve_selected_placeholder)
        self.btn_resolve_placeholder.setToolTip("Válassz egy helyfoglaló képzettséget és kattints ide a feloldásához")
        btn_bar.addWidget(self.btn_resolve_placeholder)
        btn_bar.addStretch()
        main_layout.addLayout(btn_bar)
        
        # Load skills
        self.load_class_spec_skills()
        
        # Show message if no skills found
        if self.skills_table.rowCount() == 0:
            no_skills_msg = QtWidgets.QLabel(
                "<i>Ehhez a kaszthoz/specializációhoz még nincsenek képzettségek hozzárendelve.<br>"
                "A képzettségeket a Kaszt szerkesztőben lehet megadni.</i>"
            )
            no_skills_msg.setWordWrap(True)
            no_skills_msg.setStyleSheet("color: #cc8800; font-size: 10pt; padding: 12px; background-color: rgba(200,150,50,30); border-radius: 4px;")
            main_layout.addWidget(no_skills_msg)
        
        # Note
        note = QtWidgets.QLabel(
            "<i>Megjegyzés: A képzettségek szerkesztése a karakter mentése után a külön karakterszerkesztőben lehetséges.</i>"
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #888; font-size: 9pt; padding: 8px;")
        main_layout.addWidget(note)
        
        self.step_layout.addWidget(container)
    
    def load_class_spec_skills(self):
        """Load skills assigned to the selected class/specialization"""
        self.skills_table.setRowCount(0)
        
        if not self.selected_class_id:
            return
        
        # Determine spec_id (None if "Nincs" selected)
        selected_spec_name = self.data.get("Specializáció", "Nincs")
        spec_id = None
        if selected_spec_name != "Nincs":
            spec_info = self.spec_data.get(selected_spec_name)
            if spec_info:
                spec_id = spec_info.get("specialisation_id")
        
        # Query class_skills table
        db_class_path = os.path.join(BASE_DIR, 'data', 'Class', 'class_data.db')
        db_skill_path = os.path.join(BASE_DIR, 'data', 'skills', 'skills_data.db')
        
        try:
            with sqlite3.connect(db_class_path) as conn:
                # Get skills for this class/spec
                # Include both base class skills (NULL spec) and spec-specific skills
                if spec_id:
                    skills = conn.execute(
                        """
                        SELECT skill_id, class_level, skill_level, skill_percent, specialisation_id
                        FROM class_skills 
                        WHERE class_id=? AND (specialisation_id IS NULL OR specialisation_id=?)
                        ORDER BY class_level, skill_id
                        """,
                        (self.selected_class_id, spec_id)
                    ).fetchall()
                else:
                    skills = conn.execute(
                        """
                        SELECT skill_id, class_level, skill_level, skill_percent, specialisation_id
                        FROM class_skills 
                        WHERE class_id=? AND specialisation_id IS NULL
                        ORDER BY class_level, skill_id
                        """,
                        (self.selected_class_id,)
                    ).fetchall()
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Hiba", f"Nem sikerült betölteni a képzettségeket:\n{e}")
            return
        
        # For each skill, resolve name and calculate KP cost
        with sqlite3.connect(db_skill_path) as skill_conn:
            for skill_id, class_level, skill_level, skill_percent, from_spec in skills:
                # Get skill info
                try:
                    skill_info = skill_conn.execute(
                        "SELECT name, parameter, type, placeholder FROM skills WHERE id=?",
                        (skill_id,)
                    ).fetchone()
                    
                    if not skill_info:
                        continue
                    
                    skill_name, parameter, skill_type, is_placeholder = skill_info
                    display_name = f"{skill_name} ({parameter})" if parameter else skill_name
                    
                    # Determine source
                    source = "Specializáció" if from_spec else "Alap kaszt"
                    
                    # Handle placeholders
                    if is_placeholder == 1:
                        # Check if user already made a choice for this placeholder
                        if skill_id in self.placeholder_choices:
                            resolved_id = self.placeholder_choices[skill_id]
                            # Get resolved skill info
                            resolved_info = skill_conn.execute(
                                "SELECT name, parameter FROM skills WHERE id=?",
                                (resolved_id,)
                            ).fetchone()
                            if resolved_info:
                                res_name, res_param = resolved_info
                                display_name = f"✓ {res_name} ({res_param})" if res_param else f"✓ {res_name}"
                                display_name += f" [választott: {skill_name}]"
                        else:
                            # Mark as placeholder needing resolution
                            display_name = f"❓ {display_name} [VÁLASZTANDÓ]"
                    
                    # Calculate KP cost
                    kp_cost = "?"
                    if skill_type == 1:  # Level-based
                        if skill_level:
                            # Query skill_level_costs table
                            cost_row = skill_conn.execute(
                                "SELECT kp_cost FROM skill_level_costs WHERE skill_id=? AND level=?",
                                (skill_id, skill_level)
                            ).fetchone()
                            if cost_row:
                                kp_cost = str(cost_row[0])
                    elif skill_type == 2:  # Percentage-based
                        if skill_percent:
                            # Query skill_percent_costs table
                            cost_row = skill_conn.execute(
                                "SELECT kp_per_3percent FROM skill_percent_costs WHERE skill_id=?",
                                (skill_id,)
                            ).fetchone()
                            if cost_row:
                                kp_per_3 = cost_row[0]
                                # Calculate total cost for skill_percent
                                kp_cost = str((skill_percent // 3) * kp_per_3)
                    
                    # Add row to table
                    row = self.skills_table.rowCount()
                    self.skills_table.insertRow(row)
                    
                    name_item = QtWidgets.QTableWidgetItem(display_name)
                    # Store skill_id in item data for later resolution
                    name_item.setData(QtCore.Qt.UserRole, skill_id)
                    name_item.setData(QtCore.Qt.UserRole + 1, is_placeholder)
                    
                    # Highlight placeholders that need resolution
                    if is_placeholder == 1 and skill_id not in self.placeholder_choices:
                        name_item.setBackground(QtCore.Qt.yellow)
                        name_item.setForeground(QtCore.Qt.black)
                    
                    self.skills_table.setItem(row, 0, name_item)
                    self.skills_table.setItem(row, 1, QtWidgets.QTableWidgetItem(str(skill_level) if skill_level else "-"))
                    self.skills_table.setItem(row, 2, QtWidgets.QTableWidgetItem(str(skill_percent) if skill_percent else "-"))
                    self.skills_table.setItem(row, 3, QtWidgets.QTableWidgetItem(str(kp_cost)))
                    self.skills_table.setItem(row, 4, QtWidgets.QTableWidgetItem(source))
                    
                except Exception as e:
                    print(f"Error loading skill {skill_id}: {e}")
                    continue
    
    def on_skill_double_click(self, index):
        """Handle double-click on skill to resolve placeholder"""
        row = index.row()
        name_item = self.skills_table.item(row, 0)
        if name_item:
            skill_id = name_item.data(QtCore.Qt.UserRole)
            is_placeholder = name_item.data(QtCore.Qt.UserRole + 1)
            
            if is_placeholder == 1:
                self.resolve_placeholder(skill_id)
    
    def resolve_selected_placeholder(self):
        """Resolve the currently selected placeholder skill"""
        current_row = self.skills_table.currentRow()
        if current_row < 0:
            QtWidgets.QMessageBox.information(
                self, 
                "Nincs kiválasztva", 
                "Válassz ki egy helyfoglaló képzettséget a táblázatból!"
            )
            return
        
        name_item = self.skills_table.item(current_row, 0)
        if name_item:
            skill_id = name_item.data(QtCore.Qt.UserRole)
            is_placeholder = name_item.data(QtCore.Qt.UserRole + 1)
            
            if is_placeholder != 1:
                QtWidgets.QMessageBox.information(
                    self, 
                    "Nem helyfoglaló", 
                    "A kiválasztott képzettség nem helyfoglaló típusú."
                )
                return
            
            self.resolve_placeholder(skill_id)
    
    def resolve_placeholder(self, placeholder_id):
        """Show dialog to resolve a placeholder skill"""
        # Get available resolutions
        resolutions = self.placeholder_mgr.get_resolutions(placeholder_id)
        
        if not resolutions:
            QtWidgets.QMessageBox.warning(
                self,
                "Nincs feloldás",
                f"Ehhez a helyfoglalóhoz ({placeholder_id}) nincs elérhető feloldás az adatbázisban."
            )
            return
        
        # Create resolution dialog
        dialog = PlaceholderResolutionDialog(self, placeholder_id, resolutions)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            chosen_id = dialog.get_chosen_skill()
            if chosen_id:
                self.placeholder_choices[placeholder_id] = chosen_id
                # Reload skills table to show the resolution
                self.load_class_spec_skills()

    def show_equipment(self):
        self.step_layout.addWidget(QtWidgets.QLabel("Felszerelések szerkesztése (később)"))

    def show_summary(self):
        summary = "\n".join(f"{k}: {v}" for k, v in self.data.items())
        self.step_layout.addWidget(QtWidgets.QLabel("Karakter összegzés"))
        self.step_layout.addWidget(QtWidgets.QLabel(summary))

    def next_step(self):
        if self.step == 0:
            # Validate and capture both basic data and specialization
            if not self.validate_basic_data():
                return
            self.data["Specializáció"] = self.spec_combo.currentText()
            self.data["Spec_leírás"] = self.spec_desc.toPlainText().strip()
            
            # Generate full character data to get KP values for skills step
            temp_char = generate_character(
                self.data["Név"], self.data["Nem"], self.data["Kor"], 
                self.data["Faj"], self.data["Kaszt"]
            )
            # Store KP info in data for skills step
            self.data["Képzettségpontok"] = temp_char.get("Képzettségpontok", {})
            self.data["Tulajdonságok"] = temp_char.get("Tulajdonságok", {})
            self.data["Harci értékek"] = temp_char.get("Harci értékek", {})
            
        self.step += 1
        if self.step > 3:
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
