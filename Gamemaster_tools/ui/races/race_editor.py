"""
M.A.G.U.S. Race Editor - Faj szerkesztő UI
"""

import sqlite3
import sys
from pathlib import Path

# Add Gamemaster_tools to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from engine.race import AttributeModifiers, Race
from engine.race_manager import RaceManager
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)
from utils.logger import get_logger

logger = get_logger(__name__)


class RaceEditorQt(QMainWindow):
    """M.A.G.U.S. Faj szerkesztő"""

    def __init__(self):
        super().__init__()
        logger.info("Race Editor inicializálása")

        # Data manager
        data_dir = Path(__file__).parent.parent.parent / "data"
        self.race_manager = RaceManager(data_dir)
        self.race_manager.load_all()

        self.current_race: Race | None = None

        self.setWindowTitle("M.A.G.U.S. - Faj Szerkesztő")
        self.setMinimumSize(1200, 800)

        self.init_ui()
        self.load_race_list()

    def init_ui(self):
        """UI inicializálás"""
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout()
        central.setLayout(main_layout)

        # --- Bal oldali lista ---
        left_panel = self.create_left_panel()
        main_layout.addWidget(left_panel)

        # --- Jobb oldali szerkesztő ---
        right_panel = self.create_right_panel()
        main_layout.addWidget(right_panel, stretch=1)

    def create_left_panel(self) -> QWidget:
        """Bal oldali panel létrehozása (fajok listája)"""
        panel = QWidget()
        layout = QVBoxLayout()
        panel.setLayout(layout)
        panel.setMaximumWidth(250)

        layout.addWidget(QLabel("<b>Fajok listája</b>"))

        self.race_list = QListWidget()
        self.race_list.itemClicked.connect(self.on_race_selected)
        layout.addWidget(self.race_list)

        btn_new = QPushButton("Új faj")
        btn_new.clicked.connect(self.create_new_race)
        layout.addWidget(btn_new)

        btn_delete = QPushButton("Törlés")
        btn_delete.clicked.connect(self.delete_race)
        layout.addWidget(btn_delete)

        return panel

    def create_right_panel(self) -> QWidget:
        """Jobb oldali panel létrehozása (szerkesztő)"""
        panel = QWidget()
        layout = QVBoxLayout()
        panel.setLayout(layout)

        # Név és ID
        form = QFormLayout()
        self.txt_id = QLineEdit()
        self.txt_id.setReadOnly(True)  # ID nem szerkeszthető
        self.txt_name = QLineEdit()
        form.addRow("ID:", self.txt_id)
        form.addRow("Név:", self.txt_name)
        layout.addLayout(form)

        # Tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Tabok létrehozása
        self.tabs.addTab(self.create_tab_basic(), "Alapadatok")
        self.tabs.addTab(self.create_tab_skills(), "Képzettségek")
        self.tabs.addTab(self.create_tab_special_abilities(), "Speciális képességek")
        self.tabs.addTab(self.create_tab_origins(), "Származási helyek")
        self.tabs.addTab(self.create_tab_classes(), "Kaszt korlátozások")
        self.tabs.addTab(self.create_tab_description(), "Leírás")

        # Mentés gomb
        btn_save = QPushButton("💾 Mentés")
        btn_save.setMinimumHeight(40)
        btn_save.clicked.connect(self.save_race)
        layout.addWidget(btn_save)

        return panel

    def create_tab_basic(self) -> QWidget:
        """Alapadatok tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # Tulajdonság módosítók
        group_attrs = QGroupBox("Tulajdonság módosítók")
        attrs_layout = QFormLayout()

        self.spin_str = self.create_stat_spinbox()
        self.spin_con = self.create_stat_spinbox()
        self.spin_spd = self.create_stat_spinbox()
        self.spin_dex = self.create_stat_spinbox()
        self.spin_cha = self.create_stat_spinbox()
        self.spin_hea = self.create_stat_spinbox()
        self.spin_int = self.create_stat_spinbox()
        self.spin_wil = self.create_stat_spinbox()
        self.spin_ast = self.create_stat_spinbox()
        self.spin_per = self.create_stat_spinbox()

        attrs_layout.addRow("Erő:", self.spin_str)
        attrs_layout.addRow("Állóképesség:", self.spin_con)
        attrs_layout.addRow("Gyorsaság:", self.spin_spd)
        attrs_layout.addRow("Ügyesség:", self.spin_dex)
        attrs_layout.addRow("Karizma:", self.spin_cha)
        attrs_layout.addRow("Egészség:", self.spin_hea)
        attrs_layout.addRow("Intelligencia:", self.spin_int)
        attrs_layout.addRow("Akaraterő:", self.spin_wil)
        attrs_layout.addRow("Asztrál:", self.spin_ast)
        attrs_layout.addRow("Érzékelés:", self.spin_per)

        group_attrs.setLayout(attrs_layout)
        layout.addWidget(group_attrs)

        # Életkor
        group_age = QGroupBox("Életkor határok")
        age_layout = QFormLayout()

        self.spin_age_min = QSpinBox()
        self.spin_age_min.setRange(1, 10000)
        self.spin_age_max = QSpinBox()
        self.spin_age_max.setRange(1, 10000)

        age_layout.addRow("Min életkor:", self.spin_age_min)
        age_layout.addRow("Max életkor:", self.spin_age_max)

        group_age.setLayout(age_layout)
        layout.addWidget(group_age)

        layout.addStretch()
        return tab

    def create_tab_skills(self) -> QWidget:
        """Képzettségek tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # Splitter: balra elérhető képzettségek, jobbra hozzárendelt
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Bal oldal: Elérhető képzettségek fa
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)
        left_layout.addWidget(QLabel("<b>Elérhető képzettségek</b>"))

        self.skill_tree = QTreeWidget()
        self.skill_tree.setColumnCount(3)
        self.skill_tree.setHeaderLabels(["Kategória / Alkategória", "Azonosító", "Név"])
        self.skill_tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.skill_tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.skill_tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        left_layout.addWidget(self.skill_tree)

        splitter.addWidget(left_widget)

        # Jobb oldal: Hozzárendelt faji képzettségek táblázat
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)
        right_layout.addWidget(QLabel("<b>Faji képzettségek</b>"))

        self.racial_skills_table = QTableWidget(0, 4)
        self.racial_skills_table.setHorizontalHeaderLabels(
            ["Azonosító", "Név", "Szint", "Opcionális"]
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
        self.racial_skills_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )
        right_layout.addWidget(self.racial_skills_table)

        btn_layout = QHBoxLayout()
        self.btn_add_skill = QPushButton("➕ Hozzáadás")
        self.btn_add_skill.clicked.connect(self.add_racial_skill)
        self.btn_edit_skill = QPushButton("Szerkesztés")
        self.btn_edit_skill.clicked.connect(self.edit_racial_skill)
        self.btn_delete_skill = QPushButton("➖ Eltávolít")
        self.btn_delete_skill.clicked.connect(self.delete_racial_skill)
        btn_layout.addWidget(self.btn_add_skill)
        btn_layout.addWidget(self.btn_edit_skill)
        btn_layout.addWidget(self.btn_delete_skill)
        btn_layout.addStretch()
        right_layout.addLayout(btn_layout)

        splitter.addWidget(right_widget)
        splitter.setSizes([400, 600])
        layout.addWidget(splitter)

        # Feltöltjük az elérhető képzettségeket a fából
        self.populate_skills_tree()

        # Tiltott képzettségek
        layout.addWidget(QLabel("<b>Tiltott képzettségek</b>"))
        self.list_forbidden_skills = QListWidget()
        layout.addWidget(self.list_forbidden_skills)

        btn_layout2 = QHBoxLayout()
        self.btn_add_forbidden = QPushButton("➕ Hozzáad")
        self.btn_add_forbidden.clicked.connect(self.add_forbidden_skill)
        self.btn_remove_forbidden = QPushButton("➖ Eltávolít")
        self.btn_remove_forbidden.clicked.connect(self.remove_forbidden_skill)
        btn_layout2.addWidget(self.btn_add_forbidden)
        btn_layout2.addWidget(self.btn_remove_forbidden)
        layout.addLayout(btn_layout2)

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

        btn_add_ability = QPushButton("→ Hozzáad")
        btn_add_ability.clicked.connect(self.add_special_ability)
        left_layout.addWidget(btn_add_ability)

        splitter.addWidget(left_widget)

        # Jobb oldal: Faj képességei
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)

        right_layout.addWidget(QLabel("<b>Faj képességei</b>"))
        self.list_race_abilities = QListWidget()
        right_layout.addWidget(self.list_race_abilities)

        btn_remove_ability = QPushButton("← Eltávolít")
        btn_remove_ability.clicked.connect(self.remove_special_ability)
        right_layout.addWidget(btn_remove_ability)

        splitter.addWidget(right_widget)
        layout.addWidget(splitter)

        # Képesség részletek
        layout.addWidget(QLabel("<b>Képesség részletei</b>"))
        self.txt_ability_details = QTextEdit()
        self.txt_ability_details.setReadOnly(True)
        self.txt_ability_details.setMaximumHeight(150)
        layout.addWidget(self.txt_ability_details)

        # Event handlers
        self.list_available_abilities.itemClicked.connect(self.show_ability_details)
        self.list_race_abilities.itemClicked.connect(self.show_ability_details)

        return tab

    def create_tab_origins(self) -> QWidget:
        """Származási helyek tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        layout.addWidget(QLabel("<b>Származási helyek</b>"))
        layout.addWidget(QLabel("<i>Fejlesztés alatt...</i>"))

        self.list_origins = QListWidget()
        layout.addWidget(self.list_origins)

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

    def create_tab_description(self) -> QWidget:
        """Leírás tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        layout.addWidget(QLabel("<b>Markdown leírás</b>"))
        self.txt_description = QTextEdit()
        self.txt_description.setPlaceholderText(
            "# Faj neve\n\n## Általános leírás\n\n...\n\n## Megjelenés\n\n..."
        )
        layout.addWidget(self.txt_description)

        return tab

    # === Helper Methods ===

    def create_stat_spinbox(self) -> QSpinBox:
        """Tulajdonság spinbox létrehozása"""
        spin = QSpinBox()
        spin.setRange(-10, 10)
        spin.setValue(0)
        return spin

    # === Data Loading ===

    def load_race_list(self):
        """Fajok listájának betöltése"""
        self.race_list.clear()
        for race in self.race_manager.get_all_races():
            item = QListWidgetItem(race.name)
            item.setData(Qt.ItemDataRole.UserRole, race.id)
            self.race_list.addItem(item)
        # Auto-select and load first race to display attributes on startup
        if self.race_list.count() > 0:
            self.race_list.setCurrentRow(0)
            first_item = self.race_list.item(0)
            if first_item:
                self.on_race_selected(first_item)

    def on_race_selected(self, item: QListWidgetItem):
        """Faj kiválasztva -> betöltés"""
        race_id = item.data(Qt.ItemDataRole.UserRole)
        race = self.race_manager.get_race(race_id)
        if race:
            self.load_race(race)

    def load_race(self, race: Race):
        """Faj adatok betöltése a UI-ba"""
        logger.info(f"Faj betöltése: {race.name}")
        self.current_race = race

        # Alapadatok
        self.txt_id.setText(race.id)
        self.txt_name.setText(race.name)

        # Tulajdonságok - MAGYAR mezőnevek!
        mods = race.attributes.modifiers
        self.spin_str.setValue(mods.Erő)
        self.spin_con.setValue(mods.Állóképesség)
        self.spin_spd.setValue(mods.Gyorsaság)
        self.spin_dex.setValue(mods.Ügyesség)
        self.spin_cha.setValue(mods.Karizma)
        self.spin_hea.setValue(mods.Egészség)
        self.spin_int.setValue(mods.Intelligencia)
        self.spin_wil.setValue(mods.Akaraterő)
        self.spin_ast.setValue(mods.Asztrál)
        self.spin_per.setValue(mods.Érzékelés)

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
            name = self._resolve_skill_name(rs.skill_id)
            row = self.racial_skills_table.rowCount()
            self.racial_skills_table.insertRow(row)
            self.racial_skills_table.setItem(row, 0, QTableWidgetItem(rs.skill_id))
            self.racial_skills_table.setItem(row, 1, QTableWidgetItem(name))
            level_text = "native" if rs.level == "native" else str(rs.level)
            self.racial_skills_table.setItem(row, 2, QTableWidgetItem(level_text))
            self.racial_skills_table.setItem(
                row, 3, QTableWidgetItem("igen" if rs.optional else "nem")
            )

        # Forbidden skills list
        self.list_forbidden_skills.clear()
        for skill_id in self.current_race.forbidden_skills:
            name = self._resolve_skill_name(skill_id)
            display = f"{skill_id} - {name}" if name else skill_id
            self.list_forbidden_skills.addItem(display)

    # === Skills helpers ===

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

    def _resolve_skill_name(self, skill_id: str) -> str:
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

    # === Racial skills actions ===

    def _get_selected_skill_id_from_tree(self) -> str | None:
        item = self.skill_tree.currentItem()
        if not item:
            return None
        sid = item.data(1, Qt.ItemDataRole.UserRole)
        return str(sid) if sid is not None else None

    def add_racial_skill(self):
        """Képzettség hozzáadása a faji listához"""
        if not self.current_race:
            QMessageBox.warning(self, "Nincs kiválasztva", "Előbb válassz ki egy fajt!")
            return
        sid = self._get_selected_skill_id_from_tree()
        if not sid:
            QMessageBox.information(self, "Info", "Válassz ki egy képzettséget a fából!")
            return
        name = self._resolve_skill_name(sid)
        level, optional = self._ask_racial_skill_params(sid, name)
        if level is None:
            return
        from engine.race import RacialSkill

        # If already exists and not placeholder, update instead of duplicate
        existing_idx = next(
            (i for i, rs in enumerate(self.current_race.racial_skills) if rs.skill_id == sid), None
        )
        if existing_idx is not None:
            self.current_race.racial_skills[existing_idx].level = level
            self.current_race.racial_skills[existing_idx].optional = optional
        else:
            self.current_race.racial_skills.append(
                RacialSkill(skill_id=sid, level=level, optional=optional)
            )
        self.load_skills()

    def edit_racial_skill(self):
        row = self.racial_skills_table.currentRow()
        if row < 0 or not self.current_race:
            QMessageBox.information(self, "Info", "Válassz ki egy faji képzettséget!")
            return
        item0 = self.racial_skills_table.item(row, 0)
        item1 = self.racial_skills_table.item(row, 1)
        if not item0 or not item1:
            return
        sid = item0.text()
        name = item1.text()
        # find existing
        idx = next(
            (i for i, rs in enumerate(self.current_race.racial_skills) if rs.skill_id == sid), None
        )
        if idx is None:
            return
        current = self.current_race.racial_skills[idx]
        level, optional = self._ask_racial_skill_params(sid, name, current.level, current.optional)
        if level is None:
            return
        current.level = level
        current.optional = optional
        self.load_skills()

    def delete_racial_skill(self):
        row = self.racial_skills_table.currentRow()
        if row < 0 or not self.current_race:
            return
        item0 = self.racial_skills_table.item(row, 0)
        if not item0:
            return
        sid = item0.text()
        self.current_race.racial_skills = [
            rs for rs in self.current_race.racial_skills if rs.skill_id != sid
        ]
        self.load_skills()

    def _ask_racial_skill_params(
        self, skill_id: str, skill_name: str, level_val=None, optional_val: bool | None = None
    ):
        """Egyszerű párbeszédablak a faji skill paramétereihez (szint/native + opcionális)."""
        from PySide6.QtWidgets import (
            QDialog,
            QDialogButtonBox,
            QFormLayout,
            QLabel,
            QVBoxLayout,
        )

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Képzettség hozzárendelése: {skill_name}")
        lay = QVBoxLayout(dlg)
        lay.addWidget(QLabel(f"Képzettség: {skill_name} ({skill_id})"))
        form = QFormLayout()
        lay.addLayout(form)
        level_cb = QComboBox()
        level_cb.addItem("native", userData="native")
        for i in range(1, 7):
            level_cb.addItem(str(i), userData=i)
        # set current
        if level_val == "native":
            level_cb.setCurrentIndex(0)
        elif isinstance(level_val, int) and 1 <= level_val <= 6:
            level_cb.setCurrentIndex(level_val)
        form.addRow("Szint:", level_cb)

        opt_cb = QCheckBox("Opcionális")
        if optional_val is not None:
            opt_cb.setChecked(bool(optional_val))
        form.addRow("", opt_cb)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        lay.addWidget(btns)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            return level_cb.currentData(), opt_cb.isChecked()
        return None, None

    # === Forbidden skills actions ===

    def add_forbidden_skill(self):
        if not self.current_race:
            return
        sid = self._get_selected_skill_id_from_tree()
        if not sid:
            QMessageBox.information(self, "Info", "Válassz ki egy képzettséget a fából!")
            return
        if sid not in self.current_race.forbidden_skills:
            self.current_race.forbidden_skills.append(sid)
            self.load_skills()

    def remove_forbidden_skill(self):
        if not self.current_race:
            return
        row = self.list_forbidden_skills.currentRow()
        if row < 0:
            return
        # Extract id from display "id - name" or just id
        text = self.list_forbidden_skills.item(row).text()
        sid = text.split(" - ")[0]
        try:
            self.current_race.forbidden_skills.remove(sid)
        except ValueError:
            pass
        self.load_skills()

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
                item = QListWidgetItem(f"{ability.name} ({ability.category})")
                item.setData(Qt.ItemDataRole.UserRole, ability.id)
                self.list_available_abilities.addItem(item)

        # Faj képességei
        self.list_race_abilities.clear()
        race_abilities = self.race_manager.get_race_special_abilities(self.current_race.id)
        for ability in race_abilities:
            item = QListWidgetItem(f"{ability.name} ({ability.category})")
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

    # === Special Abilities ===

    def show_ability_details(self, item: QListWidgetItem):
        """Speciális képesség részleteinek megjelenítése"""
        ability_id = item.data(Qt.ItemDataRole.UserRole)
        ability = self.race_manager.get_special_ability(ability_id)
        if ability:
            import json

            details = f"<h3>{ability.name}</h3>"
            details += f"<p><i>Kategória: {ability.category}</i></p>"
            details += f"<p>{ability.description}</p>"
            details += "<p><b>Játékmechanikai hatás:</b></p>"
            details += f"<pre>{json.dumps(ability.game_effect, indent=2, ensure_ascii=False)}</pre>"
            self.txt_ability_details.setHtml(details)

    def add_special_ability(self):
        """Speciális képesség hozzáadása a fajhoz"""
        if not self.current_race:
            return

        current_item = self.list_available_abilities.currentItem()
        if not current_item:
            QMessageBox.information(self, "Info", "Válassz ki egy képességet a listából!")
            return

        ability_id = current_item.data(Qt.ItemDataRole.UserRole)
        if ability_id not in self.current_race.special_abilities:
            self.current_race.special_abilities.append(ability_id)
            self.load_special_abilities()
            logger.info(f"Képesség hozzáadva: {ability_id}")

    def remove_special_ability(self):
        """Speciális képesség eltávolítása a fajtól"""
        if not self.current_race:
            return

        current_item = self.list_race_abilities.currentItem()
        if not current_item:
            QMessageBox.information(self, "Info", "Válassz ki egy képességet az eltávolításhoz!")
            return

        ability_id = current_item.data(Qt.ItemDataRole.UserRole)
        if ability_id in self.current_race.special_abilities:
            self.current_race.special_abilities.remove(ability_id)
            self.load_special_abilities()
            logger.info(f"Képesség eltávolítva: {ability_id}")

    # === Save/Create/Delete ===

    def save_race(self):
        """Faj mentése"""
        if not self.current_race:
            QMessageBox.warning(self, "Hiba", "Nincs betöltött faj!")
            return

        try:
            # Alapadatok
            self.current_race.name = self.txt_name.text().strip()
            if not self.current_race.name:
                QMessageBox.warning(self, "Hiba", "A faj neve nem lehet üres!")
                return

            # Tulajdonságok - MAGYAR mezőnevek!
            # Use model_validate with a dict to avoid mypy issues with non-ASCII keyword names
            self.current_race.attributes.modifiers = AttributeModifiers.model_validate(
                {
                    "Erő": self.spin_str.value(),
                    "Állóképesség": self.spin_con.value(),
                    "Gyorsaság": self.spin_spd.value(),
                    "Ügyesség": self.spin_dex.value(),
                    "Karizma": self.spin_cha.value(),
                    "Egészség": self.spin_hea.value(),
                    "Intelligencia": self.spin_int.value(),
                    "Akaraterő": self.spin_wil.value(),
                    "Asztrál": self.spin_ast.value(),
                    "Érzékelés": self.spin_per.value(),
                }
            )

            # Életkor
            self.current_race.age.min = self.spin_age_min.value()
            self.current_race.age.max = self.spin_age_max.value()

            # Leírás mentése
            desc_file = self.race_manager.data_dir / self.current_race.description_file
            desc_file.parent.mkdir(parents=True, exist_ok=True)
            desc_file.write_text(self.txt_description.toPlainText(), encoding="utf-8")

            # Faj mentése JSON-ba
            self.race_manager.save_race(self.current_race)

            QMessageBox.information(self, "Siker", f"{self.current_race.name} sikeresen mentve!")
            logger.info(f"Faj mentve: {self.current_race.id}")

            # Lista frissítése
            self.load_race_list()

        except Exception as e:
            logger.error(f"Hiba a mentés során: {e}", exc_info=True)
            QMessageBox.critical(self, "Hiba", f"Mentési hiba:\n{e}")

    def create_new_race(self):
        """Új faj létrehozása"""
        from PySide6.QtWidgets import QInputDialog

        race_name, ok = QInputDialog.getText(self, "Új faj", "Faj neve:")
        if ok and race_name.strip():
            # Generate ID from name
            race_id = (
                race_name.lower()
                .replace(" ", "_")
                .replace("á", "a")
                .replace("é", "e")
                .replace("ö", "o")
                .replace("ő", "o")
                .replace("ü", "u")
                .replace("ű", "u")
                .replace("í", "i")
            )

            # Check if exists
            if self.race_manager.get_race(race_id):
                QMessageBox.warning(self, "Hiba", f"'{race_name}' már létezik!")
                return

            # Create new race
            from engine.race import AgeData

            new_race = self.race_manager.create_race(
                race_id=race_id, name=race_name, age=AgeData(min=13, max=100, age_categories=[])
            )

            # Reload list and select new race
            self.load_race_list()
            self.load_race(new_race)

            QMessageBox.information(self, "Siker", f"'{race_name}' létrehozva!")

    def delete_race(self):
        """Faj törlése"""
        if not self.current_race:
            QMessageBox.warning(self, "Hiba", "Nincs kiválasztott faj!")
            return

        reply = QMessageBox.question(
            self,
            "Törlés megerősítése",
            f"Biztosan törölni szeretnéd: {self.current_race.name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            race_name = self.current_race.name
            if self.race_manager.delete_race(self.current_race.id):
                self.current_race = None
                self.load_race_list()
                QMessageBox.information(self, "Siker", f"'{race_name}' törölve!")
            else:
                QMessageBox.critical(self, "Hiba", "Törlés sikertelen!")


def main():
    """Main entry point"""
    app = QApplication(sys.argv)

    # Apply dark mode if available
    try:
        from utils.dark_mode import apply_dark_mode

        apply_dark_mode(app)
    except ImportError:
        pass

    window = RaceEditorQt()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
