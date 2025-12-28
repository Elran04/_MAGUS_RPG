"""
Equipment Editor - PySide6 version with dark mode
Tabbed interface for managing armor, weapons/shields, and general equipment
"""

import os
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget
from ui.editors.equipment.armor_editor import ArmorEditorQt
from ui.editors.equipment.general_equipment_editor import GeneralEquipmentEditorQt
from ui.editors.equipment.weapons_and_shields_editor import WeaponsAndShieldsEditor

# Ensure project package root (Gamemaster_tools) is on sys.path so 'ui' and 'utils' imports work
_HERE = os.path.dirname(__file__)
_PROJECT_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


class EquipmentEditorQt(QMainWindow):
    """Tabbed equipment editor for armor, weapons, and general equipment"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Felszerelés szerkesztő")
        self.resize(1400, 800)

        # Standard window controls
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowMaximizeButtonHint
            | Qt.WindowType.WindowCloseButtonHint
        )

        self.init_ui()

    def init_ui(self):
        """Initialize the tabbed user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create tab widget
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)

        # Create editor instances (but don't show them as separate windows)
        # Armor tab
        self.armor_editor = ArmorEditorQt()
        # Extract the central widget from the QMainWindow and use it as a tab
        armor_widget = self.armor_editor.centralWidget()
        tab_widget.addTab(armor_widget, "Páncélok")

        # Weapons and shields tab
        self.weapons_editor = WeaponsAndShieldsEditor()
        weapons_widget = self.weapons_editor.centralWidget()
        tab_widget.addTab(weapons_widget, "Fegyverek és pajzsok")

        # General equipment tab
        self.general_editor = GeneralEquipmentEditorQt()
        general_widget = self.general_editor.centralWidget()
        tab_widget.addTab(general_widget, "Általános felszerelés")


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    from utils.ui.dark_mode import apply_dark_mode

    app = QApplication(sys.argv)
    apply_dark_mode(app)

    editor = EquipmentEditorQt()
    editor.show()

    sys.exit(app.exec())
