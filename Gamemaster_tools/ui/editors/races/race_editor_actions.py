"""
Race Editor Actions
Handles all user actions (save, create, delete, skill management, etc.)
"""

from PySide6 import QtCore, QtWidgets
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QInputDialog,
    QLabel,
    QListWidgetItem,
    QMessageBox,
    QTableWidgetItem,
    QVBoxLayout,
)

from core.race_model import AgeData, AttributeModifiers, RacialSkill
from utils.log.logger import get_logger

logger = get_logger(__name__)


class RaceEditorActions:
    """Handles all race editor actions"""

    def __init__(self, editor):
        """
        Initialize actions handler

        Args:
            editor: RaceEditorQt instance
        """
        self.editor = editor

    # === Racial Skills Actions ===

    def get_selected_skill_id_from_tree(self) -> str | None:
        """Get selected skill ID from tree widget"""
        item = self.editor.tabs.skill_tree.currentItem()
        if not item:
            return None
        sid = item.data(1, QtCore.Qt.ItemDataRole.UserRole)
        return str(sid) if sid is not None else None

    def add_racial_skill(self):
        """Képzettség hozzáadása a faji listához"""
        if not self.editor.tabs.current_race:
            QMessageBox.warning(self.editor, "Nincs kiválasztva", "Előbb válassz ki egy fajt!")
            return

        sid = self.get_selected_skill_id_from_tree()
        if not sid:
            QMessageBox.information(self.editor, "Info", "Válassz ki egy képzettséget a fából!")
            return

        name = self.editor.tabs.resolve_skill_name(sid)
        level = self.ask_racial_skill_params(sid, name)
        if level is None:
            return

        # If already exists, update instead of duplicate
        existing_idx = next(
            (
                i
                for i, rs in enumerate(self.editor.tabs.current_race.racial_skills)
                if rs.skill_id == sid
            ),
            None,
        )
        if existing_idx is not None:
            self.editor.tabs.current_race.racial_skills[existing_idx].level = level
        else:
            self.editor.tabs.current_race.racial_skills.append(
                RacialSkill(skill_id=sid, level=level)
            )
        self.editor.tabs.load_skills()

    def edit_racial_skill(self):
        """Edit existing racial skill"""
        row = self.editor.tabs.racial_skills_table.currentRow()
        if row < 0 or not self.editor.tabs.current_race:
            QMessageBox.information(self.editor, "Info", "Válassz ki egy faji képzettséget!")
            return

        item0 = self.editor.tabs.racial_skills_table.item(row, 0)
        item1 = self.editor.tabs.racial_skills_table.item(row, 1)
        if not item0 or not item1:
            return

        sid = item0.text()
        name = item1.text()

        # Find existing
        idx = next(
            (
                i
                for i, rs in enumerate(self.editor.tabs.current_race.racial_skills)
                if rs.skill_id == sid
            ),
            None,
        )
        if idx is None:
            return

        current = self.editor.tabs.current_race.racial_skills[idx]
        level = self.ask_racial_skill_params(sid, name, current.level)
        if level is None:
            return

        current.level = level
        self.editor.tabs.load_skills()

    def delete_racial_skill(self):
        """Delete racial skill"""
        row = self.editor.tabs.racial_skills_table.currentRow()
        if row < 0 or not self.editor.tabs.current_race:
            return

        item0 = self.editor.tabs.racial_skills_table.item(row, 0)
        if not item0:
            return

        sid = item0.text()
        self.editor.tabs.current_race.racial_skills = [
            rs for rs in self.editor.tabs.current_race.racial_skills if rs.skill_id != sid
        ]
        self.editor.tabs.load_skills()

    def ask_racial_skill_params(
        self, skill_id: str, skill_name: str, level_val=None
    ) -> int | None:
        """Egyszerű párbeszédablak a faji skill paramétereihez (szint 1-6)."""
        dlg = QDialog(self.editor)
        dlg.setWindowTitle(f"Képzettség hozzárendelése: {skill_name}")
        lay = QVBoxLayout(dlg)
        lay.addWidget(QLabel(f"Képzettség: {skill_name} ({skill_id})"))

        form = QFormLayout()
        lay.addLayout(form)

        level_cb = QComboBox()
        for i in range(1, 7):
            level_cb.addItem(str(i), userData=i)

        # Set current
        if isinstance(level_val, int) and 1 <= level_val <= 6:
            level_cb.setCurrentIndex(level_val - 1)

        form.addRow("Szint:", level_cb)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        lay.addWidget(btns)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            return level_cb.currentData()
        return None

    # === Forbidden Skills Actions ===

    def add_forbidden_skill(self):
        """Add skill to forbidden list"""
        if not self.editor.tabs.current_race:
            return

        sid = self.get_selected_skill_id_from_tree()
        if not sid:
            QMessageBox.information(self.editor, "Info", "Válassz ki egy képzettséget a fából!")
            return

        if sid not in self.editor.tabs.current_race.forbidden_skills:
            self.editor.tabs.current_race.forbidden_skills.append(sid)
            self.editor.tabs.load_skills()

    def remove_forbidden_skill(self):
        """Remove skill from forbidden list"""
        if not self.editor.tabs.current_race:
            return

        row = self.editor.tabs.list_forbidden_skills.currentRow()
        if row < 0:
            return

        # Extract id from display "id - name" or just id
        text = self.editor.tabs.list_forbidden_skills.item(row).text()
        sid = text.split(" - ")[0]

        try:
            self.editor.tabs.current_race.forbidden_skills.remove(sid)
        except ValueError:
            pass

        self.editor.tabs.load_skills()

    # === Special Abilities Actions ===

    def add_special_ability(self):
        """Speciális képesség hozzáadása a fajhoz"""
        if not self.editor.tabs.current_race:
            return

        current_item = self.editor.tabs.list_available_abilities.currentItem()
        if not current_item:
            QMessageBox.information(self.editor, "Info", "Válassz ki egy képességet a listából!")
            return

        ability_id = current_item.data(QtCore.Qt.ItemDataRole.UserRole)
        if ability_id not in self.editor.tabs.current_race.special_abilities:
            self.editor.tabs.current_race.special_abilities.append(ability_id)
            self.editor.tabs.load_special_abilities()
            logger.info(f"Képesség hozzáadva: {ability_id}")

    def remove_special_ability(self):
        """Speciális képesség eltávolítása a fajtól"""
        if not self.editor.tabs.current_race:
            return

        current_item = self.editor.tabs.list_race_abilities.currentItem()
        if not current_item:
            QMessageBox.information(
                self.editor, "Info", "Válassz ki egy képességet az eltávolításhoz!"
            )
            return

        ability_id = current_item.data(QtCore.Qt.ItemDataRole.UserRole)
        if ability_id in self.editor.tabs.current_race.special_abilities:
            self.editor.tabs.current_race.special_abilities.remove(ability_id)
            self.editor.tabs.load_special_abilities()
            logger.info(f"Képesség eltávolítva: {ability_id}")

    # === Save/Create/Delete ===

    def save_race(self):
        """Faj mentése"""
        if not self.editor.tabs.current_race:
            QMessageBox.warning(self.editor, "Hiba", "Nincs betöltött faj!")
            return

        try:
            # Alapadatok
            self.editor.tabs.current_race.name = self.editor.tabs.txt_name.text().strip()
            if not self.editor.tabs.current_race.name:
                QMessageBox.warning(self.editor, "Hiba", "A faj neve nem lehet üres!")
                return

            # Tulajdonságok - MAGYAR mezőnevek!
            attr_dict = {
                attr_name: self.editor.tabs.spin_attrs[attr_name].value()
                for attr_name in self.editor.tabs.spin_attrs
            }
            self.editor.tabs.current_race.attributes.modifiers = (
                AttributeModifiers.model_validate(attr_dict)
            )

            # Életkor
            self.editor.tabs.current_race.age.min = self.editor.tabs.spin_age_min.value()
            self.editor.tabs.current_race.age.max = self.editor.tabs.spin_age_max.value()

            # Leírás mentése
            # Leírás mentése
            desc_file = (
                self.editor.race_manager.data_dir
                / self.editor.tabs.current_race.description_file
            )
            desc_file.parent.mkdir(parents=True, exist_ok=True)
            desc_file.write_text(self.editor.tabs.txt_description.toPlainText(), encoding="utf-8")

            # Faj mentése JSON-ba
            self.editor.race_manager.save_race(self.editor.tabs.current_race)

            QMessageBox.information(
                self.editor, "Siker", f"{self.editor.tabs.current_race.name} sikeresen mentve!"
            )
            logger.info(f"Faj mentve: {self.editor.tabs.current_race.id}")

            # Lista frissítése
            self.editor.race_list_panel.refresh()

        except (IOError, OSError, TypeError) as e:
            logger.error(f"Hiba a mentés során: {e}", exc_info=True)
            QMessageBox.critical(self.editor, "Hiba", f"Mentési hiba:\n{e}")

    def create_new_race(self):
        """Új faj létrehozása"""
        race_name, ok = QInputDialog.getText(self.editor, "Új faj", "Faj neve:")
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
            if self.editor.race_manager.get_race(race_id):
                QMessageBox.warning(self.editor, "Hiba", f"'{race_name}' már létezik!")
                return

            # Create new race
            new_race = self.editor.race_manager.create_race(
                race_id=race_id, name=race_name, age=AgeData(min=13, max=100, age_categories=[])
            )

            # Reload list and select new race
            self.editor.race_list_panel.refresh()
            self.editor.tabs.load_race(new_race)

            QMessageBox.information(self.editor, "Siker", f"'{race_name}' létrehozva!")

    def delete_race(self):
        """Faj törlése"""
        if not self.editor.tabs.current_race:
            QMessageBox.warning(self.editor, "Hiba", "Nincs kiválasztott faj!")
            return

        reply = QMessageBox.question(
            self.editor,
            "Törlés megerősítése",
            f"Biztosan törölni szeretnéd: {self.editor.tabs.current_race.name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            race_name = self.editor.tabs.current_race.name
            if self.editor.race_manager.delete_race(self.editor.tabs.current_race.id):
                self.editor.tabs.current_race = None
                self.editor.race_list_panel.refresh()
                QMessageBox.information(self.editor, "Siker", f"'{race_name}' törölve!")
            else:
                QMessageBox.critical(self.editor, "Hiba", "Törlés sikertelen!")
