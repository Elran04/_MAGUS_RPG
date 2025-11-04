"""
Class Editor Actions
Handles all action operations (load, save, add/delete spec, equipment, description file handling)
"""

import json
import os
import subprocess
import sys

from config.paths import (
    ARMOR_JSON,
    CLASSES_DESCRIPTIONS_DIR,
    GENERAL_EQUIPMENT_JSON,
    WEAPONS_SHIELDS_JSON,
)
from PySide6 import QtCore, QtWidgets

from .class_editor_constants import EQUIPMENT_TYPES


class ClassEditorActions:
    """Handles all class editor actions"""

    def __init__(self, parent_editor):
        """
        Initialize actions handler

        Args:
            parent_editor: Reference to parent ClassEditorQt instance
        """
        self.parent = parent_editor
        self.equipment_cache = {}  # Cache for equipment data

    def _load_equipment_data(self, equipment_type):
        """
        Load equipment data from JSON files

        Args:
            equipment_type: One of 'armor', 'weaponandshield', 'general'

        Returns:
            List of equipment items with id and name
        """
        if equipment_type in self.equipment_cache:
            return self.equipment_cache[equipment_type]

        # Map equipment types to JSON files (centralized paths)
        type_to_file = {
            "armor": ARMOR_JSON,
            "weaponandshield": WEAPONS_SHIELDS_JSON,
            "general": GENERAL_EQUIPMENT_JSON,
        }

        path_obj = type_to_file.get(equipment_type)
        if not path_obj:
            return []

        json_path = str(path_obj)

        try:
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)
                # Extract id and name pairs
                items = []
                for item in data:
                    item_id = item.get("id", "")
                    item_name = item.get("name", "")
                    if item_id:
                        items.append(
                            {
                                "id": item_id,
                                "name": item_name,
                                "display": f"{item_id} - {item_name}",
                            }
                        )
                self.equipment_cache[equipment_type] = items
                return items
        except (json.JSONDecodeError, OSError, KeyError) as e:
            print(f"Error loading equipment data from {json_path}: {e}")
            return []

    def load_details(self):
        """Load class/spec details into UI"""
        # Load class-level details
        details = self.parent.class_db.get_class_details(self.parent.current_class_id)
        tabs = self.parent.tabs

        # Names
        tabs.class_name_edit.blockSignals(True)
        tabs.spec_name_edit.blockSignals(True)
        tabs.spec_desc_edit.blockSignals(True)

        tabs.class_name_edit.setText(details["name"] or "")

        # Show/hide fields depending on selection (class vs spec)
        is_spec = self.parent.current_spec_id is not None
        tabs.class_name_edit.setEnabled(True)
        tabs.spec_name_edit.setEnabled(is_spec)

        # For specs, the description filename is auto-generated and read-only
        if is_spec:
            tabs.desc_label.setText("Spec. leírás fájl (automatikus):")
            tabs.spec_desc_edit.setEnabled(False)
        else:
            tabs.desc_label.setText("Leírás fájl:")
            tabs.spec_desc_edit.setEnabled(True)

        # Load spec fields
        if is_spec:
            # Find spec row
            specs = self.parent.class_db.list_specialisations(self.parent.current_class_id)
            row = next(
                (s for s in specs if s["specialisation_id"] == self.parent.current_spec_id), None
            )
            tabs.spec_name_edit.setText(row["specialisation_name"] if row else "")
            # Auto-generate description filename from spec id if missing; always show generated (read-only)
            generated = f"{self.parent.current_spec_id}.md" if self.parent.current_spec_id else ""
            tabs.spec_desc_edit.setText(
                row["specialisation_description"]
                if row and row.get("specialisation_description")
                else generated
            )
        else:
            tabs.spec_name_edit.setText("")
            # Base class: load description file name from classes table
            tabs.spec_desc_edit.setText(details.get("class_description_file") or "")

        tabs.class_name_edit.blockSignals(False)
        tabs.spec_name_edit.blockSignals(False)
        tabs.spec_desc_edit.blockSignals(False)

        # Stats
        tabs.stats_table.setRowCount(len(details["stats"]))
        for i, stat_row in enumerate(details["stats"]):
            stat = stat_row[0]
            minv = stat_row[1]
            maxv = stat_row[2]
            double_chance = stat_row[3] if stat_row[3] in (0, 1) else 0
            tabs.stats_table.setItem(i, 0, QtWidgets.QTableWidgetItem(stat))
            tabs.stats_table.setItem(i, 1, QtWidgets.QTableWidgetItem(str(minv)))
            tabs.stats_table.setItem(i, 2, QtWidgets.QTableWidgetItem(str(maxv)))
            chk = QtWidgets.QTableWidgetItem()
            chk.setFlags(QtCore.Qt.ItemFlag.ItemIsUserCheckable | QtCore.Qt.ItemFlag.ItemIsEnabled)
            chk.setCheckState(
                QtCore.Qt.CheckState.Checked
                if double_chance == 1
                else QtCore.Qt.CheckState.Unchecked
            )
            tabs.stats_table.setItem(i, 3, chk)

        # Combat stats (pretty 2-column table: label + value)
        with self.parent.class_db.get_connection() as conn:
            c = conn.cursor()
            c.execute("PRAGMA table_info(combat_stats)")
            columns = [row[1] for row in c.fetchall()]
            # Load row
            c.execute(
                "SELECT * FROM combat_stats WHERE class_id = ?", (self.parent.current_class_id,)
            )
            row = c.fetchone()

        # Build rows excluding class_id
        if row and columns:
            # Map column name to value
            col_vals = list(zip(columns, row, strict=True))
            pairs = [(col, val) for col, val in col_vals if col != "class_id"]
            tabs.combat_table.setRowCount(len(pairs))
            for i, (col, val) in enumerate(pairs):
                pretty = col.replace("_", " ").title()
                key_item = QtWidgets.QTableWidgetItem(pretty)
                # Store real column name for saving
                key_item.setData(QtCore.Qt.ItemDataRole.UserRole, col)
                key_item.setFlags(QtCore.Qt.ItemFlag.ItemIsEnabled)
                tabs.combat_table.setItem(i, 0, key_item)
                val_item = QtWidgets.QTableWidgetItem(str(val))
                val_item.setTextAlignment(
                    QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter
                )
                tabs.combat_table.setItem(i, 1, val_item)
        else:
            tabs.combat_table.setRowCount(0)

        # XP requirements
        levels = details["level_requirements"] or []
        tabs.xp_table.setRowCount(len(levels))
        for i, (lvl, xp) in enumerate(levels):
            tabs.xp_table.setItem(i, 0, QtWidgets.QTableWidgetItem(str(lvl)))
            tabs.xp_table.setItem(i, 1, QtWidgets.QTableWidgetItem(str(xp)))
        extra_xp = details["extra_xp"] if details["extra_xp"] else 0
        tabs.extra_xp_edit.setValue(extra_xp)

        # Starting equipment for current selection
        self.reload_equipment_table()

        # Load assigned skills for current selection
        tabs.populate_assigned_skills(self.parent.current_class_id, self.parent.current_spec_id)

        # Load description file content
        self.load_description_file()

    def save_current(self):
        """Save current class/spec data"""
        tabs = self.parent.tabs

        # Save class name
        if self.parent.current_class_id:
            new_name = tabs.class_name_edit.text()
            if new_name:
                self.parent.class_db.update_class_name(self.parent.current_class_id, new_name)

        # Save stats
        with self.parent.class_db.get_connection() as conn:
            c = conn.cursor()
            for row in range(tabs.stats_table.rowCount()):
                stat_name = tabs.stats_table.item(row, 0).text()
                min_value = int(tabs.stats_table.item(row, 1).text())
                max_value = int(tabs.stats_table.item(row, 2).text())
                double_chance = (
                    1
                    if tabs.stats_table.item(row, 3).checkState() == QtCore.Qt.CheckState.Checked
                    else 0
                )
                c.execute(
                    "UPDATE stats SET min_value = ?, max_value = ?, double_chance = ? WHERE class_id = ? AND stat_name = ?",
                    (min_value, max_value, double_chance, self.parent.current_class_id, stat_name),
                )

            # Save XP table
            for row in range(tabs.xp_table.rowCount()):
                lvl = int(tabs.xp_table.item(row, 0).text())
                xp = int(tabs.xp_table.item(row, 1).text())
                c.execute(
                    "UPDATE level_requirements SET xp = ? WHERE class_id = ? AND level = ?",
                    (xp, self.parent.current_class_id, lvl),
                )

            # Save extra XP
            extra_xp = tabs.extra_xp_edit.value()
            c.execute(
                "UPDATE further_level_requirements SET extra_xp = ? WHERE class_id = ?",
                (extra_xp, self.parent.current_class_id),
            )

            # Save combat stats from pretty table rows (key label stores real column name in UserRole)
            if tabs.combat_table.rowCount() > 0:
                set_parts = []
                set_vals = []
                for r in range(tabs.combat_table.rowCount()):
                    key_item = tabs.combat_table.item(r, 0)
                    val_item = tabs.combat_table.item(r, 1)
                    if not key_item:
                        continue
                    col_name = key_item.data(QtCore.Qt.ItemDataRole.UserRole)
                    if not col_name:
                        continue
                    val_text = val_item.text() if val_item else None
                    set_parts.append(f"{col_name} = ?")
                    set_vals.append(val_text)
                if set_parts:
                    set_sql = ", ".join(set_parts)
                    set_vals.append(self.parent.current_class_id)
                    c.execute(
                        f"UPDATE combat_stats SET {set_sql} WHERE class_id = ?", tuple(set_vals)
                    )
            conn.commit()

        # Save spec fields
        if self.parent.current_spec_id is not None:
            # Autogenerate description filename from spec ID
            spec_desc = f"{self.parent.current_spec_id}.md"
            self.parent.class_db.upsert_specialisation(
                self.parent.current_class_id,
                self.parent.current_spec_id,
                tabs.spec_name_edit.text(),
                spec_desc,
            )
        else:
            # Save base class description filename
            self.parent.class_db.update_class_description_file(
                self.parent.current_class_id, tabs.spec_desc_edit.text().strip() or None
            )

        QtWidgets.QMessageBox.information(self.parent, "Mentés", "Adatok elmentve.")
        self.parent.class_list_panel.populate(self.parent.class_db)
        # Reselect
        self.parent.class_list_panel.reselect_current(
            self.parent.current_class_id, self.parent.current_spec_id
        )

    def reload_equipment_table(self):
        """Reload the equipment table for current class/spec"""
        tabs = self.parent.tabs
        rows = self.parent.class_db.list_starting_equipment(
            self.parent.current_class_id, self.parent.current_spec_id
        )
        tabs.eq_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            tabs.eq_table.setItem(i, 0, QtWidgets.QTableWidgetItem(str(r["entry_id"])))
            tabs.eq_table.setItem(i, 1, QtWidgets.QTableWidgetItem(r["item_type"]))

            item_id = r.get("item_id") or ""
            tabs.eq_table.setItem(i, 2, QtWidgets.QTableWidgetItem(item_id))

            # Resolve item name from equipment data
            item_name = ""
            if item_id and r["item_type"] != "currency":
                equipment_items = self._load_equipment_data(r["item_type"])
                for item in equipment_items:
                    if item["id"] == item_id:
                        item_name = item["name"]
                        break

            tabs.eq_table.setItem(i, 3, QtWidgets.QTableWidgetItem(item_name))
            tabs.eq_table.setItem(
                i,
                4,
                QtWidgets.QTableWidgetItem(
                    str(r.get("min_currency") if r.get("min_currency") is not None else "")
                ),
            )
            tabs.eq_table.setItem(
                i,
                5,
                QtWidgets.QTableWidgetItem(
                    str(r.get("max_currency") if r.get("max_currency") is not None else "")
                ),
            )

    def add_specialisation(self):
        """Add a new specialisation"""
        # Must have a class selected
        if not self.parent.current_class_id:
            return

        dlg = QtWidgets.QDialog(self.parent)
        dlg.setWindowTitle("Új specializáció")
        form = QtWidgets.QFormLayout(dlg)
        inp_id = QtWidgets.QLineEdit()
        inp_name = QtWidgets.QLineEdit()
        form.addRow("Azonosító:", inp_id)
        form.addRow("Név:", inp_name)
        hint = QtWidgets.QLabel(
            "A leírás fájl neve automatikusan azonosítóból készül (pl. spec.md)"
        )
        hint.setWordWrap(True)
        form.addRow(hint)
        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        form.addRow(btns)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)

        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            sid = inp_id.text().strip()
            name = inp_name.text().strip()
            if sid and name:
                desc = f"{sid}.md"
                self.parent.class_db.upsert_specialisation(
                    self.parent.current_class_id, sid, name, desc
                )
                self.parent.current_spec_id = sid
                self.parent.class_list_panel.populate(self.parent.class_db)
                self.parent.class_list_panel.reselect_current(
                    self.parent.current_class_id, self.parent.current_spec_id
                )

    def delete_specialisation(self):
        """Delete the current specialisation"""
        if self.parent.current_spec_id is None:
            return

        reply = QtWidgets.QMessageBox.question(
            self.parent,
            "Megerősítés",
            "Biztosan törlöd a specializációt?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
        )

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            self.parent.class_db.delete_specialisation(
                self.parent.current_class_id, self.parent.current_spec_id
            )
            self.parent.current_spec_id = None
            self.parent.class_list_panel.populate(self.parent.class_db)
            self.parent.class_list_panel.reselect_current(
                self.parent.current_class_id, self.parent.current_spec_id
            )

    def add_currency_row(self):
        """Add a currency equipment row"""
        if not self.parent.current_class_id:
            return

        dlg = QtWidgets.QDialog(self.parent)
        dlg.setWindowTitle("Pénz hozzáadása")
        form = QtWidgets.QFormLayout(dlg)
        inp_min = QtWidgets.QSpinBox()
        inp_min.setMaximum(999999)
        inp_max = QtWidgets.QSpinBox()
        inp_max.setMaximum(999999)
        form.addRow("Min:", inp_min)
        form.addRow("Max:", inp_max)
        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        form.addRow(btns)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)

        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self.parent.class_db.add_starting_equipment_currency(
                self.parent.current_class_id,
                self.parent.current_spec_id,
                inp_min.value(),
                inp_max.value(),
            )
            self.reload_equipment_table()

    def add_item_row(self):
        """Add an item equipment row with autocomplete"""
        if not self.parent.current_class_id:
            return

        dlg = QtWidgets.QDialog(self.parent)
        dlg.setWindowTitle("Tárgy hozzáadása")
        dlg.resize(500, 150)
        form = QtWidgets.QFormLayout(dlg)

        # Equipment type selection
        cb_type = QtWidgets.QComboBox()
        cb_type.addItems(EQUIPMENT_TYPES)
        form.addRow("Típus:", cb_type)

        # Item ID input with autocomplete
        inp_item = QtWidgets.QLineEdit()
        inp_item.setPlaceholderText("Kezdd el gépelni az azonosítót vagy nevet...")

        # Completer setup
        completer = QtWidgets.QCompleter()
        completer.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(QtCore.Qt.MatchFlag.MatchContains)
        inp_item.setCompleter(completer)

        # Function to update completer when type changes
        def update_completer():
            selected_type = cb_type.currentText()
            equipment_items = self._load_equipment_data(selected_type)

            # Create list of display strings and ID mapping
            display_items = [item["display"] for item in equipment_items]
            completer.setModel(QtCore.QStringListModel(display_items))

        # Connect type change to update completer
        cb_type.currentTextChanged.connect(update_completer)

        # Initialize completer with first type
        update_completer()

        form.addRow("Tárgy ID:", inp_item)

        # Help text
        help_label = QtWidgets.QLabel(
            "Tipp: Válaszd ki a típust, majd kezdd el gépelni az azonosítót vagy nevet."
        )
        help_label.setWordWrap(True)
        help_label.setStyleSheet("color: #666; font-size: 9pt;")
        form.addRow(help_label)

        # Buttons
        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        form.addRow(btns)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)

        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            # Extract just the ID from the input (before the " - " separator if present)
            item_text = inp_item.text().strip()
            item_id = item_text.split(" - ")[0].strip() if " - " in item_text else item_text

            if item_id:
                self.parent.class_db.add_starting_equipment_item(
                    self.parent.current_class_id,
                    self.parent.current_spec_id,
                    cb_type.currentText(),
                    item_id,
                )
                self.reload_equipment_table()

    def delete_equipment_row(self):
        """Delete the selected equipment row"""
        tabs = self.parent.tabs
        row = tabs.eq_table.currentRow()
        if row < 0:
            return

        entry_id_item = tabs.eq_table.item(row, 0)
        if not entry_id_item:
            return

        entry_id = int(entry_id_item.text())
        self.parent.class_db.delete_starting_equipment(entry_id)
        self.reload_equipment_table()

    def get_description_filename(self):
        """Get the description filename for the current class/spec"""
        tabs = self.parent.tabs
        if self.parent.current_spec_id is not None:
            # Specialisation: auto-generated from spec ID
            return f"{self.parent.current_spec_id}.md"
        else:
            # Base class: from classes table or spec_desc_edit field
            return tabs.spec_desc_edit.text().strip() or f"{self.parent.current_class_id}.md"

    def get_description_full_path(self):
        """Return absolute path to the current class/spec description file under data/classes/descriptions"""
        desc_file = self.get_description_filename()
        if not desc_file:
            return None
        return os.path.join(str(CLASSES_DESCRIPTIONS_DIR), desc_file)

    def load_description_file(self):
        """Load description .md content into the editor area"""
        tabs = self.parent.tabs
        desc_filename = self.get_description_filename()
        tabs.desc_filename_label.setText(desc_filename if desc_filename else "(nincs fájl)")

        path = self.get_description_full_path()
        if not path:
            tabs.desc_text_editor.clear()
            return

        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    tabs.desc_text_editor.setPlainText(f.read())
            except (OSError, UnicodeDecodeError) as e:
                tabs.desc_text_editor.clear()
                QtWidgets.QMessageBox.critical(
                    self.parent, "Hiba", f"Nem sikerült beolvasni a leírást:\n{e}"
                )
        else:
            tabs.desc_text_editor.clear()
            tabs.desc_text_editor.setPlaceholderText(
                f"A fájl ({desc_filename}) még nem létezik. Mentéskor létrehozzuk."
            )

    def save_description_file(self):
        """Save the editor content to the description .md file (create if missing)"""
        tabs = self.parent.tabs
        if not self.parent.current_class_id:
            QtWidgets.QMessageBox.warning(self.parent, "Figyelem", "Nincs kiválasztott kaszt!")
            return

        path = self.get_description_full_path()
        if not path:
            QtWidgets.QMessageBox.warning(self.parent, "Figyelem", "Nincs leírás fájlnév megadva!")
            return

        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(tabs.desc_text_editor.toPlainText())
            QtWidgets.QMessageBox.information(
                self.parent, "Siker", f"Leírás elmentve: {self.get_description_filename()}"
            )
        except OSError as e:
            QtWidgets.QMessageBox.critical(
                self.parent, "Hiba", f"Nem sikerült menteni a leírást:\n{e}"
            )

    def open_description_file(self):
        """Open the description markdown file in the default external editor"""
        path = self.get_description_full_path()
        if not path:
            QtWidgets.QMessageBox.information(self.parent, "Info", "Nincs leírás fájlnév megadva.")
            return

        if not os.path.exists(path):
            QtWidgets.QMessageBox.warning(
                self.parent,
                "Hiba",
                f"A leírás fájl nem található:\n{path}\n\nMentsd el először a leírást!",
            )
            return

        # Open with default editor
        try:
            if sys.platform.startswith("win"):
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.call(["open", path])
            else:
                subprocess.call(["xdg-open", path])
        except (OSError, subprocess.SubprocessError) as e:
            QtWidgets.QMessageBox.critical(
                self.parent, "Hiba", f"Nem sikerült megnyitni a fájlt:\n{e}"
            )
