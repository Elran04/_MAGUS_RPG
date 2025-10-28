"""
Skill Editor Tabs
Handles creation of all editor tabs (Basic Info, Levels & KP, Description)
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QTextEdit, QSpinBox,
    QScrollArea, QListWidget, QGroupBox, QCompleter, QTabWidget, QSplitter
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import sys
import os
import subprocess
import re

from .skill_editor_constants import CATEGORIES, ACQ_METHOD_MAP, ACQ_DIFF_MAP, TYPE_MAP

# Stat names for prerequisites
STAT_NAMES = [
    "Erő", "Állóképesség", "Gyorsaság", "Ügyesség", "Karizma",
    "Egészség", "Intelligencia", "Akaraterő", "Asztrál", "Érzékelés"
]


class SkillEditorTabs:
    """Manages all skill editor tabs"""
    
    def __init__(self, tab_widget, parent_editor):
        """
        Initialize the tabs
        
        Args:
            tab_widget: QTabWidget to add tabs to
            parent_editor: Reference to parent SkillEditorQt instance
        """
        self.tab_widget = tab_widget
        self.parent = parent_editor
        
        # Widget references
        self.name_edit = None
        self.id_edit = None
        self.param_edit = None
        self.main_cat_combo = None
        self.sub_cat_combo = None
        self.acq_method_combo = None
        self.acq_diff_combo = None
        self.type_combo = None
        self.kp_per_3_spin = None
        self.desc_file_edit = None
        self.kp_cost_spins = []
        self.prereq_labels = []
        self.desc_text_editor = None
        
        # Create all tabs
        self.create_basic_info_tab()
        self.create_levels_tab()
        self.create_description_tab()
    
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
        
        # React to type changes to toggle fields
        self.type_combo.currentTextChanged.connect(self.parent.update_type_dependent_fields)
        
        self.tab_widget.addTab(scroll, "Alapadatok")
    
    def create_levels_tab(self):
        """Create the levels and KP costs tab with prerequisites"""
        tab = QWidget()
        main_layout = QVBoxLayout()
        tab.setLayout(main_layout)
        
        # Create splitter for top/bottom sections
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Top section: Overview grid (always visible)
        overview_scroll = QScrollArea()
        overview_scroll.setWidgetResizable(True)
        overview_widget = QWidget()
        overview_layout = QVBoxLayout()
        overview_widget.setLayout(overview_layout)
        
        # Header
        header = QLabel("Szintek, KP költségek és Előfeltételek")
        header_font = QFont()
        header_font.setPointSize(11)
        header_font.setBold(True)
        header.setFont(header_font)
        overview_layout.addWidget(header)
        
        # Create grid for levels 1-6
        grid = QGridLayout()
        
        # Headers
        grid.addWidget(QLabel("Szint"), 0, 0)
        grid.addWidget(QLabel("KP költség"), 0, 1)
        grid.addWidget(QLabel("Előfeltételek"), 0, 2)
        
        # Set column stretch so prerequisites column takes most space
        grid.setColumnStretch(0, 0)  # Szint - no stretch
        grid.setColumnStretch(1, 0)  # KP - no stretch
        grid.setColumnStretch(2, 1)  # Előfeltételek - stretch to fill
        
        self.kp_cost_spins = []
        self.prereq_labels = []
        self.prereq_widgets = []  # Store prerequisite editing widgets for each level
        
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
            prereq_label = QLabel()
            prereq_label.setWordWrap(True)
            prereq_label.setMinimumHeight(40)
            prereq_label.setMinimumWidth(300)
            prereq_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            prereq_label.setStyleSheet("QLabel { background-color: #2a2a2a; color: #ffffff; padding: 5px; border: 1px solid #767676; }")
            prereq_label.setText("")  # Initialize with empty text
            self.prereq_labels.append(prereq_label)
            grid.addWidget(prereq_label, i + 1, 2)
        
        overview_layout.addLayout(grid)
        overview_layout.addStretch()
        overview_scroll.setWidget(overview_widget)
        
        splitter.addWidget(overview_scroll)
        
        # Bottom section: Nested tab widget for prerequisite editing
        self.levels_tab_widget = QTabWidget()
        
        # Create prerequisite editor tabs for each level
        for i in range(6):
            level = i + 1
            prereq_widget = self.create_prereq_editor(level)
            self.prereq_widgets.append(prereq_widget)
            self.levels_tab_widget.addTab(prereq_widget, f"{level}. szint előfeltételei")
        
        splitter.addWidget(self.levels_tab_widget)

        # Set splitter ratio: 60% top, 40% bottom
        splitter.setSizes([600, 400])
        
        main_layout.addWidget(splitter)
        
        self.tab_widget.addTab(tab, "Szintek & KP")
    
    def create_prereq_editor(self, level):
        """Create prerequisite editor for a specific level as a tab"""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        widget = QWidget()
        widget.level = level
        scroll.setWidget(widget)
        
        main_layout = QVBoxLayout()
        tab.setLayout(main_layout)
        main_layout.addWidget(scroll)
        
        layout = QHBoxLayout()
        widget.setLayout(layout)
        
        # Stat prerequisites column
        stat_col = QVBoxLayout()
        stat_col.addWidget(QLabel("<b>Tulajdonság előfeltételek:</b>"))
        
        widget.stat_list = QListWidget()
        widget.stat_list.setMinimumHeight(200)
        stat_col.addWidget(widget.stat_list)
        
        stat_controls = QHBoxLayout()
        widget.stat_combo = QComboBox()
        widget.stat_combo.addItems(STAT_NAMES)
        widget.stat_combo.setMaximumWidth(120)
        stat_controls.addWidget(widget.stat_combo)
        
        widget.stat_value_spin = QSpinBox()
        widget.stat_value_spin.setMinimum(1)
        widget.stat_value_spin.setMaximum(20)
        widget.stat_value_spin.setValue(10)
        widget.stat_value_spin.setMaximumWidth(60)
        stat_controls.addWidget(widget.stat_value_spin)
        
        btn_add_stat = QPushButton("+")
        btn_add_stat.setMaximumWidth(30)
        btn_add_stat.clicked.connect(lambda: self.add_stat_prereq(widget))
        stat_controls.addWidget(btn_add_stat)
        
        btn_remove_stat = QPushButton("-")
        btn_remove_stat.setMaximumWidth(30)
        btn_remove_stat.clicked.connect(lambda: self.remove_stat_prereq(widget))
        stat_controls.addWidget(btn_remove_stat)
        
        stat_col.addLayout(stat_controls)
        layout.addLayout(stat_col)
        
        # Skill prerequisites column
        skill_col = QVBoxLayout()
        skill_col.addWidget(QLabel("<b>Képzettség előfeltételek:</b>"))
        
        widget.skill_list = QListWidget()
        widget.skill_list.setMinimumHeight(200)
        skill_col.addWidget(widget.skill_list)
        
        skill_controls = QHBoxLayout()
        widget.skill_combo = QComboBox()
        widget.skill_combo.addItems(self.parent.skill_names)
        widget.skill_combo.setEditable(True)
        completer = QCompleter(self.parent.skill_names)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        widget.skill_combo.setCompleter(completer)
        skill_controls.addWidget(widget.skill_combo)
        
        widget.skill_level_spin = QSpinBox()
        widget.skill_level_spin.setMinimum(1)
        widget.skill_level_spin.setMaximum(6)
        widget.skill_level_spin.setValue(1)
        widget.skill_level_spin.setMaximumWidth(50)
        skill_controls.addWidget(QLabel("szint"))
        skill_controls.addWidget(widget.skill_level_spin)
        
        btn_add_skill = QPushButton("+")
        btn_add_skill.setMaximumWidth(30)
        btn_add_skill.clicked.connect(lambda: self.add_skill_prereq(widget))
        skill_controls.addWidget(btn_add_skill)
        
        btn_remove_skill = QPushButton("-")
        btn_remove_skill.setMaximumWidth(30)
        btn_remove_skill.clicked.connect(lambda: self.remove_skill_prereq(widget))
        skill_controls.addWidget(btn_remove_skill)
        
        skill_col.addLayout(skill_controls)
        layout.addLayout(skill_col)
        
        # Store references to list widgets on the tab for easy access
        tab.stat_list = widget.stat_list
        tab.skill_list = widget.skill_list
        tab.stat_combo = widget.stat_combo
        tab.stat_value_spin = widget.stat_value_spin
        tab.skill_combo = widget.skill_combo
        tab.skill_level_spin = widget.skill_level_spin
        tab.level = level
        
        return tab
    
    def load_prereq_for_level(self, level):
        """Load prerequisites for a specific level into the editor"""
        widget = self.prereq_widgets[level - 1]
        level_key = str(level)
        prereqs = self.parent.current_prerequisites.get(level_key, {'képesség': [], 'képzettség': []})
        
        # Load stat prerequisites
        widget.stat_list.clear()
        for stat_req in prereqs.get('képesség', []):
            widget.stat_list.addItem(stat_req)
        
        # Load skill prerequisites
        widget.skill_list.clear()
        for skill_req in prereqs.get('képzettség', []):
            widget.skill_list.addItem(skill_req)
    
    def add_stat_prereq(self, widget):
        """Add a stat prerequisite"""
        stat = widget.stat_combo.currentText()
        value = widget.stat_value_spin.value()
        text = f"{stat} {value}+"
        widget.stat_list.addItem(text)
        self.save_prereq_from_widget(widget)
    
    def remove_stat_prereq(self, widget):
        """Remove selected stat prerequisite"""
        current = widget.stat_list.currentRow()
        if current >= 0:
            widget.stat_list.takeItem(current)
            self.save_prereq_from_widget(widget)
    
    def add_skill_prereq(self, widget):
        """Add a skill prerequisite"""
        skill = widget.skill_combo.currentText()
        level = widget.skill_level_spin.value()
        text = f"{skill} {level}. szint"
        widget.skill_list.addItem(text)
        self.save_prereq_from_widget(widget)
    
    def remove_skill_prereq(self, widget):
        """Remove selected skill prerequisite"""
        current = widget.skill_list.currentRow()
        if current >= 0:
            widget.skill_list.takeItem(current)
            self.save_prereq_from_widget(widget)
    
    def save_prereq_from_widget(self, widget):
        """Save prerequisites from widget back to parent's current_prerequisites"""
        level = widget.level
        level_key = str(level)
        
        # Collect stat prerequisites
        stat_prereqs = []
        for i in range(widget.stat_list.count()):
            stat_prereqs.append(widget.stat_list.item(i).text())
        
        # Collect skill prerequisites
        skill_prereqs = []
        for i in range(widget.skill_list.count()):
            skill_prereqs.append(widget.skill_list.item(i).text())
        
        # Update parent's prerequisites
        if level_key not in self.parent.current_prerequisites:
            self.parent.current_prerequisites[level_key] = {}
        
        self.parent.current_prerequisites[level_key]['képesség'] = stat_prereqs
        self.parent.current_prerequisites[level_key]['képzettség'] = skill_prereqs
    
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
        
        # Description filename field
        desc_file_layout = QFormLayout()
        self.desc_file_edit = QLineEdit()
        desc_file_layout.addRow("Leírás fájl:", self.desc_file_edit)
        layout.addLayout(desc_file_layout)
        
        # Editor area for markdown content
        self.desc_text_editor = QTextEdit()
        self.desc_text_editor.setPlaceholderText("Itt szerkesztheted a leírás .md fájl tartalmát…")
        layout.addWidget(self.desc_text_editor, stretch=1)
        
        # Actions for description
        desc_btns = QHBoxLayout()
        btn_save_desc = QPushButton("Leírás mentése (.md)")
        btn_save_desc.clicked.connect(self.parent.save_description_file)
        desc_btns.addWidget(btn_save_desc)
        
        btn_open_desc = QPushButton("Megnyitás külső szerkesztőben")
        btn_open_desc.clicked.connect(self.parent.open_description_file)
        desc_btns.addWidget(btn_open_desc)
        
        desc_btns.addStretch()
        layout.addLayout(desc_btns)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Leírás")
    
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
