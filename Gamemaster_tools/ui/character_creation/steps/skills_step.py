from PySide6 import QtWidgets, QtCore
import os
import sqlite3
from typing import Callable, Dict, Any

class SkillsStepWidget(QtWidgets.QWidget):
    """Skills step widget displaying class/spec skills with inline placeholder resolution.

    Expects callbacks to query current selection and character data.
    """
    def __init__(self,
                 base_dir: str,
                 placeholder_mgr,
                 get_selected_class_id: Callable[[], str | None],
                 get_spec_data: Callable[[], Dict[str, Any]],
                 get_character_data: Callable[[], Dict[str, Any]]):
        super().__init__()
        self.BASE_DIR = base_dir
        self.placeholder_mgr = placeholder_mgr
        self.get_selected_class_id = get_selected_class_id
        self.get_spec_data = get_spec_data
        self.get_character_data = get_character_data
        self.placeholder_choices: Dict[Any, str] = {}
        self._fixed_skill_ids = set()
        self._placeholder_row_counters = {}
        self._placeholder_combos = {}
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header with KP
        header = QtWidgets.QWidget()
        header_layout = QtWidgets.QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 10)
        self.kp_info_label = QtWidgets.QLabel("")
        self.kp_info_label.setStyleSheet("font-size: 12pt; padding: 8px; background-color: rgba(100,100,120,50); border-radius: 4px;")
        header_layout.addWidget(self.kp_info_label)
        header_layout.addStretch()
        layout.addWidget(header)

        # Table
        layout.addWidget(QtWidgets.QLabel("Kaszt/Specializáció képzettségei:"))
        self.skills_table = QtWidgets.QTableWidget()
        self.skills_table.setColumnCount(5)
        self.skills_table.setHorizontalHeaderLabels(["Képzettség", "Szint", "%", "KP költség", "Forrás"]) 
        self.skills_table.horizontalHeader().setStretchLastSection(False)
        self.skills_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.skills_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.skills_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.skills_table.doubleClicked.connect(self._on_row_double_click)
        layout.addWidget(self.skills_table)

        # Empty note placeholder
        self.empty_msg = QtWidgets.QLabel("")
        self.empty_msg.setWordWrap(True)
        self.empty_msg.setStyleSheet("color: #cc8800; font-size: 10pt; padding: 12px; background-color: rgba(200,150,50,30); border-radius: 4px;")
        layout.addWidget(self.empty_msg)

        # Footer note
        note = QtWidgets.QLabel(
            "<i>Megjegyzés: A képzettségek szerkesztése a karakter mentése után a külön karakterszerkesztőben lehetséges.</i>"
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #888; font-size: 9pt; padding: 8px;")
        layout.addWidget(note)

    def refresh(self):
        """Rebuild the table based on current selected class/spec and character data."""
        # KP header
        data = self.get_character_data() or {}
        kp_alap = data.get("Képzettségpontok", {}).get("Alap", 0)
        kp_szinten = data.get("Képzettségpontok", {}).get("Szintenként", 0)
        total_kp = kp_alap + kp_szinten
        self.kp_info_label.setText(
            f"<b>Képzettségpontok:</b> Alap: {kp_alap} + Szintenként: {kp_szinten} = <b>{total_kp} KP</b> az 1. szinten"
        )

        # Load table
        self._load_skills()

        # Empty message
        if self.skills_table.rowCount() == 0:
            self.empty_msg.setText(
                "<i>Ehhez a kaszthoz/specializációhoz még nincsenek képzettségek hozzárendelve.<br>"
                "A képzettségeket a Kaszt szerkesztőben lehet megadni.</i>"
            )
        else:
            self.empty_msg.setText("")

    def _on_row_double_click(self, index):
        row = index.row()
        widget = self.skills_table.cellWidget(row, 0)
        if isinstance(widget, QtWidgets.QComboBox):
            self.skills_table.setCurrentCell(row, 0)
            widget.setFocus(QtCore.Qt.FocusReason.MouseFocusReason)
            widget.showPopup()

    def _compute_taken_skills(self, exclude_instance=None):
        taken = set(getattr(self, '_fixed_skill_ids', set()))
        for ikey, chosen in list(self.placeholder_choices.items()):
            if exclude_instance is not None and ikey == exclude_instance:
                continue
            if chosen:
                taken.add(chosen)
        return taken

    def _refresh_placeholder_combos(self):
        for instance_key, combo in self._placeholder_combos.items():
            ph_id = instance_key[0]
            current_selected = combo.currentData()
            taken = self._compute_taken_skills(exclude_instance=instance_key)
            resolutions = self.placeholder_mgr.get_resolutions(ph_id)
            combo.blockSignals(True)
            cur_row = combo.property('row')
            req_level = int(combo.property('skill_level') or 0)
            req_percent = int(combo.property('skill_percent') or 0)
            combo.clear()
            combo.addItem("-- válassz --", None)
            for res in resolutions:
                disp = res['skill_name']
                if res['parameter']:
                    disp += f" ({res['parameter']})"
                tid = res['target_skill_id']
                if tid in taken:
                    continue
                combo.addItem(disp, tid)
            if current_selected is not None:
                idx = combo.findData(current_selected)
                if idx != -1:
                    combo.setCurrentIndex(idx)
                else:
                    combo.setCurrentIndex(0)
                    if instance_key in self.placeholder_choices:
                        del self.placeholder_choices[instance_key]
                    if isinstance(cur_row, int) and 0 <= cur_row < self.skills_table.rowCount():
                        self.skills_table.item(cur_row, 3).setText("?")
            combo.blockSignals(False)

    def _load_skills(self):
        self.skills_table.setRowCount(0)
        self._placeholder_row_counters = {}
        self._placeholder_combos = {}

        class_id = self.get_selected_class_id()
        if not class_id:
            return
        data = self.get_character_data() or {}
        spec_name = data.get("Specializáció", "Nincs")
        spec_data = self.get_spec_data() or {}
        spec_id = None
        if spec_name != "Nincs":
            info = spec_data.get(spec_name)
            if info:
                spec_id = info.get("specialisation_id")

        db_class_path = os.path.join(self.BASE_DIR, 'data', 'Class', 'class_data.db')
        db_skill_path = os.path.join(self.BASE_DIR, 'data', 'skills', 'skills_data.db')

        try:
            with sqlite3.connect(db_class_path) as conn:
                if spec_id:
                    skills = conn.execute(
                        """
                        SELECT skill_id, class_level, skill_level, skill_percent, specialisation_id
                        FROM class_skills 
                        WHERE class_id=? AND (specialisation_id IS NULL OR specialisation_id=?)
                        ORDER BY class_level, skill_id
                        """,
                        (class_id, spec_id)
                    ).fetchall()
                else:
                    skills = conn.execute(
                        """
                        SELECT skill_id, class_level, skill_level, skill_percent, specialisation_id
                        FROM class_skills 
                        WHERE class_id=? AND specialisation_id IS NULL
                        ORDER BY class_level, skill_id
                        """,
                        (class_id,)
                    ).fetchall()
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Hiba", f"Nem sikerült betölteni a képzettségeket:\n{e}")
            return

        with sqlite3.connect(db_skill_path) as skill_conn:
            # Phase 1: collect entries & fixed skills
            entries = []
            fixed = set()
            for skill_id, class_level, skill_level, skill_percent, from_spec in skills:
                try:
                    row = skill_conn.execute(
                        "SELECT name, parameter, type, placeholder FROM skills WHERE id=?",
                        (skill_id,)
                    ).fetchone()
                    if not row:
                        continue
                    name, parameter, stype, is_placeholder = row
                    display = f"{name} ({parameter})" if parameter else name
                    entries.append((skill_id, class_level, skill_level, skill_percent, from_spec, is_placeholder, display))
                    if is_placeholder != 1:
                        fixed.add(skill_id)
                except Exception as e:
                    print(f"Error probing skill {skill_id}: {e}")
                    continue

            self._fixed_skill_ids = fixed

            def calc_kp_cost_for(concrete_skill_id: str, req_level: int | None, req_percent: int | None) -> str:
                srow = skill_conn.execute("SELECT type FROM skills WHERE id=?", (concrete_skill_id,)).fetchone()
                if not srow:
                    return "?"
                ctype = srow[0]
                if ctype == 1:
                    if req_level:
                        crow = skill_conn.execute(
                            "SELECT kp_cost FROM skill_level_costs WHERE skill_id=? AND level=?",
                            (concrete_skill_id, req_level)
                        ).fetchone()
                        return str(crow[0]) if crow else "?"
                    return "?"
                elif ctype == 2:
                    if req_percent:
                        crow = skill_conn.execute(
                            "SELECT kp_per_3percent FROM skill_percent_costs WHERE skill_id=?",
                            (concrete_skill_id,)
                        ).fetchone()
                        if crow:
                            kp_per_3 = crow[0]
                            return str((req_percent // 3) * kp_per_3)
                    return "?"
                return "?"

            # Phase 2: render
            for (skill_id, class_level, req_level, req_percent, from_spec, is_placeholder, display_name) in entries:
                try:
                    row = self.skills_table.rowCount()
                    self.skills_table.insertRow(row)
                    self.skills_table.setItem(row, 1, QtWidgets.QTableWidgetItem(str(req_level) if req_level else "-"))
                    self.skills_table.setItem(row, 2, QtWidgets.QTableWidgetItem(str(req_percent) if req_percent else "-"))
                    kp_cost = calc_kp_cost_for(skill_id, req_level, req_percent) if is_placeholder != 1 else "?"
                    self.skills_table.setItem(row, 3, QtWidgets.QTableWidgetItem(str(kp_cost)))
                    source = "Specializáció" if from_spec else "Alap kaszt"
                    self.skills_table.setItem(row, 4, QtWidgets.QTableWidgetItem(source))

                    if is_placeholder == 1:
                        base_key = (skill_id, int(class_level or 0), int(req_level or 0), int(req_percent or 0), bool(from_spec))
                        occur = getattr(self, '_placeholder_row_counters', {}).get(base_key, 0)
                        self._placeholder_row_counters[base_key] = occur + 1
                        instance_key = (*base_key, occur)

                        combo = QtWidgets.QComboBox()
                        combo.setEditable(True)
                        combo.lineEdit().setPlaceholderText(f"{display_name} — válassz feloldást")
                        combo.addItem("-- válassz --", None)
                        resolutions = self.placeholder_mgr.get_resolutions(skill_id)
                        taken = self._compute_taken_skills(exclude_instance=instance_key)
                        for res in resolutions:
                            disp = res['skill_name']
                            if res['parameter']:
                                disp += f" ({res['parameter']})"
                            tid = res['target_skill_id']
                            if tid in taken:
                                continue
                            combo.addItem(disp, tid)
                        combo.setProperty('instance_key', instance_key)
                        combo.setProperty('row', row)
                        combo.setProperty('skill_level', int(req_level or 0))
                        combo.setProperty('skill_percent', int(req_percent or 0))
                        combo.currentIndexChanged.connect(self._on_placeholder_changed)

                        # Restore prior choice
                        if instance_key in self.placeholder_choices:
                            chosen = self.placeholder_choices[instance_key]
                            idx = combo.findData(chosen)
                            if idx != -1:
                                combo.setCurrentIndex(idx)
                                self.skills_table.item(row, 3).setText(calc_kp_cost_for(chosen, req_level, req_percent))
                            else:
                                combo.setCurrentIndex(0)

                        self._placeholder_combos[instance_key] = combo
                        self.skills_table.setCellWidget(row, 0, combo)
                    else:
                        name_item = QtWidgets.QTableWidgetItem(display_name)
                        name_item.setData(QtCore.Qt.UserRole, skill_id)
                        name_item.setData(QtCore.Qt.UserRole + 1, is_placeholder)
                        self.skills_table.setItem(row, 0, name_item)
                except Exception as e:
                    print(f"Error rendering skill row {skill_id}: {e}")
                    continue

    def _on_placeholder_changed(self):
        combo = self.sender()
        if not isinstance(combo, QtWidgets.QComboBox):
            return
        instance_key = combo.property('instance_key')
        row = combo.property('row')
        chosen = combo.currentData()
        if instance_key:
            if chosen:
                self.placeholder_choices[instance_key] = chosen
            else:
                if instance_key in self.placeholder_choices:
                    del self.placeholder_choices[instance_key]
            # Update KP cost cell
            req_level = int(combo.property('skill_level') or 0)
            req_percent = int(combo.property('skill_percent') or 0)
            if isinstance(row, int) and 0 <= row < self.skills_table.rowCount():
                if chosen:
                    # Compute cost quickly
                    db_skill_path = os.path.join(self.BASE_DIR, 'data', 'skills', 'skills_data.db')
                    try:
                        with sqlite3.connect(db_skill_path) as sconn:
                            srow = sconn.execute("SELECT type FROM skills WHERE id=?", (chosen,)).fetchone()
                            cost = "?"
                            if srow:
                                ctype = srow[0]
                                if ctype == 1 and req_level:
                                    crow = sconn.execute("SELECT kp_cost FROM skill_level_costs WHERE skill_id=? AND level=?", (chosen, req_level)).fetchone()
                                    cost = str(crow[0]) if crow else "?"
                                elif ctype == 2 and req_percent:
                                    crow = sconn.execute("SELECT kp_per_3percent FROM skill_percent_costs WHERE skill_id=?", (chosen,)).fetchone()
                                    if crow:
                                        cost = str((req_percent // 3) * crow[0])
                            self.skills_table.item(row, 3).setText(cost)
                    except Exception as e:
                        print("Error updating KP cost:", e)
                else:
                    self.skills_table.item(row, 3).setText("?")
        # Refresh combos to enforce uniqueness
        self._refresh_placeholder_combos()

