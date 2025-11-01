"""
Skill Editor - PySide6 version with dark mode support
Modern tabbed interface for M.A.G.U.S. skill management
Refactored into modular components for better maintainability
"""
import os
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from ui.skills.skill_editor_actions import SkillEditorActions
from ui.skills.skill_editor_constants import TYPE_MAP_REV
from ui.skills.skill_editor_list import SkillListPanel
from ui.skills.skill_editor_tabs import SkillEditorTabs
from utils.skilldata_manager import SkillManager


class SkillEditorQt(QMainWindow):
    """Modern skill editor with tabbed interface"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Képzettség szerkesztő")
        self.resize(1400, 900)  
        
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
        
        # Set splitter sizes (50% list, 50% editor for equal space)
        splitter.setSizes([600, 800])
    
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
        # Live-update prereq editor skill names as the user edits name/parameter
        self.tabs.name_edit.textChanged.connect(self.on_basic_info_changed)
        self.tabs.param_edit.textChanged.connect(self.on_basic_info_changed)
        
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

        # Also suggest this skill in the Placeholder tab's search/selection, if it's not a placeholder itself
        try:
            if getattr(self.tabs, 'placeholder_tab', None):
                skill = self.current_skill
                if skill and skill.get('placeholder', 0) != 1:
                    name = skill.get('name', '')
                    param = skill.get('parameter', '')
                    display = f"{name} ({param})" if param else name
                    self.tabs.placeholder_tab.suggest_skill_selection(skill.get('id'), display)
        except Exception:
            # Non-fatal: ignore wiring errors
            pass
    
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

    def on_basic_info_changed(self):
        """Rebuild the list of displayable skill names and propagate to prereq editors.
        Includes the current unsaved name/parameter so self-referencing is possible immediately.
        """
        names = []
        for s in self.all_skills:
            # Use live UI values for the current skill to allow self-referencing before save
            if self.current_skill is not None and s is self.current_skill:
                name = self.tabs.name_edit.text().strip()
                param = self.tabs.param_edit.text().strip()
            else:
                name = s.get("name", "")
                param = s.get("parameter", "")
            display = f"{name} ({param})" if param else name
            if display:
                names.append(display)
        # Update cached names
        self.skill_names = names
        # Push into all per-level prerequisite editor widgets
        if hasattr(self.tabs, 'update_prereq_skill_names'):
            self.tabs.update_prereq_skill_names(self.skill_names)
    
    def open_description_file(self):
        """Open description file - delegates to actions"""
        self.actions.open_description_file()
    
    def save_description_file(self):
        """Save description file - delegates to actions"""
        self.actions.save_description_file()


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
