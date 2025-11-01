import os
import sqlite3
from typing import Any, Callable, Dict

from PySide6 import QtCore, QtGui, QtWidgets


class SkillsStepWidget(QtWidgets.QWidget):
    """Skills step widget displaying class/spec skills with inline placeholder resolution."""
    
    def __init__(self, base_dir: str, placeholder_mgr, get_selected_class_id: Callable[[], str | None],
                 get_spec_data: Callable[[], Dict[str, Any]], get_character_data: Callable[[], Dict[str, Any]]):
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
        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        
        # Left panel: Attributes display
        from ui.character_creation.widgets.attributes_display import AttributesDisplayWidget
        from utils.class_db_manager import ClassDBManager
        
        self.attributes_widget = AttributesDisplayWidget(
            self.get_character_data,
            lambda key, value: (self.get_character_data() or {}).update({key: value}),
            ClassDBManager
        )
        self.attributes_widget.attributes_changed.connect(self._on_attributes_changed)
        splitter.addWidget(self.attributes_widget)
        
        # Right panel: Skills table and KP info
        right_panel = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(right_panel)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header with KP
        self.kp_info_label = QtWidgets.QLabel("")
        self.kp_info_label.setStyleSheet("font-size: 12pt; padding: 8px; background-color: rgba(100,100,120,50); border-radius: 4px;")
        layout.addWidget(self.kp_info_label)

        # Table
        layout.addWidget(QtWidgets.QLabel("Kaszt/Specializáció képzettségei:"))
        self.skills_table = QtWidgets.QTableWidget()
        self.skills_table.setColumnCount(6)
        self.skills_table.setHorizontalHeaderLabels(["Képzettség", "Szint", "%", "KP költség", "Forrás", "Előfeltételek"])
        self.skills_table.horizontalHeader().setStretchLastSection(False)
        self.skills_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.skills_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.skills_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.skills_table.doubleClicked.connect(self._on_row_double_click)
        layout.addWidget(self.skills_table)

        # Empty note
        self.empty_msg = QtWidgets.QLabel("")
        self.empty_msg.setWordWrap(True)
        self.empty_msg.setStyleSheet("color: #cc8800; font-size: 10pt; padding: 12px; background-color: rgba(200,150,50,30); border-radius: 4px;")
        layout.addWidget(self.empty_msg)

        # Footer note
        note = QtWidgets.QLabel("<i>Megjegyzés: A képzettségek szerkesztése a karakter mentése után a külön karakterszerkesztőben lehetséges.</i>")
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
        skills = []
        current_map = self._build_current_skills_map()
        if not current_map:
            return skills
        try:
            with sqlite3.connect(self._get_db_path('skill')) as sconn:
                for sid, req in current_map.items():
                    row = sconn.execute("SELECT name, parameter FROM skills WHERE id=?", (sid,)).fetchone()
                    if not row:
                        continue
                    name, parameter = row
                    display = f"{name} ({parameter})" if parameter else name
                    skills.append({
                        "id": sid,
                        "Képzettség": display,
                        "Szint": int(req.get("level", 0)),
                        "%": int(req.get("%", 0)),
                    })
        except Exception as e:
            print("Error exporting selected skills:", e)
        return skills
    
    def _get_db_path(self, db_type: str) -> str:
        """Get database path for given type ('class' or 'skill')."""
        if db_type == 'class':
            return os.path.join(self.BASE_DIR, 'data', 'Class', 'class_data.db')
        return os.path.join(self.BASE_DIR, 'data', 'skills', 'skills_data.db')
    
    def _get_spec_id(self, data: dict) -> str | None:
        """Extract specialization ID from character data."""
        spec_name = data.get("Specializáció", "Nincs")
        if spec_name == "Nincs":
            return None
        spec_data = self.get_spec_data() or {}
        info = spec_data.get(spec_name)
        return info.get("specialisation_id") if info else None
    
    def _fetch_class_skills(self, conn, class_id: str, spec_id: str | None):
        """Fetch class skills from database, optionally including specialization skills."""
        query = """
            SELECT skill_id, class_level, skill_level, skill_percent, specialisation_id
            FROM class_skills 
            WHERE class_id=? AND {}
            ORDER BY class_level, skill_id
        """
        if spec_id:
            return conn.execute(query.format("(specialisation_id IS NULL OR specialisation_id=?)"), (class_id, spec_id)).fetchall()
        return conn.execute(query.format("specialisation_id IS NULL"), (class_id,)).fetchall()
    
    def _process_skill_entries(self, skill_conn, skills):
        """Process raw skills data into entries with display names and fixed skill tracking."""
        entries = []
        fixed = set()
        for skill_id, class_level, skill_level, skill_percent, from_spec in skills:
            try:
                row = skill_conn.execute(
                    "SELECT name, parameter, type, placeholder FROM skills WHERE id=?", (skill_id,)
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
        return entries, fixed

    def refresh(self):
        """Rebuild the table based on current selected class/spec and character data."""
        data = self.get_character_data() or {}
        
        # Initialize and refresh attributes display
        if hasattr(self, 'attributes_widget'):
            class_name = data.get("Kaszt")
            race = data.get("Faj", "Ember")
            age = int(data.get("Kor", 20))
            
            if class_name and race:
                try:
                    self.attributes_widget.initialize(class_name, race, age)
                except Exception as e:
                    print(f"Error initializing attributes: {e}")
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
            if self.skills_table.rowCount() == 0 else ""
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

    def _compute_taken_skills(self, exclude_instance=None):
        """Compute set of all skill IDs currently assigned (fixed + placeholder choices)."""
        taken = set(self._fixed_skill_ids)
        for ikey, chosen in self.placeholder_choices.items():
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
            # Build current skill map for prereq checks
            attributes = (self.get_character_data() or {}).get("Tulajdonságok", {})
            current_map = self._build_current_skills_map(req_override_instance=instance_key)
            for res in resolutions:
                disp = res['skill_name']
                if res['parameter']:
                    disp += f" ({res['parameter']})"
                tid = res['target_skill_id']
                if tid in taken:
                    continue
                # Prerequisite check for hypothetical selection
                # temporarily include candidate in current_map
                check_map = dict(current_map)
                check_map[tid] = {"level": req_level, "%": req_percent}
                ok, _ = self._check_prerequisites(tid, req_level, req_percent, check_map, attributes)
                if ok:
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
            with sqlite3.connect(self._get_db_path('class')) as conn:
                skills = self._fetch_class_skills(conn, class_id, spec_id)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Hiba", f"Nem sikerült betölteni a képzettségeket:\n{e}")
            return

        with sqlite3.connect(self._get_db_path('skill')) as skill_conn:
            entries, self._fixed_skill_ids = self._process_skill_entries(skill_conn, skills)
            current_map = self._build_current_skills_map_from_entries(entries)
            self._render_skill_rows(skill_conn, entries, current_map)
    
    def _calc_kp_cost(self, skill_conn, concrete_skill_id: str, req_level: int | None, req_percent: int | None) -> str:
        """Calculate KP cost for a concrete skill at given level/percent."""
        srow = skill_conn.execute("SELECT type FROM skills WHERE id=?", (concrete_skill_id,)).fetchone()
        if not srow:
            return "?"
        ctype = srow[0]
        if ctype == 1 and req_level:
            crow = skill_conn.execute(
                "SELECT kp_cost FROM skill_level_costs WHERE skill_id=? AND level=?",
                (concrete_skill_id, req_level)
            ).fetchone()
            return str(crow[0]) if crow else "?"
        elif ctype == 2 and req_percent:
            crow = skill_conn.execute(
                "SELECT kp_per_3percent FROM skill_percent_costs WHERE skill_id=?", (concrete_skill_id,)
            ).fetchone()
            return str((req_percent // 3) * crow[0]) if crow else "?"
        return "?"
    
    def _render_skill_rows(self, skill_conn, entries, current_map):
        """Render skill entries into table rows with placeholders and prerequisites."""
        attributes = (self.get_character_data() or {}).get("Tulajdonságok", {})
        
        for (skill_id, class_level, req_level, req_percent, from_spec, is_placeholder, display_name) in entries:
            try:
                row = self.skills_table.rowCount()
                self.skills_table.insertRow(row)
                self.skills_table.setItem(row, 1, QtWidgets.QTableWidgetItem(str(req_level) if req_level else "-"))
                self.skills_table.setItem(row, 2, QtWidgets.QTableWidgetItem(str(req_percent) if req_percent else "-"))
                kp_cost = self._calc_kp_cost(skill_conn, skill_id, req_level, req_percent) if is_placeholder != 1 else "?"
                self.skills_table.setItem(row, 3, QtWidgets.QTableWidgetItem(str(kp_cost)))
                source = "Specializáció" if from_spec else "Alap kaszt"
                self.skills_table.setItem(row, 4, QtWidgets.QTableWidgetItem(source))

                if is_placeholder == 1:
                    self._render_placeholder_row(skill_conn, row, skill_id, class_level, req_level, req_percent, from_spec, display_name, attributes)
                else:
                    self._render_fixed_skill_row(row, skill_id, req_level, req_percent, display_name, current_map, attributes)
            except Exception as e:
                print(f"Error rendering skill row {skill_id}: {e}")
    
    def _render_placeholder_row(self, skill_conn, row, skill_id, class_level, req_level, req_percent, from_spec, display_name, attributes):
        """Render a placeholder skill row with combo box selector."""
        base_key = (skill_id, int(class_level or 0), int(req_level or 0), int(req_percent or 0), bool(from_spec))
        occur = self._placeholder_row_counters.get(base_key, 0)
        self._placeholder_row_counters[base_key] = occur + 1
        instance_key = (*base_key, occur)

        combo = QtWidgets.QComboBox()
        combo.setEditable(True)
        combo.lineEdit().setPlaceholderText(f"{display_name} — válassz feloldást")
        combo.addItem("-- válassz --", None)
        
        resolutions = self.placeholder_mgr.get_resolutions(skill_id)
        taken = self._compute_taken_skills(exclude_instance=instance_key)
        map_excl = self._build_current_skills_map(req_override_instance=instance_key)
        
        for res in resolutions:
            disp = res['skill_name']
            if res['parameter']:
                disp += f" ({res['parameter']})"
            tid = res['target_skill_id']
            if tid in taken:
                continue
            # Prereq check for hypothetical selection
            temp_map = dict(map_excl)
            temp_map[tid] = {"level": int(req_level or 0), "%": int(req_percent or 0)}
            ok, _ = self._check_prerequisites(tid, int(req_level or 0), int(req_percent or 0), temp_map, attributes)
            if ok:
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
                self.skills_table.item(row, 3).setText(self._calc_kp_cost(skill_conn, chosen, req_level, req_percent))
            else:
                combo.setCurrentIndex(0)

        self._placeholder_combos[instance_key] = combo
        self.skills_table.setCellWidget(row, 0, combo)
    
    def _render_fixed_skill_row(self, row, skill_id, req_level, req_percent, display_name, current_map, attributes):
        """Render a fixed (non-placeholder) skill row with prerequisite check."""
        name_item = QtWidgets.QTableWidgetItem(display_name)
        self.skills_table.setItem(row, 0, name_item)
        
        ok, reasons = self._check_prerequisites(skill_id, int(req_level or 0), int(req_percent or 0), current_map, attributes)
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
        
        instance_key = combo.property('instance_key')
        row = combo.property('row')
        chosen = combo.currentData()
        
        if not instance_key:
            return
        
        # Update placeholder choices
        if chosen:
            self.placeholder_choices[instance_key] = chosen
        elif instance_key in self.placeholder_choices:
            del self.placeholder_choices[instance_key]
        
        # Update KP cost cell
        if isinstance(row, int) and 0 <= row < self.skills_table.rowCount():
            if chosen:
                req_level = int(combo.property('skill_level') or 0)
                req_percent = int(combo.property('skill_percent') or 0)
                try:
                    with sqlite3.connect(self._get_db_path('skill')) as sconn:
                        cost = self._calc_kp_cost(sconn, chosen, req_level, req_percent)
                        self.skills_table.item(row, 3).setText(cost)
                except Exception as e:
                    print("Error updating KP cost:", e)
            else:
                self.skills_table.item(row, 3).setText("?")
        
        # Refresh combos to enforce uniqueness
        self._refresh_placeholder_combos()

    def _build_current_skills_map_from_entries(self, entries):
        """Construct a map of concrete skills -> assigned level/percent from fixed skills
        and currently selected placeholder resolutions.
        """
        current_map = {}
        counters = {}
        for (skill_id, class_level, req_level, req_percent, from_spec, is_placeholder, _display_name) in entries:
            if is_placeholder == 1:
                base_key = (skill_id, int(class_level or 0), int(req_level or 0), int(req_percent or 0), bool(from_spec))
                occur = counters.get(base_key, 0)
                counters[base_key] = occur + 1
                instance_key = (*base_key, occur)
                chosen = self.placeholder_choices.get(instance_key)
                if chosen:
                    current_map[chosen] = {"level": int(req_level or 0), "%": int(req_percent or 0)}
            else:
                current_map[skill_id] = {"level": int(req_level or 0), "%": int(req_percent or 0)}
        return current_map

    def _build_current_skills_map(self, req_override_instance=None):
        """Build map based on current table/choices, excluding a specific instance if provided."""
        current_map = {}
        
        try:
            with sqlite3.connect(self._get_db_path('skill')) as sconn:
                for row in range(self.skills_table.rowCount()):
                    name_widget = self.skills_table.cellWidget(row, 0)
                    if name_widget is None:
                        name_item = self.skills_table.item(row, 0)
                        if not name_item:
                            continue
                        display = name_item.text()
                        name, param = self._parse_skill_display(display)
                        res = sconn.execute("SELECT id FROM skills WHERE name=? AND IFNULL(parameter,'')=?", (name, param)).fetchone()
                        if not res:
                            continue
                        sid = res[0]
                        lvl_item = self.skills_table.item(row, 1)
                        pct_item = self.skills_table.item(row, 2)
                        lvl = int(lvl_item.text()) if lvl_item and lvl_item.text().isdigit() else 0
                        pct = int(pct_item.text()) if pct_item and pct_item.text().isdigit() else 0
                        current_map[sid] = {"level": lvl, "%": pct}
        except Exception as e:
            print("Error building current skills map:", e)
        
        # Add placeholder choices
        for ikey, chosen in self.placeholder_choices.items():
            if req_override_instance is not None and ikey == req_override_instance:
                continue
            _, _class_level, req_level, req_percent, _from_spec, _occ = ikey
            current_map[chosen] = {"level": int(req_level or 0), "%": int(req_percent or 0)}
        return current_map
    
    def _parse_skill_display(self, display: str) -> tuple[str, str]:
        """Parse skill display text into (name, parameter) tuple."""
        if "(" in display and display.endswith(")"):
            try:
                base, p = display.rsplit("(", 1)
                return base.strip(), p[:-1].strip()
            except Exception:
                pass
        return display, ""

    def _check_prerequisites(self, skill_id: str, req_level: int, req_percent: int, current_skills: dict, attributes: dict):
        """Check attribute and skill prerequisites for a concrete skill at a given target level/percent.
        Returns (ok: bool, reasons: list[str]) listing unmet requirements.
        """
        reasons = []
        try:
            with sqlite3.connect(self._get_db_path('skill')) as sconn:
                max_check_level = max(1, int(req_level or 0))
                # Attributes
                rows = sconn.execute(
                    "SELECT attribute, min_value, level FROM skill_prerequisites_attributes WHERE skill_id=? ORDER BY level",
                    (skill_id,)
                ).fetchall()
                for attr, min_val, lvl in rows:
                    if lvl and int(lvl) > max_check_level:
                        continue
                    current_val = attributes.get(attr, None)
                    if current_val is None or int(current_val) < int(min_val):
                        reasons.append(f"Képesség: {attr} {min_val}+ (most: {current_val if current_val is not None else '-'})")
                # Skills
                srows = sconn.execute(
                    "SELECT required_skill_id, min_level, level FROM skill_prerequisites_skills WHERE skill_id=? ORDER BY level",
                    (skill_id,)
                ).fetchall()
                for req_id, min_lvl, lvl in srows:
                    if lvl and int(lvl) > max_check_level:
                        continue
                    # Determine required skill type
                    trow = sconn.execute("SELECT type FROM skills WHERE id=?", (req_id,)).fetchone()
                    req_type = trow[0] if trow else 1
                    have = current_skills.get(req_id)
                    if not have:
                        # try also accept if skill_id equals requirement and requested level itself satisfies? avoid circular; treat as missing
                        reasons.append(self._format_skill_req(req_id, min_lvl, sconn))
                    else:
                        if req_type == 1:
                            if int(have.get("level", 0)) < int(min_lvl or 0):
                                reasons.append(self._format_skill_req(req_id, min_lvl, sconn, have.get("level")))
                        else:
                            # percent-based: interpret min_level as minimum percent
                            if int(have.get("%", 0)) < int(min_lvl or 0):
                                reasons.append(self._format_skill_req(req_id, min_lvl, sconn, have.get("%"), percent=True))
        except Exception as e:
            print("Prereq check error:", e)
        return (len(reasons) == 0, reasons)

    def _format_skill_req(self, skill_id, min_lvl, conn, have_val=None, percent: bool=False):
        name_row = conn.execute("SELECT name, parameter FROM skills WHERE id=?", (skill_id,)).fetchone()
        if name_row:
            name, param = name_row
            base = f"{name}{f' ({param})' if param else ''}"
        else:
            base = str(skill_id)
        if percent:
            return f"Képzettség: {base} {int(min_lvl)}%+ (most: {have_val if have_val is not None else '-'}%)"
        else:
            return f"Képzettség: {base} {int(min_lvl)}. szint (most: {have_val if have_val is not None else '-'.strip()})"

