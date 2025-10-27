"""
Skill Editor - PySide6 version with dark mode support
Modern tabbed interface for M.A.G.U.S. skill management
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QTextEdit, QSpinBox,
    QListWidget, QSplitter, QGroupBox, QMessageBox, QTabWidget, QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import sys
import os
import subprocess
import copy

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from utils.skilldata_manager import SkillManager
from utils.validation import validate_skill, ValidationError
# Note: Legacy Tkinter-based PrerequisiteManager is no longer used


# Skill categories
CATEGORIES = {
    "Harci képzettségek": ["Közkeletű", "Szakértő", "Titkos"],
    "Szociális képzettségek": ["Általános", "Nemesi", "Polgári", "Póri", "Művész"],
    "Alvilági képzettségek": ["Álcázó", "Kommunikációs", "Pénzszerző", "Harci", "Behatoló", "Ellenálló"],
    "Túlélő képzettségek": ["Vadonjáró", "Atlétikai"],
    "Elméleti képzettségek": ["Közkeletű", "Szakértő", "Titkos elméleti", "Titkos szervezeti"],
    "Helyfoglaló képzettségek": ["Harci képzettségek", "Szociális képzettségek", "Alvilági képzettségek", 
                                  "Túlélő képzettségek", "Elméleti képzettségek"]
}

ACQ_METHOD_MAP = {1: "Gyakorlás", 2: "Tapasztalás", 3: "Tanulás"}
ACQ_METHOD_MAP_REV = {v: k for k, v in ACQ_METHOD_MAP.items()}

ACQ_DIFF_MAP = {1: "Egyszerű", 2: "Könnyű", 3: "Közepes", 4: "Nehéz", 5: "Szinte lehetetlen"}
ACQ_DIFF_MAP_REV = {v: k for k, v in ACQ_DIFF_MAP.items()}

TYPE_MAP = {1: "szint", 2: "%"}
TYPE_MAP_REV = {v: k for k, v in TYPE_MAP.items()}


class SkillEditorQt(QMainWindow):
    """Modern skill editor with tabbed interface"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Képzettség szerkesztő")
        self.resize(1200, 800)
        
        # Initialize skill manager
        self.skill_manager = SkillManager()
        self.all_skills = self.skill_manager.load()
        
        # Ensure description_file is not None
        for skill in self.all_skills:
            if skill.get("description_file") is None:
                skill["description_file"] = ""
        
        self.skill_names = [s["name"] for s in self.all_skills]
        self.current_skill = None
        self.current_prerequisites = {}
        
        # Initialize UI
        self.init_ui()
        
        # Load first skill if available
        if self.all_skills:
            self.skill_list.setCurrentRow(0)
    
    def init_ui(self):
        """Initialize the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout - horizontal splitter
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Create splitter for skill list and editor
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - Skill list
        self.create_skill_list_panel(splitter)
        
        # Right panel - Editor
        self.create_editor_panel(splitter)
        
        # Set splitter sizes (30% list, 70% editor)
        splitter.setSizes([300, 900])
    
    def create_skill_list_panel(self, parent):
        """Create the skill list panel on the left"""
        list_widget = QWidget()
        list_layout = QVBoxLayout()
        list_widget.setLayout(list_layout)
        
        # Header
        header_label = QLabel("Képzettségek")
        header_font = QFont()
        header_font.setPointSize(12)
        header_font.setBold(True)
        header_label.setFont(header_font)
        list_layout.addWidget(header_label)
        
        # Skill list
        self.skill_list = QListWidget()
        self.populate_skill_list()
        self.skill_list.currentRowChanged.connect(self.on_skill_selected)
        list_layout.addWidget(self.skill_list)
        
        # Action buttons
        btn_layout = QVBoxLayout()
        
        btn_new = QPushButton("Új képzettség")
        btn_new.clicked.connect(self.new_skill)
        btn_layout.addWidget(btn_new)
        
        btn_duplicate = QPushButton("Képzettség másolása")
        btn_duplicate.clicked.connect(self.duplicate_skill)
        btn_layout.addWidget(btn_duplicate)
        
        btn_delete = QPushButton("Törlés")
        btn_delete.clicked.connect(self.delete_skill)
        btn_layout.addWidget(btn_delete)
        
        btn_layout.addStretch()
        list_layout.addLayout(btn_layout)
        
        parent.addWidget(list_widget)
    
    def create_editor_panel(self, parent):
        """Create the editor panel on the right"""
        editor_widget = QWidget()
        editor_layout = QVBoxLayout()
        editor_widget.setLayout(editor_layout)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        editor_layout.addWidget(self.tab_widget)
        
        # Tab 1: Basic Info
        self.create_basic_info_tab()
        
        # Tab 2: Levels & KP
        self.create_levels_tab()
        
        # Tab 3: Description
        self.create_description_tab()
        
        # Save button
        btn_save = QPushButton("Mentés")
        btn_save.setMinimumHeight(40)
        btn_save.clicked.connect(self.save_skill)
        editor_layout.addWidget(btn_save)
        
        parent.addWidget(editor_widget)
    
    def create_basic_info_tab(self):
        """Create the basic information tab"""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(tab)
        
        layout = QFormLayout()
        tab.setLayout(layout)
        
        # Name
        self.name_edit = QLineEdit()
        layout.addRow("Név:", self.name_edit)
        
        # ID
        self.id_edit = QLineEdit()
        layout.addRow("Azonosító:", self.id_edit)
        
        # Parameter
        param_layout = QHBoxLayout()
        self.param_edit = QLineEdit()
        param_layout.addWidget(self.param_edit)
        param_layout.addWidget(QLabel("(pl. Rövid kardok, Elf nyelv, Dobótőr)"))
        layout.addRow("Paraméter:", param_layout)
        
        # Main category
        self.main_cat_combo = QComboBox()
        self.main_cat_combo.addItems(CATEGORIES.keys())
        self.main_cat_combo.currentTextChanged.connect(self.on_main_category_changed)
        layout.addRow("Főkategória:", self.main_cat_combo)
        
        # Sub category
        self.sub_cat_combo = QComboBox()
        layout.addRow("Alkategória:", self.sub_cat_combo)
        
        # Initialize subcategories for the first main category
        first_main_cat = list(CATEGORIES.keys())[0]
        if first_main_cat in CATEGORIES:
            self.sub_cat_combo.addItems(CATEGORIES[first_main_cat])
        
        # Acquisition method
        self.acq_method_combo = QComboBox()
        self.acq_method_combo.addItems(ACQ_METHOD_MAP.values())
        layout.addRow("Elsajátítás módja:", self.acq_method_combo)
        
        # Acquisition difficulty
        self.acq_diff_combo = QComboBox()
        self.acq_diff_combo.addItems(ACQ_DIFF_MAP.values())
        layout.addRow("Elsajátítás nehézsége:", self.acq_diff_combo)
        
    # Type
        self.type_combo = QComboBox()
        self.type_combo.addItems(TYPE_MAP.values())
        layout.addRow("Típus:", self.type_combo)
        
    # KP per 3 (percent-based)
        self.kp_per_3_spin = QSpinBox()
        self.kp_per_3_spin.setMaximum(999)
        layout.addRow("KP/3:", self.kp_per_3_spin)
        
        # Description file
        self.desc_file_edit = QLineEdit()
        layout.addRow("Leírás fájl:", self.desc_file_edit)
        
        # React to type changes to toggle fields
        self.type_combo.currentTextChanged.connect(self._update_type_dependent_fields)

        self.tab_widget.addTab(scroll, "Alapadatok")
    
    def create_levels_tab(self):
        """Create the levels and KP costs tab with prerequisites"""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(tab)
        
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # Header
        header = QLabel("Szintek, KP költségek és Előfeltételek")
        header_font = QFont()
        header_font.setPointSize(11)
        header_font.setBold(True)
        header.setFont(header_font)
        layout.addWidget(header)
        
        # Create grid for levels 1-6
        grid = QGridLayout()
        
        # Headers
        grid.addWidget(QLabel("Szint"), 0, 0)
        grid.addWidget(QLabel("KP költség"), 0, 1)
        grid.addWidget(QLabel("Előfeltételek"), 0, 2)
        
        self.kp_cost_spins = []
        self.prereq_labels = []
        
        for i in range(6):
            level = i + 1
            
            # Level label
            grid.addWidget(QLabel(f"{level}. szint:"), i + 1, 0)
            
            # KP cost
            kp_spin = QSpinBox()
            kp_spin.setMaximum(9999)
            kp_spin.setMinimumWidth(80)
            self.kp_cost_spins.append(kp_spin)
            grid.addWidget(kp_spin, i + 1, 1)
            
            # Prerequisite summary label
            prereq_label = QLabel("")
            prereq_label.setWordWrap(True)
            prereq_label.setStyleSheet("color: #666; font-family: Consolas;")
            prereq_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            self.prereq_labels.append(prereq_label)
            grid.addWidget(prereq_label, i + 1, 2)
        
        layout.addLayout(grid)
        
        # Button to edit prerequisites
        btn_prereq = QPushButton("Előfeltételek szerkesztése")
        btn_prereq.clicked.connect(self.open_prereq_editor)
        btn_prereq.setMinimumHeight(35)
        layout.addWidget(btn_prereq)
        
        layout.addStretch()
        
        self.tab_widget.addTab(scroll, "Szintek & KP")
    
    def create_description_tab(self):
        """Create the description tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # Header
        header = QLabel("Leírás")
        header_font = QFont()
        header_font.setPointSize(11)
        header_font.setBold(True)
        header.setFont(header_font)
        layout.addWidget(header)
        
        # Description file info
        info_label = QLabel("A képzettség részletes leírása külső .md fájlban található.")
        info_label.setStyleSheet("color: #666; margin: 10px 0;")
        layout.addWidget(info_label)
        
        # Editor area for markdown content
        self.desc_text_editor = QTextEdit()
        self.desc_text_editor.setPlaceholderText("Itt szerkesztheted a leírás .md fájl tartalmát…")
        layout.addWidget(self.desc_text_editor, stretch=1)

        # Actions for description
        desc_btns = QHBoxLayout()
        btn_save_desc = QPushButton("Leírás mentése (.md)")
        btn_save_desc.clicked.connect(self.save_description_file)
        desc_btns.addWidget(btn_save_desc)

        btn_open_desc = QPushButton("Megnyitás külső szerkesztőben")
        btn_open_desc.clicked.connect(self.open_description_file)
        desc_btns.addWidget(btn_open_desc)

        desc_btns.addStretch()
        layout.addLayout(desc_btns)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Leírás")
    
    def _update_type_dependent_fields(self):
        """Enable/disable KP fields depending on skill type selection."""
        current = self.type_combo.currentText()
        st = TYPE_MAP_REV.get(current, 1)
        is_level = (st == 1)
        # Level-based: enable per-level KP, disable KP/3%
        for spin in getattr(self, 'kp_cost_spins', []):
            spin.setEnabled(is_level)
        self.kp_per_3_spin.setEnabled(not is_level)
    
    def on_main_category_changed(self, main_category):
        """Update subcategory combo when main category changes"""
        # Clear and repopulate subcategory combo
        self.sub_cat_combo.clear()
        
        # Get subcategories for selected main category
        if main_category in CATEGORIES:
            subcategories = CATEGORIES[main_category]
            self.sub_cat_combo.addItems(subcategories)
            
            # Disable fields for placeholder category
            is_placeholder = main_category == "Helyfoglaló képzettségek"
            self.sub_cat_combo.setEnabled(not is_placeholder)
            self.acq_method_combo.setEnabled(not is_placeholder)
            self.acq_diff_combo.setEnabled(not is_placeholder)
            self.type_combo.setEnabled(not is_placeholder)
            self.kp_per_3_spin.setEnabled(not is_placeholder)
    
    def populate_skill_list(self):
        """Populate the skill list"""
        self.skill_list.clear()
        for skill in self.all_skills:
            name = skill.get("name", "Névtelen")
            param = skill.get("parameter", "")
            display_name = f"{name}" + (f" ({param})" if param else "")
            self.skill_list.addItem(display_name)
    
    def on_skill_selected(self, index):
        """Handle skill selection from list"""
        if index < 0 or index >= len(self.all_skills):
            return
        
        self.current_skill = self.all_skills[index]
        self.load_skill_to_ui()
    
    def load_skill_to_ui(self):
        """Load current skill data to UI fields"""
        if not self.current_skill:
            return
        
        skill = self.current_skill
        
        # Basic info
        self.name_edit.setText(skill.get("name", ""))
        self.id_edit.setText(skill.get("id", ""))
        self.param_edit.setText(skill.get("parameter", ""))
        
        # Categories
        main_cat = skill.get("main_category", list(CATEGORIES.keys())[0])
        self.main_cat_combo.setCurrentText(main_cat)
        
        sub_cat = skill.get("sub_category", "")
        if sub_cat:
            self.sub_cat_combo.setCurrentText(sub_cat)
        
        # Acquisition
        acq_method = skill.get("acquisition_method", 1)
        self.acq_method_combo.setCurrentText(ACQ_METHOD_MAP.get(acq_method, "Tanulás"))
        
        acq_diff = skill.get("acquisition_difficulty", 3)
        self.acq_diff_combo.setCurrentText(ACQ_DIFF_MAP.get(acq_diff, "Közepes"))
        
        # Type (DB uses 'skill_type')
        skill_type = skill.get("skill_type", skill.get("type", 1))
        self.type_combo.setCurrentText(TYPE_MAP.get(skill_type, "szint"))
        # Update field enables based on type
        self._update_type_dependent_fields()
        
        # KP/3 for percent-based skills
        self.kp_per_3_spin.setValue(skill.get("kp_per_3_percent", 0))
        
        # Description file
        self.desc_file_edit.setText(skill.get("description_file", ""))
        # Load description content into editor (if available)
        self.load_description_file(silent=True)
        
        # Levels and KP costs
        kp_costs = skill.get("kp_costs", {})
        
        # Handle both dict and list formats
        if isinstance(kp_costs, dict):
            kp_list = [kp_costs.get(str(i+1), 0) for i in range(6)]
        else:
            kp_list = kp_costs if isinstance(kp_costs, list) else []
        
        for i in range(6):
            # KP cost
            kp = kp_list[i] if i < len(kp_list) else 0
            if isinstance(kp, (int, float)):
                self.kp_cost_spins[i].setValue(int(kp))
            else:
                self.kp_cost_spins[i].setValue(0)
        
        # Prerequisites - load and update summary
        self.current_prerequisites = skill.get("prerequisites", {})
        self.update_prereq_summary()
    
    # Removed duplicate on_main_category_changed; the version above handles disabling fields
    
    def update_prereq_summary(self):
        """Update prerequisite summary labels for all levels"""
        if not hasattr(self, 'current_prerequisites') or not self.current_prerequisites:
            # Clear all labels if no prerequisites
            for label in self.prereq_labels:
                label.setText("")
            return
        
        # Parse prerequisites for each level (1-6)
        for i in range(6):
            level_key = str(i + 1)
            level_prereqs = self.current_prerequisites.get(level_key, {})
            
            # Handle the actual format: {'képesség': ['Ügyesség 10+'], 'képzettség': ['Skill 1. szint']}
            if isinstance(level_prereqs, dict):
                stat_list = level_prereqs.get('képesség', [])
                skill_list = level_prereqs.get('képzettség', [])
                
                # Build summary text
                summary = ""
                if stat_list:
                    summary += "Tulajdonság: " + ", ".join(stat_list)
                if skill_list:
                    if summary:
                        summary += "\n"
                    summary += "Képzettség: " + ", ".join(skill_list)
                
                self.prereq_labels[i].setText(summary.strip())
            else:
                # Old format or empty
                self.prereq_labels[i].setText("")
    
    def open_description_file(self):
        """Open the description markdown file in the default editor"""
        if not self.current_skill:
            QMessageBox.warning(self, "Figyelem", "Nincs kiválasztott képzettség!")
            return
        
        desc_file = self.current_skill.get("description_file", "")
        if not desc_file:
            QMessageBox.information(
                self, "Info", 
                "Nincs leírás fájl megadva ehhez a képzettséghez."
            )
            return
        
        # Build full path - descriptions are in data/skills/descriptions
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        full_path = os.path.join(base_path, 'data', 'skills', 'descriptions', desc_file)
        
        if os.path.exists(full_path):
            # Open with default editor
            if sys.platform.startswith('win'):
                os.startfile(full_path)
            elif sys.platform == 'darwin':
                subprocess.call(['open', full_path])
            else:
                subprocess.call(['xdg-open', full_path])
        else:
            QMessageBox.warning(
                self, "Hiba",
                f"A leírás fájl nem található:\n{full_path}"
            )

    def _description_full_path(self):
        """Return absolute path to the current skill's description file under data/skills/descriptions"""
        if not self.current_skill:
            return None
        desc_file = self.current_skill.get("description_file", "") or self.desc_file_edit.text().strip()
        if not desc_file:
            return None
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        return os.path.join(base_path, 'data', 'skills', 'descriptions', desc_file)

    def load_description_file(self, silent=False):
        """Load description .md content into the editor area"""
        path = self._description_full_path()
        if not path:
            self.desc_text_editor.clear()
            if not silent:
                QMessageBox.information(self, "Info", "Nincs leírás fájlnév megadva. Add meg az Alapadatok fülön.")
            return
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self.desc_text_editor.setPlainText(f.read())
            except Exception as e:
                self.desc_text_editor.clear()
                if not silent:
                    QMessageBox.critical(self, "Hiba", f"Nem sikerült beolvasni a leírást:\n{e}")
        else:
            self.desc_text_editor.clear()
            if not silent:
                QMessageBox.information(self, "Info", "A leírás fájl nem létezik. Mentéskor létrehozzuk.")

    def save_description_file(self):
        """Save the editor content to the description .md file (create if missing)"""
        if not self.current_skill:
            QMessageBox.warning(self, "Figyelem", "Nincs kiválasztott képzettség!")
            return
        # Ensure filename is provided
        desc_file = self.desc_file_edit.text().strip()
        if not desc_file:
            QMessageBox.warning(self, "Figyelem", "Add meg a leírás fájl nevét az Alapadatok fülön (pl. uszas.md)")
            return
        # Update current skill's field from UI
        self.current_skill["description_file"] = desc_file
        # Resolve path and ensure directory
        path = self._description_full_path()
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self.desc_text_editor.toPlainText())
            QMessageBox.information(self, "Siker", "Leírás elmentve a .md fájlba.")
        except Exception as e:
            QMessageBox.critical(self, "Hiba", f"Nem sikerült menteni a leírást:\n{e}")
    
    def new_skill(self):
        """Create a new skill"""
        new_skill = {
            "name": "Új képzettség",
            "id": "new_skill",
            "parameter": "",
            "main_category": list(CATEGORIES.keys())[0],
            "sub_category": CATEGORIES[list(CATEGORIES.keys())[0]][0],
            "acquisition_method": 3,
            "acquisition_difficulty": 3,
            "skill_type": 1,
            "kp_per_3_percent": 0,
            "kp_costs": {str(i): 0 for i in range(1,7)},
            "level_descriptions": {},
            "description_file": "",
            "prerequisites": {}
        }
        
        self.all_skills.append(new_skill)
        self.populate_skill_list()
        self.skill_list.setCurrentRow(len(self.all_skills) - 1)
    
    def duplicate_skill(self):
        """Duplicate the current skill"""
        if not self.current_skill:
            QMessageBox.warning(self, "Figyelem", "Nincs kiválasztott képzettség!")
            return
        
        new_skill = copy.deepcopy(self.current_skill)
        new_skill["name"] = new_skill["name"] + " (másolat)"
        new_skill["id"] = new_skill["id"] + "_copy"
        
        self.all_skills.append(new_skill)
        self.populate_skill_list()
        self.skill_list.setCurrentRow(len(self.all_skills) - 1)
    
    def delete_skill(self):
        """Delete the current skill"""
        if not self.current_skill:
            QMessageBox.warning(self, "Figyelem", "Nincs kiválasztott képzettség!")
            return
        
        reply = QMessageBox.question(
            self, "Megerősítés",
            f"Biztosan törlöd ezt a képzettséget?\n{self.current_skill.get('name', '')}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            index = self.skill_list.currentRow()
            self.all_skills.pop(index)
            self.populate_skill_list()
            if self.all_skills:
                self.skill_list.setCurrentRow(min(index, len(self.all_skills) - 1))
    
    def save_skill(self):
        """Save the current skill"""
        if not self.current_skill:
            QMessageBox.warning(self, "Figyelem", "Nincs kiválasztott képzettség!")
            return
        
        # Collect data from UI
        self.current_skill["name"] = self.name_edit.text()
        self.current_skill["id"] = self.id_edit.text()
        self.current_skill["parameter"] = self.param_edit.text()
        self.current_skill["main_category"] = self.main_cat_combo.currentText()
        self.current_skill["sub_category"] = self.sub_cat_combo.currentText()
        
        # Acquisition
        self.current_skill["acquisition_method"] = ACQ_METHOD_MAP_REV.get(
            self.acq_method_combo.currentText(), 3
        )
        self.current_skill["acquisition_difficulty"] = ACQ_DIFF_MAP_REV.get(
            self.acq_diff_combo.currentText(), 3
        )
        
        # Type
        # Persist DB-compatible key
        self.current_skill["skill_type"] = TYPE_MAP_REV.get(self.type_combo.currentText(), 1)

        # KP per 3 percent (only for percent-based skills)
        if self.current_skill["skill_type"] == 2:
            self.current_skill["kp_per_3_percent"] = self.kp_per_3_spin.value()
            # For percent-based skills, ensure kp_costs is empty dict for cleanliness
            self.current_skill["kp_costs"] = {}
        else:
            # Ensure percent field is cleared for level-based skills
            self.current_skill["kp_per_3_percent"] = 0

        # Description file
        self.current_skill["description_file"] = self.desc_file_edit.text()
        # Sync description text from editor so DB manager writes the same content
        self.current_skill["description"] = self.desc_text_editor.toPlainText()
        # We no longer use per-level descriptions; ensure it's empty
        self.current_skill["level_descriptions"] = {}

        # Levels - save with string keys to match database format (only for level-based)
        if self.current_skill["skill_type"] == 1:
            kp_costs = {str(i+1): self.kp_cost_spins[i].value() for i in range(6)}
            self.current_skill["kp_costs"] = kp_costs

        # Prerequisites (already stored in current_prerequisites)
        self.current_skill["prerequisites"] = self.current_prerequisites

        # Validate before save
        try:
            validate_skill(self.current_skill)
        except ValidationError as ve:
            QMessageBox.critical(self, "Hiba", f"Érvénytelen adatok:\n{ve}")
            return

        # Save to database
        try:
            self.skill_manager.save(self.all_skills)
            self.populate_skill_list()
            QMessageBox.information(self, "Siker", "Képzettség mentve!")
        except Exception as e:
            QMessageBox.critical(self, "Hiba", f"Mentési hiba:\n{str(e)}")
    
    def open_prereq_editor(self):
        """Open prerequisite editor dialog"""
        if not self.current_skill:
            QMessageBox.warning(self, "Figyelem", "Nincs kiválasztott képzettség!")
            return
        
        # Import and open the PySide6 prerequisite editor
        try:
            from ui.skills.skill_prerequisite_editor import SkillPrerequisiteEditorQt
            editor = SkillPrerequisiteEditorQt(self)
            if editor.exec():
                # Dialog was accepted, prerequisites are already updated
                pass
        except Exception as e:
            QMessageBox.critical(
                self, "Hiba",
                f"Az előfeltétel szerkesztő nem nyitható meg:\n{str(e)}"
            )


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    
    # Import dark mode
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from utils.dark_mode import apply_dark_mode
    
    app = QApplication(sys.argv)
    apply_dark_mode(app)
    
    editor = SkillEditorQt()
    editor.show()
    
    sys.exit(app.exec())
