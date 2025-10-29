"""
Class Editor Tabs
Handles creation of all editor tabs (Attributes, Combat, XP, Equipment, Skills, Description)
"""
from PySide6 import QtWidgets, QtCore
from PySide6.QtGui import QFont

from .class_editor_constants import EQUIPMENT_TYPES
from .class_skill_editor import ClassSkillEditorWidget


class ClassEditorTabs:
    """Manages all class editor tabs"""
    
    def __init__(self, tab_widget, parent_editor):
        """
        Initialize the tabs
        
        Args:
            tab_widget: QTabWidget to add tabs to
            parent_editor: Reference to parent ClassEditorQt instance
        """
        self.tab_widget = tab_widget
        self.parent = parent_editor
        
        # Widget references
        self.class_name_edit = None
        self.spec_name_edit = None
        self.spec_desc_edit = None
        self.desc_label = None
        self.desc_filename_label = None
        self.desc_text_editor = None
        self.stats_table = None
        self.xp_table = None
        self.extra_xp_edit = None
        self.eq_table = None
        
        # Skill editor widget
        self.skill_editor_widget = None
        
        # Create all tabs
        self.create_attributes_tab()
        self.create_combat_tab()
        self.create_xp_tab()
        self.create_equipment_tab()
        self.create_skills_tab()
        self.create_description_tab()
    
    def create_attributes_tab(self):
        """Create the attributes tab with name and stats"""
        tab = QtWidgets.QWidget()
        attr_layout = QtWidgets.QFormLayout(tab)
        
        # Class vs Spec name fields
        self.class_name_edit = QtWidgets.QLineEdit()
        self.spec_name_edit = QtWidgets.QLineEdit()
        attr_layout.addRow("Kaszt név:", self.class_name_edit)
        attr_layout.addRow("Spec. név:", self.spec_name_edit)
        
        # Stats table with double_chance
        self.stats_table = QtWidgets.QTableWidget()
        self.stats_table.setColumnCount(4)
        self.stats_table.setHorizontalHeaderLabels(["Tulajdonság", "Min", "Max", "Duplázási esély"])
        self.stats_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.stats_table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.stats_table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        self.stats_table.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        attr_layout.addRow("Tulajdonságok:", self.stats_table)
        
        self.tab_widget.addTab(tab, "Tulajdonságok")
    
    def create_combat_tab(self):
        """Create the combat stats tab"""
        tab = QtWidgets.QWidget()
        cs_layout = QtWidgets.QVBoxLayout(tab)
        
        self.combat_table = QtWidgets.QTableWidget()
        self.combat_table.setColumnCount(2)
        self.combat_table.setHorizontalHeaderLabels(["Mutató", "Érték"])
        self.combat_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.combat_table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        cs_layout.addWidget(self.combat_table)
        
        self.tab_widget.addTab(tab, "Harci statok")
    
    def create_xp_tab(self):
        """Create the experience requirements tab"""
        tab = QtWidgets.QWidget()
        xp_layout = QtWidgets.QFormLayout(tab)
        
        self.xp_table = QtWidgets.QTableWidget()
        self.xp_table.setColumnCount(2)
        self.xp_table.setHorizontalHeaderLabels(["Szint", "XP"])
        self.xp_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.xp_table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        xp_layout.addRow("Követelmények:", self.xp_table)
        
        self.extra_xp_edit = QtWidgets.QSpinBox()
        self.extra_xp_edit.setMaximum(999999)
        xp_layout.addRow("További szintenkénti XP:", self.extra_xp_edit)
        
        self.tab_widget.addTab(tab, "Tapasztalat")
    
    def create_equipment_tab(self):
        """Create the starting equipment tab"""
        tab = QtWidgets.QWidget()
        eq_layout = QtWidgets.QVBoxLayout(tab)
        
        # Action buttons
        btn_row = QtWidgets.QHBoxLayout()
        self.btn_add_currency = QtWidgets.QPushButton("Pénz hozzáadása")
        self.btn_add_item = QtWidgets.QPushButton("Tárgy hozzáadása")
        self.btn_del_equipment = QtWidgets.QPushButton("Kijelölt törlése")
        btn_row.addWidget(self.btn_add_currency)
        btn_row.addWidget(self.btn_add_item)
        btn_row.addWidget(self.btn_del_equipment)
        btn_row.addStretch()
        eq_layout.addLayout(btn_row)
        
        # Equipment table
        self.eq_table = QtWidgets.QTableWidget()
        self.eq_table.setColumnCount(6)
        self.eq_table.setHorizontalHeaderLabels(["entry_id", "Típus", "Tárgy ID", "Tárgy név", "Min pénz", "Max pénz"])
        self.eq_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self.eq_table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.eq_table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        self.eq_table.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)
        self.eq_table.horizontalHeader().setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)
        self.eq_table.horizontalHeader().setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeToContents)
        self.eq_table.setColumnHidden(0, True)
        eq_layout.addWidget(self.eq_table)
        
        # Connect signals
        self.btn_add_currency.clicked.connect(self.parent.add_currency_row)
        self.btn_add_item.clicked.connect(self.parent.add_item_row)
        self.btn_del_equipment.clicked.connect(self.parent.delete_equipment_row)
        
        self.tab_widget.addTab(tab, "Kezdő felszerelés")
    
    def create_skills_tab(self):
        """Create the skills assignment tab using the reusable widget"""
        self.skill_editor_widget = ClassSkillEditorWidget()
        self.tab_widget.addTab(self.skill_editor_widget, "Képzettségek")
    
    def populate_assigned_skills(self, class_id, spec_id=None):
        """Update the skill editor widget with new class/spec selection"""
        if self.skill_editor_widget:
            self.skill_editor_widget.set_class_spec(class_id, spec_id)
    
    def create_description_tab(self):
        """Create the description tab"""
        tab = QtWidgets.QWidget()
        desc_layout = QtWidgets.QVBoxLayout(tab)
        
        # Header
        header = QtWidgets.QLabel("Leírás")
        header_font = QFont()
        header_font.setPointSize(11)
        header_font.setBold(True)
        header.setFont(header_font)
        desc_layout.addWidget(header)
        
        # Info about description file
        desc_info = QtWidgets.QLabel("A kaszt/specializáció részletes leírása külső .md fájlban található.")
        desc_info.setStyleSheet("color: #666; margin: 10px 0;")
        desc_layout.addWidget(desc_info)
        
        # Description filename (base class editable; spec auto-generated, read-only)
        filename_form = QtWidgets.QFormLayout()
        self.desc_label = QtWidgets.QLabel("Leírás fájl:")
        self.spec_desc_edit = QtWidgets.QLineEdit()
        filename_form.addRow(self.desc_label, self.spec_desc_edit)
        desc_layout.addLayout(filename_form)
        
        # Current filename display (read-only indicator)
        filename_layout = QtWidgets.QHBoxLayout()
        filename_layout.addWidget(QtWidgets.QLabel("Jelenlegi fájl:"))
        self.desc_filename_label = QtWidgets.QLabel("")
        self.desc_filename_label.setStyleSheet("font-weight: bold; color: #0066cc;")
        filename_layout.addWidget(self.desc_filename_label)
        filename_layout.addStretch()
        desc_layout.addLayout(filename_layout)
        
        # Editor for markdown content
        self.desc_text_editor = QtWidgets.QTextEdit()
        self.desc_text_editor.setPlaceholderText("Itt szerkesztheted a leírás .md fájl tartalmát…")
        desc_layout.addWidget(self.desc_text_editor, stretch=1)
        
        # Action buttons
        desc_btns = QtWidgets.QHBoxLayout()
        self.btn_save_desc = QtWidgets.QPushButton("Leírás mentése (.md)")
        self.btn_save_desc.clicked.connect(self.parent.save_description_file)
        desc_btns.addWidget(self.btn_save_desc)
        
        self.btn_open_desc = QtWidgets.QPushButton("Megnyitás külső szerkesztőben")
        self.btn_open_desc.clicked.connect(self.parent.open_description_file)
        desc_btns.addWidget(self.btn_open_desc)
        
        desc_btns.addStretch()
        desc_layout.addLayout(desc_btns)
        
        self.tab_widget.addTab(tab, "Leírás")
