"""
Skill Editor Actions
Handles all action operations (new, duplicate, delete, save, load, etc.)
"""

import copy
import os
import subprocess
import sys

from PySide6.QtWidgets import QMessageBox
from utils.ui.validation import ValidationError, validate_skill

from .skill_editor_constants import (
    ACQ_DIFF_MAP,
    ACQ_DIFF_MAP_REV,
    ACQ_METHOD_MAP,
    ACQ_METHOD_MAP_REV,
    CATEGORIES,
    TYPE_MAP,
    TYPE_MAP_REV,
)


class SkillEditorActions:
    """Handles all skill editor actions"""

    def __init__(self, parent_editor):
        """
        Initialize actions handler

        Args:
            parent_editor: Reference to parent SkillEditorQt instance
        """
        self.parent = parent_editor

    def new_skill(self):
        """Create a new skill"""
        new_skill = {
            "name": "Új képzettség",
            "id": "new_skill",
            "parameter": "",
            "main_category": list(CATEGORIES.keys())[0],
            "sub_category": CATEGORIES[list(CATEGORIES.keys())[0]][0],
            "acquisition_method": 3,
            "acquisition_difficulty": 3,
            "skill_type": 1,
            "kp_per_3_percent": 0,
            "kp_costs": {str(i): 0 for i in range(1, 7)},
            "level_descriptions": {},
            "description_file": "",
            "prerequisites": {},
        }

        self.parent.all_skills.append(new_skill)
        self.parent.skill_list_panel.populate(self.parent.all_skills)
        self.parent.skill_list_panel.set_current_row(len(self.parent.all_skills) - 1)

    def duplicate_skill(self):
        """Duplicate the current skill"""
        if not self.parent.current_skill:
            QMessageBox.warning(self.parent, "Figyelem", "Nincs kiválasztott képzettség!")
            return

        new_skill = copy.deepcopy(self.parent.current_skill)
        new_skill["name"] = new_skill["name"] + " (másolat)"
        new_skill["id"] = new_skill["id"] + "_copy"

        self.parent.all_skills.append(new_skill)
        self.parent.skill_list_panel.populate(self.parent.all_skills)
        self.parent.skill_list_panel.set_current_row(len(self.parent.all_skills) - 1)

    def delete_skill(self):
        """Delete the current skill"""
        if not self.parent.current_skill:
            QMessageBox.warning(self.parent, "Figyelem", "Nincs kiválasztott képzettség!")
            return

        reply = QMessageBox.question(
            self.parent,
            "Megerősítés",
            f"Biztosan törlöd ezt a képzettséget?\n{self.parent.current_skill.get('name', '')}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            index = self.parent.skill_list_panel.get_current_row()
            self.parent.all_skills.pop(index)
            self.parent.skill_list_panel.populate(self.parent.all_skills)
            if self.parent.all_skills:
                self.parent.skill_list_panel.set_current_row(
                    min(index, len(self.parent.all_skills) - 1)
                )

    def save_skill(self):
        """Save the current skill"""
        if not self.parent.current_skill:
            QMessageBox.warning(self.parent, "Figyelem", "Nincs kiválasztott képzettség!")
            return

        # Collect data from UI
        tabs = self.parent.tabs
        self.parent.current_skill["name"] = tabs.name_edit.text()
        self.parent.current_skill["id"] = tabs.id_edit.text()
        self.parent.current_skill["parameter"] = tabs.param_edit.text()
        self.parent.current_skill["main_category"] = tabs.main_cat_combo.currentText()
        self.parent.current_skill["sub_category"] = tabs.sub_cat_combo.currentText()

        # Acquisition
        self.parent.current_skill["acquisition_method"] = ACQ_METHOD_MAP_REV.get(
            tabs.acq_method_combo.currentText(), 3
        )
        self.parent.current_skill["acquisition_difficulty"] = ACQ_DIFF_MAP_REV.get(
            tabs.acq_diff_combo.currentText(), 3
        )

        # Type
        # Persist DB-compatible key
        self.parent.current_skill["skill_type"] = TYPE_MAP_REV.get(tabs.type_combo.currentText(), 1)

        # KP per 3 percent (only for percent-based skills)
        if self.parent.current_skill["skill_type"] == 2:
            self.parent.current_skill["kp_per_3_percent"] = tabs.kp_per_3_spin.value()
            # For percent-based skills, ensure kp_costs is empty dict for cleanliness
            self.parent.current_skill["kp_costs"] = {}
        else:
            # Ensure percent field is cleared for level-based skills
            self.parent.current_skill["kp_per_3_percent"] = 0

        # Description file - auto-generate from ID if empty
        desc_file = tabs.desc_file_edit.text().strip()
        if not desc_file:
            skill_id = self.parent.current_skill.get("id", "") or tabs.id_edit.text().strip()
            if skill_id:
                desc_file = f"{skill_id}.md"
                tabs.desc_file_edit.setText(desc_file)
        self.parent.current_skill["description_file"] = desc_file
        # Sync description text from editor so DB manager writes the same content
        self.parent.current_skill["description"] = tabs.desc_text_editor.toPlainText()
        # We no longer use per-level descriptions; ensure it's empty
        self.parent.current_skill["level_descriptions"] = {}

        # Levels - save with string keys to match database format (only for level-based)
        if self.parent.current_skill["skill_type"] == 1:
            kp_costs = {str(i + 1): tabs.kp_cost_spins[i].value() for i in range(6)}
            self.parent.current_skill["kp_costs"] = kp_costs

        # Prerequisites – sync from inline editor widgets into current_prerequisites first
        if hasattr(self.parent.tabs, "prereq_widgets") and self.parent.tabs.prereq_widgets:
            new_prereqs = {}
            for i in range(6):
                level = i + 1
                level_key = str(level)
                if i < len(self.parent.tabs.prereq_widgets):
                    w = self.parent.tabs.prereq_widgets[i]
                    if hasattr(w, "get_prerequisites"):
                        new_prereqs[level_key] = w.get_prerequisites()
                    else:
                        # Fallback: read directly from list widgets
                        stats = []
                        skills = []
                        for j in range(w.stat_list.count()):
                            stats.append(w.stat_list.item(j).text())
                        for j in range(w.skill_list.count()):
                            skills.append(w.skill_list.item(j).text())
                        new_prereqs[level_key] = {"képesség": stats, "képzettség": skills}
            self.parent.current_prerequisites = new_prereqs

        # Prerequisites (use synced current_prerequisites)
        self.parent.current_skill["prerequisites"] = self.parent.current_prerequisites
        # Refresh quick summaries in the UI so the top overview reflects latest edits
        self.parent.update_prereq_summary()

        # Validate before save
        try:
            validate_skill(self.parent.current_skill)
        except ValidationError as ve:
            QMessageBox.critical(self.parent, "Hiba", f"Érvénytelen adatok:\n{ve}")
            return

        # Save to database
        try:
            self.parent.skill_manager.save(self.parent.all_skills)
            self.parent.skill_list_panel.populate(self.parent.all_skills)
            QMessageBox.information(self.parent, "Siker", "Képzettség mentve!")
        except (IOError, OSError, TypeError) as e:
            QMessageBox.critical(self.parent, "Hiba", f"Mentési hiba:\n{str(e)}")

    def load_skill_to_ui(self):
        """Load current skill data to UI fields"""
        if not self.parent.current_skill:
            return

        skill = self.parent.current_skill
        tabs = self.parent.tabs

        # Basic info
        tabs.name_edit.setText(skill.get("name", ""))
        tabs.id_edit.setText(skill.get("id", ""))
        tabs.param_edit.setText(skill.get("parameter", ""))

        # Categories
        main_cat = skill.get("main_category", list(CATEGORIES.keys())[0])
        tabs.main_cat_combo.setCurrentText(main_cat)

        sub_cat = skill.get("sub_category", "")
        if sub_cat:
            tabs.sub_cat_combo.setCurrentText(sub_cat)

        # Acquisition
        acq_method = skill.get("acquisition_method", 1)
        tabs.acq_method_combo.setCurrentText(ACQ_METHOD_MAP.get(acq_method, "Tanulás"))

        acq_diff = skill.get("acquisition_difficulty", 3)
        tabs.acq_diff_combo.setCurrentText(ACQ_DIFF_MAP.get(acq_diff, "Közepes"))

        # Type (DB uses 'skill_type')
        skill_type = skill.get("skill_type", skill.get("type", 1))
        tabs.type_combo.setCurrentText(TYPE_MAP.get(skill_type, "szint"))
        # Update field enables based on type
        self.parent.update_type_dependent_fields()

        # KP/3 for percent-based skills
        tabs.kp_per_3_spin.setValue(skill.get("kp_per_3_percent", 0))

        # Description file
        tabs.desc_file_edit.setText(skill.get("description_file", ""))
        # Load description content into editor (if available)
        self.load_description_file(silent=True)

        # Levels and KP costs
        kp_costs = skill.get("kp_costs", {})

        # Handle both dict and list formats
        if isinstance(kp_costs, dict):
            kp_list = [kp_costs.get(str(i + 1), 0) for i in range(6)]
        else:
            kp_list = kp_costs if isinstance(kp_costs, list) else []

        for i in range(6):
            # KP cost
            kp = kp_list[i] if i < len(kp_list) else 0
            if isinstance(kp, (int, float)):
                tabs.kp_cost_spins[i].setValue(int(kp))
            else:
                tabs.kp_cost_spins[i].setValue(0)

        # Prerequisites - load and update summary labels
        self.parent.current_prerequisites = skill.get("prerequisites", {})
        self.update_prereq_summary()

    def update_prereq_summary(self):
        """Update prerequisite summary labels for all levels, mapping id (param) to name (param) for display."""
        tabs = self.parent.tabs
        if not hasattr(self.parent, "current_prerequisites"):
            self.parent.current_prerequisites = {}

        # Build id(param) -> name(param) mapping
        id_to_name = {}
        for s in self.parent.all_skills:
            skill_id = s.get("id", "")
            name = s.get("name", "")
            param = s.get("parameter", "")
            id_with_param = f"{skill_id} ({param})" if param else skill_id
            name_with_param = f"{name} ({param})" if param else name
            id_to_name[id_with_param] = name_with_param

        # Update summary labels and load data into inline editors for each level (1-6)
        for i in range(6):
            level = i + 1
            level_key = str(level)
            level_prereqs = self.parent.current_prerequisites.get(level_key, {})

            # Build summary text for the label
            summary = ""
            if isinstance(level_prereqs, dict):
                stat_list = level_prereqs.get("képesség", [])
                skill_list = level_prereqs.get("képzettség", [])

                if stat_list:
                    summary += ", ".join(stat_list)
                if skill_list:
                    if stat_list:
                        summary += "\n"
                    # Map id(param) to name(param) for display
                    display_skills = []
                    for skill_req in skill_list:
                        # skill_req is like "id (param) N. szint" or "name (param) N. szint"
                        # Extract the id/name part (everything before the last "N. szint" pattern)
                        import re
                        match = re.match(r'^(.+?)\s+(\d+)\.\s+szint$', skill_req)
                        if match:
                            id_or_name_part = match.group(1).strip()
                            level_num = match.group(2)
                            # Try to map id to name
                            name_part = id_to_name.get(id_or_name_part, id_or_name_part)
                            display_skills.append(f"{name_part} {level_num}. szint")
                        else:
                            # Fallback: use as-is
                            display_skills.append(skill_req)
                    summary += "\n".join(display_skills)

            # Update the summary label
            if i < len(tabs.prereq_labels):
                tabs.prereq_labels[i].setText(summary.strip())

            # Also load into the editor widgets
            if i < len(tabs.prereq_widgets):
                widget = tabs.prereq_widgets[i]

                # Clear existing items
                widget.stat_list.clear()
                widget.skill_list.clear()

                # Load stat and skill prerequisites
                if isinstance(level_prereqs, dict):
                    stat_list = level_prereqs.get("képesség", [])
                    skill_list = level_prereqs.get("képzettség", [])

                    for stat_req in stat_list:
                        widget.stat_list.addItem(stat_req)

                    for skill_req in skill_list:
                        widget.skill_list.addItem(skill_req)

    def open_description_file(self):
        """Open the description markdown file in the default editor"""
        if not self.parent.current_skill:
            QMessageBox.warning(self.parent, "Figyelem", "Nincs kiválasztott képzettség!")
            return

        desc_file = self.parent.current_skill.get("description_file", "")
        if not desc_file:
            QMessageBox.information(
                self.parent, "Info", "Nincs leírás fájl megadva ehhez a képzettséghez."
            )
            return

        # Build full path - descriptions are in Gamemaster_tools/data/skills/descriptions
        # __file__ is at Gamemaster_tools/ui/skills/skill_editor_actions.py
        # Go up 2 levels: ui/skills -> ui -> Gamemaster_tools
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        full_path = os.path.join(base_path, "data", "skills", "descriptions", desc_file)

        if os.path.exists(full_path):
            # Open with default editor
            if sys.platform.startswith("win"):
                os.startfile(full_path)
            elif sys.platform == "darwin":
                subprocess.call(["open", full_path])
            else:
                subprocess.call(["xdg-open", full_path])
        else:
            QMessageBox.warning(self.parent, "Hiba", f"A leírás fájl nem található:\n{full_path}")

    def description_full_path(self):
        """Return absolute path to the current skill's description file under data/skills/descriptions"""
        if not self.parent.current_skill:
            return None
        tabs = self.parent.tabs
        desc_file = (
            self.parent.current_skill.get("description_file", "")
            or tabs.desc_file_edit.text().strip()
        )
        # Auto-generate filename from skill ID if not specified
        if not desc_file:
            skill_id = self.parent.current_skill.get("id", "")
            if skill_id:
                desc_file = f"{skill_id}.md"
            else:
                return None
        # __file__ is at Gamemaster_tools/ui/skills/skill_editor_actions.py
        # Go up 2 levels: ui/skills -> ui -> Gamemaster_tools
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        return os.path.join(base_path, "data", "skills", "descriptions", desc_file)

    def load_description_file(self, silent=False):
        """Load description .md content into the editor area"""
        path = self.description_full_path()
        tabs = self.parent.tabs
        if not path:
            tabs.desc_text_editor.clear()
            if not silent:
                QMessageBox.information(
                    self.parent,
                    "Info",
                    "Nincs leírás fájlnév megadva. Add meg az Alapadatok fülön.",
                )
            return
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    tabs.desc_text_editor.setPlainText(f.read())
            except (IOError, OSError, UnicodeDecodeError) as e:
                tabs.desc_text_editor.clear()
                if not silent:
                    QMessageBox.critical(
                        self.parent, "Hiba", f"Nem sikerült beolvasni a leírást:\n{e}"
                    )
        else:
            tabs.desc_text_editor.clear()
            if not silent:
                QMessageBox.information(
                    self.parent, "Info", "A leírás fájl nem létezik. Mentéskor létrehozzuk."
                )

    def save_description_file(self):
        """Save the editor content to the description .md file (create if missing)"""
        if not self.parent.current_skill:
            QMessageBox.warning(self.parent, "Figyelem", "Nincs kiválasztott képzettség!")
            return

        tabs = self.parent.tabs
        # Auto-generate filename from skill ID if not specified
        desc_file = tabs.desc_file_edit.text().strip()
        if not desc_file:
            skill_id = self.parent.current_skill.get("id", "")
            if not skill_id:
                QMessageBox.warning(
                    self.parent,
                    "Figyelem",
                    "Nincs skill ID megadva. Mentsd először a képzettséget!",
                )
                return
            desc_file = f"{skill_id}.md"
            # Update the UI field and current skill
            tabs.desc_file_edit.setText(desc_file)
        # Update current skill's field from UI
        self.parent.current_skill["description_file"] = desc_file
        # Resolve path and ensure directory
        path = self.description_full_path()
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(tabs.desc_text_editor.toPlainText())
            QMessageBox.information(self.parent, "Siker", "Leírás elmentve a .md fájlba.")
        except (IOError, OSError) as e:
            QMessageBox.critical(self.parent, "Hiba", f"Nem sikerült menteni a leírást:\n{e}")
