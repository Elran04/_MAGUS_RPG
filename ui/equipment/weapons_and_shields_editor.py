import tkinter as tk
import os
from utils.json_manager import JsonManager

class WeaponsAndShieldsJsonManager(JsonManager):
    def validate(self, item):
        required = ["name", "type", "category", "damage", "weight", "price"]
        return all(field in item for field in required)

WEAPONS_JSON = os.path.join(os.path.dirname(__file__), "..", "..", "data", "equipment", "weapons_and_shields.json")

class WeaponsAndShieldsEditor:
    def __init__(self):
        self.win = tk.Toplevel()
        self.win.title("Fegyverek és pajzsok szerkesztője")
        self.win.geometry("800x600")
        self.manager = WeaponsAndShieldsJsonManager(WEAPONS_JSON)
        self.items = self.manager.load()
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.win, text="Fegyverek és pajzsok listája", font=("Arial", 16, "bold")).pack(pady=10)
        self.listbox = tk.Listbox(self.win, width=80, height=20)
        for item in self.items:
            self.listbox.insert(tk.END, f"{item['name']} ({item.get('type', '-')})")
        self.listbox.pack(pady=10)
        tk.Button(self.win, text="Kilépés", command=self.win.destroy).pack(pady=10)

if __name__ == "__main__":
    WeaponsAndShieldsEditor()
