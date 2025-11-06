from collections.abc import Callable
from typing import Any

from PySide6 import QtGui, QtWidgets
from utils.ui.themes import CharacterCreationTheme


class SkillsTableRenderer:
    """
    Encapsulates rendering of skills rows (fixed and placeholders),
    managing placeholder combo boxes, KP cost updates, and prereq coloring.
    """

    def __init__(
        self,
        table: QtWidgets.QTableWidget,
        skill_db_service: Any,
        placeholder_manager: Any,
        prereq_checker: Any,
        build_current_map_cb: Callable[
            [tuple[str, int, int, int, bool, int] | None], dict[str, dict[str, int]]
        ],
        attributes_getter: Callable[[], dict[str, Any]],
    ) -> None:
        self.table = table
        self.skill_db_service = skill_db_service
        self.placeholder_manager = placeholder_manager
        self.prereq_checker = prereq_checker
        self.build_current_map_cb = build_current_map_cb
        self.attributes_getter = attributes_getter
        self._placeholder_row_counters: dict[tuple[str, int, int, int, bool], int] = {}
        self._placeholder_combos: dict[
            tuple[str, int, int, int, bool, int], QtWidgets.QComboBox
        ] = {}

    # ---- Public API ----

    def clear_state(self) -> None:
        self._placeholder_row_counters.clear()
        self._placeholder_combos.clear()

    def render_rows(
        self,
        entries: list[tuple[str, int | None, int | None, int | None, Any, int, str]],
        current_map: dict[str, dict[str, int]],
    ) -> None:
        attributes: dict[str, Any] = self.attributes_getter() or {}

        for (
            skill_id,
            class_level,
            req_level,
            req_percent,
            from_spec,
            is_placeholder,
            display_name,
        ) in entries:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(
                row, 1, QtWidgets.QTableWidgetItem(str(req_level) if req_level else "-")
            )
            self.table.setItem(
                row, 2, QtWidgets.QTableWidgetItem(str(req_percent) if req_percent else "-")
            )
            kp_cost = (
                self.skill_db_service.calc_kp_cost(skill_id, req_level, req_percent)
                if is_placeholder != 1
                else "?"
            )
            self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(str(kp_cost)))

            # Determine source: handle "Faji" marker
            if from_spec == "Faji":
                source = "Faji"
            elif from_spec:
                source = "Specializáció"
            else:
                source = "Alap kaszt"
            self.table.setItem(row, 4, QtWidgets.QTableWidgetItem(source))

            if is_placeholder == 1:
                self._render_placeholder_row(
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

    def refresh_placeholder_combos(self) -> None:
        """Refresh all placeholder combo boxes to enforce uniqueness and prerequisites."""
        attributes: dict[str, Any] = self.attributes_getter() or {}
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
            current_map = self.build_current_map_cb(instance_key)
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
                    if isinstance(cur_row, int) and 0 <= cur_row < self.table.rowCount():
                        item = self.table.item(cur_row, 3)
                        if item:
                            item.setText("?")
            combo.blockSignals(False)

    # ---- Internal utility methods ----

    def _render_placeholder_row(
        self,
        row: int,
        skill_id: str,
        class_level: int | None,
        req_level: int | None,
        req_percent: int | None,
        from_spec: Any,
        display_name: str,
        attributes: dict[str, Any],
    ) -> None:
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

        # Get initial valid resolutions
        current_map = self.build_current_map_cb(instance_key)
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
        combo.currentIndexChanged.connect(lambda _: self._on_placeholder_changed(combo))

        # Restore prior choice using the manager
        chosen = self.placeholder_manager.get_choice(instance_key)
        if chosen:
            idx = combo.findData(chosen)
            if idx != -1:
                combo.setCurrentIndex(idx)
                item = self.table.item(row, 3)
                if item:
                    item.setText(self.skill_db_service.calc_kp_cost(chosen, req_level, req_percent))
            else:
                combo.setCurrentIndex(0)

        self._placeholder_combos[instance_key] = combo
        self.table.setCellWidget(row, 0, combo)

    def _render_fixed_skill_row(
        self,
        row: int,
        skill_id: str,
        req_level: int | None,
        req_percent: int | None,
        display_name: str,
        current_map: dict[str, dict[str, int]],
        attributes: dict[str, Any],
    ) -> None:
        name_item = QtWidgets.QTableWidgetItem(display_name)
        self.table.setItem(row, 0, name_item)

        ok, reasons = self.prereq_checker.check_prerequisites(
            skill_id, int(req_level or 0), int(req_percent or 0), current_map, attributes
        )
        prereq_item = QtWidgets.QTableWidgetItem("OK" if ok else "Hiányzik")
        if ok:
            prereq_item.setForeground(
                QtGui.QBrush(QtGui.QColor(CharacterCreationTheme.SUCCESS_GREEN_DARK))
            )
        else:
            prereq_item.setForeground(QtGui.QBrush(QtGui.QColor(CharacterCreationTheme.ERROR_RED)))
            prereq_item.setToolTip("\n".join(reasons))
        self.table.setItem(row, 5, prereq_item)

    def _on_placeholder_changed(self, combo: QtWidgets.QComboBox) -> None:
        instance_key = combo.property("instance_key")
        row = combo.property("row")
        chosen = combo.currentData()

        if not instance_key:
            return

        # Update placeholder choice using the manager
        self.placeholder_manager.set_choice(instance_key, chosen)

        # Update KP cost cell
        if isinstance(row, int) and 0 <= row < self.table.rowCount():
            if chosen:
                req_level = int(combo.property("skill_level") or 0)
                req_percent = int(combo.property("skill_percent") or 0)
                try:
                    cost = self.skill_db_service.calc_kp_cost(chosen, req_level, req_percent)
                    item = self.table.item(row, 3)
                    if item:
                        item.setText(cost)
                except Exception:
                    # Log suppressed here; parent can log via error hooks if needed
                    pass
            else:
                item = self.table.item(row, 3)
                if item:
                    item.setText("?")

        # Refresh combos to enforce uniqueness
        self.refresh_placeholder_combos()
