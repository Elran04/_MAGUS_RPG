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
        # Placeholder: ide jön majd a felszerelés lista, szerkesztés, stb.
        tk.Label(self.win, text="A funkció fejlesztés alatt!", font=("Arial", 12)).pack(pady=10)
        tk.Button(self.win, text="Kilépés", command=self.win.destroy).pack(pady=30)

if __name__ == "__main__":
    EquipmentEditor()
