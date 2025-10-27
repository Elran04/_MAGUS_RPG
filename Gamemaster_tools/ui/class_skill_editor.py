import os
import sqlite3

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QTreeWidget, QTreeWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QFormLayout,
    QLineEdit, QSpinBox, QMessageBox
)
from PySide6.QtCore import Qt

# Keep original database paths to avoid changing data access
DB_CLASS = "d:/_Projekt/_MAGUS_RPG/data/Class/class_data.db"
DB_SKILL = "d:/_Projekt/_MAGUS_RPG/data/skills/skills_data.db"


def get_classes():
    with sqlite3.connect(DB_CLASS) as conn:
        return conn.execute("SELECT id, name FROM classes ORDER BY name").fetchall()


def get_skills():
    with sqlite3.connect(DB_SKILL) as conn:
        return conn.execute("SELECT id, name, category, subcategory, parameter FROM skills").fetchall()


def get_class_skills(class_id, spec_id=None):
    with sqlite3.connect(DB_CLASS) as conn:
        return conn.execute(
            "SELECT skill_id, class_level, skill_level, skill_percent FROM class_skills WHERE class_id=? AND (specialisation_id=? OR specialisation_id IS NULL)",
            (class_id, spec_id)
        ).fetchall()


def add_class_skill(class_id, spec_id, class_level, skill_id, skill_level, skill_percent):
    with sqlite3.connect(DB_CLASS) as conn:
        conn.execute(
            "INSERT INTO class_skills (class_id, specialisation_id, class_level, skill_id, skill_level, skill_percent) VALUES (?, ?, ?, ?, ?, ?)",
            (class_id, spec_id, class_level, skill_id, skill_level, skill_percent)
        )
        conn.commit()


def update_class_skill(class_id, spec_id, skill_id, class_level, skill_level, skill_percent):
    with sqlite3.connect(DB_CLASS) as conn:
        conn.execute(
            "UPDATE class_skills SET class_level=?, skill_level=?, skill_percent=? WHERE class_id=? AND specialisation_id=? AND skill_id=?",
            (class_level, skill_level, skill_percent, class_id, spec_id, skill_id)
        )
        conn.commit()


def delete_class_skill(class_id, spec_id, skill_id):
    with sqlite3.connect(DB_CLASS) as conn:
        conn.execute(
            "DELETE FROM class_skills WHERE class_id=? AND specialisation_id=? AND skill_id=?",
            (class_id, spec_id, skill_id)
        )
        conn.commit()


def ensure_table():
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


class SkillAssignDialogQt(QDialog):
    def __init__(self, parent, skill_id, skill_name, class_level=None, skill_level=None, skill_percent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Képzettség hozzárendelése: {skill_name}")
        self.setModal(True)
        self.result_values = None

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel(f"Képzettség: {skill_name} ({skill_id})"))

        form = QFormLayout()
        layout.addLayout(form)

        self.inp_class_level = QSpinBox()
        self.inp_class_level.setRange(1, 99)
        if class_level is not None:
            try:
                self.inp_class_level.setValue(int(class_level))
            except Exception:
                pass
        form.addRow("Szint (class_level):", self.inp_class_level)

        self.inp_skill_level = QSpinBox()
        self.inp_skill_level.setRange(0, 6)
        self.inp_skill_level.setValue(int(skill_level) if skill_level else 0)
        form.addRow("Képzettség szint:", self.inp_skill_level)

        self.inp_skill_percent = QSpinBox()
        self.inp_skill_percent.setRange(0, 100)
        self.inp_skill_percent.setValue(int(skill_percent) if skill_percent else 0)
        form.addRow("Képzettség %:", self.inp_skill_percent)

        btns = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.on_ok)
        btn_cancel = QPushButton("Mégsem")
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
        layout.addLayout(btns)

        self.resize(360, 200)

    def on_ok(self):
        class_level = self.inp_class_level.value()
        skill_level = self.inp_skill_level.value()
        skill_percent = self.inp_skill_percent.value()

        # Only one of skill_level or skill_percent should be set (non-zero)
        if skill_level and skill_percent:
            QMessageBox.critical(self, "Hiba", "Csak az egyik mezőt töltsd ki: szint vagy százalék!")
            return

        self.result_values = (
            int(class_level),
            int(skill_level) if skill_level != 0 else None,
            int(skill_percent) if skill_percent != 0 else None,
        )
        self.accept()


class ClassSkillEditorQt(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kaszt képzettség szerkesztő")
        self.resize(1100, 650)

        ensure_table()

        self.selected_class = None
        self.selected_spec = None

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout()
        central.setLayout(root)

        # Top controls
        top = QHBoxLayout()
        root.addLayout(top)

        top.addWidget(QLabel("Kaszt:"))
        self.class_cb = QComboBox()
        self.class_cb.currentIndexChanged.connect(self.on_class_selected)
        top.addWidget(self.class_cb)

        top.addWidget(QLabel("Specializáció:"))
        self.spec_cb = QComboBox()
        self.spec_cb.addItems(["(nincs)", "(placeholder)"])
        self.spec_cb.currentIndexChanged.connect(self.on_spec_selected)
        top.addWidget(self.spec_cb)
        top.addStretch()

        # Main split: left tree (available), right table (assigned)
        main = QHBoxLayout()
        root.addLayout(main, stretch=1)

        # Left panel
        left_layout = QVBoxLayout()
        main.addLayout(left_layout, stretch=1)
        left_layout.addWidget(QLabel("Elérhető képzettségek"))
        self.skill_tree = QTreeWidget()
        self.skill_tree.setColumnCount(3)
        self.skill_tree.setHeaderLabels(["Kategória / Alkategória", "Azonosító", "Név"])
        self.skill_tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.skill_tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.skill_tree.header().setSectionResizeMode(2, QHeaderView.Stretch)
        left_layout.addWidget(self.skill_tree)

        # Right panel
        right_layout = QVBoxLayout()
        main.addLayout(right_layout, stretch=1)
        right_layout.addWidget(QLabel("Hozzárendelt képzettségek"))
        self.assigned_table = QTableWidget(0, 5)
        self.assigned_table.setHorizontalHeaderLabels(["Azonosító", "Név", "Szint", "Képzettség szint", "Képzettség %"])
        self.assigned_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.assigned_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.assigned_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.assigned_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.assigned_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        right_layout.addWidget(self.assigned_table)

        # Bottom buttons
        btns = QHBoxLayout()
        root.addLayout(btns)
        self.btn_add = QPushButton("Hozzáadás")
        self.btn_add.clicked.connect(self.add_skill)
        btns.addWidget(self.btn_add)
        self.btn_edit = QPushButton("Szerkesztés")
        self.btn_edit.clicked.connect(self.edit_skill)
        btns.addWidget(self.btn_edit)
        self.btn_delete = QPushButton("Törlés")
        self.btn_delete.clicked.connect(self.delete_skill)
        btns.addWidget(self.btn_delete)
        btns.addStretch()

        # Populate data
        self.populate_classes()
        self.populate_skills()

    # Data population
    def populate_classes(self):
        self.class_cb.clear()
        classes = get_classes()
        for cid, name in classes:
            self.class_cb.addItem(f"{cid} - {name}", userData=cid)
        if classes:
            self.class_cb.setCurrentIndex(0)
            self.on_class_selected()

    def populate_skills(self):
        self.skill_tree.clear()
        skills = get_skills()
        cat_items = {}
        subcat_items = {}
        for skill_id, skill_name, cat, subcat, parameter in skills:
            if cat not in cat_items:
                item = QTreeWidgetItem([cat, "", ""])
                item.setFirstColumnSpanned(True)
                self.skill_tree.addTopLevelItem(item)
                cat_items[cat] = item
            parent = cat_items[cat]
            if subcat:
                key = (cat, subcat)
                if key not in subcat_items:
                    sub = QTreeWidgetItem([subcat, "", ""])
                    sub.setFirstColumnSpanned(True)
                    parent.addChild(sub)
                    subcat_items[key] = sub
                parent = subcat_items[key]
            display_name = f"{skill_name} ({parameter})" if parameter else skill_name
            leaf = QTreeWidgetItem(["", str(skill_id), display_name])
            leaf.setData(1, Qt.UserRole, str(skill_id))
            parent.addChild(leaf)
        self.skill_tree.expandAll()

    def populate_class_skills(self):
        self.assigned_table.setRowCount(0)
        if not self.selected_class:
            return
        records = get_class_skills(self.selected_class, None)
        for skill_id, class_level, skill_level, skill_percent in records:
            # Resolve skill name from skills DB (column names: id, name)
            with sqlite3.connect(DB_SKILL) as conn:
                res = conn.execute("SELECT name, parameter FROM skills WHERE id=?", (skill_id,)).fetchone()
                if res:
                    name, param = res
                    skill_name = f"{name} ({param})" if param else name
                else:
                    skill_name = ""
            row = self.assigned_table.rowCount()
            self.assigned_table.insertRow(row)
            self.assigned_table.setItem(row, 0, QTableWidgetItem(str(skill_id)))
            self.assigned_table.setItem(row, 1, QTableWidgetItem(skill_name))
            self.assigned_table.setItem(row, 2, QTableWidgetItem(str(class_level if class_level is not None else "")))
            self.assigned_table.setItem(row, 3, QTableWidgetItem(str(skill_level if skill_level is not None else "")))
            self.assigned_table.setItem(row, 4, QTableWidgetItem(str(skill_percent if skill_percent is not None else "")))

    # Events
    def on_class_selected(self):
        data = self.class_cb.currentData()
        self.selected_class = data
        self.populate_class_skills()

    def on_spec_selected(self):
        self.selected_spec = self.spec_cb.currentText()
        self.populate_class_skills()

    def _selected_skill_from_tree(self):
        item = self.skill_tree.currentItem()
        if not item:
            return None
        # Must be a leaf with an ID
        skill_id = item.data(1, Qt.UserRole)
        if not skill_id:
            return None
        skill_name = item.text(2)
        return str(skill_id), skill_name

    def _selected_assigned_row(self):
        row = self.assigned_table.currentRow()
        if row < 0:
            return None
        skill_id = self.assigned_table.item(row, 0).text()
        skill_name = self.assigned_table.item(row, 1).text()
        class_level = self.assigned_table.item(row, 2).text()
        skill_level = self.assigned_table.item(row, 3).text()
        skill_percent = self.assigned_table.item(row, 4).text()
        return skill_id, skill_name, class_level, skill_level, skill_percent, row

    def add_skill(self):
        sel = self._selected_skill_from_tree()
        if not sel:
            QMessageBox.warning(self, "Nincs kiválasztva", "Válassz ki egy képzettséget!")
            return
        skill_id, skill_name = sel
        dlg = SkillAssignDialogQt(self, skill_id, skill_name)
        if dlg.exec():
            class_level, skill_level, skill_percent = dlg.result_values
            add_class_skill(self.selected_class, None, class_level, skill_id, skill_level, skill_percent)
            self.populate_class_skills()

    def edit_skill(self):
        sel = self._selected_assigned_row()
        if not sel:
            QMessageBox.warning(self, "Nincs kiválasztva", "Válassz ki egy hozzárendelt képzettséget!")
            return
        skill_id, skill_name, class_level, skill_level, skill_percent, _ = sel
        # Convert blanks to None
        cl = int(class_level) if class_level else None
        sl = int(skill_level) if skill_level else None
        sp = int(skill_percent) if skill_percent else None
        dlg = SkillAssignDialogQt(self, skill_id, skill_name, cl, sl, sp)
        if dlg.exec():
            class_level, skill_level, skill_percent = dlg.result_values
            update_class_skill(self.selected_class, None, skill_id, class_level, skill_level, skill_percent)
            self.populate_class_skills()

    def delete_skill(self):
        sel = self._selected_assigned_row()
        if not sel:
            QMessageBox.warning(self, "Nincs kiválasztva", "Válassz ki egy hozzárendelt képzettséget!")
            return
        skill_id = sel[0]
        delete_class_skill(self.selected_class, None, skill_id)
        self.populate_class_skills()


if __name__ == "__main__":
    import sys
    # Make utils importable and apply dark mode
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    try:
        from utils.dark_mode import apply_dark_mode
    except Exception:
        apply_dark_mode = None

    app = QApplication(sys.argv)
    if apply_dark_mode:
        apply_dark_mode(app)
    win = ClassSkillEditorQt()
    win.show()
    sys.exit(app.exec())