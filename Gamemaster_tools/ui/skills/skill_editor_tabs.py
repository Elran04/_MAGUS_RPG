"""
Skill Editor Tabs
Handles creation of all editor tabs (Basic Info, Levels & KP, Description)
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QTextEdit, QSpinBox,
    QScrollArea, QTabWidget, QSplitter
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from .skill_editor_constants import CATEGORIES, ACQ_METHOD_MAP, ACQ_DIFF_MAP, TYPE_MAP
from .skill_prerequisite_editor import SkillPrerequisiteEditorWidget


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
        """Create the Levels & KP tab with a top overview and bottom editor tabs."""
        tab = QWidget()
        main_layout = QVBoxLayout()
        tab.setLayout(main_layout)

        # Vertical splitter: top = overview (KP + summaries), bottom = editor tabs
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Top section: Overview with KP per level and quick prerequisite summary labels
        overview_scroll = QScrollArea()
        overview_scroll.setWidgetResizable(True)

        overview_widget = QWidget()
        overview_layout = QVBoxLayout()
        overview_widget.setLayout(overview_layout)

        header = QLabel("Szintek áttekintése és KP költségek")
        header_font = QFont()
        header_font.setPointSize(11)
        header_font.setBold(True)
        header.setFont(header_font)
        overview_layout.addWidget(header)

        grid = QGridLayout()
        grid.addWidget(QLabel("Szint"), 0, 0)
        grid.addWidget(QLabel("KP"), 0, 1)
        grid.addWidget(QLabel("Előfeltételek összefoglaló"), 0, 2)

        # Keep references for other components
        self.kp_cost_spins = []
        self.prereq_labels = []
        self.prereq_widgets = []

        for i in range(6):
            level = i + 1
            # Level label
            grid.addWidget(QLabel(f"{level}."), i + 1, 0)

            # KP spin per level
            kp_spin = QSpinBox()
            kp_spin.setMaximum(999)
            self.kp_cost_spins.append(kp_spin)
            grid.addWidget(kp_spin, i + 1, 1)

            # Prerequisite summary label per level
            lbl = QLabel("")
            lbl.setWordWrap(True)
            lbl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            # Dark-mode friendly: transparent background, palette-driven text
            lbl.setStyleSheet("QLabel { background: transparent; color: palette(text); }")
            lbl.setMinimumHeight(40)
            self.prereq_labels.append(lbl)
            grid.addWidget(lbl, i + 1, 2)

        # Make summary column expand
        grid.setColumnStretch(2, 1)
        overview_layout.addLayout(grid)
        overview_layout.addStretch()

        overview_scroll.setWidget(overview_widget)
        splitter.addWidget(overview_scroll)

        # Bottom section: Nested tab widget for prerequisite editing
        self.levels_tab_widget = QTabWidget()

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
           """
           Create prerequisite editor for a specific level using the reusable widget component.
           Delegates to SkillPrerequisiteEditorWidget from skill_prerequisite_editor module.
           """
           widget = SkillPrerequisiteEditorWidget(level, self.parent.skill_names)
           return widget

    def update_prereq_skill_names(self, skill_names):
        """Propagate updated skill name list to all per-level prerequisite editor widgets."""
        if not hasattr(self, 'prereq_widgets'):
            return
        for w in self.prereq_widgets:
            if hasattr(w, 'set_skill_names'):
                w.set_skill_names(skill_names)
    
    def load_prereq_for_level(self, level):
        """Load prerequisites for a specific level into the editor"""
        widget = self.prereq_widgets[level - 1]
        level_key = str(level)
        prereqs = self.parent.current_prerequisites.get(level_key, {'képesség': [], 'képzettség': []})
        
        # Use the widget's API to load prerequisites
        if hasattr(widget, 'load_prerequisites'):
            widget.load_prerequisites(prereqs)
        else:
            # Fallback for older widget structure
            widget.stat_list.clear()
            for stat_req in prereqs.get('képesség', []):
                widget.stat_list.addItem(stat_req)
            widget.skill_list.clear()
            for skill_req in prereqs.get('képzettség', []):
                widget.skill_list.addItem(skill_req)
    
    # Deprecated helper methods removed – the embedded widget handles interactions
    
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
