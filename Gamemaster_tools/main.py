# --- IMPORTOK ÉS KONFIGURÁCIÓ ---
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
import subprocess
import sys
import os
from utils.dark_mode import apply_dark_mode

last_character = {}

# --- KÉPZETTSÉG SZERKESZTŐ ABLAK MEGNYITÁSA ---
def open_skill_editor():
    script_path = os.path.join(os.path.dirname(__file__), "ui", "skills", "skill_editor.py")
    subprocess.Popen([sys.executable, script_path])

# --- FELSZERELÉS SZERKESZTŐ ABLAK MEGNYITÁSA ---
def open_equipment_editor():
    script_path = os.path.join(os.path.dirname(__file__), "ui", "equipment", "equipment_editor.py")
    subprocess.Popen([sys.executable, script_path])

# --- KARAKTERALKOTÁS MEGNYITÁSA ---
def open_character_creator():
    script_path = os.path.join(os.path.dirname(__file__), "ui", "character_creator.py")
    subprocess.Popen([sys.executable, script_path])

# --- KASZT SZERKESZTŐ MEGNYITÁSA ---
def open_class_editor():
    script_path = os.path.join(os.path.dirname(__file__), "ui", "class_editor.py")
    subprocess.Popen([sys.executable, script_path])


class MagusGMTools(QMainWindow):
    """M.A.G.U.S. Kalandmesteri eszköztár - Főablak"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("M.A.G.U.S. Kalandmesteri eszköztár")
        self.setMinimumSize(500, 400)
        self.resize(600, 500)
        
        # Egyedi ikon beállítása
        icon_path = os.path.join(os.path.dirname(__file__), "assets_icons", "MAGUS.ico")
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
        
        btn_skill_editor = QPushButton("Képzettség szerkesztő")
        btn_skill_editor.setMinimumHeight(40)
        btn_skill_editor.clicked.connect(open_skill_editor)
        layout.addWidget(btn_skill_editor)
        
        btn_equipment_editor = QPushButton("Felszerelés szerkesztő")
        btn_equipment_editor.setMinimumHeight(40)
        btn_equipment_editor.clicked.connect(open_equipment_editor)
        layout.addWidget(btn_equipment_editor)
        
        btn_class_editor = QPushButton("Kaszt szerkesztő")
        btn_class_editor.setMinimumHeight(40)
        btn_class_editor.clicked.connect(open_class_editor)
        layout.addWidget(btn_class_editor)
        
        layout.addStretch()
        
        # Kilépés gomb
        btn_exit = QPushButton("Kilépés")
        btn_exit.setMinimumHeight(35)
        btn_exit.clicked.connect(self.close)
        layout.addWidget(btn_exit)
        
        central_widget.setLayout(layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_dark_mode(app)
    
    window = MagusGMTools()
    window.show()
    
    sys.exit(app.exec())
