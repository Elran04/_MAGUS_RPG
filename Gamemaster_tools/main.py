# --- IMPORTOK ÉS KONFIGURÁCIÓ ---
import os
import sys
from typing import Any

from config.paths import ICONS_DIR
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget
from utils.log.logger import get_logger
from utils.ui.dark_mode import apply_dark_mode

# Logger inicializálása
logger = get_logger(__name__)

last_character: dict[str, Any] = {}

# Keep references to child windows/dialogs to prevent garbage collection
_windows: list[Any] = []


# --- KÉPZETTSÉG SZERKESZTŐ ABLAK MEGNYITÁSA ---
def open_skill_editor():
    try:
        logger.info("Képzettség szerkesztő megnyitása")
        from ui.editors.skills.skill_editor import SkillEditorQt

        win = SkillEditorQt()
        win.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        _windows.append(win)
        win.show()
        logger.debug("Képzettség szerkesztő sikeresen megnyitva")
    except Exception as e:
        logger.error(f"Hiba a képzettség szerkesztő megnyitásakor: {e}", exc_info=True)


# --- FELSZERELÉS SZERKESZTŐ ABLAK MEGNYITÁSA ---
def open_equipment_editor():
    try:
        logger.info("Felszerelés szerkesztő megnyitása")
        from ui.editors.equipment.equipment_editor import EquipmentEditorQt

        win = EquipmentEditorQt()
        win.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        _windows.append(win)
        win.show()
        logger.debug("Felszerelés szerkesztő sikeresen megnyitva")
    except Exception as e:
        logger.error(f"Hiba a felszerelés szerkesztő megnyitásakor: {e}", exc_info=True)


# --- KARAKTERALKOTÁS MEGNYITÁSA ---
def open_character_creator():
    try:
        logger.info("Karakteralkotó megnyitása")
        from ui.character_creation.character_creator import CharacterWizardQt

        dlg = CharacterWizardQt()
        # Non-modal to avoid blocking main window; keep reference
        _windows.append(dlg)
        dlg.show()
        logger.debug("Karakteralkotó sikeresen megnyitva")
    except Exception as e:
        logger.error(f"Hiba a karakteralkotó megnyitásakor: {e}", exc_info=True)


# --- KASZT SZERKESZTŐ MEGNYITÁSA ---
def open_class_editor():
    try:
        logger.info("Kaszt szerkesztő megnyitása")
        from ui.editors.classes.class_editor import ClassEditorQt

        dlg = ClassEditorQt()
        _windows.append(dlg)
        dlg.show()
        logger.debug("Kaszt szerkesztő sikeresen megnyitva")
    except Exception as e:
        logger.error(f"Hiba a kaszt szerkesztő megnyitásakor: {e}", exc_info=True)


# --- FAJ SZERKESZTŐ MEGNYITÁSA ---
def open_race_editor():
    try:
        logger.info("Faj szerkesztő megnyitása")
        from ui.editors.races.race_editor import RaceEditorQt

        win = RaceEditorQt()
        win.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        _windows.append(win)
        win.show()
        logger.debug("Faj szerkesztő sikeresen megnyitva")
    except Exception as e:
        logger.error(f"Hiba a faj szerkesztő megnyitásakor: {e}", exc_info=True)


class MagusGMTools(QMainWindow):
    """M.A.G.U.S. Kalandmesteri eszköztár - Főablak"""

    def __init__(self):
        super().__init__()
        logger.info("MAGUS Kalandmesteri eszköztár indítása")
        self.setWindowTitle("M.A.G.U.S. Kalandmesteri eszköztár")
        self.setMinimumSize(500, 400)
        self.resize(600, 500)

        # Egyedi ikon beállítása
        icon_path = str(ICONS_DIR / "MAGUS.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.init_ui()

    def init_ui(self):
        """Felhasználói felület inicializálása"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(40, 40, 40, 40)

        # Címke
        title_label = QLabel("M.A.G.U.S. Kalandmesteri eszköztár")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)

        layout.addStretch()

        # Gombok
        btn_create_char = QPushButton("Karaktergenerálás")
        btn_create_char.setMinimumHeight(40)
        btn_create_char.clicked.connect(open_character_creator)
        layout.addWidget(btn_create_char)

        btn_race_editor = QPushButton("🧝 Faj szerkesztő")
        btn_race_editor.setMinimumHeight(40)
        btn_race_editor.clicked.connect(open_race_editor)
        layout.addWidget(btn_race_editor)

        btn_class_editor = QPushButton("Kaszt szerkesztő")
        btn_class_editor.setMinimumHeight(40)
        btn_class_editor.clicked.connect(open_class_editor)
        layout.addWidget(btn_class_editor)

        btn_skill_editor = QPushButton("Képzettség szerkesztő")
        btn_skill_editor.setMinimumHeight(40)
        btn_skill_editor.clicked.connect(open_skill_editor)
        layout.addWidget(btn_skill_editor)

        btn_equipment_editor = QPushButton("Felszerelés szerkesztő")
        btn_equipment_editor.setMinimumHeight(40)
        btn_equipment_editor.clicked.connect(open_equipment_editor)
        layout.addWidget(btn_equipment_editor)

        layout.addStretch()

        # Kilépés gomb
        btn_exit = QPushButton("Kilépés")
        btn_exit.setMinimumHeight(35)
        btn_exit.clicked.connect(self.close)
        layout.addWidget(btn_exit)

        central_widget.setLayout(layout)


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("MAGUS RPG Gamemaster Tools alkalmazás indítása")
    logger.info("=" * 60)

    app = QApplication(sys.argv)
    apply_dark_mode(app)
    logger.debug("Dark mode alkalmazva")

    window = MagusGMTools()
    window.show()

    logger.info("Főablak megjelenítve, alkalmazás fut")
    exit_code = app.exec()
    logger.info(f"Alkalmazás leállítva, exit code: {exit_code}")
    sys.exit(exit_code)
