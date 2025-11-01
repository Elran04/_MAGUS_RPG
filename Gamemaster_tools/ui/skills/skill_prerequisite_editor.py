"""
Skill Prerequisite Editor - PySide6 version
Modern tabbed interface for editing skill prerequisites

Refactored to provide reusable prerequisite editor components:
- SkillPrerequisiteEditorWidget: Embeddable widget for inline editing
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QCompleter,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

# Stat names (tulajdonságok)
STAT_NAMES = [
    "Erő", "Állóképesség", "Gyorsaság", "Ügyesség", "Karizma",
    "Egészség", "Intelligencia", "Akaraterő", "Asztrál", "Érzékelés"
]


class SkillPrerequisiteEditorWidget(QWidget):
    """
    Reusable prerequisite editor widget for a single skill level.
    Can be embedded in tabs or other containers.
    """
    
    def __init__(self, level, skill_names, parent=None):
        super().__init__(parent)
        self.level = level
        self.skill_names = skill_names
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        widget = QWidget()
        scroll.setWidget(widget)
        
        layout = QHBoxLayout()
        widget.setLayout(layout)
        
        # Stat prerequisites column
        stat_col = QVBoxLayout()
        stat_col.addWidget(QLabel("<b>Tulajdonság előfeltételek:</b>"))
        
        self.stat_list = QListWidget()
        self.stat_list.setMinimumHeight(200)
        stat_col.addWidget(self.stat_list)
        
        stat_controls = QHBoxLayout()
        self.stat_combo = QComboBox()
        self.stat_combo.addItems(STAT_NAMES)
        self.stat_combo.setMaximumWidth(120)
        stat_controls.addWidget(self.stat_combo)
        
        self.stat_value_spin = QSpinBox()
        self.stat_value_spin.setMinimum(1)
        self.stat_value_spin.setMaximum(20)
        self.stat_value_spin.setValue(10)
        self.stat_value_spin.setMaximumWidth(60)
        stat_controls.addWidget(self.stat_value_spin)
        
        btn_add_stat = QPushButton("+")
        btn_add_stat.setMaximumWidth(30)
        btn_add_stat.clicked.connect(self.add_stat_prereq)
        stat_controls.addWidget(btn_add_stat)
        
        btn_remove_stat = QPushButton("-")
        btn_remove_stat.setMaximumWidth(30)
        btn_remove_stat.clicked.connect(self.remove_stat_prereq)
        stat_controls.addWidget(btn_remove_stat)
        
        stat_col.addLayout(stat_controls)
        layout.addLayout(stat_col)
        
        # Skill prerequisites column
        skill_col = QVBoxLayout()
        skill_col.addWidget(QLabel("<b>Képzettség előfeltételek:</b>"))
        
        self.skill_list = QListWidget()
        self.skill_list.setMinimumHeight(200)
        skill_col.addWidget(self.skill_list)
        
        skill_controls = QHBoxLayout()
        self.skill_combo = QComboBox()
        self.skill_combo.addItems(self.skill_names)
        self.skill_combo.setEditable(True)
        completer = QCompleter(self.skill_names)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.skill_combo.setCompleter(completer)
        skill_controls.addWidget(self.skill_combo)
        
        self.skill_level_spin = QSpinBox()
        self.skill_level_spin.setMinimum(1)
        self.skill_level_spin.setMaximum(6)
        self.skill_level_spin.setValue(1)
        self.skill_level_spin.setMaximumWidth(50)
        skill_controls.addWidget(QLabel("szint"))
        skill_controls.addWidget(self.skill_level_spin)
        
        btn_add_skill = QPushButton("+")
        btn_add_skill.setMaximumWidth(30)
        btn_add_skill.clicked.connect(self.add_skill_prereq)
        skill_controls.addWidget(btn_add_skill)
        
        btn_remove_skill = QPushButton("-")
        btn_remove_skill.setMaximumWidth(30)
        btn_remove_skill.clicked.connect(self.remove_skill_prereq)
        skill_controls.addWidget(btn_remove_skill)
        
        skill_col.addLayout(skill_controls)
        layout.addLayout(skill_col)
        
        main_layout.addWidget(scroll)

    def set_skill_names(self, skill_names):
        """Update the available skill names for the skill prerequisite combo and completer."""
        # Preserve current edit text to avoid disrupting in-progress typing
        current_text = self.skill_combo.currentText().strip()
        self.skill_names = list(skill_names) if isinstance(skill_names, (list, tuple)) else []
        self.skill_combo.blockSignals(True)
        try:
            self.skill_combo.clear()
            self.skill_combo.addItems(self.skill_names)
            self.skill_combo.setEditable(True)
            completer = QCompleter(self.skill_names)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            self.skill_combo.setCompleter(completer)
            if current_text:
                self.skill_combo.setEditText(current_text)
        finally:
            self.skill_combo.blockSignals(False)
    
    def add_stat_prereq(self):
        """Add a stat prerequisite"""
        stat = self.stat_combo.currentText()
        value = self.stat_value_spin.value()
        text = f"{stat} {value}+"
        self.stat_list.addItem(text)
    
    def remove_stat_prereq(self):
        """Remove selected stat prerequisite"""
        current_item = self.stat_list.currentItem()
        if current_item:
            self.stat_list.takeItem(self.stat_list.row(current_item))
    
    def add_skill_prereq(self):
        """Add a skill prerequisite"""
        skill = self.skill_combo.currentText().strip()
        level = self.skill_level_spin.value()
        
        if not skill:
            return
        
        text = f"{skill} {level}. szint"
        self.skill_list.addItem(text)
    
    def remove_skill_prereq(self):
        """Remove selected skill prerequisite"""
        current_item = self.skill_list.currentItem()
        if current_item:
            self.skill_list.takeItem(self.skill_list.row(current_item))
    
    def load_prerequisites(self, prereqs):
        """Load prerequisites into the widget"""
        self.stat_list.clear()
        self.skill_list.clear()
        
        if isinstance(prereqs, dict):
            stat_list = prereqs.get('képesség', [])
            skill_list = prereqs.get('képzettség', [])
            
            for stat_req in stat_list:
                self.stat_list.addItem(stat_req)
            
            for skill_req in skill_list:
                self.skill_list.addItem(skill_req)
    
    def get_prerequisites(self):
        """Get current prerequisites from the widget"""
        stats = []
        for i in range(self.stat_list.count()):
            stats.append(self.stat_list.item(i).text())
        
        skills = []
        for i in range(self.skill_list.count()):
            skills.append(self.skill_list.item(i).text())
        
        return {
            'képesség': stats,
            'képzettség': skills
        }

 
