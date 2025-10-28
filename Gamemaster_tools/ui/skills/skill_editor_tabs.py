"""
Skill Editor Tabs
Handles creation of all editor tabs (Basic Info, Levels & KP, Description)
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QTextEdit, QSpinBox,
    QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import sys
import os
import subprocess

from .skill_editor_constants import CATEGORIES, ACQ_METHOD_MAP, ACQ_DIFF_MAP, TYPE_MAP


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
        
        # Description file
        self.desc_file_edit = QLineEdit()
        layout.addRow("Leírás fájl:", self.desc_file_edit)
        
        # React to type changes to toggle fields
        self.type_combo.currentTextChanged.connect(self.parent.update_type_dependent_fields)
        
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
        btn_prereq.clicked.connect(self.parent.open_prereq_editor)
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
