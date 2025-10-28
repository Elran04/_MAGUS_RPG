from PySide6 import QtWidgets, QtCore
from PySide6.QtGui import QFont
import sys
import os
import subprocess
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.class_db_manager import ClassDBManager

class ClassEditorQt(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kaszt szerkesztő")
        self.resize(1000, 700)
        # Standard ablakvezérlők (min/max/close)
        self.setWindowFlags(
            QtCore.Qt.WindowType.Window
            | QtCore.Qt.WindowType.WindowMinimizeButtonHint
            | QtCore.Qt.WindowType.WindowMaximizeButtonHint
            | QtCore.Qt.WindowType.WindowCloseButtonHint
        )
        self.class_db = ClassDBManager()
        # Ensure required tables exist (safe no-ops if already exist)
        try:
            self.class_db.ensure_specialisations_table()
        except Exception:
            pass
        try:
            self.class_db.ensure_starting_equipment_table()
        except Exception:
            pass
        try:
            self.class_db.ensure_classes_description_column()
        except Exception:
            pass
        self.current_class_id = None
        self.current_spec_id = None
        self.init_ui()
        self.load_tree()

    def init_ui(self):
        root = QtWidgets.QVBoxLayout(self)
        # Top action bar
        actions = QtWidgets.QHBoxLayout()
        self.btn_add_spec = QtWidgets.QPushButton("Specializáció hozzáadása")
        self.btn_del_spec = QtWidgets.QPushButton("Specializáció törlése")
        self.btn_save_all = QtWidgets.QPushButton("Mentés")
        actions.addWidget(self.btn_add_spec)
        actions.addWidget(self.btn_del_spec)
        actions.addStretch()
        actions.addWidget(self.btn_save_all)
        root.addLayout(actions)

        # Splitter with tree (left) and editor (right)
        splitter = QtWidgets.QSplitter()
        splitter.setOrientation(QtCore.Qt.Orientation.Horizontal)
        root.addWidget(splitter, stretch=1)

        # Left: class/spec tree
        left = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left)
        left_layout.addWidget(QtWidgets.QLabel("Kasztok és specializációk:"))
        self.class_tree = QtWidgets.QTreeWidget()
        # Only show the name column; IDs are stored in UserRole
        self.class_tree.setHeaderLabels(["Név"])
        self.class_tree.header().setStretchLastSection(True)
        self.class_tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        left_layout.addWidget(self.class_tree)
        splitter.addWidget(left)

        # Right: tabbed editor
        right = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right)
        self.tabs = QtWidgets.QTabWidget()
        right_layout.addWidget(self.tabs)
        splitter.addWidget(right)

        # Set initial splitter sizes: 30% tree, 70% tabs
        splitter.setSizes([300, 700])

        # Tab: Attributes (class name, stats)
        self.tab_attributes = QtWidgets.QWidget()
        attr_layout = QtWidgets.QFormLayout(self.tab_attributes)
        # Class vs Spec name fields
        self.class_name_edit = QtWidgets.QLineEdit()
        self.spec_name_edit = QtWidgets.QLineEdit()
        attr_layout.addRow("Kaszt név:", self.class_name_edit)
        attr_layout.addRow("Spec. név:", self.spec_name_edit)
        # Stats table with double_chance
        self.stats_table = QtWidgets.QTableWidget()
        self.stats_table.setColumnCount(4)
        self.stats_table.setHorizontalHeaderLabels(["Tulajdonság", "Min", "Max", "Duplázási esély"])
        self.stats_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.stats_table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.stats_table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        self.stats_table.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        attr_layout.addRow("Tulajdonságok:", self.stats_table)
        self.tabs.addTab(self.tab_attributes, "Tulajdonságok")

        # Tab: Combat stats
        self.tab_combat = QtWidgets.QWidget()
        cs_layout = QtWidgets.QVBoxLayout(self.tab_combat)
        self.combat_table = QtWidgets.QTableWidget()
        self.combat_table.setColumnCount(2)
        self.combat_table.setHorizontalHeaderLabels(["Mutató", "Érték"])
        self.combat_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.combat_table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        cs_layout.addWidget(self.combat_table)
        self.tabs.addTab(self.tab_combat, "Harci statok")

        # Tab: Experience requirements
        self.tab_xp = QtWidgets.QWidget()
        xp_layout = QtWidgets.QFormLayout(self.tab_xp)
        self.xp_table = QtWidgets.QTableWidget()
        self.xp_table.setColumnCount(2)
        self.xp_table.setHorizontalHeaderLabels(["Szint", "XP"])
        self.xp_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.xp_table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        xp_layout.addRow("Követelmények:", self.xp_table)
        self.extra_xp_edit = QtWidgets.QSpinBox()
        self.extra_xp_edit.setMaximum(999999)
        xp_layout.addRow("További szintenkénti XP:", self.extra_xp_edit)
        self.tabs.addTab(self.tab_xp, "Tapasztalat")

        # Tab: Starting equipment editor
        self.tab_equipment = QtWidgets.QWidget()
        eq_layout = QtWidgets.QVBoxLayout(self.tab_equipment)
        btn_row = QtWidgets.QHBoxLayout()
        self.btn_add_currency = QtWidgets.QPushButton("Pénz hozzáadása")
        self.btn_add_item = QtWidgets.QPushButton("Tárgy hozzáadása")
        self.btn_del_equipment = QtWidgets.QPushButton("Kijelölt törlése")
        btn_row.addWidget(self.btn_add_currency)
        btn_row.addWidget(self.btn_add_item)
        btn_row.addWidget(self.btn_del_equipment)
        btn_row.addStretch()
        eq_layout.addLayout(btn_row)
        self.eq_table = QtWidgets.QTableWidget()
        self.eq_table.setColumnCount(5)
        self.eq_table.setHorizontalHeaderLabels(["entry_id", "Típus", "Tárgy ID", "Min pénz", "Max pénz"])
        self.eq_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self.eq_table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.eq_table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        self.eq_table.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        self.eq_table.horizontalHeader().setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)
        self.eq_table.setColumnHidden(0, True)
        eq_layout.addWidget(self.eq_table)
        self.tabs.addTab(self.tab_equipment, "Kezdő felszerelés")

        # Tab: Description editor
        self.tab_description = QtWidgets.QWidget()
        desc_layout = QtWidgets.QVBoxLayout(self.tab_description)
        
        # Header
        header = QtWidgets.QLabel("Leírás")
        header_font = QFont()
        header_font.setPointSize(11)
        header_font.setBold(True)
        header.setFont(header_font)
        desc_layout.addWidget(header)
        
        # Info about description file
        desc_info = QtWidgets.QLabel("A kaszt/specializáció részletes leírása külső .md fájlban található.")
        desc_info.setStyleSheet("color: #666; margin: 10px 0;")
        desc_layout.addWidget(desc_info)
        
        # Description filename (base class editable; spec auto-generated, read-only)
        filename_form = QtWidgets.QFormLayout()
        self.desc_label = QtWidgets.QLabel("Leírás fájl:")
        self.spec_desc_edit = QtWidgets.QLineEdit()
        filename_form.addRow(self.desc_label, self.spec_desc_edit)
        desc_layout.addLayout(filename_form)
        
        # Current filename display (read-only indicator)
        filename_layout = QtWidgets.QHBoxLayout()
        filename_layout.addWidget(QtWidgets.QLabel("Jelenlegi fájl:"))
        self.desc_filename_label = QtWidgets.QLabel("")
        self.desc_filename_label.setStyleSheet("font-weight: bold; color: #0066cc;")
        filename_layout.addWidget(self.desc_filename_label)
        filename_layout.addStretch()
        desc_layout.addLayout(filename_layout)
        
        # Editor for markdown content
        self.desc_text_editor = QtWidgets.QTextEdit()
        self.desc_text_editor.setPlaceholderText("Itt szerkesztheted a leírás .md fájl tartalmát…")
        desc_layout.addWidget(self.desc_text_editor, stretch=1)
        
        # Action buttons
        desc_btns = QtWidgets.QHBoxLayout()
        self.btn_save_desc = QtWidgets.QPushButton("Leírás mentése (.md)")
        self.btn_save_desc.clicked.connect(self.save_description_file)
        desc_btns.addWidget(self.btn_save_desc)
        
        self.btn_open_desc = QtWidgets.QPushButton("Megnyitás külső szerkesztőben")
        self.btn_open_desc.clicked.connect(self.open_description_file)
        desc_btns.addWidget(self.btn_open_desc)
        
        desc_btns.addStretch()
        desc_layout.addLayout(desc_btns)
        
        self.tabs.addTab(self.tab_description, "Leírás")

        # Signals
        self.class_tree.currentItemChanged.connect(self.on_tree_selection_changed)
        self.btn_save_all.clicked.connect(self.save_current)
        self.btn_add_spec.clicked.connect(self.add_specialisation)
        self.btn_del_spec.clicked.connect(self.delete_specialisation)
        self.btn_add_currency.clicked.connect(self.add_currency_row)
        self.btn_add_item.clicked.connect(self.add_item_row)
        self.btn_del_equipment.clicked.connect(self.delete_equipment_row)

    def load_tree(self):
        self.class_tree.clear()
        # Sort by ID (not alphabetically)
        classes = sorted(self.class_db.list_classes(), key=lambda x: x[0])
        for cid, name in classes:
            class_item = QtWidgets.QTreeWidgetItem([name])
            class_item.setData(0, QtCore.Qt.ItemDataRole.UserRole, (cid, None))
            # Load specs
            try:
                specs = self.class_db.list_specialisations(cid)
            except Exception:
                specs = []
            for spec in specs:
                s_item = QtWidgets.QTreeWidgetItem([spec["specialisation_name"]])
                s_item.setData(0, QtCore.Qt.ItemDataRole.UserRole, (cid, spec["specialisation_id"]))
                class_item.addChild(s_item)
            class_item.setExpanded(True)
            self.class_tree.addTopLevelItem(class_item)
        # Select first if available
        if self.class_tree.topLevelItemCount() > 0:
            self.class_tree.setCurrentItem(self.class_tree.topLevelItem(0))

    def on_tree_selection_changed(self, current: QtWidgets.QTreeWidgetItem, previous):
        if not current:
            return
        data = current.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if not data:
            return
        class_id, spec_id = data
        self.current_class_id = class_id
        self.current_spec_id = spec_id
        self.load_details()

    def load_details(self):
        # Load class-level details
        details = self.class_db.get_class_details(self.current_class_id)
        # Names
        self.class_name_edit.blockSignals(True)
        self.spec_name_edit.blockSignals(True)
        self.spec_desc_edit.blockSignals(True)
        self.class_name_edit.setText(details["name"] or "")
        # Show/hide fields depending on selection (class vs spec)
        is_spec = self.current_spec_id is not None
        self.class_name_edit.setEnabled(True)
        self.spec_name_edit.setEnabled(is_spec)
        # For specs, the description filename is auto-generated and read-only
        if is_spec:
            self.desc_label.setText("Spec. leírás fájl (automatikus):")
            self.spec_desc_edit.setEnabled(False)
        else:
            self.desc_label.setText("Leírás fájl:")
            self.spec_desc_edit.setEnabled(True)
        # Load spec fields
        if is_spec:
            # find spec row
            specs = self.class_db.list_specialisations(self.current_class_id)
            row = next((s for s in specs if s["specialisation_id"] == self.current_spec_id), None)
            self.spec_name_edit.setText(row["specialisation_name"] if row else "")
            # Auto-generate description filename from spec id if missing; always show generated (read-only)
            generated = f"{self.current_spec_id}.md" if self.current_spec_id else ""
            self.spec_desc_edit.setText(row["specialisation_description"] if row and row.get("specialisation_description") else generated)
        else:
            self.spec_name_edit.setText("")
            # Base class: load description file name from classes table
            self.spec_desc_edit.setText(details.get("class_description_file") or "")
        self.class_name_edit.blockSignals(False)
        self.spec_name_edit.blockSignals(False)
        self.spec_desc_edit.blockSignals(False)
        # Stats
        self.stats_table.setRowCount(len(details["stats"]))
        for i, stat_row in enumerate(details["stats"]):
            stat = stat_row[0]
            minv = stat_row[1]
            maxv = stat_row[2]
            double_chance = stat_row[3] if stat_row[3] in (0, 1) else 0
            self.stats_table.setItem(i, 0, QtWidgets.QTableWidgetItem(stat))
            self.stats_table.setItem(i, 1, QtWidgets.QTableWidgetItem(str(minv)))
            self.stats_table.setItem(i, 2, QtWidgets.QTableWidgetItem(str(maxv)))
            chk = QtWidgets.QTableWidgetItem()
            chk.setFlags(QtCore.Qt.ItemFlag.ItemIsUserCheckable | QtCore.Qt.ItemFlag.ItemIsEnabled)
            chk.setCheckState(QtCore.Qt.CheckState.Checked if double_chance == 1 else QtCore.Qt.CheckState.Unchecked)
            self.stats_table.setItem(i, 3, chk)
        # Combat stats (pretty 2-column table: label + value)
        with self.class_db.get_connection() as conn:
            c = conn.cursor()
            c.execute("PRAGMA table_info(combat_stats)")
            columns = [row[1] for row in c.fetchall()]
            # Load row
            c.execute("SELECT * FROM combat_stats WHERE class_id = ?", (self.current_class_id,))
            row = c.fetchone()
        # Build rows excluding class_id
        if row and columns:
            # Map column name to value
            col_vals = list(zip(columns, row))
            pairs = [(col, val) for col, val in col_vals if col != "class_id"]
            self.combat_table.setRowCount(len(pairs))
            for i, (col, val) in enumerate(pairs):
                pretty = col.replace("_", " ").title()
                key_item = QtWidgets.QTableWidgetItem(pretty)
                # Store real column name for saving
                key_item.setData(QtCore.Qt.ItemDataRole.UserRole, col)
                key_item.setFlags(QtCore.Qt.ItemFlag.ItemIsEnabled)
                self.combat_table.setItem(i, 0, key_item)
                val_item = QtWidgets.QTableWidgetItem(str(val))
                val_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
                self.combat_table.setItem(i, 1, val_item)
        else:
            self.combat_table.setRowCount(0)
        # XP requirements
        levels = details["level_requirements"] or []
        self.xp_table.setRowCount(len(levels))
        for i, (lvl, xp) in enumerate(levels):
            self.xp_table.setItem(i, 0, QtWidgets.QTableWidgetItem(str(lvl)))
            self.xp_table.setItem(i, 1, QtWidgets.QTableWidgetItem(str(xp)))
        extra_xp = details["extra_xp"] if details["extra_xp"] else 0
        self.extra_xp_edit.setValue(extra_xp)
        # Starting equipment for current selection
        self.reload_equipment_table()
        # Load description file content
        self.load_description_file()

    def reload_equipment_table(self):
        rows = self.class_db.list_starting_equipment(self.current_class_id, self.current_spec_id)
        self.eq_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.eq_table.setItem(i, 0, QtWidgets.QTableWidgetItem(str(r["entry_id"])))
            self.eq_table.setItem(i, 1, QtWidgets.QTableWidgetItem(r["item_type"]))
            self.eq_table.setItem(i, 2, QtWidgets.QTableWidgetItem(r.get("item_id") or ""))
            self.eq_table.setItem(i, 3, QtWidgets.QTableWidgetItem(str(r.get("min_currency") if r.get("min_currency") is not None else "")))
            self.eq_table.setItem(i, 4, QtWidgets.QTableWidgetItem(str(r.get("max_currency") if r.get("max_currency") is not None else "")))

    def save_current(self):
        # Save class name
        if self.current_class_id:
            new_name = self.class_name_edit.text()
            if new_name:
                self.class_db.update_class_name(self.current_class_id, new_name)
        # Save stats
        with self.class_db.get_connection() as conn:
            c = conn.cursor()
            for row in range(self.stats_table.rowCount()):
                stat_name = self.stats_table.item(row, 0).text()
                min_value = int(self.stats_table.item(row, 1).text())
                max_value = int(self.stats_table.item(row, 2).text())
                double_chance = 1 if self.stats_table.item(row, 3).checkState() == QtCore.Qt.CheckState.Checked else 0
                c.execute(
                    "UPDATE stats SET min_value = ?, max_value = ?, double_chance = ? WHERE class_id = ? AND stat_name = ?",
                    (min_value, max_value, double_chance, self.current_class_id, stat_name)
                )
            # Save XP table
            for row in range(self.xp_table.rowCount()):
                lvl = int(self.xp_table.item(row, 0).text())
                xp = int(self.xp_table.item(row, 1).text())
                c.execute(
                    "UPDATE level_requirements SET xp = ? WHERE class_id = ? AND level = ?",
                    (xp, self.current_class_id, lvl)
                )
            # Save extra XP
            extra_xp = self.extra_xp_edit.value()
            c.execute(
                "UPDATE further_level_requirements SET extra_xp = ? WHERE class_id = ?",
                (extra_xp, self.current_class_id)
            )
            # Save combat stats from pretty table rows (key label stores real column name in UserRole)
            if self.combat_table.rowCount() > 0:
                set_parts = []
                set_vals = []
                for r in range(self.combat_table.rowCount()):
                    key_item = self.combat_table.item(r, 0)
                    val_item = self.combat_table.item(r, 1)
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
                    set_vals.append(self.current_class_id)
                    c.execute(f"UPDATE combat_stats SET {set_sql} WHERE class_id = ?", tuple(set_vals))
            conn.commit()
        # Save spec fields
        if self.current_spec_id is not None:
            # Autogenerate description filename from spec ID
            spec_desc = f"{self.current_spec_id}.md"
            self.class_db.upsert_specialisation(
                self.current_class_id,
                self.current_spec_id,
                self.spec_name_edit.text(),
                spec_desc,
            )
        else:
            # Save base class description filename
            self.class_db.update_class_description_file(self.current_class_id, self.spec_desc_edit.text().strip() or None)
        QtWidgets.QMessageBox.information(self, "Mentés", "Adatok elmentve.")
        self.load_tree()
        # Reselect
        self.reselect_current()

    def reselect_current(self):
        # Find and select current class/spec in tree
        root_count = self.class_tree.topLevelItemCount()
        for i in range(root_count):
            item = self.class_tree.topLevelItem(i)
            cid, _ = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            if cid == self.current_class_id:
                if self.current_spec_id is None:
                    self.class_tree.setCurrentItem(item)
                    return
                # find child
                for j in range(item.childCount()):
                    child = item.child(j)
                    cid2, sid = child.data(0, QtCore.Qt.ItemDataRole.UserRole)
                    if sid == self.current_spec_id:
                        self.class_tree.setCurrentItem(child)
                        return

    def add_specialisation(self):
        # Must have a class selected
        if not self.current_class_id:
            return
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("Új specializáció")
        form = QtWidgets.QFormLayout(dlg)
        inp_id = QtWidgets.QLineEdit()
        inp_name = QtWidgets.QLineEdit()
        form.addRow("Azonosító:", inp_id)
        form.addRow("Név:", inp_name)
        hint = QtWidgets.QLabel("A leírás fájl neve automatikusan azonosítóból készül (pl. spec.md)")
        hint.setWordWrap(True)
        form.addRow(hint)
        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        form.addRow(btns)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            sid = inp_id.text().strip()
            name = inp_name.text().strip()
            if sid and name:
                desc = f"{sid}.md"
                self.class_db.upsert_specialisation(self.current_class_id, sid, name, desc)
                self.current_spec_id = sid
                self.load_tree()
                self.reselect_current()

    def delete_specialisation(self):
        if self.current_spec_id is None:
            return
        reply = QtWidgets.QMessageBox.question(self, "Megerősítés", "Biztosan törlöd a specializációt?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            self.class_db.delete_specialisation(self.current_class_id, self.current_spec_id)
            self.current_spec_id = None
            self.load_tree()
            self.reselect_current()

    def add_currency_row(self):
        if not self.current_class_id:
            return
        # simple dialog for min/max
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("Pénz hozzáadása")
        form = QtWidgets.QFormLayout(dlg)
        inp_min = QtWidgets.QSpinBox(); inp_min.setMaximum(999999)
        inp_max = QtWidgets.QSpinBox(); inp_max.setMaximum(999999)
        form.addRow("Min:", inp_min)
        form.addRow("Max:", inp_max)
        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        form.addRow(btns)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self.class_db.add_starting_equipment_currency(self.current_class_id, self.current_spec_id, inp_min.value(), inp_max.value())
            self.reload_equipment_table()

    def add_item_row(self):
        if not self.current_class_id:
            return
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("Tárgy hozzáadása")
        form = QtWidgets.QFormLayout(dlg)
        cb_type = QtWidgets.QComboBox()
        cb_type.addItems(["armor", "weaponandshield", "general"])
        inp_item = QtWidgets.QLineEdit()
        form.addRow("Típus:", cb_type)
        form.addRow("Tárgy ID:", inp_item)
        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        form.addRow(btns)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self.class_db.add_starting_equipment_item(self.current_class_id, self.current_spec_id, cb_type.currentText(), inp_item.text().strip())
            self.reload_equipment_table()

    def delete_equipment_row(self):
        row = self.eq_table.currentRow()
        if row < 0:
            return
        entry_id_item = self.eq_table.item(row, 0)
        if not entry_id_item:
            return
        entry_id = int(entry_id_item.text())
        self.class_db.delete_starting_equipment(entry_id)
        self.reload_equipment_table()

    def get_description_filename(self):
        """Get the description filename for the current class/spec"""
        if self.current_spec_id is not None:
            # Specialisation: auto-generated from spec ID
            return f"{self.current_spec_id}.md"
        else:
            # Base class: from classes table or spec_desc_edit field
            return self.spec_desc_edit.text().strip() or f"{self.current_class_id}.md"

    def get_description_full_path(self):
        """Return absolute path to the current class/spec description file under data/Class/descriptions"""
        desc_file = self.get_description_filename()
        if not desc_file:
            return None
        # __file__ is at Gamemaster_tools/ui/class_editor.py
        # Go up 1 level: ui -> Gamemaster_tools
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        return os.path.join(base_path, 'data', 'Class', 'descriptions', desc_file)

    def load_description_file(self):
        """Load description .md content into the editor area"""
        desc_filename = self.get_description_filename()
        self.desc_filename_label.setText(desc_filename if desc_filename else "(nincs fájl)")
        
        path = self.get_description_full_path()
        if not path:
            self.desc_text_editor.clear()
            return
        
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self.desc_text_editor.setPlainText(f.read())
            except Exception as e:
                self.desc_text_editor.clear()
                QtWidgets.QMessageBox.critical(self, "Hiba", f"Nem sikerült beolvasni a leírást:\n{e}")
        else:
            self.desc_text_editor.clear()
            self.desc_text_editor.setPlaceholderText(f"A fájl ({desc_filename}) még nem létezik. Mentéskor létrehozzuk.")

    def save_description_file(self):
        """Save the editor content to the description .md file (create if missing)"""
        if not self.current_class_id:
            QtWidgets.QMessageBox.warning(self, "Figyelem", "Nincs kiválasztott kaszt!")
            return
        
        path = self.get_description_full_path()
        if not path:
            QtWidgets.QMessageBox.warning(self, "Figyelem", "Nincs leírás fájlnév megadva!")
            return
        
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self.desc_text_editor.toPlainText())
            QtWidgets.QMessageBox.information(self, "Siker", f"Leírás elmentve: {self.get_description_filename()}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Hiba", f"Nem sikerült menteni a leírást:\n{e}")

    def open_description_file(self):
        """Open the description markdown file in the default external editor"""
        path = self.get_description_full_path()
        if not path:
            QtWidgets.QMessageBox.information(self, "Info", "Nincs leírás fájlnév megadva.")
            return
        
        if not os.path.exists(path):
            QtWidgets.QMessageBox.warning(
                self, "Hiba",
                f"A leírás fájl nem található:\n{path}\n\nMentsd el először a leírást!"
            )
            return
        
        # Open with default editor
        try:
            if sys.platform.startswith('win'):
                os.startfile(path)
            elif sys.platform == 'darwin':
                subprocess.call(['open', path])
            else:
                subprocess.call(['xdg-open', path])
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Hiba", f"Nem sikerült megnyitni a fájlt:\n{e}")

if __name__ == "__main__":
    from utils.dark_mode import apply_dark_mode
    
    app = QtWidgets.QApplication(sys.argv)
    apply_dark_mode(app)
    
    editor = ClassEditorQt()
    editor.exec()
