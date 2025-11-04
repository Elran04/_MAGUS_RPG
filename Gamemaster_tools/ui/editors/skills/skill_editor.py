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
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from ui.editors.skills.skill_editor_actions import SkillEditorActions
from ui.editors.skills.skill_editor_constants import TYPE_MAP_REV
from ui.editors.skills.skill_editor_list import SkillListPanel
from ui.editors.skills.skill_editor_tabs import SkillEditorTabs
from utils.data.skilldata_manager import SkillManager


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

        self.current_skill: dict | None = None
        self.current_prerequisites: dict = {}

        # Initialize component handlers
        self.skill_list_panel: SkillListPanel | None = None
        self.tabs: SkillEditorTabs | None = None
        self.editor_actions: SkillEditorActions | None = None

        # Initialize UI
        self.init_ui()

        # Load first skill if available
        if self.all_skills and self.skill_list_panel is not None:
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
        self.editor_actions = SkillEditorActions(self)

        # Left panel - Skill list
        self.skill_list_panel = SkillListPanel(
            splitter,
            on_skill_selected=self.on_skill_selected,
            on_new_skill=self.editor_actions.new_skill if self.editor_actions else (lambda: None),
            on_duplicate_skill=(
                self.editor_actions.duplicate_skill if self.editor_actions else (lambda: None)
            ),
            on_delete_skill=(
                self.editor_actions.delete_skill if self.editor_actions else (lambda: None)
            ),
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

        # (Button now placed inside levels tab, not here)

        # Create tab widget
        tab_widget = QTabWidget()
        editor_layout.addWidget(tab_widget)

        # Initialize tabs
        self.tabs = SkillEditorTabs(tab_widget, self)
        # Live-update prereq editor skill names as the user edits name/parameter
        if (
            self.tabs is not None
            and self.tabs.name_edit is not None
            and self.tabs.param_edit is not None
        ):
            self.tabs.name_edit.textChanged.connect(self.on_basic_info_changed)
            self.tabs.param_edit.textChanged.connect(self.on_basic_info_changed)

        # Save button
        btn_save = QPushButton("Mentés")
        btn_save.setMinimumHeight(40)
        if self.editor_actions is not None:
            btn_save.clicked.connect(self.editor_actions.save_skill)
        editor_layout.addWidget(btn_save)

        parent.addWidget(editor_widget)

    def autofill_level_prereqs(self):
        """Autofill level 2-5 (and 6 if KP>0) prereqs with previous level of this skill, showing name (param) but saving id (param)."""
        if not self.tabs or not self.current_skill:
            return
        skill_id = (
            self.tabs.id_edit.text().strip()
            if self.tabs.id_edit
            else self.current_skill.get("id", "")
        )
        skill_name = (
            self.tabs.name_edit.text().strip()
            if self.tabs.name_edit
            else self.current_skill.get("name", "")
        )
        param = (
            self.tabs.param_edit.text().strip()
            if self.tabs.param_edit
            else self.current_skill.get("parameter", "")
        )
        for i in range(1, 6):  # 1-based: 2-6
            kp_spin = self.tabs.kp_cost_spins[i] if i < len(self.tabs.kp_cost_spins) else None
            kp_val = kp_spin.value() if kp_spin else 0
            if i == 5 and kp_val == 0:
                continue  # skip 6th level if KP is 0
            prereq_widget = (
                self.tabs.prereq_widgets[i] if i < len(self.tabs.prereq_widgets) else None
            )
            if prereq_widget:
                # Clear all skill prereqs
                prereq_widget.skill_list.clear()
                # Add previous level as prereq (show name, store id)
                prev_level = i  # 1-based: level 2 gets 1, 3 gets 2, etc.
                prereq_widget.add_skill_prereq(
                    skill_id=skill_id, skill_name=skill_name, param=param, level=prev_level
                )

    def on_skill_selected(self, index):
        """Handle skill selection from list"""
        if index < 0 or index >= len(self.all_skills):
            return

        self.current_skill = self.all_skills[index]
        if self.editor_actions is not None:
            self.editor_actions.load_skill_to_ui()

        # Also suggest this skill in the Placeholder tab's search/selection, if it's not a placeholder itself
        try:
            if self.tabs is not None:
                placeholder_tab = getattr(self.tabs, "placeholder_tab", None)
                if placeholder_tab is not None:
                    skill = self.current_skill
                    if skill and skill.get("placeholder", 0) != 1:
                        name = skill.get("name", "")
                        param = skill.get("parameter", "")
                        display = f"{name} ({param})" if param else name
                        placeholder_tab.suggest_skill_selection(skill.get("id"), display)
        except (AttributeError, KeyError, TypeError):
            # Non-fatal: ignore wiring errors
            pass

    def update_type_dependent_fields(self):
        """Enable/disable KP fields depending on skill type selection."""
        if self.tabs is None or self.tabs.type_combo is None:
            return
        current = self.tabs.type_combo.currentText()
        st = TYPE_MAP_REV.get(current, 1)
        is_level = st == 1
        # Level-based: enable per-level KP, disable KP/3%
        for spin in self.tabs.kp_cost_spins:
            spin.setEnabled(is_level)
        if self.tabs.kp_per_3_spin is not None:
            self.tabs.kp_per_3_spin.setEnabled(not is_level)

    def update_prereq_summary(self):
        """Update prerequisite summary labels - delegates to actions"""
        if self.editor_actions is not None:
            self.editor_actions.update_prereq_summary()

    def on_basic_info_changed(self):
        """Rebuild the list of displayable skill names and propagate to prereq editors.
        Includes the current unsaved name/parameter so self-referencing is possible immediately.
        """
        if self.tabs is None or self.tabs.name_edit is None or self.tabs.param_edit is None:
            return
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
        if hasattr(self.tabs, "update_prereq_skill_names"):
            self.tabs.update_prereq_skill_names(self.skill_names)

    def open_description_file(self):
        """Open description file - delegates to actions"""
        if self.editor_actions is not None:
            self.editor_actions.open_description_file()

    def save_description_file(self):
        """Save description file - delegates to actions"""
        if self.editor_actions is not None:
            self.editor_actions.save_description_file()


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    # Import dark mode
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    from utils.ui.dark_mode import apply_dark_mode

    app = QApplication(sys.argv)
    apply_dark_mode(app)

    editor = SkillEditorQt()
    editor.show()

    sys.exit(app.exec())
