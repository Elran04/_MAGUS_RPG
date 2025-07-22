import tkinter as tk
import os
from utils.json_manager import JsonManager

class ArmorJsonManager(JsonManager):
    def validate(self, item):
        required = ["id", "name", "protection", "mgt", "weight", "price", "description"]
        return all(field in item for field in required)

ARMOR_JSON = os.path.join(os.path.dirname(__file__), "..", "..", "data", "equipment", "armor.json")

class ArmorEditor:
    def __init__(self):
        self.win = tk.Toplevel()
        self.win.title("Páncél szerkesztő")
        self.win.geometry("800x600")
        self.manager = ArmorJsonManager(ARMOR_JSON)
        self.armors = self.manager.load()
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.win, text="Páncélok listája", font=("Arial", 16, "bold")).pack(pady=10)
        self.listbox = tk.Listbox(self.win, width=80, height=20)
        for armor in self.armors:
            self.listbox.insert(tk.END, f"{armor['name']} (ID: {armor.get('id', '-')})")
        self.listbox.pack(pady=10)
        tk.Button(self.win, text="Kilépés", command=self.win.destroy).pack(pady=10)

if __name__ == "__main__":
    ArmorEditor()
