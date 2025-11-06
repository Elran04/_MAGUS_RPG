import sqlite3
from collections.abc import Callable
from typing import Any

from config.paths import DATA_DIR
from engine.race_manager import RaceManager
from PySide6 import QtCore, QtWidgets
from utils.log.logger import get_logger
from utils.ui.themes import (
    header_label_style,
    info_label_style,
    warning_label_style,
)

from ui.character_creation.services import (
    PlaceholderSkillManager,
    SkillDatabaseService,
    SkillPrerequisiteChecker,
)
from ui.character_creation.widgets.skills import SkillsTableRenderer

logger = get_logger(__name__)

# Initialize race manager for accessing racial skills
_race_manager = RaceManager(DATA_DIR)
_race_manager.load_all()


class SkillsStepWidget(QtWidgets.QWidget):
    """Skills step widget displaying class/spec skills with inline placeholder resolution."""

    def __init__(
        self,
        base_dir: str,
        placeholder_mgr: Any,
        get_selected_class_id: Callable[[], str | None],
        get_spec_data: Callable[[], dict[str, Any]],
        get_character_data: Callable[[], dict[str, Any]],
    ) -> None:
        super().__init__()
        self.BASE_DIR = base_dir
        self.get_selected_class_id = get_selected_class_id
        self.get_spec_data = get_spec_data
        self.get_character_data = get_character_data

        # Initialize service classes
        self.skill_db_service = SkillDatabaseService(base_dir)
        self.prereq_checker = SkillPrerequisiteChecker(self.skill_db_service, placeholder_mgr)
        self.placeholder_manager = PlaceholderSkillManager(placeholder_mgr, self.prereq_checker)

        self._placeholder_row_counters: dict[tuple[Any, ...], int] = {}
        self._placeholder_combos: dict[tuple[Any, ...], QtWidgets.QComboBox] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)

        # Left panel: Attributes display
        from utils.data.class_db_manager import ClassDBManager

        from ui.character_creation.widgets.common import AttributesDisplayWidget

        self.attributes_widget = AttributesDisplayWidget(
            self.get_character_data,
            lambda key, value: (self.get_character_data() or {}).update({key: value}),
            ClassDBManager,
        )
        self.attributes_widget.attributes_changed.connect(self._on_attributes_changed)
        splitter.addWidget(self.attributes_widget)

        # Right panel: Skills table and KP info
        right_panel = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(right_panel)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header with KP
        self.kp_info_label = QtWidgets.QLabel("")
        self.kp_info_label.setStyleSheet(header_label_style())
        layout.addWidget(self.kp_info_label)

        # Table
        layout.addWidget(QtWidgets.QLabel("Kaszt/Specializáció képzettségei:"))
        self.skills_table = QtWidgets.QTableWidget()
        self.skills_table.setColumnCount(6)
        self.skills_table.setHorizontalHeaderLabels(
            ["Képzettség", "Szint", "%", "KP költség", "Forrás", "Előfeltételek"]
        )
        self.skills_table.horizontalHeader().setStretchLastSection(False)
        self.skills_table.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        self.skills_table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.skills_table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.skills_table.doubleClicked.connect(self._on_row_double_click)
        layout.addWidget(self.skills_table)

        # Renderer for table rows and placeholder logic
        self.table_renderer = SkillsTableRenderer(
            table=self.skills_table,
            skill_db_service=self.skill_db_service,
            placeholder_manager=self.placeholder_manager,
            prereq_checker=self.prereq_checker,
            build_current_map_cb=self._build_current_skills_map,
            attributes_getter=lambda: (self.get_character_data() or {}).get("Tulajdonságok", {}),
        )

        # Empty note
        self.empty_msg = QtWidgets.QLabel("")
        self.empty_msg.setWordWrap(True)
        self.empty_msg.setStyleSheet(warning_label_style())
        layout.addWidget(self.empty_msg)

        # Footer note
        note = QtWidgets.QLabel(
            "<i>Megjegyzés: A képzettségek szerkesztése a karakter mentése után a külön karakterszerkesztőben lehetséges.</i>"
        )
        note.setWordWrap(True)
        note.setStyleSheet(info_label_style())
        layout.addWidget(note)

        splitter.addWidget(right_panel)
        splitter.setSizes([200, 1000])  # ~20% left, ~80% right
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)

    def validate(self) -> bool:
        """
        Validate skill selection before allowing progression.
        Returns True if valid, False otherwise (with user warning).

        Checks:
        1. All placeholder skills are resolved (chosen from combo)
        2. All mandatory skill prerequisites are fulfilled
        """
        # Check for unresolved placeholders
        unresolved_placeholders = []
        for row_idx in range(self.skills_table.rowCount()):
            name_widget = self.skills_table.cellWidget(row_idx, 0)
            if isinstance(name_widget, QtWidgets.QComboBox):
                chosen = name_widget.currentData()
                if chosen is None:  # No selection made
                    # Get the placeholder name from line edit placeholder text
                    line_edit = name_widget.lineEdit()
                    placeholder_text = line_edit.placeholderText() if line_edit else "Ismeretlen"
                    unresolved_placeholders.append(
                        placeholder_text.split(" — ")[0]
                        if " — " in placeholder_text
                        else placeholder_text
                    )

        if unresolved_placeholders:
            QtWidgets.QMessageBox.warning(
                self,
                "Hiányos képzettség választás",
                "Válassza ki a következő helyettesítő képzettség(ek)et:\n\n• "
                + "\n• ".join(unresolved_placeholders),
            )
            return False

        # Check for unmet prerequisites
        unmet_prereqs: list[str] = []
        current_map = self._build_current_skills_map()
        attributes = (self.get_character_data() or {}).get("Tulajdonságok", {})

        for row_idx in range(self.skills_table.rowCount()):
            # Only check fixed skills (placeholders are validated when resolved)
            name_widget = self.skills_table.cellWidget(row_idx, 0)
            if name_widget is not None:
                continue  # Skip placeholder rows

            name_item = self.skills_table.item(row_idx, 0)
            if not name_item:
                continue

            display = name_item.text()
            skill_id = self.skill_db_service.get_skill_by_display(display)
            if not skill_id:
                continue

            # Get level and percent
            lvl_item = self.skills_table.item(row_idx, 1)
            pct_item = self.skills_table.item(row_idx, 2)
            req_level = int(lvl_item.text()) if lvl_item and lvl_item.text().isdigit() else 0
            req_percent = int(pct_item.text()) if pct_item and pct_item.text().isdigit() else 0

            # Check prerequisites
            ok, reasons = self.prereq_checker.check_prerequisites(
                skill_id, req_level, req_percent, current_map, attributes
            )
            if not ok:
                unmet_prereqs.append(f"{display}: {', '.join(reasons)}")

        if unmet_prereqs:
            # Create custom dialog with Continue/Back buttons
            msg_box = QtWidgets.QMessageBox(self)
            msg_box.setIcon(QtWidgets.QMessageBox.Icon.Warning)
            msg_box.setWindowTitle("Előfeltételek nem teljesülnek")
            msg_box.setText(
                "Nem teljesül minden előfeltétel — bizonyos képzettségek nem lesznek elérhetők.\n\n"
                + "\n".join(unmet_prereqs[:5])  # Show max 5 to avoid giant dialog
                + ("\n\n... és további hiányosságok" if len(unmet_prereqs) > 5 else "")
                + "\n\nHa folytatja, ezek a képzettségek nem kerülnek hozzáadásra a karakterhez."
            )

            # Add custom buttons
            msg_box.addButton("Folytatás", QtWidgets.QMessageBox.ButtonRole.AcceptRole)
            back_btn = msg_box.addButton("Vissza", QtWidgets.QMessageBox.ButtonRole.RejectRole)
            msg_box.setDefaultButton(back_btn)

            msg_box.exec()

            # Check which button was clicked
            if msg_box.clickedButton() == back_btn:
                return False  # Stay on current step
            # else: continue_btn was clicked, return True to proceed (invalid skills will be filtered out)

        return True

    def get_selected_skills(self) -> list[dict[str, Any]]:
        """Export current selected skills (fixed + placeholder resolutions) as a list of dicts.
        Each entry contains: {"id": skill_id, "Képzettség": name( (param)), "Szint": int, "%": int, "Forrás": source}.
        Only includes skills with fulfilled prerequisites.
        """
        skills: list[dict[str, Any]] = []

        # Build a map from the table to get source information
        skill_sources: dict[str, str] = {}
        try:
            for row_idx in range(self.skills_table.rowCount()):
                # Get skill ID
                name_widget = self.skills_table.cellWidget(row_idx, 0)
                if name_widget is None:
                    name_item = self.skills_table.item(row_idx, 0)
                    if name_item:
                        display = name_item.text()
                        sid = self.skill_db_service.get_skill_by_display(display)
                        if sid:
                            source_item = self.skills_table.item(row_idx, 4)
                            if source_item:
                                skill_sources[sid] = source_item.text()
                else:
                    # Placeholder - get chosen skill
                    if isinstance(name_widget, QtWidgets.QComboBox):
                        chosen = name_widget.currentData()
                        if chosen:
                            source_item = self.skills_table.item(row_idx, 4)
                            if source_item:
                                skill_sources[chosen] = source_item.text()
        except Exception as e:
            logger.error(f"Error building skill sources map: {e}", exc_info=True)

        current_map = self._build_current_skills_map()
        if not current_map:
            return skills

        # Get current attributes for prerequisite checking
        attributes = (self.get_character_data() or {}).get("Tulajdonságok", {})

        try:
            with sqlite3.connect(self.skill_db_service.get_db_path("skill")) as sconn:
                for sid, req in current_map.items():
                    row = sconn.execute(
                        "SELECT name, parameter FROM skills WHERE id=?", (sid,)
                    ).fetchone()
                    if not row:
                        continue
                    name, parameter = row
                    display = f"{name} ({parameter})" if parameter else name

                    # Check prerequisites before adding to export list
                    req_level = int(req.get("level", 0))
                    req_percent = int(req.get("%", 0))
                    ok, _ = self.prereq_checker.check_prerequisites(
                        sid, req_level, req_percent, current_map, attributes
                    )

                    # Only add skills with fulfilled prerequisites
                    if not ok:
                        logger.info(f"Skipping skill {display} due to unmet prerequisites")
                        continue

                    # Get source from table or default to "Előismeret"
                    source = skill_sources.get(sid, "Előismeret")

                    skills.append(
                        {
                            "id": sid,
                            "Képzettség": display,
                            "Szint": req_level,
                            "%": req_percent,
                            "Forrás": source,
                        }
                    )
        except Exception as e:
            logger.error(f"Error exporting selected skills: {e}", exc_info=True)
        return skills

    def _get_spec_id(self, data: dict[str, Any]) -> str | None:
        """Extract specialization ID from character data."""
        spec_name = data.get("Specializáció", "Nincs")
        if spec_name == "Nincs":
            return None
        spec_data = self.get_spec_data() or {}
        info = spec_data.get(spec_name)
        return info.get("specialisation_id") if info else None

    def _get_racial_skill_entries(
        self, data: dict[str, Any]
    ) -> list[tuple[str, None, int, int, str, int, str]]:
        """
        Get racial skill entries from character's race.

        Returns:
            List of tuples in the same format as class skills:
            (skill_id, class_level, req_level, req_percent, from_racial, is_placeholder, display_name)
            where from_racial is a string "Faji" to distinguish from class/spec skills
        """
        racial_entries: list[tuple[str, None, int, int, str, int, str]] = []
        race_name = data.get("Faj", "Ember")

        try:
            race_obj = _race_manager.get_race_by_name(race_name)
            if not race_obj or not race_obj.racial_skills:
                return racial_entries

            # Fetch skill names and placeholder status from database
            with sqlite3.connect(self.skill_db_service.get_db_path("skill")) as skill_conn:
                for racial_skill in race_obj.racial_skills:
                    try:
                        row = skill_conn.execute(
                            "SELECT name, parameter, placeholder FROM skills WHERE id=?",
                            (racial_skill.skill_id,),
                        ).fetchone()

                        if row:
                            name, parameter, is_placeholder = row
                            display_name = f"{name} ({parameter})" if parameter else name

                            # Format: (skill_id, class_level, req_level, req_percent, from_source, is_placeholder, display_name)
                            # Use "Faji" as the from_source marker instead of boolean
                            racial_entries.append(
                                (
                                    racial_skill.skill_id,
                                    None,  # class_level not applicable for racial skills
                                    racial_skill.level,  # required level from race definition
                                    0,  # no % requirement for racial skills (level-based only)
                                    "Faji",  # source marker
                                    is_placeholder,  # 0 or 1 from database
                                    display_name,
                                )
                            )
                    except Exception as e:
                        logger.error(
                            f"Error loading racial skill {racial_skill.skill_id}: {e}",
                            exc_info=True,
                        )

        except Exception as e:
            logger.error(f"Error getting racial skills for race {race_name}: {e}", exc_info=True)

        return racial_entries

    def refresh(self) -> None:
        """Rebuild the table based on current selected class/spec and character data."""
        data = self.get_character_data() or {}

        # Initialize and refresh attributes display
        if hasattr(self, "attributes_widget"):
            class_name = data.get("Kaszt")
            race = data.get("Faj", "Ember")
            age = int(data.get("Kor", 20))

            if class_name and race:
                try:
                    # Preserve current values/mode; only (re)initialize if needed or class changed
                    self.attributes_widget.refresh_from_basic_selection(class_name, race, age)
                except Exception as e:
                    logger.error(f"Error refreshing attributes: {e}", exc_info=True)
            else:
                # Fallback simple repaint
                self.attributes_widget.refresh()

        # Update KP header
        kp_alap = data.get("Képzettségpontok", {}).get("Alap", 0)
        kp_szinten = data.get("Képzettségpontok", {}).get("Szintenként", 0)
        total_kp = kp_alap + kp_szinten
        self.kp_info_label.setText(
            f"<b>Képzettségpontok:</b> Alap: {kp_alap} + Szintenként: {kp_szinten} = <b>{total_kp} KP</b> az 1. szinten"
        )

        # Load skills table
        self._load_skills()

        # Update empty message
        self.empty_msg.setText(
            "<i>Ehhez a kaszthoz/specializációhoz még nincsenek képzettségek hozzárendelve.<br>"
            "A képzettségeket a Kaszt szerkesztőben lehet megadni.</i>"
            if self.skills_table.rowCount() == 0
            else ""
        )

    def _on_attributes_changed(self, attributes: dict[str, int]) -> None:
        """Handle attribute changes - refresh skills to update prereq checks."""
        self._load_skills()

    def _on_row_double_click(self, index: QtCore.QModelIndex) -> None:
        """Handle double-click on placeholder combo rows to open dropdown."""
        widget = self.skills_table.cellWidget(index.row(), 0)
        if isinstance(widget, QtWidgets.QComboBox):
            self.skills_table.setCurrentCell(index.row(), 0)
            widget.setFocus(QtCore.Qt.FocusReason.MouseFocusReason)
            widget.showPopup()

    def _refresh_placeholder_combos(self) -> None:
        """Delegate to table renderer to refresh placeholder combos."""
        self.table_renderer.refresh_placeholder_combos()

    def _load_skills(self) -> None:
        """Load and display class/spec skills with placeholder resolution and racial skills."""
        self.skills_table.setRowCount(0)
        self._placeholder_row_counters = {}
        self._placeholder_combos = {}

        class_id = self.get_selected_class_id()
        if not class_id:
            return

        data = self.get_character_data() or {}
        spec_id = self._get_spec_id(data)

        # Get racial skills
        racial_entries = self._get_racial_skill_entries(data)

        try:
            skills = self.skill_db_service.fetch_class_skills(class_id, spec_id)
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self, "Hiba", f"Nem sikerült betölteni a képzettségeket:\n{e}"
            )
            return

        # Process skill entries using the service
        entries, fixed_skill_ids = self.skill_db_service.process_skill_entries(skills)

        # Add non-placeholder racial skill IDs to fixed skills to prevent them from being selected as placeholders
        # Placeholder racial skills should remain available as resolution options
        racial_skill_ids = {
            entry[0] for entry in racial_entries if entry[5] != 1
        }  # entry[5] is is_placeholder
        fixed_skill_ids.update(racial_skill_ids)

        self.placeholder_manager.set_fixed_skills(fixed_skill_ids)

        # Combine racial and class/spec entries
        all_entries = racial_entries + entries
        current_map = self._build_current_skills_map_from_entries(all_entries)
        # Use renderer
        self.table_renderer.clear_state()
        self.table_renderer.render_rows(all_entries, current_map)

    def _build_current_skills_map_from_entries(
        self, entries: list[tuple[str, int | None, int, int, Any, int, str]]
    ) -> dict[str, dict[str, int]]:
        """Construct a map of concrete skills -> assigned level/percent from fixed skills
        and currently selected placeholder resolutions.
        """
        current_map: dict[str, dict[str, int]] = {}
        counters: dict[tuple[Any, ...], int] = {}
        for (
            skill_id,
            class_level,
            req_level,
            req_percent,
            from_spec,
            is_placeholder,
            _display_name,
        ) in entries:
            if is_placeholder == 1:
                # Convert from_spec to boolean for placeholder key generation
                # "Faji" is treated as False (not from spec) for key purposes
                from_spec_bool = from_spec not in (False, 0, "Faji", None)

                base_key = (
                    skill_id,
                    int(class_level or 0),
                    int(req_level or 0),
                    int(req_percent or 0),
                    from_spec_bool,
                )
                occur = counters.get(base_key, 0)
                counters[base_key] = occur + 1
                instance_key = (*base_key, occur)
                chosen = self.placeholder_manager.get_choice(instance_key)
                if chosen:
                    current_map[chosen] = {"level": int(req_level or 0), "%": int(req_percent or 0)}
            else:
                current_map[skill_id] = {"level": int(req_level or 0), "%": int(req_percent or 0)}
        return current_map

    def _build_current_skills_map(
        self, req_override_instance: tuple[Any, ...] | None = None
    ) -> dict[str, dict[str, int]]:
        """Build map based on current table/choices, excluding a specific instance if provided."""
        current_map: dict[str, dict[str, int]] = {}

        try:
            for row in range(self.skills_table.rowCount()):
                name_widget = self.skills_table.cellWidget(row, 0)
                if name_widget is None:
                    name_item = self.skills_table.item(row, 0)
                    if not name_item:
                        continue
                    display = name_item.text()
                    sid = self.skill_db_service.get_skill_by_display(display)
                    if not sid:
                        continue
                    lvl_item = self.skills_table.item(row, 1)
                    pct_item = self.skills_table.item(row, 2)
                    lvl = int(lvl_item.text()) if lvl_item and lvl_item.text().isdigit() else 0
                    pct = int(pct_item.text()) if pct_item and pct_item.text().isdigit() else 0
                    current_map[sid] = {"level": lvl, "%": pct}
        except Exception as e:
            logger.error(f"Error building current skills map: {e}", exc_info=True)

        # Add placeholder choices using the manager
        for ikey, chosen in self.placeholder_manager.placeholder_choices.items():
            if req_override_instance is not None and ikey == req_override_instance:
                continue
            _, _class_level, req_level, req_percent, _from_spec, _occ = ikey
            current_map[chosen] = {"level": int(req_level or 0), "%": int(req_percent or 0)}
        return current_map
