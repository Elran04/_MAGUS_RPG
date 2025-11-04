import sqlite3
from collections.abc import Callable
from typing import Any

from PySide6 import QtCore, QtGui, QtWidgets
from ui.character_creation.helpers.skill_db_helper import SkillDatabaseHelper
from ui.character_creation.helpers.skill_prerequisites import SkillPrerequisiteChecker
from ui.character_creation.widgets.placeholder_skill_manager import PlaceholderSkillManager
from utils.log.logger import get_logger

logger = get_logger(__name__)


class SkillsStepWidget(QtWidgets.QWidget):
    """Skills step widget displaying class/spec skills with inline placeholder resolution."""

    def __init__(
        self,
        base_dir: str,
        placeholder_mgr,
        get_selected_class_id: Callable[[], str | None],
        get_spec_data: Callable[[], dict[str, Any]],
        get_character_data: Callable[[], dict[str, Any]],
    ):
        super().__init__()
        self.BASE_DIR = base_dir
        self.get_selected_class_id = get_selected_class_id
        self.get_spec_data = get_spec_data
        self.get_character_data = get_character_data

        # Initialize helper classes
        self.db_helper = SkillDatabaseHelper(base_dir)
        self.prereq_checker = SkillPrerequisiteChecker(self.db_helper)
        self.placeholder_manager = PlaceholderSkillManager(placeholder_mgr, self.prereq_checker)

        self._placeholder_row_counters: dict[tuple, int] = {}
        self._placeholder_combos: dict[tuple, QtWidgets.QComboBox] = {}
        self._build_ui()

    def _build_ui(self):
        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)

        # Left panel: Attributes display
        from ui.character_creation.widgets.attributes_display import AttributesDisplayWidget
        from utils.data.class_db_manager import ClassDBManager

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
        self.kp_info_label.setStyleSheet(
            "font-size: 12pt; padding: 8px; background-color: rgba(100,100,120,50); border-radius: 4px;"
        )
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

        # Empty note
        self.empty_msg = QtWidgets.QLabel("")
        self.empty_msg.setWordWrap(True)
        self.empty_msg.setStyleSheet(
            "color: #cc8800; font-size: 10pt; padding: 12px; background-color: rgba(200,150,50,30); border-radius: 4px;"
        )
        layout.addWidget(self.empty_msg)

        # Footer note
        note = QtWidgets.QLabel(
            "<i>Megjegyzés: A képzettségek szerkesztése a karakter mentése után a külön karakterszerkesztőben lehetséges.</i>"
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #888; font-size: 9pt; padding: 8px;")
        layout.addWidget(note)

        splitter.addWidget(right_panel)
        splitter.setSizes([200, 1000])  # ~20% left, ~80% right
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)

    def get_selected_skills(self):
        """Export current selected skills (fixed + placeholder resolutions) as a list of dicts.
        Each entry contains: {"id": skill_id, "Képzettség": name( (param)), "Szint": int, "%": int}.
        """
        skills: list[dict[str, Any]] = []
        current_map = self._build_current_skills_map()
        if not current_map:
            return skills
        try:
            with sqlite3.connect(self.db_helper.get_db_path("skill")) as sconn:
                for sid, req in current_map.items():
                    row = sconn.execute(
                        "SELECT name, parameter FROM skills WHERE id=?", (sid,)
                    ).fetchone()
                    if not row:
                        continue
                    name, parameter = row
                    display = f"{name} ({parameter})" if parameter else name
                    skills.append(
                        {
                            "id": sid,
                            "Képzettség": display,
                            "Szint": int(req.get("level", 0)),
                            "%": int(req.get("%", 0)),
                        }
                    )
        except Exception as e:
            logger.error(f"Error exporting selected skills: {e}", exc_info=True)
        return skills

    def _get_spec_id(self, data: dict) -> str | None:
        """Extract specialization ID from character data."""
        spec_name = data.get("Specializáció", "Nincs")
        if spec_name == "Nincs":
            return None
        spec_data = self.get_spec_data() or {}
        info = spec_data.get(spec_name)
        return info.get("specialisation_id") if info else None

    def refresh(self):
        """Rebuild the table based on current selected class/spec and character data."""
        data = self.get_character_data() or {}

        # Initialize and refresh attributes display
        if hasattr(self, "attributes_widget"):
            class_name = data.get("Kaszt")
            race = data.get("Faj", "Ember")
            age = int(data.get("Kor", 20))

            if class_name and race:
                try:
                    self.attributes_widget.initialize(class_name, race, age)
                except Exception as e:
                    logger.error(f"Error initializing attributes: {e}", exc_info=True)
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

    def _on_attributes_changed(self, attributes: dict):
        """Handle attribute changes - refresh skills to update prereq checks."""
        self._load_skills()

    def _on_row_double_click(self, index):
        """Handle double-click on placeholder combo rows to open dropdown."""
        widget = self.skills_table.cellWidget(index.row(), 0)
        if isinstance(widget, QtWidgets.QComboBox):
            self.skills_table.setCurrentCell(index.row(), 0)
            widget.setFocus(QtCore.Qt.FocusReason.MouseFocusReason)
            widget.showPopup()

    def _refresh_placeholder_combos(self):
        """Refresh all placeholder combo boxes to enforce uniqueness and prerequisites."""
        for instance_key, combo in self._placeholder_combos.items():
            ph_id = instance_key[0]
            current_selected = combo.currentData()
            combo.blockSignals(True)
            cur_row = combo.property("row")
            req_level = int(combo.property("skill_level") or 0)
            req_percent = int(combo.property("skill_percent") or 0)
            combo.clear()
            combo.addItem("-- válassz --", None)

            # Get valid resolutions using the placeholder manager
            attributes = (self.get_character_data() or {}).get("Tulajdonságok", {})
            current_map = self._build_current_skills_map(req_override_instance=instance_key)
            valid_resolutions = self.placeholder_manager.get_valid_resolutions(
                ph_id,
                instance_key,
                req_level,
                req_percent,
                current_map,
                attributes,
            )

            for res in valid_resolutions:
                disp = res["skill_name"]
                if res["parameter"]:
                    disp += f" ({res['parameter']})"
                combo.addItem(disp, res["target_skill_id"])

            if current_selected is not None:
                idx = combo.findData(current_selected)
                if idx != -1:
                    combo.setCurrentIndex(idx)
                else:
                    combo.setCurrentIndex(0)
                    self.placeholder_manager.set_choice(instance_key, None)
                    if isinstance(cur_row, int) and 0 <= cur_row < self.skills_table.rowCount():
                        item = self.skills_table.item(cur_row, 3)
                        if item:
                            item.setText("?")
            combo.blockSignals(False)

    def _load_skills(self):
        """Load and display class/spec skills with placeholder resolution."""
        self.skills_table.setRowCount(0)
        self._placeholder_row_counters = {}
        self._placeholder_combos = {}

        class_id = self.get_selected_class_id()
        if not class_id:
            return

        data = self.get_character_data() or {}
        spec_id = self._get_spec_id(data)

        try:
            skills = self.db_helper.fetch_class_skills(class_id, spec_id)
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self, "Hiba", f"Nem sikerült betölteni a képzettségeket:\n{e}"
            )
            return

        # Process skill entries using the helper
        entries, fixed_skill_ids = self.db_helper.process_skill_entries(skills)
        self.placeholder_manager.set_fixed_skills(fixed_skill_ids)

        with sqlite3.connect(self.db_helper.get_db_path("skill")) as skill_conn:
            current_map = self._build_current_skills_map_from_entries(entries)
            self._render_skill_rows(skill_conn, entries, current_map)

    def _render_skill_rows(self, skill_conn, entries, current_map):
        """Render skill entries into table rows with placeholders and prerequisites."""
        attributes = (self.get_character_data() or {}).get("Tulajdonságok", {})

        for (
            skill_id,
            class_level,
            req_level,
            req_percent,
            from_spec,
            is_placeholder,
            display_name,
        ) in entries:
            try:
                row = self.skills_table.rowCount()
                self.skills_table.insertRow(row)
                self.skills_table.setItem(
                    row, 1, QtWidgets.QTableWidgetItem(str(req_level) if req_level else "-")
                )
                self.skills_table.setItem(
                    row, 2, QtWidgets.QTableWidgetItem(str(req_percent) if req_percent else "-")
                )
                kp_cost = (
                    self.db_helper.calc_kp_cost(skill_id, req_level, req_percent)
                    if is_placeholder != 1
                    else "?"
                )
                self.skills_table.setItem(row, 3, QtWidgets.QTableWidgetItem(str(kp_cost)))
                source = "Specializáció" if from_spec else "Alap kaszt"
                self.skills_table.setItem(row, 4, QtWidgets.QTableWidgetItem(source))

                if is_placeholder == 1:
                    self._render_placeholder_row(
                        skill_conn,
                        row,
                        skill_id,
                        class_level,
                        req_level,
                        req_percent,
                        from_spec,
                        display_name,
                        attributes,
                    )
                else:
                    self._render_fixed_skill_row(
                        row, skill_id, req_level, req_percent, display_name, current_map, attributes
                    )
            except Exception as e:
                logger.error(f"Error rendering skill row {skill_id}: {e}", exc_info=True)

    def _render_placeholder_row(
        self,
        skill_conn,
        row,
        skill_id,
        class_level,
        req_level,
        req_percent,
        from_spec,
        display_name,
        attributes,
    ):
        """Render a placeholder skill row with combo box selector."""
        base_key = (
            skill_id,
            int(class_level or 0),
            int(req_level or 0),
            int(req_percent or 0),
            bool(from_spec),
        )
        occur = self._placeholder_row_counters.get(base_key, 0)
        self._placeholder_row_counters[base_key] = occur + 1
        instance_key = (*base_key, occur)

        combo = QtWidgets.QComboBox()
        combo.setEditable(True)
        line_edit = combo.lineEdit()
        if line_edit:
            line_edit.setPlaceholderText(f"{display_name} — válassz feloldást")
        combo.addItem("-- válassz --", None)

        # Get valid resolutions using the placeholder manager
        current_map = self._build_current_skills_map(req_override_instance=instance_key)
        valid_resolutions = self.placeholder_manager.get_valid_resolutions(
            skill_id,
            instance_key,
            int(req_level or 0),
            int(req_percent or 0),
            current_map,
            attributes,
        )

        for res in valid_resolutions:
            disp = res["skill_name"]
            if res["parameter"]:
                disp += f" ({res['parameter']})"
            combo.addItem(disp, res["target_skill_id"])

        combo.setProperty("instance_key", instance_key)
        combo.setProperty("row", row)
        combo.setProperty("skill_level", int(req_level or 0))
        combo.setProperty("skill_percent", int(req_percent or 0))
        combo.currentIndexChanged.connect(self._on_placeholder_changed)

        # Restore prior choice using the manager
        chosen = self.placeholder_manager.get_choice(instance_key)
        if chosen:
            idx = combo.findData(chosen)
            if idx != -1:
                combo.setCurrentIndex(idx)
                item = self.skills_table.item(row, 3)
                if item:
                    item.setText(self.db_helper.calc_kp_cost(chosen, req_level, req_percent))
            else:
                combo.setCurrentIndex(0)

        self._placeholder_combos[instance_key] = combo
        self.skills_table.setCellWidget(row, 0, combo)

    def _render_fixed_skill_row(
        self, row, skill_id, req_level, req_percent, display_name, current_map, attributes
    ):
        """Render a fixed (non-placeholder) skill row with prerequisite check."""
        name_item = QtWidgets.QTableWidgetItem(display_name)
        self.skills_table.setItem(row, 0, name_item)

        ok, reasons = self.prereq_checker.check_prerequisites(
            skill_id, int(req_level or 0), int(req_percent or 0), current_map, attributes
        )
        prereq_item = QtWidgets.QTableWidgetItem("OK" if ok else "Hiányzik")
        if ok:
            prereq_item.setForeground(QtGui.QBrush(QtGui.QColor("#2e7d32")))
        else:
            prereq_item.setForeground(QtGui.QBrush(QtGui.QColor("#c62828")))
            prereq_item.setToolTip("\n".join(reasons))
        self.skills_table.setItem(row, 5, prereq_item)

    def _on_placeholder_changed(self):
        """Handle placeholder combo selection change."""
        combo = self.sender()
        if not isinstance(combo, QtWidgets.QComboBox):
            return

        instance_key = combo.property("instance_key")
        row = combo.property("row")
        chosen = combo.currentData()

        if not instance_key:
            return

        # Update placeholder choice using the manager
        self.placeholder_manager.set_choice(instance_key, chosen)

        # Update KP cost cell
        if isinstance(row, int) and 0 <= row < self.skills_table.rowCount():
            if chosen:
                req_level = int(combo.property("skill_level") or 0)
                req_percent = int(combo.property("skill_percent") or 0)
                try:
                    cost = self.db_helper.calc_kp_cost(chosen, req_level, req_percent)
                    item = self.skills_table.item(row, 3)
                    if item:
                        item.setText(cost)
                except Exception as e:
                    logger.error(f"Error updating KP cost: {e}", exc_info=True)
            else:
                item = self.skills_table.item(row, 3)
                if item:
                    item.setText("?")

        # Refresh combos to enforce uniqueness
        self._refresh_placeholder_combos()

    def _build_current_skills_map_from_entries(self, entries):
        """Construct a map of concrete skills -> assigned level/percent from fixed skills
        and currently selected placeholder resolutions.
        """
        current_map = {}
        counters: dict[tuple, int] = {}
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
                base_key = (
                    skill_id,
                    int(class_level or 0),
                    int(req_level or 0),
                    int(req_percent or 0),
                    bool(from_spec),
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

    def _build_current_skills_map(self, req_override_instance=None):
        """Build map based on current table/choices, excluding a specific instance if provided."""
        current_map = {}

        try:
            for row in range(self.skills_table.rowCount()):
                name_widget = self.skills_table.cellWidget(row, 0)
                if name_widget is None:
                    name_item = self.skills_table.item(row, 0)
                    if not name_item:
                        continue
                    display = name_item.text()
                    sid = self.db_helper.get_skill_by_display(display)
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
