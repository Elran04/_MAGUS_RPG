"""
Skill Prerequisite Editor - PySide6 version
Modern tabbed interface for editing skill prerequisites

Refactored to provide reusable prerequisite editor components:
- SkillPrerequisiteEditorWidget: Embeddable widget for inline editing
"""

import sqlite3

from config.paths import SKILLS_DB
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
    "Erő",
    "Állóképesség",
    "Gyorsaság",
    "Ügyesség",
    "Karizma",
    "Egészség",
    "Intelligencia",
    "Akaraterő",
    "Asztrál",
    "Érzékelés",
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

        # Level input (for type=1)
        self.skill_level_spin = QSpinBox()
        self.skill_level_spin.setMinimum(1)
        self.skill_level_spin.setMaximum(6)
        self.skill_level_spin.setValue(1)
        self.skill_level_spin.setMaximumWidth(60)

        # Percent input (for type=2)
        self.skill_percent_spin = QSpinBox()
        self.skill_percent_spin.setRange(0, 100)
        self.skill_percent_spin.setSingleStep(5)
        self.skill_percent_spin.setSuffix("%")
        self.skill_percent_spin.setValue(30)
        self.skill_percent_spin.setMaximumWidth(80)

        # Placeholder label that we toggle with the inputs
        self._level_label = QLabel("szint")
        self._percent_label = QLabel("%")
        self._percent_label.setVisible(False)

        # Start with level spin visible by default; switch on selection
        skill_controls.addWidget(self._level_label)
        skill_controls.addWidget(self.skill_level_spin)
        self.skill_percent_spin.setVisible(False)
        skill_controls.addWidget(self._percent_label)
        skill_controls.addWidget(self.skill_percent_spin)

        # React to selection changes to switch input type
        self.skill_combo.currentTextChanged.connect(self._on_skill_combo_changed)

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

    def add_skill_prereq(self, skill_id=None, skill_name=None, param=None, level=None):
        """Add a skill prerequisite. Autofill stores id(param) for saving, manual adds use name(param) as before."""
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QListWidgetItem

        if skill_id is not None and skill_name is not None and level is not None:
            # Autofill: store id (with param) in UserRole, display name (with param) as text
            id_with_param = f"{skill_id} ({param})" if param else skill_id
            name_with_param = f"{skill_name} ({param})" if param else skill_name
            # Determine required skill type for proper suffix
            req_type = self._get_skill_type_by_id(skill_id)
            if req_type == 2:
                text = f"{name_with_param} {int(level)}%"
                user_val = f"{id_with_param} {int(level)}%"
            else:
                text = f"{name_with_param} {int(level)}. szint"
                user_val = f"{id_with_param} {int(level)}. szint"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, user_val)
            self.skill_list.addItem(item)
            return
        # Manual add: use display name for both text and storage (original behavior)
        skill = self.skill_combo.currentText().strip()
        if not skill:
            return
        req_type = self._get_skill_type_from_text(skill)
        if req_type == 2:
            value = int(self.skill_percent_spin.value())
            text = f"{skill} {value}%"
        else:
            value = int(self.skill_level_spin.value())
            text = f"{skill} {value}. szint"
        item = QListWidgetItem(text)
        item.setData(Qt.ItemDataRole.UserRole, text)
        self.skill_list.addItem(item)

    def _on_skill_combo_changed(self, text: str):
        """Switch input controls depending on the selected skill's type."""
        req_type = self._get_skill_type_from_text(text or "")
        is_percent = req_type == 2
        self.skill_level_spin.setVisible(not is_percent)
        self._level_label.setVisible(not is_percent)
        self.skill_percent_spin.setVisible(is_percent)
        self._percent_label.setVisible(is_percent)

    def _get_skill_type_from_text(self, text: str) -> int:
        """Resolve skill type (1 level-based, 2 percent-based) from display text 'Name' or 'Name (Param)'."""
        name = (text or "").strip()
        if not name:
            return 1
        # Parse optional parameter in parentheses
        param = None
        if name.endswith(")") and " (" in name:
            try:
                base, paren = name.rsplit(" (", 1)
                param = paren[:-1]
                name = base
            except Exception:
                pass
        try:
            with sqlite3.connect(str(SKILLS_DB)) as conn:
                if param is None:
                    row = conn.execute(
                        "SELECT type FROM skills WHERE name=? AND IFNULL(parameter,'')='' LIMIT 1",
                        (name,),
                    ).fetchone()
                else:
                    row = conn.execute(
                        "SELECT type FROM skills WHERE name=? AND parameter=? LIMIT 1",
                        (name, param),
                    ).fetchone()
                return int(row[0]) if row else 1
        except Exception:
            return 1

    def _get_skill_type_by_id(self, skill_id: str) -> int:
        try:
            with sqlite3.connect(str(SKILLS_DB)) as conn:
                row = conn.execute(
                    "SELECT type FROM skills WHERE id=? LIMIT 1", (skill_id,)
                ).fetchone()
                return int(row[0]) if row else 1
        except Exception:
            return 1

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
            stat_list = prereqs.get("képesség", [])
            skill_list = prereqs.get("képzettség", [])

            for stat_req in stat_list:
                self.stat_list.addItem(stat_req)

            for skill_req in skill_list:
                # If it's a tuple (display, id), use display as text, id as UserRole
                from PySide6.QtCore import Qt
                from PySide6.QtWidgets import QListWidgetItem

                if isinstance(skill_req, tuple) and len(skill_req) == 2:
                    item = QListWidgetItem(skill_req[0])
                    item.setData(Qt.ItemDataRole.UserRole, skill_req[1])
                    self.skill_list.addItem(item)
                else:
                    # Fallback: treat as string, both text and UserRole
                    item = QListWidgetItem(skill_req)
                    item.setData(Qt.ItemDataRole.UserRole, skill_req)
                    self.skill_list.addItem(item)

    def get_prerequisites(self):
        """Get current prerequisites from the widget (skills: use UserRole for saving, text for display)."""
        stats = []
        for i in range(self.stat_list.count()):
            stats.append(self.stat_list.item(i).text())

        skills = []
        for i in range(self.skill_list.count()):
            item = self.skill_list.item(i)
            val = item.data(256) if item is not None else None  # Qt.UserRole = 256
            if val:
                skills.append(val)
            else:
                skills.append(item.text() if item else "")

        return {"képesség": stats, "képzettség": skills}
