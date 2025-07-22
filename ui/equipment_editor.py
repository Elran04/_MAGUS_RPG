import tkinter as tk
from tkinter import messagebox

class EquipmentEditor:
    def __init__(self):
        self.win = tk.Tk()
        self.win.title("Felszerelés szerkesztő")
        self.win.geometry("900x600")
        self.create_widgets()
        self.win.mainloop()

    def create_widgets(self):
        tk.Label(self.win, text="Felszerelés szerkesztő", font=("Arial", 18, "bold")).pack(pady=20)

        button_frame = tk.Frame(self.win)
        button_frame.pack(pady=30)

        tk.Button(button_frame, text="Páncélok szerkesztése", width=30, command=self.open_armor_editor).pack(pady=10)
        tk.Button(button_frame, text="Fegyverek és pajzsok szerkesztése", width=30, command=self.open_weapons_editor).pack(pady=10)
        tk.Button(button_frame, text="Általános felszerelés szerkesztése", width=30, command=self.open_general_editor).pack(pady=10)

        tk.Button(self.win, text="Kilépés", command=self.win.destroy).pack(pady=30)

    def open_armor_editor(self):
        from ui.equipment.armor_editor import ArmorEditor
        ArmorEditor()

    def open_weapons_editor(self):
        from ui.equipment.weapons_and_shields_editor import WeaponsAndShieldsEditor
        WeaponsAndShieldsEditor()

    def open_general_editor(self):
        from ui.equipment.general_equipment_editor import GeneralEquipmentEditor
        GeneralEquipmentEditor()

if __name__ == "__main__":
    EquipmentEditor()
