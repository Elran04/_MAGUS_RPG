"""
Race Editor Tabs
Contains all tab widgets for race editing
"""

import json
import sqlite3
from pathlib import Path

from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from engine.race import Race
from engine.race_manager import RaceManager
from ui.races.race_editor_constants import ATTRIBUTE_NAMES
from ui.races.special_ability_editor import SpecialAbilityEditor


class RaceEditorTabs:
    """Manages all race editor tabs"""

    def __init__(self, race_manager: RaceManager):
        self.race_manager = race_manager
        self.current_race: Race | None = None

        # Tab widgets will be created as properties
        self.tab_widget = QtWidgets.QTabWidget()

        # Basic tab widgets
        self.txt_id = QtWidgets.QLineEdit()
        self.txt_name = QtWidgets.QLineEdit()
        self.spin_attrs: dict[str, QSpinBox] = {}
        self.spin_age_min = QSpinBox()
        self.spin_age_max = QSpinBox()

        # Skills tab widgets
        self.skill_tree = QTreeWidget()
        self.racial_skills_table = QTableWidget()
        self.list_forbidden_skills = QListWidget()
        self.btn_add_skill = QPushButton("➕ Hozzáadás")
        self.btn_edit_skill = QPushButton("✏️ Szerkesztés")
        self.btn_delete_skill = QPushButton("➖ Eltávolít")
        self.btn_add_forbidden = QPushButton("➕ Hozzáad")
        self.btn_remove_forbidden = QPushButton("➖ Eltávolít")

        # Special abilities tab widgets
        self.list_available_abilities = QListWidget()
        self.list_race_abilities = QListWidget()
        self.txt_ability_details = QTextEdit()

        # Origins tab widgets
        self.list_origins = QListWidget()

        # Classes tab widgets
        self.list_allowed_classes = QListWidget()
        self.list_forbidden_specs = QListWidget()

        # Description tab widget
        self.txt_description = QTextEdit()

        self.create_tabs()

    def create_tabs(self):
        """Create all tabs"""
        self.tab_widget.addTab(self.create_tab_basic(), "Alapadatok & Leírás")
        self.tab_widget.addTab(self.create_tab_skills(), "Képzettségek")
        self.tab_widget.addTab(self.create_tab_special_abilities(), "Speciális képességek")
        self.tab_widget.addTab(self.create_tab_classes(), "Kaszt korlátozások")
        self.tab_widget.addTab(self.create_tab_ability_editor(), "Képesség szerkesztő")

    def create_tab_basic(self) -> QWidget:
        """Alapadatok & Leírás tab - Splitter layout with left (attrs/age + origins) and right (description)"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # Main horizontal splitter: left = attributes/age + origins, right = description
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side uses a vertical splitter: top = attributes/age, bottom = origins
        left_splitter = QSplitter(Qt.Orientation.Vertical)

        # Top: Attributes and Age
        top_left_widget = QWidget()
        top_left_layout = QVBoxLayout()
        top_left_widget.setLayout(top_left_layout)

        # Tulajdonság módosítók
        group_attrs = QGroupBox("Tulajdonság módosítók")
        attrs_layout = QFormLayout()

        for attr_name in ATTRIBUTE_NAMES:
            spin = self.create_stat_spinbox()
            self.spin_attrs[attr_name] = spin
            attrs_layout.addRow(f"{attr_name}:", spin)

        group_attrs.setLayout(attrs_layout)
        top_left_layout.addWidget(group_attrs)

        # Életkor
        group_age = QGroupBox("Életkor határok")
        age_layout = QFormLayout()

        self.spin_age_min.setRange(1, 10000)
        self.spin_age_max.setRange(1, 10000)

        age_layout.addRow("Min életkor:", self.spin_age_min)
        age_layout.addRow("Max életkor:", self.spin_age_max)

        group_age.setLayout(age_layout)
        top_left_layout.addWidget(group_age)

        # Add the top-left widget to the vertical splitter
        left_splitter.addWidget(top_left_widget)

        # Bottom: Origins
        bottom_left_widget = QWidget()
        bottom_left_layout = QVBoxLayout()
        bottom_left_widget.setLayout(bottom_left_layout)

        bottom_left_layout.addWidget(QLabel("<b>Származási helyek</b>"))
        bottom_left_layout.addWidget(QLabel("<i>Fejlesztés alatt...</i>"))

        self.list_origins = QListWidget()
        bottom_left_layout.addWidget(self.list_origins)

        left_splitter.addWidget(bottom_left_widget)

        # Fine-tune left vertical splitter sizes: emphasize attributes/age
        left_splitter.setSizes([700, 300])

        # Add the left vertical splitter to the main splitter
        splitter.addWidget(left_splitter)

        # Right: Description editor
        right_desc_widget = QWidget()
        right_desc_layout = QVBoxLayout()
        right_desc_widget.setLayout(right_desc_layout)

        right_desc_layout.addWidget(QLabel("<b>Markdown leírás</b>"))
        # Ensure placeholder is set here since description tab is removed
        self.txt_description.setPlaceholderText(
            "# Faj neve\n\n## Általános leírás\n\n...\n\n## Megjelenés\n\n..."
        )
        right_desc_layout.addWidget(self.txt_description)

        splitter.addWidget(right_desc_widget)

        # Set main splitter sizes: left vs right
        splitter.setSizes([200, 1000])

        layout.addWidget(splitter)
        return tab

    def create_tab_skills(self) -> QWidget:
        """Képzettségek tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # Main horizontal splitter: left = skills tree, right = racial/forbidden skills
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Bal oldal: Elérhető képzettségek fa
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)
        left_layout.addWidget(QLabel("<b>Elérhető képzettségek</b>"))

        self.skill_tree.setColumnCount(3)
        self.skill_tree.setHeaderLabels(["Kategória / Alkategória", "Azonosító", "Név"])
        self.skill_tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.skill_tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.skill_tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        left_layout.addWidget(self.skill_tree)

        main_splitter.addWidget(left_widget)

        # Jobb oldal: Vertical splitter for racial skills (top) and forbidden skills (bottom)
        right_splitter = QSplitter(Qt.Orientation.Vertical)

        # Felső rész: Faji képzettségek táblázat
        top_widget = QWidget()
        top_layout = QVBoxLayout()
        top_widget.setLayout(top_layout)
        top_layout.addWidget(QLabel("<b>Faji képzettségek</b>"))

        self.racial_skills_table.setColumnCount(3)
        self.racial_skills_table.setHorizontalHeaderLabels(
            ["Azonosító", "Név", "Szint"]
        )
        self.racial_skills_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.racial_skills_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.racial_skills_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        top_layout.addWidget(self.racial_skills_table)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.btn_add_skill)
        btn_layout.addWidget(self.btn_edit_skill)
        btn_layout.addWidget(self.btn_delete_skill)
        btn_layout.addStretch()
        top_layout.addLayout(btn_layout)

        right_splitter.addWidget(top_widget)

        # Alsó rész: Tiltott képzettségek
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout()
        bottom_widget.setLayout(bottom_layout)
        bottom_layout.addWidget(QLabel("<b>Tiltott képzettségek</b>"))

        self.list_forbidden_skills = QListWidget()
        bottom_layout.addWidget(self.list_forbidden_skills)

        btn_layout2 = QHBoxLayout()
        btn_layout2.addWidget(self.btn_add_forbidden)
        btn_layout2.addWidget(self.btn_remove_forbidden)
        btn_layout2.addStretch()
        bottom_layout.addLayout(btn_layout2)

        right_splitter.addWidget(bottom_widget)

        # Set right splitter sizes: 60% racial skills, 40% forbidden skills
        right_splitter.setSizes([600, 400])

        main_splitter.addWidget(right_splitter)

        # Set main splitter sizes: 40% tree, 60% right panel
        main_splitter.setSizes([400, 600])

        layout.addWidget(main_splitter)

        # Populate skills tree
        self.populate_skills_tree()

        return tab

    def create_tab_special_abilities(self) -> QWidget:
        """Speciális képességek tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # Splitter: elérhető vs hozzáadott
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Bal oldal: Elérhető képességek
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)

        left_layout.addWidget(QLabel("<b>Elérhető képességek</b>"))
        self.list_available_abilities = QListWidget()
        left_layout.addWidget(self.list_available_abilities)

        splitter.addWidget(left_widget)

        # Jobb oldal: Faj képességei
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)

        right_layout.addWidget(QLabel("<b>Faj képességei</b>"))
        self.list_race_abilities = QListWidget()
        right_layout.addWidget(self.list_race_abilities)

        splitter.addWidget(right_widget)
        layout.addWidget(splitter)

        # Képesség részletek
        layout.addWidget(QLabel("<b>Képesség részletei</b>"))
        self.txt_ability_details.setReadOnly(True)
        self.txt_ability_details.setMaximumHeight(150)
        layout.addWidget(self.txt_ability_details)

        return tab

    def create_tab_classes(self) -> QWidget:
        """Kaszt korlátozások tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        layout.addWidget(QLabel("<b>Engedélyezett kasztok</b>"))
        self.list_allowed_classes = QListWidget()
        layout.addWidget(self.list_allowed_classes)

        layout.addWidget(QLabel("<b>Tiltott specializációk</b>"))
        self.list_forbidden_specs = QListWidget()
        layout.addWidget(self.list_forbidden_specs)

        return tab

    # Note: Leírás tab removed – description editor integrated into the first tab

    def create_tab_ability_editor(self) -> QWidget:
        """Képesség szerkesztő tab (CRUD for Special Abilities)."""
        # Pass a callback to refresh available abilities in the main tab when changed
        def refresh_abilities():
            self.load_special_abilities()
        editor = SpecialAbilityEditor(self.race_manager, on_change=refresh_abilities)
        return editor

    # === Helper Methods ===

    def create_stat_spinbox(self) -> QSpinBox:
        """Tulajdonság spinbox létrehozása"""
        spin = QSpinBox()
        spin.setRange(-10, 10)
        spin.setValue(0)
        return spin

    def _skills_db_path(self) -> Path:
        return self.race_manager.data_dir / "skills" / "skills_data.db"

    def populate_skills_tree(self):
        """Elérhető képzettségek fa feltöltése az adatbázisból"""
        self.skill_tree.clear()
        db_path = self._skills_db_path()
        if not db_path.exists():
            return
        try:
            with sqlite3.connect(str(db_path)) as conn:
                rows = conn.execute(
                    "SELECT id, name, category, subcategory, parameter, type, placeholder FROM skills ORDER BY category, subcategory, name"
                ).fetchall()
        except Exception:
            return

        cat_items: dict[str, QTreeWidgetItem] = {}
        subcat_items: dict[tuple[str, str], QTreeWidgetItem] = {}
        for skill_id, name, cat, subcat, parameter, skill_type, placeholder in rows:
            if cat not in cat_items:
                item = QTreeWidgetItem([cat or "", "", ""])
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
            display_name = f"{name} ({parameter})" if parameter else name
            leaf = QTreeWidgetItem(["", str(skill_id), display_name])
            leaf.setData(1, Qt.ItemDataRole.UserRole, str(skill_id))
            parent.addChild(leaf)
        self.skill_tree.expandAll()

    def resolve_skill_name(self, skill_id: str) -> str:
        """Visszaadja a skill nevét a DB-ből (ha elérhető)."""
        db_path = self._skills_db_path()
        if not db_path.exists():
            return ""
        try:
            with sqlite3.connect(str(db_path)) as conn:
                res = conn.execute(
                    "SELECT name, parameter FROM skills WHERE id=?", (skill_id,)
                ).fetchone()
                if res:
                    name, param = res
                    return f"{name} ({param})" if param else name
        except Exception:
            return ""
        return ""

    # === Data Loading ===

    def load_race(self, race: Race):
        """Faj adatok betöltése a UI-ba"""
        self.current_race = race

        # Alapadatok
        self.txt_id.setText(race.id)
        self.txt_name.setText(race.name)

        # Tulajdonságok - MAGYAR mezőnevek!
        mods = race.attributes.modifiers
        for attr_name in ATTRIBUTE_NAMES:
            value = getattr(mods, attr_name, 0)
            self.spin_attrs[attr_name].setValue(value)

        # Életkor
        self.spin_age_min.setValue(race.age.min)
        self.spin_age_max.setValue(race.age.max)

        # Képzettségek
        self.load_skills()

        # Speciális képességek
        self.load_special_abilities()

        # Origins
        self.load_origins()

        # Class restrictions
        self.load_class_restrictions()

        # Leírás
        desc = race.get_description(self.race_manager.data_dir)
        self.txt_description.setPlainText(desc)

    def load_skills(self):
        """Képzettségek betöltése"""
        if not self.current_race:
            return

        # Assigned racial skills table
        self.racial_skills_table.setRowCount(0)
        for rs in self.current_race.racial_skills:
            name = self.resolve_skill_name(rs.skill_id)
            row = self.racial_skills_table.rowCount()
            self.racial_skills_table.insertRow(row)
            self.racial_skills_table.setItem(row, 0, QTableWidgetItem(rs.skill_id))
            self.racial_skills_table.setItem(row, 1, QTableWidgetItem(name))
            # Display level in 1-6 scale
            level_text = str(rs.level)
            self.racial_skills_table.setItem(row, 2, QTableWidgetItem(level_text))

        # Forbidden skills list
        self.list_forbidden_skills.clear()
        for skill_id in self.current_race.forbidden_skills:
            name = self.resolve_skill_name(skill_id)
            display = f"{skill_id} - {name}" if name else skill_id
            self.list_forbidden_skills.addItem(display)

    def load_special_abilities(self):
        """Speciális képességek listák feltöltése"""
        if not self.current_race:
            return

        # Elérhető képességek (összes - már hozzáadott)
        all_abilities = self.race_manager.get_all_special_abilities()
        race_ability_ids = set(self.current_race.special_abilities)

        self.list_available_abilities.clear()
        for ability in all_abilities:
            if ability.id not in race_ability_ids:
                item = QListWidgetItem(f"{ability.name}")
                item.setData(Qt.ItemDataRole.UserRole, ability.id)
                self.list_available_abilities.addItem(item)

        # Faj képességei
        self.list_race_abilities.clear()
        race_abilities = self.race_manager.get_race_special_abilities(self.current_race.id)
        for ability in race_abilities:
            item = QListWidgetItem(f"{ability.name}")
            item.setData(Qt.ItemDataRole.UserRole, ability.id)
            self.list_race_abilities.addItem(item)

    def load_origins(self):
        """Származási helyek betöltése"""
        if not self.current_race:
            return

        self.list_origins.clear()
        for origin in self.current_race.origins:
            self.list_origins.addItem(f"{origin.name} ({origin.probability}%)")

    def load_class_restrictions(self):
        """Kaszt korlátozások betöltése"""
        if not self.current_race:
            return

        self.list_allowed_classes.clear()
        for class_id in self.current_race.class_restrictions.allowed_classes:
            self.list_allowed_classes.addItem(class_id)

        self.list_forbidden_specs.clear()
        for spec_id in self.current_race.class_restrictions.forbidden_specializations:
            self.list_forbidden_specs.addItem(spec_id)

    def show_ability_details(self, item: QListWidgetItem):
        """Speciális képesség részleteinek megjelenítése"""
        ability_id = item.data(Qt.ItemDataRole.UserRole)
        ability = self.race_manager.get_special_ability(ability_id)
        if ability:
            details = f"<h3>{ability.name}</h3>"
            details += f"<p>{ability.description}</p>"
            details += "<p><b>Játékmechanikai hatás:</b></p>"
            details += f"<pre>{json.dumps(ability.game_effect, indent=2, ensure_ascii=False)}</pre>"
            self.txt_ability_details.setHtml(details)
