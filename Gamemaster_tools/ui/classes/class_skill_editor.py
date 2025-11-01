"""
Class Skill Editor Widget
Reusable widget for managing class/specialization skill assignments
Can be used standalone or embedded in other editors
"""

import os
import sqlite3

from PySide6 import QtCore, QtWidgets

# Database paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_CLASS = os.path.join(BASE_DIR, "data", "Class", "class_data.db")
DB_SKILL = os.path.join(BASE_DIR, "data", "skills", "skills_data.db")


class SkillAssignDialog(QtWidgets.QDialog):
    """Dialog for assigning/editing skill parameters"""

    def __init__(
        self,
        parent,
        skill_id,
        skill_name,
        class_level=None,
        skill_level=None,
        skill_percent=None,
        skill_type=None,
    ):
        super().__init__(parent)
        self.setWindowTitle(f"Képzettség hozzárendelése: {skill_name}")
        self.setModal(True)
        self.result_values = None
        self.skill_type = skill_type

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel(f"Képzettség: {skill_name} ({skill_id})"))

        form = QtWidgets.QFormLayout()
        layout.addLayout(form)

        self.inp_class_level = QtWidgets.QSpinBox()
        self.inp_class_level.setRange(1, 99)
        if class_level is not None:
            try:
                self.inp_class_level.setValue(int(class_level))
            except Exception:
                pass
        form.addRow("Szint (class_level):", self.inp_class_level)

        self.inp_skill_level = QtWidgets.QSpinBox()
        self.inp_skill_level.setRange(0, 6)
        self.inp_skill_level.setValue(int(skill_level) if skill_level else 0)
        form.addRow("Képzettség szint:", self.inp_skill_level)

        self.inp_skill_percent = QtWidgets.QSpinBox()
        self.inp_skill_percent.setRange(0, 100)
        self.inp_skill_percent.setValue(int(skill_percent) if skill_percent else 0)
        form.addRow("Képzettség %:", self.inp_skill_percent)

        # Auto-set based on skill type
        if skill_type == 1:  # Level-based
            self.inp_skill_level.setEnabled(True)
            self.inp_skill_percent.setEnabled(False)
            if skill_level is None:
                self.inp_skill_level.setValue(1)
            self.inp_skill_percent.setValue(0)
        elif skill_type == 2:  # Percentage-based
            self.inp_skill_level.setEnabled(False)
            self.inp_skill_percent.setEnabled(True)
            self.inp_skill_level.setValue(0)
            if skill_percent is None:
                self.inp_skill_percent.setValue(10)

        btns = QtWidgets.QHBoxLayout()
        btn_ok = QtWidgets.QPushButton("OK")
        btn_ok.clicked.connect(self.on_ok)
        btn_cancel = QtWidgets.QPushButton("Mégsem")
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
        layout.addLayout(btns)

        self.resize(360, 200)

    def on_ok(self):
        class_level = self.inp_class_level.value()
        skill_level = self.inp_skill_level.value()
        skill_percent = self.inp_skill_percent.value()

        # Auto-validation based on skill type
        if self.skill_type == 1:  # Level-based
            skill_percent_val: int | None = None
            if skill_level == 0:
                QtWidgets.QMessageBox.critical(
                    self, "Hiba", "A szint alapú képzettségnél add meg a szintet!"
                )
                return
        elif self.skill_type == 2:  # Percentage-based
            skill_level_val: int | None = None
            if skill_percent == 0:
                QtWidgets.QMessageBox.critical(
                    self, "Hiba", "A % alapú képzettségnél add meg a százalékot!"
                )
                return
        else:
            # No type info - manual validation
            if skill_level and skill_percent:
                QtWidgets.QMessageBox.critical(
                    self, "Hiba", "Csak az egyik mezőt töltsd ki: szint vagy százalék!"
                )
                return
            skill_level_val = skill_level if skill_level != 0 else None
            skill_percent_val = skill_percent if skill_percent != 0 else None

        # Use the validated values
        if self.skill_type == 1:
            final_skill_level = int(skill_level) if skill_level != 0 else None
            final_skill_percent = None
        elif self.skill_type == 2:
            final_skill_level = None
            final_skill_percent = int(skill_percent) if skill_percent != 0 else None
        else:
            final_skill_level = int(skill_level) if skill_level and skill_level != 0 else None
            final_skill_percent = (
                int(skill_percent) if skill_percent and skill_percent != 0 else None
            )

        self.result_values = (
            int(class_level),
            final_skill_level,
            final_skill_percent,
        )
        self.accept()


class ClassSkillEditorWidget(QtWidgets.QWidget):
    """Reusable widget for managing class skill assignments"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_class_id = None
        self.current_spec_id = None

        self._init_ui()
        self._ensure_table()
        self._populate_skills_tree()

    def _init_ui(self):
        """Initialize the UI layout"""
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Info label
        # info = QtWidgets.QLabel("Képzettségek hozzárendelése az adott kaszthoz/specializációhoz")
        # info.setStyleSheet("color: #666; margin-bottom: 10px;")
        # main_layout.addWidget(info)

        # Main split: left tree (available), right table (assigned)
        splitter = QtWidgets.QSplitter()
        splitter.setOrientation(QtCore.Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter, stretch=1)

        # Left panel - Available skills tree
        left_widget = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(QtWidgets.QLabel("Elérhető képzettségek"))

        self.skill_tree = QtWidgets.QTreeWidget()
        self.skill_tree.setColumnCount(3)
        self.skill_tree.setHeaderLabels(["Kategória / Alkategória", "Azonosító", "Név"])
        self.skill_tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.skill_tree.header().setSectionResizeMode(
            1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents
        )
        self.skill_tree.header().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.Stretch)
        left_layout.addWidget(self.skill_tree)
        splitter.addWidget(left_widget)

        # Right panel - Assigned skills table
        right_widget = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(QtWidgets.QLabel("Hozzárendelt képzettségek"))

        self.assigned_skills_table = QtWidgets.QTableWidget(0, 5)
        self.assigned_skills_table.setHorizontalHeaderLabels(
            ["Azonosító", "Név", "Szint", "Képzettség szint", "Képzettség %"]
        )
        self.assigned_skills_table.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents
        )
        self.assigned_skills_table.horizontalHeader().setSectionResizeMode(
            1, QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        self.assigned_skills_table.horizontalHeader().setSectionResizeMode(
            2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents
        )
        self.assigned_skills_table.horizontalHeader().setSectionResizeMode(
            3, QtWidgets.QHeaderView.ResizeMode.ResizeToContents
        )
        self.assigned_skills_table.horizontalHeader().setSectionResizeMode(
            4, QtWidgets.QHeaderView.ResizeMode.ResizeToContents
        )
        right_layout.addWidget(self.assigned_skills_table)
        splitter.addWidget(right_widget)

        # Set splitter sizes: 40% tree, 60% assigned
        splitter.setSizes([400, 600])

        # Action buttons
        btns = QtWidgets.QHBoxLayout()
        self.btn_add_skill = QtWidgets.QPushButton("Hozzáadás")
        self.btn_add_skill.clicked.connect(self.add_skill)
        btns.addWidget(self.btn_add_skill)

        self.btn_edit_skill = QtWidgets.QPushButton("Szerkesztés")
        self.btn_edit_skill.clicked.connect(self.edit_skill)
        btns.addWidget(self.btn_edit_skill)

        self.btn_delete_skill = QtWidgets.QPushButton("Törlés")
        self.btn_delete_skill.clicked.connect(self.delete_skill)
        btns.addWidget(self.btn_delete_skill)

        btns.addStretch()
        main_layout.addLayout(btns)

    def _ensure_table(self):
        """Ensure class_skills table exists"""
        try:
            with sqlite3.connect(DB_CLASS) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS class_skills (
                        class_id TEXT,
                        specialisation_id TEXT,
                        class_level INTEGER,
                        skill_id TEXT,
                        skill_level INTEGER,
                        skill_percent INTEGER,
                        PRIMARY KEY (class_id, specialisation_id, skill_id)
                    )
                """
                )
                conn.commit()
        except Exception:
            pass

    def _populate_skills_tree(self):
        """Populate the available skills tree"""
        self.skill_tree.clear()

        try:
            with sqlite3.connect(DB_SKILL) as conn:
                skills = conn.execute(
                    "SELECT id, name, category, subcategory, parameter, type, placeholder FROM skills"
                ).fetchall()
        except Exception:
            return

        cat_items = {}
        subcat_items = {}

        for skill_id, skill_name, cat, subcat, parameter, skill_type, placeholder in skills:
            # Create category items
            if cat not in cat_items:
                item = QtWidgets.QTreeWidgetItem([cat, "", ""])
                item.setFirstColumnSpanned(True)
                self.skill_tree.addTopLevelItem(item)
                cat_items[cat] = item

            parent = cat_items[cat]

            # Create subcategory items if needed
            if subcat:
                key = (cat, subcat)
                if key not in subcat_items:
                    sub = QtWidgets.QTreeWidgetItem([subcat, "", ""])
                    sub.setFirstColumnSpanned(True)
                    parent.addChild(sub)
                    subcat_items[key] = sub
                parent = subcat_items[key]

            # Create skill leaf
            display_name = f"{skill_name} ({parameter})" if parameter else skill_name
            leaf = QtWidgets.QTreeWidgetItem(["", str(skill_id), display_name])
            leaf.setData(1, QtCore.Qt.ItemDataRole.UserRole, str(skill_id))
            parent.addChild(leaf)

        self.skill_tree.expandAll()

    def set_class_spec(self, class_id, spec_id=None):
        """Set the current class/spec and reload assigned skills"""
        self.current_class_id = class_id
        self.current_spec_id = spec_id
        self.populate_assigned_skills()

    def populate_assigned_skills(self):
        """Populate the assigned skills table for the current class/spec"""
        self.assigned_skills_table.setRowCount(0)
        if not self.current_class_id:
            return

        try:
            with sqlite3.connect(DB_CLASS) as conn:
                records = conn.execute(
                    "SELECT skill_id, class_level, skill_level, skill_percent FROM class_skills WHERE class_id=? AND (specialisation_id=? OR specialisation_id IS NULL)",
                    (self.current_class_id, self.current_spec_id),
                ).fetchall()
        except Exception:
            return

        for skill_id, class_level, skill_level, skill_percent in records:
            # Resolve skill name from skills DB
            try:
                with sqlite3.connect(DB_SKILL) as conn:
                    res = conn.execute(
                        "SELECT name, parameter FROM skills WHERE id=?", (skill_id,)
                    ).fetchone()
                    if res:
                        name, param = res
                        skill_name = f"{name} ({param})" if param else name
                    else:
                        skill_name = ""
            except Exception:
                skill_name = ""

            row = self.assigned_skills_table.rowCount()
            self.assigned_skills_table.insertRow(row)
            self.assigned_skills_table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(skill_id)))
            self.assigned_skills_table.setItem(row, 1, QtWidgets.QTableWidgetItem(skill_name))
            self.assigned_skills_table.setItem(
                row,
                2,
                QtWidgets.QTableWidgetItem(str(class_level if class_level is not None else "")),
            )
            self.assigned_skills_table.setItem(
                row,
                3,
                QtWidgets.QTableWidgetItem(str(skill_level if skill_level is not None else "")),
            )
            self.assigned_skills_table.setItem(
                row,
                4,
                QtWidgets.QTableWidgetItem(str(skill_percent if skill_percent is not None else "")),
            )

    # Database operations
    def _get_skill_type(self, skill_id):
        """Get the type of a skill (1=level-based, 2=percentage-based)"""
        try:
            with sqlite3.connect(DB_SKILL) as conn:
                result = conn.execute("SELECT type FROM skills WHERE id=?", (skill_id,)).fetchone()
                return result[0] if result else None
        except Exception:
            return None

    def _is_skill_already_assigned(self, skill_id):
        """Check if a skill is already assigned"""
        try:
            with sqlite3.connect(DB_CLASS) as conn:
                if self.current_spec_id is None:
                    result = conn.execute(
                        "SELECT class_level, skill_level, skill_percent FROM class_skills WHERE class_id=? AND specialisation_id IS NULL AND skill_id=?",
                        (self.current_class_id, skill_id),
                    ).fetchone()
                else:
                    result = conn.execute(
                        "SELECT class_level, skill_level, skill_percent FROM class_skills WHERE class_id=? AND specialisation_id=? AND skill_id=?",
                        (self.current_class_id, self.current_spec_id, skill_id),
                    ).fetchone()
                return result
        except Exception:
            return None

    def _add_class_skill(self, class_level, skill_id, skill_level, skill_percent):
        """Add a skill to the current class/spec"""
        try:
            with sqlite3.connect(DB_CLASS) as conn:
                conn.execute(
                    "INSERT INTO class_skills (class_id, specialisation_id, class_level, skill_id, skill_level, skill_percent) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        self.current_class_id,
                        self.current_spec_id,
                        class_level,
                        skill_id,
                        skill_level,
                        skill_percent,
                    ),
                )
                conn.commit()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Hiba", f"Képzettség hozzáadása sikertelen:\n{e}")

    def _update_class_skill(self, skill_id, class_level, skill_level, skill_percent):
        """Update a skill assignment"""
        try:
            with sqlite3.connect(DB_CLASS) as conn:
                if self.current_spec_id is None:
                    conn.execute(
                        "UPDATE class_skills SET class_level=?, skill_level=?, skill_percent=? WHERE class_id=? AND specialisation_id IS NULL AND skill_id=?",
                        (class_level, skill_level, skill_percent, self.current_class_id, skill_id),
                    )
                else:
                    conn.execute(
                        "UPDATE class_skills SET class_level=?, skill_level=?, skill_percent=? WHERE class_id=? AND specialisation_id=? AND skill_id=?",
                        (
                            class_level,
                            skill_level,
                            skill_percent,
                            self.current_class_id,
                            self.current_spec_id,
                            skill_id,
                        ),
                    )
                conn.commit()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Hiba", f"Képzettség frissítése sikertelen:\n{e}")

    def _delete_class_skill(self, skill_id):
        """Delete a skill from the current class/spec"""
        try:
            with sqlite3.connect(DB_CLASS) as conn:
                if self.current_spec_id is None:
                    conn.execute(
                        "DELETE FROM class_skills WHERE class_id=? AND specialisation_id IS NULL AND skill_id=?",
                        (self.current_class_id, skill_id),
                    )
                else:
                    conn.execute(
                        "DELETE FROM class_skills WHERE class_id=? AND specialisation_id=? AND skill_id=?",
                        (self.current_class_id, self.current_spec_id, skill_id),
                    )
                conn.commit()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Hiba", f"Képzettség törlése sikertelen:\n{e}")

    # User actions
    def add_skill(self):
        """Add a skill from the available skills tree"""
        if not self.current_class_id:
            QtWidgets.QMessageBox.warning(self, "Nincs kiválasztva", "Válassz ki egy kasztot!")
            return

        item = self.skill_tree.currentItem()
        if not item:
            QtWidgets.QMessageBox.warning(self, "Nincs kiválasztva", "Válassz ki egy képzettséget!")
            return

        # Must be a leaf with an ID
        skill_id = item.data(1, QtCore.Qt.ItemDataRole.UserRole)
        if not skill_id:
            QtWidgets.QMessageBox.warning(
                self, "Nincs kiválasztva", "Válassz ki egy képzettséget (nem kategóriát)!"
            )
            return

        skill_name = item.text(2)
        skill_type = self._get_skill_type(skill_id)

        # Get placeholder status
        try:
            with sqlite3.connect(DB_SKILL) as conn:
                placeholder_result = conn.execute(
                    "SELECT placeholder FROM skills WHERE id=?", (skill_id,)
                ).fetchone()
                is_placeholder = (
                    placeholder_result[0] if placeholder_result and placeholder_result[0] else 0
                )
        except Exception:
            is_placeholder = 0

        # Check if skill is already assigned
        existing = self._is_skill_already_assigned(skill_id)

        if existing:
            existing_class_level, existing_skill_level, existing_skill_percent = existing

            # If it's a placeholder skill, always add as new (never overwrite)
            if is_placeholder:
                dlg = SkillAssignDialog(self, skill_id, skill_name, skill_type=skill_type)
                if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted and dlg.result_values:
                    class_level, skill_level, skill_percent = dlg.result_values
                    self._add_class_skill(class_level, skill_id, skill_level, skill_percent)
                    self.populate_assigned_skills()
            else:
                # Non-placeholder: ask if they want to update the existing entry
                reply = QtWidgets.QMessageBox.question(
                    self,
                    "Képzettség már hozzáadva",
                    f"A '{skill_name}' képzettség már hozzá van rendelve ehhez a kaszthoz.\n\nFrissíted a meglévő bejegyzést?",
                    QtWidgets.QMessageBox.StandardButton.Yes
                    | QtWidgets.QMessageBox.StandardButton.No,
                )
                if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                    dlg = SkillAssignDialog(
                        self,
                        skill_id,
                        skill_name,
                        existing_class_level,
                        existing_skill_level,
                        existing_skill_percent,
                        skill_type,
                    )
                    if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted and dlg.result_values:
                        class_level, skill_level, skill_percent = dlg.result_values
                        self._update_class_skill(skill_id, class_level, skill_level, skill_percent)
                        self.populate_assigned_skills()
        else:
            # New skill - show dialog
            dlg = SkillAssignDialog(self, skill_id, skill_name, skill_type=skill_type)
            if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted and dlg.result_values:
                class_level, skill_level, skill_percent = dlg.result_values
                self._add_class_skill(class_level, skill_id, skill_level, skill_percent)
                self.populate_assigned_skills()

    def edit_skill(self):
        """Edit a selected assigned skill"""
        row = self.assigned_skills_table.currentRow()
        if row < 0:
            QtWidgets.QMessageBox.warning(
                self, "Nincs kiválasztva", "Válassz ki egy hozzárendelt képzettséget!"
            )
            return

        item_id = self.assigned_skills_table.item(row, 0)
        item_name = self.assigned_skills_table.item(row, 1)
        item_cl = self.assigned_skills_table.item(row, 2)
        item_sl = self.assigned_skills_table.item(row, 3)
        item_sp = self.assigned_skills_table.item(row, 4)

        skill_id = item_id.text() if item_id is not None else ""
        skill_name = item_name.text() if item_name is not None else ""
        class_level = item_cl.text() if item_cl is not None else ""
        skill_level = item_sl.text() if item_sl is not None else ""
        skill_percent = item_sp.text() if item_sp is not None else ""

        # Convert blanks to None
        cl = int(class_level) if class_level else None
        sl = int(skill_level) if skill_level else None
        sp = int(skill_percent) if skill_percent else None

        skill_type = self._get_skill_type(skill_id)

        dlg = SkillAssignDialog(self, skill_id, skill_name, cl, sl, sp, skill_type)
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted and dlg.result_values:
            class_level, skill_level, skill_percent = dlg.result_values
            self._update_class_skill(skill_id, class_level, skill_level, skill_percent)
            self.populate_assigned_skills()

    def delete_skill(self):
        """Delete a selected assigned skill"""
        row = self.assigned_skills_table.currentRow()
        if row < 0:
            QtWidgets.QMessageBox.warning(
                self, "Nincs kiválasztva", "Válassz ki egy hozzárendelt képzettséget!"
            )
            return

        item_id = self.assigned_skills_table.item(row, 0)
        skill_id = item_id.text() if item_id is not None else ""
        self._delete_class_skill(skill_id)
        self.populate_assigned_skills()


# Standalone wrapper for running as independent application
class ClassSkillEditorQt(QtWidgets.QMainWindow):
    """Standalone window wrapper for the ClassSkillEditorWidget"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kaszt képzettség szerkesztő")
        self.resize(1100, 650)

        # Top controls for class selection
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        root = QtWidgets.QVBoxLayout(central)

        # Class selection
        top = QtWidgets.QHBoxLayout()
        root.addLayout(top)

        top.addWidget(QtWidgets.QLabel("Kaszt:"))
        self.class_cb = QtWidgets.QComboBox()
        self.class_cb.currentIndexChanged.connect(self.on_class_selected)
        top.addWidget(self.class_cb)

        top.addWidget(QtWidgets.QLabel("Specializáció:"))
        self.spec_cb = QtWidgets.QComboBox()
        self.spec_cb.addItems(["(nincs)"])
        self.spec_cb.currentIndexChanged.connect(self.on_spec_selected)
        top.addWidget(self.spec_cb)
        top.addStretch()

        # Add the widget
        self.skill_editor_widget = ClassSkillEditorWidget()
        root.addWidget(self.skill_editor_widget, stretch=1)

        # Populate classes
        self.populate_classes()

    def populate_classes(self):
        """Load available classes"""
        self.class_cb.clear()
        try:
            with sqlite3.connect(DB_CLASS) as conn:
                classes = conn.execute("SELECT id, name FROM classes ORDER BY name").fetchall()
                for cid, name in classes:
                    self.class_cb.addItem(f"{cid} - {name}", userData=cid)
        except Exception:
            pass

        if self.class_cb.count() > 0:
            self.class_cb.setCurrentIndex(0)
            self.on_class_selected()

    def on_class_selected(self):
        """Handle class selection"""
        class_id = self.class_cb.currentData()
        if class_id:
            self.skill_editor_widget.set_class_spec(class_id, None)

    def on_spec_selected(self):
        """Handle spec selection (placeholder for future enhancement)"""
        # Currently only supports base class (no specs in standalone mode)
        pass


if __name__ == "__main__":
    import sys
    from collections.abc import Callable
    from typing import Any

    # Make utils importable and apply dark mode
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

    _apply_dark_mode: Callable[[Any], Any] | None
    try:
        from utils.dark_mode import apply_dark_mode as _apply_dark_mode
    except Exception:
        _apply_dark_mode = None

    app = QtWidgets.QApplication(sys.argv)
    if _apply_dark_mode is not None:
        _apply_dark_mode(app)
    win = ClassSkillEditorQt()
    win.show()
    sys.exit(app.exec())
