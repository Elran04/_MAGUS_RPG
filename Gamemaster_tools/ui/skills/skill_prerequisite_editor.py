"""
Skill Prerequisite Editor - PySide6 version
Modern tabbed interface for editing skill prerequisites
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QTabWidget,
    QLabel, QLineEdit, QComboBox, QPushButton, QSpinBox, QListWidget,
    QGroupBox, QMessageBox, QWidget, QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import re

# Stat names (tulajdonságok)
STAT_NAMES = [
    "Erő", "Állóképesség", "Gyorsaság", "Ügyesség", "Karizma",
    "Egészség", "Intelligencia", "Akaraterő", "Asztrál", "Érzékelés"
]


class SkillPrerequisiteEditorQt(QDialog):
    """Modern prerequisite editor for skills"""
    
    def __init__(self, parent_editor):
        # Parent should be the QWidget (the editor window), not the editor object itself
        super().__init__(parent_editor if hasattr(parent_editor, 'windowTitle') else None)
        self.parent_editor = parent_editor
        self.skill_names = parent_editor.skill_names
        self.prerequisites = parent_editor.current_prerequisites.copy()
        
        # Ensure prerequisites has structure for all 6 levels
        for i in range(1, 7):
            level_key = str(i)
            if level_key not in self.prerequisites:
                self.prerequisites[level_key] = {'képesség': [], 'képzettség': []}
        
        self.setWindowTitle("Előfeltételek szerkesztése")
        self.resize(1000, 700)
        self.setModal(True)
        
        self.init_ui()
        self.load_prerequisites()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header
        header = QLabel("Képzettség előfeltételek szerkesztése")
        header_font = QFont()
        header_font.setPointSize(12)
        header_font.setBold(True)
        header.setFont(header_font)
        layout.addWidget(header)
        
        # Create tab widget for 6 levels
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Store widgets for each level
        self.level_widgets = []
        
        for i in range(6):
            level = i + 1
            tab = self.create_level_tab(level)
            self.tab_widget.addTab(tab, f"{level}. szint")
            self.level_widgets.append(tab)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        btn_save = QPushButton("Mentés")
        btn_save.setMinimumHeight(40)
        btn_save.clicked.connect(self.save_and_close)
        btn_layout.addWidget(btn_save)
        
        btn_cancel = QPushButton("Mégse")
        btn_cancel.setMinimumHeight(40)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)
        
        layout.addLayout(btn_layout)
    
    def create_level_tab(self, level):
        """Create a tab for one skill level"""
        widget = QWidget()
        widget.level = level
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Stat prerequisites section
        stat_group = QGroupBox("Tulajdonság előfeltételek")
        stat_layout = QVBoxLayout()
        stat_group.setLayout(stat_layout)
        
        # Stat list
        widget.stat_list = QListWidget()
        widget.stat_list.setMaximumHeight(150)
        stat_layout.addWidget(widget.stat_list)
        
        # Add stat controls
        stat_add_layout = QHBoxLayout()
        widget.stat_combo = QComboBox()
        widget.stat_combo.addItems(STAT_NAMES)
        stat_add_layout.addWidget(QLabel("Tulajdonság:"))
        stat_add_layout.addWidget(widget.stat_combo)
        
        widget.stat_value_spin = QSpinBox()
        widget.stat_value_spin.setMinimum(1)
        widget.stat_value_spin.setMaximum(20)
        widget.stat_value_spin.setValue(10)
        stat_add_layout.addWidget(QLabel("Minimum érték:"))
        stat_add_layout.addWidget(widget.stat_value_spin)
        
        btn_add_stat = QPushButton("Hozzáadás")
        btn_add_stat.clicked.connect(lambda checked, w=widget: self.add_stat_prereq(w))
        stat_add_layout.addWidget(btn_add_stat)
        
        btn_remove_stat = QPushButton("Törlés")
        btn_remove_stat.clicked.connect(lambda checked, w=widget: self.remove_stat_prereq(w))
        stat_add_layout.addWidget(btn_remove_stat)
        
        stat_add_layout.addStretch()
        stat_layout.addLayout(stat_add_layout)
        
        layout.addWidget(stat_group)
        
        # Skill prerequisites section
        skill_group = QGroupBox("Képzettség előfeltételek")
        skill_layout = QVBoxLayout()
        skill_group.setLayout(skill_layout)
        
        # Skill list
        widget.skill_list = QListWidget()
        widget.skill_list.setMaximumHeight(200)
        skill_layout.addWidget(widget.skill_list)
        
        # Add skill controls
        skill_add_layout = QVBoxLayout()
        
        # Row 1: Skill name
        skill_name_layout = QHBoxLayout()
        widget.skill_combo = QComboBox()
        widget.skill_combo.addItems(self.skill_names)
        widget.skill_combo.setEditable(True)
        skill_name_layout.addWidget(QLabel("Képzettség:"))
        skill_name_layout.addWidget(widget.skill_combo)
        skill_add_layout.addLayout(skill_name_layout)
        
        # Row 2: Parameter and level
        skill_details_layout = QHBoxLayout()
        widget.skill_param_edit = QLineEdit()
        widget.skill_param_edit.setPlaceholderText("Paraméter (opcionális, pl. Rövid kardok)")
        skill_details_layout.addWidget(QLabel("Paraméter:"))
        skill_details_layout.addWidget(widget.skill_param_edit)
        
        widget.skill_level_spin = QSpinBox()
        widget.skill_level_spin.setMinimum(1)
        widget.skill_level_spin.setMaximum(6)
        widget.skill_level_spin.setValue(1)
        skill_details_layout.addWidget(QLabel("Szint:"))
        skill_details_layout.addWidget(widget.skill_level_spin)
        skill_add_layout.addLayout(skill_details_layout)
        
        # Row 3: Buttons
        skill_btn_layout = QHBoxLayout()
        btn_add_skill = QPushButton("Hozzáadás")
        btn_add_skill.clicked.connect(lambda checked, w=widget: self.add_skill_prereq(w))
        skill_btn_layout.addWidget(btn_add_skill)
        
        btn_remove_skill = QPushButton("Törlés")
        btn_remove_skill.clicked.connect(lambda checked, w=widget: self.remove_skill_prereq(w))
        skill_btn_layout.addWidget(btn_remove_skill)
        
        skill_btn_layout.addStretch()
        skill_add_layout.addLayout(skill_btn_layout)
        
        skill_layout.addLayout(skill_add_layout)
        
        layout.addWidget(skill_group)
        layout.addStretch()
        
        return widget
    
    def add_stat_prereq(self, widget):
        """Add a stat prerequisite"""
        stat = widget.stat_combo.currentText()
        value = widget.stat_value_spin.value()
        
        prereq_text = f"{stat} {value}+"
        
        # Check if already exists
        for i in range(widget.stat_list.count()):
            if widget.stat_list.item(i).text().startswith(stat):
                QMessageBox.warning(self, "Figyelem", f"{stat} már hozzá van adva!")
                return
        
        widget.stat_list.addItem(prereq_text)
    
    def remove_stat_prereq(self, widget):
        """Remove selected stat prerequisite"""
        current_item = widget.stat_list.currentItem()
        if current_item:
            widget.stat_list.takeItem(widget.stat_list.row(current_item))
    
    def add_skill_prereq(self, widget):
        """Add a skill prerequisite"""
        skill = widget.skill_combo.currentText().strip()
        param = widget.skill_param_edit.text().strip()
        level = widget.skill_level_spin.value()
        
        if not skill:
            QMessageBox.warning(self, "Figyelem", "Válassz ki egy képzettséget!")
            return
        
        # Build display text
        prereq_text = skill
        if param:
            prereq_text += f" ({param})"
        prereq_text += f" {level}. szint"
        
        widget.skill_list.addItem(prereq_text)
        
        # Clear param for next entry
        widget.skill_param_edit.clear()
    
    def remove_skill_prereq(self, widget):
        """Remove selected skill prerequisite"""
        current_item = widget.skill_list.currentItem()
        if current_item:
            widget.skill_list.takeItem(widget.skill_list.row(current_item))
    
    def load_prerequisites(self):
        """Load existing prerequisites into the UI"""
        for i in range(6):
            level = i + 1
            level_key = str(level)
            widget = self.level_widgets[i]
            
            prereqs = self.prerequisites.get(level_key, {'képesség': [], 'képzettség': []})
            
            # Load stats
            for stat_prereq in prereqs.get('képesség', []):
                widget.stat_list.addItem(stat_prereq)
            
            # Load skills
            for skill_prereq in prereqs.get('képzettség', []):
                widget.skill_list.addItem(skill_prereq)
    
    def save_and_close(self):
        """Save prerequisites and close dialog"""
        # Collect data from all tabs
        new_prereqs = {}
        
        for i in range(6):
            level = i + 1
            level_key = str(level)
            widget = self.level_widgets[i]
            
            # Collect stat prerequisites
            stats = []
            for j in range(widget.stat_list.count()):
                stats.append(widget.stat_list.item(j).text())
            
            # Collect skill prerequisites
            skills = []
            for j in range(widget.skill_list.count()):
                skills.append(widget.skill_list.item(j).text())
            
            new_prereqs[level_key] = {
                'képesség': stats,
                'képzettség': skills
            }
        
        # Update parent editor
        self.parent_editor.current_prerequisites = new_prereqs
        self.parent_editor.update_prereq_summary()
        
        self.accept()


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # Mock parent editor for testing
    class MockEditor:
        def __init__(self):
            self.skill_names = ["Fegyverhasználat", "Lovaglás", "Úszás"]
            self.current_prerequisites = {
                '1': {'képesség': ['Ügyesség 10+'], 'képzettség': []},
                '2': {'képesség': ['Ügyesség 11+'], 'képzettség': ['Fegyverhasználat (Rövid kardok) 1. szint']}
            }
        
        def update_prereq_summary(self):
            print("Prerequisites updated:", self.current_prerequisites)
    
    # Apply dark mode
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from utils.dark_mode import apply_dark_mode
    apply_dark_mode(app)
    
    mock = MockEditor()
    editor = SkillPrerequisiteEditorQt(mock)
    editor.show()
    
    sys.exit(app.exec())
