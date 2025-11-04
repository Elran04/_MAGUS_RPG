"""
Special Ability Editor
CRUD UI for managing SpecialAbilities stored by RaceManager in special_abilities.json
"""

from __future__ import annotations

import json
from typing import Callable

from core.race_model import SpecialAbility
from engine.race_manager import RaceManager
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

ABILITY_CATEGORIES = [
    "vision",
    "senses",
    "environmental",
    "resistance",
    "learning",
    "combat",
    "psionic",
    "transformation",
]


class SpecialAbilityEditor(QWidget):
    """Widget for editing SpecialAbility definitions."""

    def __init__(
        self,
        race_manager: RaceManager,
        parent: QWidget | None = None,
        on_change: Callable[[], None] | None = None,
    ):
        super().__init__(parent)
        self.race_manager = race_manager
        self.current_id: str | None = None
        self._on_change = on_change

        self._build_ui()
        self.refresh_list()

    def _build_ui(self):
        root = QHBoxLayout(self)

        # Left: list of abilities
        left = QVBoxLayout()
        self.list_abilities = QListWidget()
        left.addWidget(QLabel("<b>Speciális képességek</b>"))
        left.addWidget(self.list_abilities)

        btn_row = QHBoxLayout()
        self.btn_new = QPushButton("Új")
        self.btn_delete = QPushButton("Törlés")
        btn_row.addWidget(self.btn_new)
        btn_row.addWidget(self.btn_delete)
        btn_row.addStretch()
        left.addLayout(btn_row)

        left_w = QWidget()
        left_w.setLayout(left)
        root.addWidget(left_w, 1)

        # Right: editor form
        right = QVBoxLayout()
        form = QFormLayout()
        self.txt_id = QLineEdit()
        self.txt_name = QLineEdit()
        self.txt_icon = QLineEdit()
        self.btn_browse_icon = QPushButton("Tallózás…")

        icon_row = QHBoxLayout()
        icon_row.addWidget(self.txt_icon)
        icon_row.addWidget(self.btn_browse_icon)

        self.txt_description = QTextEdit()
        self.txt_description.setPlaceholderText("Rövid leírás…")

        self.txt_game_effect = QTextEdit()
        self.txt_game_effect.setPlaceholderText("{" "example" ": 1}")
        self.txt_game_effect.setAcceptRichText(False)
        self.txt_game_effect.setTabChangesFocus(True)

        form.addRow("ID:", self.txt_id)
        form.addRow("Név:", self.txt_name)
        form.addRow("Ikon:", icon_row)
        form.addRow("Leírás:", self.txt_description)
        form.addRow("Játékmenet (JSON):", self.txt_game_effect)

        right.addLayout(form)

        # Action buttons
        actions = QHBoxLayout()
        self.btn_validate = QPushButton("JSON ellenőrzés")
        self.btn_save = QPushButton("Mentés")
        actions.addStretch()
        actions.addWidget(self.btn_validate)
        actions.addWidget(self.btn_save)
        right.addLayout(actions)

        right_w = QWidget()
        right_w.setLayout(right)
        root.addWidget(right_w, 2)

        # Signals
        self.list_abilities.itemSelectionChanged.connect(self.on_select_ability)
        self.btn_new.clicked.connect(self.create_new)
        self.btn_delete.clicked.connect(self.delete_current)
        self.btn_browse_icon.clicked.connect(self.browse_icon)
        self.btn_validate.clicked.connect(self.validate_json)
        self.btn_save.clicked.connect(self.save_current)

    # === Data operations ===

    def refresh_list(self):
        self.list_abilities.clear()
        for ability in self.race_manager.get_all_special_abilities():
            item = QListWidgetItem(ability.name)
            item.setData(Qt.ItemDataRole.UserRole, ability.id)
            self.list_abilities.addItem(item)

    def on_select_ability(self):
        item = self.list_abilities.currentItem()
        if not item:
            self.clear_form()
            return
        ability_id = item.data(Qt.ItemDataRole.UserRole)
        ability = self.race_manager.get_special_ability(ability_id)
        if ability:
            self.load_ability(ability)

    def clear_form(self):
        self.current_id = None
        self.txt_id.setText("")
        self.txt_id.setReadOnly(False)
        self.txt_name.setText("")
        self.txt_icon.setText("")
        self.txt_description.setPlainText("")
        self.txt_game_effect.setPlainText("{}")

    def load_ability(self, ability: SpecialAbility):
        self.current_id = ability.id
        self.txt_id.setText(ability.id)
        self.txt_id.setReadOnly(True)  # prevent ID changes for existing entries
        self.txt_name.setText(ability.name)
        self.txt_icon.setText(ability.icon or "")
        self.txt_description.setPlainText(ability.description)
        self.txt_game_effect.setPlainText(
            json.dumps(ability.game_effect, ensure_ascii=False, indent=2)
        )

    def browse_icon(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Ikon kiválasztása", "", "Képfájlok (*.png *.jpg *.svg)"
        )
        if path:
            self.txt_icon.setText(path)

    def validate_json(self) -> bool:
        text = self.txt_game_effect.toPlainText().strip() or "{}"
        try:
            json.loads(text)
            QMessageBox.information(self, "OK", "Érvényes JSON.")
            return True
        except (json.JSONDecodeError, ValueError) as e:
            QMessageBox.critical(self, "Hiba", f"Érvénytelen JSON:\n{e}")
            return False

    def save_current(self):
        # Validate input
        ability_id = self.txt_id.text().strip()
        name = self.txt_name.text().strip()
        if not ability_id or not name:
            QMessageBox.warning(self, "Hiba", "ID és Név kötelező.")
            return
        # Parse JSON
        try:
            game_effect = json.loads(self.txt_game_effect.toPlainText().strip() or "{}")
        except (json.JSONDecodeError, ValueError) as e:
            QMessageBox.critical(self, "Hiba", f"Érvénytelen JSON:\n{e}")
            return

        # Build ability
        ability = SpecialAbility(
            id=ability_id,
            name=name,
            description=self.txt_description.toPlainText(),
            game_effect=game_effect,
            icon=self.txt_icon.text().strip() or None,
        )

        # If creating new and ID exists, confirm overwrite
        if self.current_id is None and self.race_manager.get_special_ability(ability_id):
            reply = QMessageBox.question(
                self,
                "Felülírás megerősítése",
                f"A(z) '{ability_id}' már létezik. Felülírja?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        try:
            self.race_manager.save_special_ability(ability)
            self.current_id = ability.id
            self.txt_id.setReadOnly(True)
            QMessageBox.information(self, "Siker", "Képesség mentve.")
            self.refresh_list()
            # Reselect saved item
            self._select_item_by_id(ability.id)
            if self._on_change is not None:
                self._on_change()
        except (OSError, TypeError) as e:
            QMessageBox.critical(self, "Hiba", f"Mentési hiba:\n{e}")

    def delete_current(self):
        item = self.list_abilities.currentItem()
        if not item:
            return
        ability_id = item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(
            self,
            "Törlés megerősítése",
            f"Biztosan törli a képességet: {ability_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        if self.race_manager.delete_special_ability(ability_id):
            QMessageBox.information(self, "Siker", "Képesség törölve.")
            self.clear_form()
            self.refresh_list()
            if self._on_change is not None:
                self._on_change()
        else:
            QMessageBox.critical(self, "Hiba", "Törlés sikertelen.")

    def _select_item_by_id(self, ability_id: str):
        for i in range(self.list_abilities.count()):
            it = self.list_abilities.item(i)
            if it.data(Qt.ItemDataRole.UserRole) == ability_id:
                self.list_abilities.setCurrentRow(i)
                break

    # === UI helper actions ===

    def create_new(self):
        """Start creating a new ability: clear form and unlock ID field."""
        self.clear_form()
        self.txt_id.setReadOnly(False)
        self.txt_id.setFocus()
