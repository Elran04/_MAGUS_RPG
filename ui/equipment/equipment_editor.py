"""
Main equipment editor UI for MAGUS RPG.

This module provides the main equipment editor interface that allows access
to specialized editors for armor, weapons/shields, and general equipment.
"""

import tkinter as tk
from tkinter import messagebox

class EquipmentEditor:
    """
    Main equipment editor window.
    
    Provides a hub for accessing different equipment editors:
    - Armor editor
    - Weapons and shields editor
    - General equipment editor
    
    Attributes:
        win (tk.Toplevel): Main editor window
    """
    def __init__(self):
        from utils.reopen_prevention import WindowSingleton
        self.win, created = WindowSingleton.get('equipment_editor', lambda: tk.Toplevel())
        if not created:
            return
        self.win.title("Felszerelés szerkesztő")
        self.win.geometry("900x600")
        self.create_widgets()
        self.win.mainloop()

    def create_widgets(self):
        """Create and layout UI widgets."""
        tk.Label(self.win, text="Felszerelés szerkesztő", font=("Arial", 18, "bold")).pack(pady=20)

        button_frame = tk.Frame(self.win)
        button_frame.pack(pady=30)

        tk.Button(button_frame, text="Páncélok szerkesztése", width=30, command=self.open_armor_editor).pack(pady=10)
        tk.Button(button_frame, text="Fegyverek és pajzsok szerkesztése", width=30, command=self.open_weapons_editor).pack(pady=10)
        tk.Button(button_frame, text="Általános felszerelés szerkesztése", width=30, command=self.open_general_editor).pack(pady=10)

        tk.Button(self.win, text="Kilépés", command=self.win.destroy).pack(pady=30)

    def open_armor_editor(self):
        """Open the armor editor window."""
        from ui.equipment.armor_editor import ArmorEditor
        ArmorEditor()

    def open_weapons_editor(self):
        """Open the weapons and shields editor in a subprocess."""
        import subprocess, sys, os
        script_path = os.path.join(os.path.dirname(__file__), "weapons_and_shields_editor.py")
        subprocess.Popen([sys.executable, script_path])

    def open_general_editor(self):
        """Open the general equipment editor window."""
        from ui.equipment.general_equipment_editor import GeneralEquipmentEditor
        GeneralEquipmentEditor()

if __name__ == "__main__":
    EquipmentEditor()
