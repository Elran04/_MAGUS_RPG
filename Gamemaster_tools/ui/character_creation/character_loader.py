"""Character Loader and Editor Dialog.

Allows users to:
1. Browse and select saved characters from characters/ directory
2. View character details
3. Edit character data
4. Save changes back to JSON
"""

import os
import sys
from typing import Any

from PySide6 import QtWidgets

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from config.paths import CHARACTERS_DIR
from ui.character_creation.steps.summary_step import SummaryStepWidget
from utils.data.character_storage import load_character, save_character
from utils.log.logger import get_logger

logger = get_logger(__name__)


class CharacterLoaderQt(QtWidgets.QDialog):
    """Character loader and editor dialog."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Karakter betöltése és szerkesztése")
        self.resize(1200, 700)

        self.current_character: dict[str, Any] = {}
        self.character_filename: str | None = None

        self.init_ui()
        self.refresh_character_list()

    def init_ui(self) -> None:
        """Build the UI layout."""
        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(12, 12, 12, 12)

        # Left panel: Character list
        left_panel = self._build_left_panel()
        main_layout.addWidget(left_panel, stretch=1)

        # Right panel: Character details and editor
        right_panel = self._build_right_panel()
        main_layout.addWidget(right_panel, stretch=2)

    def _build_left_panel(self) -> QtWidgets.QWidget:
        """Build left panel with character list."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Title
        title = QtWidgets.QLabel("Mentett karakterek")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)

        # Character list
        self.character_list = QtWidgets.QListWidget()
        self.character_list.itemSelectionChanged.connect(self._on_character_selected)
        layout.addWidget(self.character_list)

        # Buttons
        button_layout = QtWidgets.QVBoxLayout()

        self.btn_delete = QtWidgets.QPushButton("Törlés")
        self.btn_delete.clicked.connect(self._delete_character)
        self.btn_delete.setEnabled(False)
        button_layout.addWidget(self.btn_delete)

        self.btn_refresh = QtWidgets.QPushButton("Frissítés")
        self.btn_refresh.clicked.connect(self.refresh_character_list)
        button_layout.addWidget(self.btn_refresh)

        layout.addLayout(button_layout)
        return widget

    def _build_right_panel(self) -> QtWidgets.QWidget:
        """Build right panel with character details and editor."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Title
        title = QtWidgets.QLabel("Karakteradatok")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)

        # Summary widget (read-only display)
        def _get_current_character() -> dict[str, Any]:
            return self.current_character

        self.summary_widget = SummaryStepWidget(_get_current_character)
        layout.addWidget(self.summary_widget, stretch=1)

        # Button layout at bottom
        button_layout = QtWidgets.QHBoxLayout()

        self.btn_save = QtWidgets.QPushButton("Mentés")
        self.btn_save.clicked.connect(self._save_character)
        self.btn_save.setEnabled(False)
        button_layout.addWidget(self.btn_save)

        self.btn_close = QtWidgets.QPushButton("Bezárás")
        self.btn_close.clicked.connect(self.close)
        button_layout.addWidget(self.btn_close)

        layout.addLayout(button_layout)
        return widget

    def refresh_character_list(self) -> None:
        """Refresh the list of available characters."""
        self.character_list.clear()
        self.current_character = {}
        self.character_filename = None

        try:
            character_dir = str(CHARACTERS_DIR)
            if not os.path.exists(character_dir):
                logger.warning(f"Character directory not found: {character_dir}")
                return

            files = [f for f in os.listdir(character_dir) if f.endswith(".json")]
            for filename in sorted(files):
                self.character_list.addItem(filename)

            logger.info(f"Character list refreshed: {len(files)} characters found")
        except Exception as e:
            logger.error(f"Error refreshing character list: {e}", exc_info=True)
            QtWidgets.QMessageBox.critical(
                self, "Hiba", f"Hiba a karakterlista frissítésekor:\n{e}"
            )

    def _on_character_selected(self) -> None:
        """Handle character selection."""
        current_item = self.character_list.currentItem()
        if not current_item:
            self.current_character = {}
            self.character_filename = None
            self.btn_delete.setEnabled(False)
            self.btn_save.setEnabled(False)
            self.summary_widget.refresh()
            return

        filename = current_item.text()
        try:
            char_data = load_character(filename)
            if char_data:
                self.current_character = char_data
                self.character_filename = filename
                self.btn_delete.setEnabled(True)
                self.btn_save.setEnabled(True)
                logger.info(f"Character loaded: {filename}")
            else:
                logger.warning(f"Failed to load character: {filename}")
                QtWidgets.QMessageBox.warning(
                    self, "Figyelmeztetés", f"A karakter nem tölthető be:\n{filename}"
                )
                self.current_character = {}
                self.character_filename = None
        except Exception as e:
            logger.error(f"Error loading character {filename}: {e}", exc_info=True)
            QtWidgets.QMessageBox.critical(self, "Hiba", f"Hiba a karakter betöltésekor:\n{e}")
            self.current_character = {}
            self.character_filename = None

        self.summary_widget.refresh()

    def _save_character(self) -> None:
        """Save the current character."""
        if not self.character_filename or not self.current_character:
            QtWidgets.QMessageBox.warning(self, "Figyelmeztetés", "Nincs karakter kiválasztva")
            return

        try:
            success = save_character(self.current_character, self.character_filename)
            if success:
                QtWidgets.QMessageBox.information(
                    self, "Siker", f"Karakter mentve:\n{self.character_filename}"
                )
                logger.info(f"Character saved: {self.character_filename}")
            else:
                QtWidgets.QMessageBox.critical(
                    self, "Hiba", f"Nem sikerült menteni a karaktert:\n{self.character_filename}"
                )
        except Exception as e:
            logger.error(f"Error saving character: {e}", exc_info=True)
            QtWidgets.QMessageBox.critical(self, "Hiba", f"Hiba a karakter mentésekor:\n{e}")

    def _delete_character(self) -> None:
        """Delete the selected character."""
        if not self.character_filename:
            return

        reply = QtWidgets.QMessageBox.question(
            self,
            "Megerősítés",
            f"Biztosan törlöd:\n{self.character_filename}?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No,
        )

        if reply != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        try:
            character_path = os.path.join(str(CHARACTERS_DIR), self.character_filename)
            if os.path.exists(character_path):
                os.remove(character_path)
                logger.info(f"Character deleted: {self.character_filename}")
                QtWidgets.QMessageBox.information(
                    self, "Siker", f"Karakter törölve:\n{self.character_filename}"
                )
                self.refresh_character_list()
            else:
                logger.warning(f"Character file not found: {character_path}")
                QtWidgets.QMessageBox.warning(
                    self,
                    "Figyelmeztetés",
                    f"A karakterfájl nem található:\n{self.character_filename}",
                )
        except Exception as e:
            logger.error(f"Error deleting character: {e}", exc_info=True)
            QtWidgets.QMessageBox.critical(self, "Hiba", f"Hiba a karakter törlésekor:\n{e}")


if __name__ == "__main__":
    from utils.ui.dark_mode import apply_dark_mode

    app = QtWidgets.QApplication(sys.argv)
    apply_dark_mode(app)

    loader = CharacterLoaderQt()
    loader.exec()
