"""
Equipment Editor Hub - PySide6 version with dark mode
Launch point for armor, weapons, and general equipment editors
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import subprocess
import sys
import os


class EquipmentEditorQt(QMainWindow):
    """Equipment editor hub window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Felszerelés szerkesztő")
        self.resize(600, 500)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(50, 50, 50, 50)
        central_widget.setLayout(layout)
        
        # Title
        title_label = QLabel("Felszerelés szerkesztő")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # Armor button
        btn_armor = QPushButton("Páncélok szerkesztése")
        btn_armor.setMinimumHeight(50)
        btn_armor.clicked.connect(self.open_armor_editor)
        layout.addWidget(btn_armor)
        
        # Weapons button
        btn_weapons = QPushButton("Fegyverek és pajzsok szerkesztése")
        btn_weapons.setMinimumHeight(50)
        btn_weapons.clicked.connect(self.open_weapons_editor)
        layout.addWidget(btn_weapons)
        
        # General equipment button
        btn_general = QPushButton("Általános felszerelés szerkesztése")
        btn_general.setMinimumHeight(50)
        btn_general.clicked.connect(self.open_general_editor)
        layout.addWidget(btn_general)
        
        layout.addStretch()
        
        # Close button
        btn_close = QPushButton("Bezárás")
        btn_close.setMinimumHeight(40)
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close)
    
    def open_armor_editor(self):
        """Open armor editor"""
        try:
            # Use absolute import since this file runs as a script
            from ui.equipment.armor_editor import ArmorEditorQt
            if not hasattr(self, '_children'):
                self._children = []
            win = ArmorEditorQt()
            win.setAttribute(Qt.WA_DeleteOnClose, True)
            self._children.append(win)
            win.show()
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Hiba", f"Nem sikerült megnyitni a páncél szerkesztőt.\n{e}")
    
    def open_weapons_editor(self):
        """Open weapons and shields editor"""
        script_path = os.path.join(os.path.dirname(__file__), "weapons_and_shields_editor.py")
        subprocess.Popen([sys.executable, script_path])
    
    def open_general_editor(self):
        """Open general equipment editor"""
        try:
            # Use absolute import since this file runs as a script
            from ui.equipment.general_equipment_editor import GeneralEquipmentEditorQt
            if not hasattr(self, '_children'):
                self._children = []
            win = GeneralEquipmentEditorQt()
            win.setAttribute(Qt.WA_DeleteOnClose, True)
            self._children.append(win)
            win.show()
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Hiba", f"Nem sikerült megnyitni az általános felszerelés szerkesztőt.\n{e}")


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from utils.dark_mode import apply_dark_mode
    
    app = QApplication(sys.argv)
    apply_dark_mode(app)
    
    editor = EquipmentEditorQt()
    editor.show()
    
    sys.exit(app.exec())
