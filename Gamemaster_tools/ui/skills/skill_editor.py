"""
Skill Editor - PySide6 version with dark mode support
Modern tabbed interface for M.A.G.U.S. skill management
Refactored into modular components for better maintainability
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QPushButton, QSplitter,
    QTabWidget, QMessageBox, QVBoxLayout
)
from PySide6.QtCore import Qt
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from utils.skilldata_manager import SkillManager
from ui.skills.skill_editor_constants import TYPE_MAP_REV
from ui.skills.skill_editor_list import SkillListPanel
from ui.skills.skill_editor_tabs import SkillEditorTabs
from ui.skills.skill_editor_actions import SkillEditorActions



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
        
        # Build skill names with parameters for autocomplete
        self.skill_names = []
        for s in self.all_skills:
            name = s["name"]
            param = s.get("parameter", "")
            display_name = f"{name} ({param})" if param else name
            self.skill_names.append(display_name)
        
        self.current_skill = None
        self.current_prerequisites = {}
        
        # Initialize component handlers
        self.skill_list_panel = None
        self.tabs = None
        self.actions = None
        
        # Initialize UI
        self.init_ui()
        
        # Load first skill if available
        if self.all_skills:
            self.skill_list_panel.set_current_row(0)
    
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
        
        # Initialize actions handler
        self.actions = SkillEditorActions(self)
        
        # Left panel - Skill list
        self.skill_list_panel = SkillListPanel(
            splitter,
            on_skill_selected=self.on_skill_selected,
            on_new_skill=self.actions.new_skill,
            on_duplicate_skill=self.actions.duplicate_skill,
            on_delete_skill=self.actions.delete_skill
        )
        self.skill_list_panel.populate(self.all_skills)
        
        # Right panel - Editor
        self.create_editor_panel(splitter)
        
        # Set splitter sizes (30% list, 70% editor)
        splitter.setSizes([300, 900])
    
    def create_editor_panel(self, parent):
        """Create the editor panel on the right"""
        editor_widget = QWidget()
        editor_layout = QVBoxLayout()
        editor_widget.setLayout(editor_layout)
        
        # Create tab widget
        tab_widget = QTabWidget()
        editor_layout.addWidget(tab_widget)
        
        # Initialize tabs
        self.tabs = SkillEditorTabs(tab_widget, self)
        
        # Save button
        btn_save = QPushButton("Mentés")
        btn_save.setMinimumHeight(40)
        btn_save.clicked.connect(self.actions.save_skill)
        editor_layout.addWidget(btn_save)
        
        parent.addWidget(editor_widget)
    
    def on_skill_selected(self, index):
        """Handle skill selection from list"""
        if index < 0 or index >= len(self.all_skills):
            return
        
        self.current_skill = self.all_skills[index]
        self.actions.load_skill_to_ui()
    
    def update_type_dependent_fields(self):
        """Enable/disable KP fields depending on skill type selection."""
        current = self.tabs.type_combo.currentText()
        st = TYPE_MAP_REV.get(current, 1)
        is_level = (st == 1)
        # Level-based: enable per-level KP, disable KP/3%
        for spin in self.tabs.kp_cost_spins:
            spin.setEnabled(is_level)
        self.tabs.kp_per_3_spin.setEnabled(not is_level)
    
    def update_prereq_summary(self):
        """Update prerequisite summary labels - delegates to actions"""
        self.actions.update_prereq_summary()
    
    def open_description_file(self):
        """Open description file - delegates to actions"""
        self.actions.open_description_file()
    
    def save_description_file(self):
        """Save description file - delegates to actions"""
        self.actions.save_description_file()
    
    def open_prereq_editor(self):
        """Open prerequisite editor dialog"""
        if not self.current_skill:
            QMessageBox.warning(self, "Figyelem", "Nincs kiválasztott képzettség!")
            return
        
        # Import and open the PySide6 prerequisite editor
        try:
            from .skill_prerequisite_editor import SkillPrerequisiteEditorQt
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
