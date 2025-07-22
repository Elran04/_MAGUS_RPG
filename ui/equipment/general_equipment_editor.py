import tkinter as tk
import os
from utils.json_manager import JsonManager

class GeneralEquipmentJsonManager(JsonManager):
    def validate(self, item):
        required = ["name", "type", "category", "weight", "price"]
        return all(field in item for field in required)

GENERAL_JSON = os.path.join(os.path.dirname(__file__), "..", "..", "data", "equipment", "general_equipment.json")

class GeneralEquipmentEditor:
    def __init__(self):
        self.win = tk.Toplevel()
        self.win.title("Általános felszerelés szerkesztő")
        self.win.geometry("800x600")
        self.manager = GeneralEquipmentJsonManager(GENERAL_JSON)
        self.items = self.manager.load()
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.win, text="Általános felszerelések listája", font=("Arial", 16, "bold")).pack(pady=10)
        self.listbox = tk.Listbox(self.win, width=80, height=20)
        for item in self.items:
            self.listbox.insert(tk.END, f"{item['name']} ({item.get('type', '-')})")
        self.listbox.pack(pady=10)
        tk.Button(self.win, text="Kilépés", command=self.win.destroy).pack(pady=10)

if __name__ == "__main__":
    GeneralEquipmentEditor()
