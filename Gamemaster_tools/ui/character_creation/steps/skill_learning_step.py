"""
Skill Learning Step
Allows players to spend KP on learning new skills during character creation.
Refactored to use renderer pattern and centralized KP logic in manager.
"""

import sqlite3
from collections.abc import Callable
from typing import Any

from PySide6 import QtCore, QtWidgets
from ui.character_creation.services import (
    SkillDatabaseHelper,
    SkillPrerequisiteChecker,
    PrerequisiteInfoHelper,
    SkillSelectionManager,
)
from ui.character_creation.widgets.learning import LearningRow, LearningSkillsTableRenderer
from utils.log.logger import get_logger
from utils.ui.themes import header_label_style, info_label_style
from ui.character_creation.dialogs.add_skill_dialog import AddSkillDialog

logger = get_logger(__name__)


class SkillLearningStepWidget(QtWidgets.QWidget):
    """
    Skill learning interface for spending KP on new skills.
    Delegates rendering to LearningSkillsTableRenderer and KP logic to SkillSelectionManager.
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
        self.prereq_info = PrerequisiteInfoHelper(self.db_helper, self.prereq_checker)
        self.selection_manager: SkillSelectionManager | None = None

        # UI components
        self.kp_info_label: QtWidgets.QLabel | None = None
        self.skills_table: QtWidgets.QTableWidget | None = None
        self.table_renderer: LearningSkillsTableRenderer | None = None
        self.attributes_widget = None

        self._build_ui()

    def _build_ui(self):
        """Build the UI with left panel (attributes) and right panel (skills)."""
        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)

        # Left panel: Read-only attributes display
        from ui.character_creation.widgets.common import AttributesReadOnlyWidget
        
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
        self.skills_table.setColumnCount(4)
        self.skills_table.setHorizontalHeaderLabels([
            "Képzettség", "Érték", "KP költség", "Művelet"
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

        # Initialize table renderer
        self.table_renderer = LearningSkillsTableRenderer(
            self.skills_table,
            can_increase_cb=self._can_increase_skill,
            on_increase_cb=self._on_increase_skill,
            on_decrease_cb=self._on_decrease_skill,
        )

    def refresh(self):
        """Refresh the UI with current character data and initialize selection manager."""
        data = self.get_character_data() or {}
        
        # Refresh attributes display
        if self.attributes_widget:
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
        """Load all skills (mandatory + learned) using the renderer."""
        if not self.table_renderer or not self.selection_manager:
            return

        self.table_renderer.clear()

        # Build current skills map for prerequisite checking
        current_map = self._get_current_map()
        attributes = self._get_attributes()

        # Collect all skills and sort: level-based first, then %-based
        all_rows = []

        # Load mandatory skills
        for skill_id, data in self.selection_manager.mandatory_skills.items():
            info = self.db_helper.get_skill_info(skill_id)
            if not info:
                continue
            name, parameter, skill_type = info
            display_name = f"{name} ({parameter})" if parameter else name
            
            level = int(data.get("level", 0) or 0)
            percent = int(data.get("%", 0) or 0)
            # Use baseline minima for mandatory skills to decide if minus can be enabled
            mandatory_level = int(data.get("base_level", level) or 0)
            mandatory_percent = int(data.get("base_percent", percent) or 0)
            
            # KP spent only in this step (exclude mandatory base)
            kp_spent_here = int(data.get("kp_cost", 0) or 0)
            
            prereq_text, prereq_met = self.prereq_info.get_prerequisite_info(
                skill_id, level, percent, current_map, attributes
            )
            
            row_data = LearningRow(
                skill_id=skill_id,
                display_name=display_name,
                level=level,
                percent=percent,
                kp_cost=kp_spent_here,
                skill_type=skill_type,
                prereq_text=prereq_text,
                prereq_met=prereq_met,
                is_mandatory=True,
                mandatory_level=mandatory_level,
                mandatory_percent=mandatory_percent,
            )
            all_rows.append(row_data)

        # Load learned skills
        for skill_id, data in self.selection_manager.learned_skills.items():
            info = self.db_helper.get_skill_info(skill_id)
            if not info:
                continue
            name, parameter, skill_type = info
            display_name = f"{name} ({parameter})" if parameter else name
            
            level = int(data.get("level", 0) or 0)
            percent = int(data.get("%", 0) or 0)
            kp_cost = int(data.get("kp_cost", 0) or 0)
            
            prereq_text, prereq_met = self.prereq_info.get_prerequisite_info(
                skill_id, level, percent, current_map, attributes
            )
            
            row_data = LearningRow(
                skill_id=skill_id,
                display_name=display_name,
                level=level,
                percent=percent,
                kp_cost=kp_cost,
                skill_type=skill_type,
                prereq_text=prereq_text,
                prereq_met=prereq_met,
                is_mandatory=False,
                mandatory_level=0,
                mandatory_percent=0,
            )
            all_rows.append(row_data)

        # Sort: level-based (type 1) first, then %-based (type 2)
        all_rows.sort(key=lambda r: (r.skill_type, r.display_name))

        # Render sorted rows
        for row_data in all_rows:
            self.table_renderer.add_row(row_data)

    def _can_increase_skill(
        self, skill_id: str, skill_type: int, current_level: int, current_percent: int
    ) -> tuple[bool, str, int]:
        """
        Check if a skill can be increased.
        Returns (can_increase, tooltip_message, next_kp_cost).
        """
        # Determine next level/percent
        if skill_type == 1:  # Level only
            next_level = current_level + 1
            next_percent = 0
        else:  # Percent only (type 2)
            next_level = 0
            next_percent = current_percent + 3

        # Determine step KP cost (per-level for level-based, delta cumulative for percent-based)
        try:
            if skill_type == 1:
                # Per-level cost for the next level
                step_cost_str = self.db_helper.calc_kp_cost(skill_id, next_level, None)
                step_cost = int(step_cost_str) if step_cost_str and step_cost_str != "?" else 0
            else:
                # Cumulative difference for percent-based
                old_cum_str = self.db_helper.calc_kp_cost(skill_id, None, current_percent) if current_percent > 0 else "0"
                new_cum_str = self.db_helper.calc_kp_cost(skill_id, None, next_percent)
                old_cum = int(old_cum_str) if old_cum_str and old_cum_str != "?" else 0
                new_cum = int(new_cum_str) if new_cum_str and new_cum_str != "?" else 0
                step_cost = new_cum - old_cum
        except (ValueError, TypeError):
            return False, "Nem lehet kiszámítani a KP költséget", 0
        
        if step_cost <= 0:
            # Level doesn't exist or no cost
            return False, "Elérted a maximális szintet", 0
        
        # Get current skills map - DON'T modify it with next level
        # The prereq checker needs to see current state to verify if we can reach next level
        current_map = self._get_current_map()
        
        # Check prerequisites for next level using CURRENT skills state
        ok, reasons = self.prereq_checker.check_prerequisites(
            skill_id, next_level, next_percent, current_map, self._get_attributes()
        )
        
        if not ok:
            # Use the reasons returned by the prerequisite checker
            tooltip = "Hiányzó előfeltételek:\n" + "\n".join(reasons) if reasons else "Előfeltételek nem teljesülnek"
            return False, tooltip, 0
        
        # Check if we have enough KP
        if not self.selection_manager:
            return False, "Nincs inicializálva a KP kezelő", 0
        
        breakdown = self.selection_manager.get_kp_breakdown()
        
        # Calculate delta
        old_cost = self.db_helper.calc_kp_cost(skill_id, current_level, current_percent)
        try:
            old_cost = int(old_cost) if old_cost else 0
        except (ValueError, TypeError):
            old_cost = 0
        
        delta = step_cost
        
        if breakdown['remaining'] < delta:
            return False, f"Nincs elég KP (szükséges: {delta}, elérhető: {breakdown['remaining']})", 0
        
        return True, "", step_cost

    def _on_increase_skill(self, skill_id: str):
        """Handle + button click to increase skill level/percent."""
        if not self.selection_manager:
            return
        
        success, msg = self.selection_manager.increase_skill(skill_id)
        if not success:
            QtWidgets.QMessageBox.warning(self, "Hiba", msg)
            return
        
        # Refresh display
        self._update_kp_display()
        self._load_skills_table()

    def _on_decrease_skill(self, skill_id: str):
        """Handle - button click to decrease skill level/percent."""
        if not self.selection_manager:
            return
        
        success, msg = self.selection_manager.decrease_skill(skill_id)
        if not success:
            QtWidgets.QMessageBox.warning(self, "Hiba", msg)
            return
        
        # Refresh display
        self._update_kp_display()
        self._load_skills_table()

    # --- Helpers to reduce duplication ---
    def _get_current_map(self) -> dict[str, dict[str, int]]:
        """Build current skills map for prerequisite checks."""
        current_map: dict[str, dict[str, int]] = {}
        if not self.selection_manager:
            return current_map
        for skill_id in self.selection_manager.get_all_skills():
            if skill_id in self.selection_manager.mandatory_skills:
                data = self.selection_manager.mandatory_skills[skill_id]
            else:
                data = self.selection_manager.learned_skills[skill_id]
            current_map[skill_id] = {
                "level": int(data.get("level", 0) or 0),
                "%": int(data.get("%", 0) or 0),
            }
        return current_map

    def _get_attributes(self) -> dict:
        data = self.get_character_data() or {}
        return data.get("Tulajdonságok", {})

    def _show_add_skill_dialog(self):
        """Show dialog to select and add a new skill to learn (refactored component)."""
        if not self.selection_manager:
            return

        dialog = AddSkillDialog(
            parent=self,
            db_path_getter=self.db_helper.get_db_path,
            prereq_checker=self.prereq_checker,
            get_current_map=self._get_current_map,
            get_attributes=self._get_attributes,
            get_current_skill_ids=lambda: self.selection_manager.get_all_skills(),
            kp_cost_getter=self.db_helper.calc_kp_cost,
        )
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            selected = dialog.get_selected()
            if selected:
                skill_id, skill_type = selected
                self._add_new_skill(skill_id, skill_type)
    
    def _add_new_skill(self, skill_id: str, skill_type: int):
        """Add a new skill at level 1 or 3%."""
        if not self.selection_manager:
            return
        
        # Determine initial level/percent
        level = 1 if skill_type == 1 else 0
        percent = 3 if skill_type == 2 else 0
        
        # Calculate KP cost
        kp_cost = self.db_helper.calc_kp_cost(skill_id, level, percent)
        try:
            kp_cost = int(kp_cost) if kp_cost else 0
        except (ValueError, TypeError):
            QtWidgets.QMessageBox.warning(self, "Hiba", "Nem lehet kiszámítani a KP költséget")
            return
        
        # Check if can learn
        current_skills = self.selection_manager.get_all_skills()
        can_learn, reason, _ = self.selection_manager.can_learn_skill(
            skill_id, level, percent, current_skills, self._get_attributes()
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
        """Get learned skills for character save (includes increased mandatory skills)."""
        if not self.selection_manager:
            return []
        
        skills = []
        # Include learned skills
        for skill_data in self.selection_manager.get_learned_skills_for_save():
            skills.append(skill_data)
        
        # Also include mandatory skills that were increased (have kp_cost > 0)
        for skill_id, data in self.selection_manager.mandatory_skills.items():
            kp_cost = data.get("kp_cost", 0)
            if kp_cost > 0:
                # This mandatory skill was increased, include it in learned skills
                info = self.db_helper.get_skill_info(skill_id)
                if info:
                    name, parameter, _ = info
                    display = f"{name} ({parameter})" if parameter else name
                    skills.append({
                        "id": skill_id,
                        "Képzettség": display,
                        "Szint": data.get("level", 0),
                        "%": data.get("%", 0),
                        "KP": kp_cost,
                        "Forrás": "Növelt (Kaszt)",
                    })
        
        return skills

    def validate(self) -> bool:
        """Validate that the step is ready to proceed."""
        # Always valid - player can choose not to spend all KP
        return True
