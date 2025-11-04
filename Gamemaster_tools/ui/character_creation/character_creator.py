import os
import sys
from typing import Any

from PySide6 import QtWidgets

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from core.character_model import calculate_combat_stats, calculate_skill_points
from ui.character_creation.steps.skills_step import SkillsStepWidget
from utils.data.character_storage import save_character
from utils.data.class_db_manager import ClassDBManager
from utils.placeholder_manager import PlaceholderManager

# Base directory for data paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


"""
This dialog orchestrates the character creation wizard. Step UIs are modularized
into dedicated widgets under ui/character_creation/steps.
"""


class CharacterWizardQt(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Karakteralkotás varázsló")
        # Larger window to show class and specialization side-by-side
        self.resize(1200, 700)
        self.class_db = ClassDBManager()
        self.placeholder_mgr = PlaceholderManager()
        self.data: dict[str, Any] = {}
        self.step = 0
        self.specializations = ["Nincs"]
        self.spec_data: dict[str, Any] = {}
        self.selected_class_id: str | None = None
        self.placeholder_choices: dict[Any, str] = {}  # Store user's placeholder resolutions

        # Step widgets (initialized lazily)
        self.basic_spec_step: Any | None = None
        self.skills_step: Any | None = None
        self.equipment_step: Any | None = None
        self.summary_step: Any | None = None

        self.init_ui()
        self.show_step()

    def init_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        self.step_widget = QtWidgets.QWidget(self)
        self.step_layout = QtWidgets.QVBoxLayout(self.step_widget)
        main_layout.addWidget(self.step_widget)
        self.btn_frame = QtWidgets.QHBoxLayout()
        main_layout.addLayout(self.btn_frame)
        self.back_btn = QtWidgets.QPushButton("Vissza")
        self.next_btn = QtWidgets.QPushButton("Következő")
        self.back_btn.clicked.connect(self.prev_step)
        self.next_btn.clicked.connect(self.next_step)
        self.btn_frame.addWidget(self.back_btn)
        self.btn_frame.addWidget(self.next_btn)

    def show_step(self):
        for i in reversed(range(self.step_layout.count())):
            widget = self.step_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        if self.step == 0:
            # Merged step: basic data + specialization (modular)
            self.show_basic_spec_modular()
            self.back_btn.setEnabled(False)
            self.next_btn.setText("Következő")
        elif self.step == 1:
            self.show_skills_modular()
            self.back_btn.setEnabled(True)
            self.next_btn.setText("Következő")
        elif self.step == 2:
            self.show_equipment()
            self.back_btn.setEnabled(True)
            self.next_btn.setText("Következő")
        elif self.step == 3:
            self.show_summary()
            self.back_btn.setEnabled(True)
            self.next_btn.setText("Mentés")

    def show_basic_spec_modular(self):
        """Show the Basic+Spec step via modular widget."""
        from ui.character_creation.steps.basic_spec_step import BasicSpecStepWidget

        # Reuse existing widget instance if present to preserve user input
        if not hasattr(self, "basic_spec_step") or self.basic_spec_step is None:
            self.basic_spec_step = BasicSpecStepWidget(BASE_DIR, self.class_db)
            # Prefill if we already have data
            if getattr(self, "data", None):
                try:
                    self.basic_spec_step.set_data(self.data)
                except Exception:
                    pass
        self.step_layout.addWidget(self.basic_spec_step)

    # Basic+Spec step moved to BasicSpecStepWidget

    def show_skills_modular(self):
        """Show skills step via modular widget."""

        def _get_class_id():
            return self.selected_class_id

        def _get_spec_data():
            return self.spec_data

        def _get_data():
            return self.data

        # Reuse existing instance to preserve inline selections
        if not hasattr(self, "skills_step") or self.skills_step is None:
            self.skills_step = SkillsStepWidget(
                BASE_DIR,
                self.placeholder_mgr,
                _get_class_id,
                _get_spec_data,
                _get_data,
            )
            # if we previously had choices, pass them in
            if hasattr(self, "placeholder_choices") and self.placeholder_choices:
                self.skills_step.placeholder_manager.placeholder_choices = dict(
                    self.placeholder_choices
                )
        self.skills_step.refresh()
        self.step_layout.addWidget(self.skills_step)

    # Skills logic moved into SkillsStepWidget

    # Legacy inline skills/placeholder handlers removed; handled inside SkillsStepWidget

    def show_equipment(self):
        """Show equipment step via modular widget (placeholder for now)."""
        from ui.character_creation.steps.equipment_step import EquipmentStepWidget

        def _get_class_id():
            return self.selected_class_id

        def _get_spec_data():
            return self.spec_data

        def _get_data():
            return self.data

        if not hasattr(self, "equipment_step") or self.equipment_step is None:
            self.equipment_step = EquipmentStepWidget(self)
            self.equipment_step.set_context(
                get_class_id=_get_class_id,
                get_spec_data=_get_spec_data,
                get_data=_get_data,
            )
        self.step_layout.addWidget(self.equipment_step)

    def show_summary(self):
        """Show summary step via modular widget."""
        from ui.character_creation.steps.summary_step import SummaryStepWidget

        def _get_data():
            return self.data

        if not hasattr(self, "summary_step") or self.summary_step is None:
            self.summary_step = SummaryStepWidget(_get_data, self)
        self.summary_step.refresh()
        self.step_layout.addWidget(self.summary_step)

    def next_step(self):
        if self.step == 0:
            # Validate via modular widget and capture data
            if (
                not hasattr(self, "basic_spec_step")
                or self.basic_spec_step is None
                or not self.basic_spec_step.validate_basic_data()
            ):
                return
            self.data = self.basic_spec_step.get_data()
            # Keep selected class/spec info for later steps
            self.selected_class_id = self.basic_spec_step.get_selected_class_id()
            self.spec_data = self.basic_spec_step.get_spec_data()
            # Calculate KP from class info (needed for skills step display)
            try:
                self.data["Képzettségpontok"] = calculate_skill_points(self.data["Kaszt"])
            except Exception as e:
                print(f"Error calculating KP: {e}")
                self.data["Képzettségpontok"] = {"Alap": 0, "Szintenként": 0}
            # If skills step already exists (user is returning to it), refresh attributes explicitly now
            if hasattr(self, "skills_step") and self.skills_step is not None:
                try:
                    class_name = self.data.get("Kaszt")
                    race = self.data.get("Faj", "Ember")
                    age = int(self.data.get("Kor", 20))
                    if (
                        getattr(self.skills_step, "attributes_widget", None) is not None
                        and class_name
                        and race
                    ):
                        self.skills_step.attributes_widget.refresh_from_basic_selection(
                            class_name, race, age
                        )
                except Exception:
                    pass
        elif self.step == 1:
            # Persist skills placeholder choices from widget back to wizard state
            if hasattr(self, "skills_step") and self.skills_step is not None:
                try:
                    self.placeholder_choices = dict(
                        self.skills_step.placeholder_manager.placeholder_choices
                    )
                    # Also persist concrete selected skills into wizard data
                    try:
                        self.data["Képzettségek"] = self.skills_step.get_selected_skills()
                    except Exception:
                        pass
                except Exception:
                    pass
            # Calculate KP and combat values from user's selected attributes
            # Attributes are in self.data["Tulajdonságok"] from the attributes widget
            if "Tulajdonságok" in self.data:
                # Build a temporary character dict with user's attributes to calculate combat stats
                temp_char = {
                    "Név": self.data["Név"],
                    "Nem": self.data["Nem"],
                    "Kor": self.data["Kor"],
                    "Faj": self.data["Faj"],
                    "Kaszt": self.data["Kaszt"],
                    "Tulajdonságok": self.data["Tulajdonságok"],
                }
                temp_char = calculate_combat_stats(temp_char)
                # Store KP and combat values
                self.data["Képzettségpontok"] = temp_char.get("Képzettségpontok", {})
                self.data["Harci értékek"] = temp_char.get("Harci értékek", {})
        elif self.step == 2:
            # Optionally validate and collect equipment data (placeholder)
            if (
                hasattr(self, "equipment_step")
                and self.equipment_step is not None
                and not self.equipment_step.validate()
            ):
                return
            if hasattr(self, "equipment_step") and self.equipment_step is not None:
                equip_data = self.equipment_step.get_data() or {}
                # Merge equipment data into the main data dict without overwriting existing keys unexpectedly
                for k, v in equip_data.items():
                    if k not in self.data:
                        self.data[k] = v
                    else:
                        # If conflict and both dicts, merge shallowly
                        if isinstance(self.data[k], dict) and isinstance(v, dict):
                            self.data[k].update(v)
                        else:
                            self.data[k] = v

        self.step += 1
        if self.step > 3:
            self.finish()
        else:
            self.show_step()

    def prev_step(self):
        if self.step > 0:
            self.step -= 1
            self.show_step()

    def finish(self):
        # Build final character payload: only base info, attributes, skills, equipment
        final_data = None
        if hasattr(self, "summary_step") and self.summary_step is not None:
            try:
                final_data = self.summary_step.get_result()
            except Exception:
                final_data = None
        if not final_data:
            # Fallback: filter self.data directly
            src = dict(self.data or {})
            allowed = {
                "Név",
                "Nem",
                "Kor",
                "Faj",
                "Kaszt",
                "Specializáció",
                "Tulajdonságok",
                "Képzettségek",
                "Felszerelés",
                "Képzettségpontok",
                "Harci értékek",
            }
            final_data = {k: v for k, v in src.items() if k in allowed and not k.startswith("_")}
            final_data.setdefault("Képzettségek", [])
            final_data.setdefault("Felszerelés", [])

        char = final_data

        # Save character to JSON file
        filename = f"{self.data['Név'].replace(' ', '_')}.json"
        save_character(char, filename)

        # Itt bővíthető a char a specializációval, képzettségekkel, felszereléssel
        self.accept()
        # Optionally show summary or pass char to another window
        QtWidgets.QMessageBox.information(
            self,
            "Karakter létrehozva",
            f"Sikeres karaktergenerálás!\nMentve: characters/{filename}",
        )


if __name__ == "__main__":
    import sys

    from utils.ui.dark_mode import apply_dark_mode

    app = QtWidgets.QApplication(sys.argv)
    apply_dark_mode(app)

    wizard = CharacterWizardQt()
    wizard.exec()
