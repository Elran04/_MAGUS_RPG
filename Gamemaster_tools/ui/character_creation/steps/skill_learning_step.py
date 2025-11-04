"""
Skill Learning Step
Allows players to spend KP on learning new skills during character creation.
Separate from mandatory class skills and placeholder resolution.
"""

import sqlite3
from collections.abc import Callable
from typing import Any

from PySide6 import QtCore, QtGui, QtWidgets
from ui.character_creation.helpers.skill_db_helper import SkillDatabaseHelper
from ui.character_creation.helpers.skill_prerequisites import SkillPrerequisiteChecker
from ui.character_creation.helpers.skill_selection_manager import SkillSelectionManager
from utils.log.logger import get_logger
from utils.ui.themes import CharacterCreationTheme, header_label_style, info_label_style

logger = get_logger(__name__)


class SkillLearningStepWidget(QtWidgets.QWidget):
    """
    Skill learning interface for spending KP on new skills.
    Shows available skills catalog and tracks KP spending.
    """

    def __init__(
        self,
        base_dir: str,
        get_character_data: Callable[[], dict[str, Any]],
    ):
        super().__init__()
        self.BASE_DIR = base_dir
        self.get_character_data = get_character_data

        # Initialize helpers
        self.db_helper = SkillDatabaseHelper(base_dir)
        self.prereq_checker = SkillPrerequisiteChecker(self.db_helper)
        self.selection_manager: SkillSelectionManager | None = None

        # UI components
        self.kp_info_label: QtWidgets.QLabel | None = None
        self.skills_table: QtWidgets.QTableWidget | None = None
        self.attributes_widget = None

        self._build_ui()

    def _build_ui(self):
        """Build the UI with left panel (attributes) and right panel (skills)."""
        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)

        # Left panel: Read-only attributes display
        from ui.character_creation.widgets.attributes_readonly_display import AttributesReadOnlyWidget
        
        self.attributes_widget = AttributesReadOnlyWidget(self.get_character_data)
        splitter.addWidget(self.attributes_widget)

        # Right panel: Skills section
        right_panel = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(right_panel)
        layout.setContentsMargins(0, 0, 0, 0)

        # Title and KP info
        header = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("Képzettségek Tanulása")
        title.setStyleSheet("font-weight: bold; font-size: 14px; padding: 4px;")
        header.addWidget(title)
        header.addStretch()
        
        self.kp_info_label = QtWidgets.QLabel("")
        self.kp_info_label.setStyleSheet(header_label_style())
        header.addWidget(self.kp_info_label)
        layout.addLayout(header)

        # Info text
        info = QtWidgets.QLabel(
            "Itt tudsz új képzettségeket tanulni a rendelkezésre álló KP-ból. "
            "A kötelező kaszt képzettségek alább láthatóak."
        )
        info.setWordWrap(True)
        info.setStyleSheet(info_label_style())
        layout.addWidget(info)

        # Add skill button
        add_skill_btn = QtWidgets.QPushButton("➕ Új képzettség tanulása")
        add_skill_btn.clicked.connect(self._show_add_skill_dialog)
        layout.addWidget(add_skill_btn)

        # Skills table (showing mandatory + learned skills)
        layout.addWidget(QtWidgets.QLabel("Képzettségek:"))
        self.skills_table = QtWidgets.QTableWidget()
        self.skills_table.setColumnCount(6)
        self.skills_table.setHorizontalHeaderLabels([
            "Képzettség", "Szint", "%", "KP költség", "Forrás", "Művelet"
        ])
        self.skills_table.horizontalHeader().setStretchLastSection(False)
        self.skills_table.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        self.skills_table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.skills_table.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers
        )
        layout.addWidget(self.skills_table)

        splitter.addWidget(right_panel)
        splitter.setSizes([200, 1000])  # ~20% left, ~80% right
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)



    def refresh(self):
        """Refresh the UI with current character data and initialize selection manager."""
        data = self.get_character_data() or {}
        
        # Refresh attributes display
        if hasattr(self, 'attributes_widget'):
            self.attributes_widget.refresh()
        
        # Initialize selection manager if not already done
        if self.selection_manager is None:
            kp_data = data.get("Képzettségpontok", {})
            kp_base = kp_data.get("Alap", 0)
            kp_per_level = kp_data.get("Szintenként", 0)
            kp_total = kp_base + kp_per_level  # 1st level
            
            # Get attribute bonuses
            attributes = data.get("Tulajdonságok", {})
            intelligence = attributes.get("Intelligencia", 10)
            dexterity = attributes.get("Ügyesség", 10)
            kp_int_bonus = max(0, intelligence - 10)
            kp_dex_bonus = max(0, dexterity - 10)
            
            self.selection_manager = SkillSelectionManager(
                self.db_helper,
                self.prereq_checker,
                kp_total,
                kp_int_bonus,
                kp_dex_bonus,
            )
            
            # Set mandatory skills from previous step
            mandatory = {}
            for skill in data.get("Képzettségek", []):
                skill_id = skill.get("id")
                if skill_id:
                    mandatory[skill_id] = {
                        "level": skill.get("Szint", 0),
                        "%": skill.get("%", 0),
                        "source": skill.get("Forrás", "Kaszt"),
                    }
            self.selection_manager.set_mandatory_skills(mandatory)
        
        # Update KP display
        self._update_kp_display()
        
        # Load all skills into single table
        self._load_skills_table()

    def _update_kp_display(self):
        """Update the KP info label."""
        if not self.selection_manager or not self.kp_info_label:
            return
        
        breakdown = self.selection_manager.get_kp_breakdown()
        text = (
            f"KP: <b>{breakdown['remaining']}</b> / {breakdown['total']} "
            f"(Alap: {breakdown['base']}"
        )
        if breakdown['intelligence'] > 0:
            text += f" + Int: {breakdown['intelligence']}"
        if breakdown['dexterity'] > 0:
            text += f" + Ügy: {breakdown['dexterity']}"
        text += f" | Elköltve: {breakdown['spent']})"
        
        self.kp_info_label.setText(text)

    def _load_skills_table(self):
        """Load all skills (mandatory + learned) into the table, similar to skills_step."""
        if not self.skills_table or not self.selection_manager:
            return
        
        self.skills_table.setRowCount(0)
        
        try:
            with sqlite3.connect(self.db_helper.get_db_path("skill")) as conn:
                # Load mandatory skills (from previous step)
                for skill_id, data in self.selection_manager.mandatory_skills.items():
                    row_data = conn.execute(
                        "SELECT name, parameter FROM skills WHERE id=?", (skill_id,)
                    ).fetchone()
                    
                    if not row_data:
                        continue
                    
                    name, parameter = row_data
                    display_name = f"{name} ({parameter})" if parameter else name
                    
                    self._add_skill_row(
                        display_name,
                        data.get("level", 0),
                        data.get("%", 0),
                        0,  # No KP cost for mandatory skills
                        data.get("source", "Kaszt"),
                        is_mandatory=True,
                    )
                
                # Load learned skills (optional, user-added)
                for skill_id, data in self.selection_manager.learned_skills.items():
                    row_data = conn.execute(
                        "SELECT name, parameter FROM skills WHERE id=?", (skill_id,)
                    ).fetchone()
                    
                    if not row_data:
                        continue
                    
                    name, parameter = row_data
                    display_name = f"{name} ({parameter})" if parameter else name
                    
                    self._add_skill_row(
                        display_name,
                        data.get("level", 0),
                        data.get("%", 0),
                        data.get("kp_cost", 0),
                        "Tanult",
                        is_mandatory=False,
                        skill_id=skill_id,
                    )
        
        except Exception as e:
            logger.error(f"Error loading skills table: {e}", exc_info=True)

    def _add_skill_row(
        self,
        display_name: str,
        level: int,
        percent: int,
        kp_cost: int,
        source: str,
        is_mandatory: bool,
        skill_id: str | None = None,
    ):
        """Add a skill row to the table."""
        if not self.skills_table:
            return
        
        row = self.skills_table.rowCount()
        self.skills_table.insertRow(row)
        
        # Skill name
        name_item = QtWidgets.QTableWidgetItem(display_name)
        if is_mandatory:
            # Gray out mandatory skills
            name_item.setForeground(QtGui.QBrush(QtGui.QColor("#888888")))
        self.skills_table.setItem(row, 0, name_item)
        
        # Level
        level_item = QtWidgets.QTableWidgetItem(str(level) if level else "-")
        if is_mandatory:
            level_item.setForeground(QtGui.QBrush(QtGui.QColor("#888888")))
        self.skills_table.setItem(row, 1, level_item)
        
        # Percent
        percent_item = QtWidgets.QTableWidgetItem(str(percent) if percent else "-")
        if is_mandatory:
            percent_item.setForeground(QtGui.QBrush(QtGui.QColor("#888888")))
        self.skills_table.setItem(row, 2, percent_item)
        
        # KP cost
        kp_item = QtWidgets.QTableWidgetItem(str(kp_cost))
        if is_mandatory:
            kp_item.setForeground(QtGui.QBrush(QtGui.QColor("#888888")))
        self.skills_table.setItem(row, 3, kp_item)
        
        # Source
        source_item = QtWidgets.QTableWidgetItem(source)
        if is_mandatory:
            source_item.setForeground(QtGui.QBrush(QtGui.QColor("#888888")))
        self.skills_table.setItem(row, 4, source_item)
        
        # Action column
        if is_mandatory:
            # No action for mandatory skills
            self.skills_table.setItem(row, 5, QtWidgets.QTableWidgetItem("-"))
        else:
            # Remove button for learned skills
            remove_btn = QtWidgets.QPushButton("❌ Törlés")
            remove_btn.setProperty("skill_id", skill_id)
            remove_btn.clicked.connect(self._on_remove_skill)
            self.skills_table.setCellWidget(row, 5, remove_btn)

    def _on_remove_skill(self):
        """Handle remove button click for learned skills."""
        btn = self.sender()
        if not isinstance(btn, QtWidgets.QPushButton) or not self.selection_manager:
            return
        
        skill_id = btn.property("skill_id")
        if not skill_id:
            return
        
        if self.selection_manager.unlearn_skill(skill_id):
            self._update_kp_display()
            self._load_skills_table()

    def _show_add_skill_dialog(self):
        """Show dialog to select and add a new skill to learn."""
        if not self.selection_manager:
            return
        
        # Create dialog
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Új képzettség tanulása")
        dialog.setMinimumSize(800, 600)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        
        # Filters
        filter_layout = QtWidgets.QHBoxLayout()
        
        # Category filter
        filter_layout.addWidget(QtWidgets.QLabel("Kategória:"))
        category_combo = QtWidgets.QComboBox()
        category_combo.addItem("Minden kategória", None)
        filter_layout.addWidget(category_combo, stretch=1)
        
        # Search box
        filter_layout.addWidget(QtWidgets.QLabel("Keresés:"))
        search_box = QtWidgets.QLineEdit()
        search_box.setPlaceholderText("Képzettség neve...")
        filter_layout.addWidget(search_box, stretch=1)
        
        layout.addLayout(filter_layout)
        
        # Available skills table
        skills_table = QtWidgets.QTableWidget()
        skills_table.setColumnCount(5)
        skills_table.setHorizontalHeaderLabels([
            "Képzettség", "Kategória", "Típus", "Min. KP", "Előfeltételek"
        ])
        skills_table.horizontalHeader().setStretchLastSection(True)
        skills_table.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        skills_table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )
        skills_table.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers
        )
        skills_table.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.SingleSelection
        )
        layout.addWidget(skills_table)
        
        # Load categories
        try:
            with sqlite3.connect(self.db_helper.get_db_path("skill")) as conn:
                cursor = conn.execute(
                    "SELECT DISTINCT category FROM skills WHERE placeholder = 0 AND category IS NOT NULL ORDER BY category"
                )
                for (category,) in cursor.fetchall():
                    if category:
                        category_combo.addItem(category, category)
        except Exception as e:
            logger.error(f"Error loading categories: {e}", exc_info=True)
        
        # Function to load skills into table
        def load_skills():
            skills_table.setRowCount(0)
            category_filter = category_combo.currentData()
            search_filter = search_box.text().lower()
            current_skills = self.selection_manager.get_all_skills()
            
            try:
                with sqlite3.connect(self.db_helper.get_db_path("skill")) as conn:
                    query = "SELECT id, name, parameter, category, type FROM skills WHERE placeholder = 0"
                    params = []
                    
                    if category_filter:
                        query += " AND category = ?"
                        params.append(category_filter)
                    
                    query += " ORDER BY category, name"
                    
                    cursor = conn.execute(query, params)
                    
                    for skill_id, name, parameter, category, skill_type in cursor.fetchall():
                        # Skip if already have this skill
                        if skill_id in current_skills:
                            continue
                        
                        # Apply search filter
                        display_name = f"{name} ({parameter})" if parameter else name
                        if search_filter and search_filter not in display_name.lower():
                            continue
                        
                        # Add row
                        row = skills_table.rowCount()
                        skills_table.insertRow(row)
                        
                        # Store skill_id and type in first item
                        name_item = QtWidgets.QTableWidgetItem(display_name)
                        name_item.setData(QtCore.Qt.ItemDataRole.UserRole, (skill_id, skill_type))
                        skills_table.setItem(row, 0, name_item)
                        
                        skills_table.setItem(row, 1, QtWidgets.QTableWidgetItem(category or ""))
                        
                        type_text = "Szint" if skill_type == 1 else ("%" if skill_type == 2 else "Mindkettő")
                        skills_table.setItem(row, 2, QtWidgets.QTableWidgetItem(type_text))
                        
                        # KP cost for minimum (level 1 or 3%)
                        level = 1 if skill_type == 1 else 0
                        percent = 3 if skill_type == 2 else 0
                        kp_cost = self.db_helper.calc_kp_cost(skill_id, level, percent)
                        skills_table.setItem(row, 3, QtWidgets.QTableWidgetItem(str(kp_cost)))
                        
                        # Prerequisites - TODO
                        skills_table.setItem(row, 4, QtWidgets.QTableWidgetItem("-"))
            
            except Exception as e:
                logger.error(f"Error loading skills: {e}", exc_info=True)
        
        # Connect filters
        category_combo.currentIndexChanged.connect(load_skills)
        search_box.textChanged.connect(load_skills)
        
        # Initial load
        load_skills()
        
        # Buttons
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        # Show dialog
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            # Get selected skill
            selected_rows = skills_table.selectionModel().selectedRows()
            if not selected_rows:
                QtWidgets.QMessageBox.warning(self, "Nincs kiválasztva", "Válassz ki egy képzettséget!")
                return
            
            row = selected_rows[0].row()
            name_item = skills_table.item(row, 0)
            skill_id, skill_type = name_item.data(QtCore.Qt.ItemDataRole.UserRole)
            
            # Show level/percent selection dialog
            self._show_skill_level_dialog(skill_id, skill_type)
    
    def _show_skill_level_dialog(self, skill_id: str, skill_type: int):
        """Show dialog to select level and/or percent for the skill."""
        if not self.selection_manager:
            return
        
        # Get skill name
        try:
            with sqlite3.connect(self.db_helper.get_db_path("skill")) as conn:
                row = conn.execute("SELECT name, parameter FROM skills WHERE id=?", (skill_id,)).fetchone()
                if not row:
                    return
                name, parameter = row
                display_name = f"{name} ({parameter})" if parameter else name
        except Exception as e:
            logger.error(f"Error getting skill name: {e}", exc_info=True)
            return
        
        # Create dialog
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(f"Tanulás: {display_name}")
        dialog.setMinimumWidth(400)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        
        # Info
        info = QtWidgets.QLabel(f"Állítsd be a tanulni kívánt szintet/százalékot:")
        layout.addWidget(info)
        
        form = QtWidgets.QFormLayout()
        
        # Level spinbox (if applicable)
        level_spin = None
        if skill_type in (1, 3):  # Has level
            level_spin = QtWidgets.QSpinBox()
            level_spin.setMinimum(1)
            level_spin.setMaximum(5)
            level_spin.setValue(1)
            form.addRow("Szint:", level_spin)
        
        # Percent spinbox (if applicable)
        percent_spin = None
        if skill_type in (2, 3):  # Has percent
            percent_spin = QtWidgets.QSpinBox()
            percent_spin.setMinimum(0)
            percent_spin.setMaximum(100)
            percent_spin.setSingleStep(3)
            percent_spin.setValue(3)
            form.addRow("%:", percent_spin)
        
        layout.addLayout(form)
        
        # KP cost label
        kp_label = QtWidgets.QLabel("")
        kp_label.setStyleSheet("font-weight: bold; padding: 8px;")
        layout.addWidget(kp_label)
        
        # Update KP cost
        def update_kp_cost():
            level = level_spin.value() if level_spin else 0
            percent = percent_spin.value() if percent_spin else 0
            cost = self.db_helper.calc_kp_cost(skill_id, level, percent)
            kp_label.setText(f"KP költség: {cost}")
        
        if level_spin:
            level_spin.valueChanged.connect(update_kp_cost)
        if percent_spin:
            percent_spin.valueChanged.connect(update_kp_cost)
        
        update_kp_cost()
        
        # Buttons
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        # Show dialog
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            level = level_spin.value() if level_spin else 0
            percent = percent_spin.value() if percent_spin else 0
            
            # Try to learn the skill
            current_skills = self.selection_manager.get_all_skills()
            can_learn, reason, kp_cost = self.selection_manager.can_learn_skill(
                skill_id, level, percent, current_skills
            )
            
            if not can_learn:
                QtWidgets.QMessageBox.warning(self, "Nem tanulható", reason)
                return
            
            # Learn the skill
            if self.selection_manager.learn_skill(skill_id, level, percent, kp_cost):
                self._update_kp_display()
                self._load_skills_table()
            else:
                QtWidgets.QMessageBox.warning(self, "Hiba", "Nem sikerült megtanulni a képzettséget")

    def get_learned_skills(self) -> list[dict[str, Any]]:
        """Get learned skills for character save."""
        if not self.selection_manager:
            return []
        return self.selection_manager.get_learned_skills_for_save()

    def validate(self) -> bool:
        """Validate that the step is ready to proceed."""
        # Always valid - player can choose not to spend all KP
        return True
