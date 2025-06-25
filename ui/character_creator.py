# ui/character_creator.py

import tkinter as tk
from engine.character import generate_character , is_valid_character

def open_character_creator(root, on_character_created):
    def create():
        result_label.config(text="")  # <--- Ez a sor a kulcs!

        name = name_entry.get()
        gender = gender_var.get()
        age = age_entry.get()
        race = race_var.get()
        klass = class_var.get()

        if not name:
            result_label.config(text="Adj meg egy nevet!")
            return
        if not age:
            result_label.config(text="Add meg a karakter korát!")
            return
        if not is_valid_character(gender, race, klass):
            result_label.config(
            text=f"A(z) {race.lower()} {gender.lower()} nem lehet {klass.lower()}!"
        )
            return
    
        char = generate_character(name, gender, age, race, klass)
        on_character_created(char)
        creator.destroy()

    creator = tk.Toplevel(root)
    creator.title("Karaktergenerálás")
    creator.geometry("400x350")

    tk.Label(creator, text="Név:").pack()
    name_entry = tk.Entry(creator)
    name_entry.pack()

    tk.Label(creator, text="Nem:").pack()
    gender_var = tk.StringVar(creator)
    gender_var.set("Férfi")
    tk.OptionMenu(creator, gender_var, "Férfi", "Nő").pack()

    tk.Label(creator, text="Kor:").pack()
    age_entry = tk.Entry(creator)
    age_entry.pack()

    tk.Label(creator, text="Faj:").pack()
    race_var = tk.StringVar(creator)
    race_var.set("Ember")
    tk.OptionMenu(creator, race_var, "Ember", "Elf", "Félelf", "Törpe", "Udvari ork", "Amund", "Dzsenn", "Khál", "Wier").pack()

    tk.Label(creator, text="Kaszt:").pack()
    class_var = tk.StringVar(creator)
    class_var.set("Harcos")
    tk.OptionMenu(creator, class_var,
                  "Harcos", "Gladiátor", "Fejvadász", "Lovag", "Bajvívó", "Amazon", "Barbár",
                  "Tolvaj", "Bárd", "Harcművész", "Kardművész", "Pap", "Szerzetes", "Sámán",
                  "Paplovag", "Boszorkány", "Boszorkánymester", "Tűzvarázsló",
                  "Varázsló", "Pszi mester").pack()

    tk.Button(creator, text="Létrehozás", command=create).pack(pady=10)
    result_label = tk.Label(creator, text="")
    result_label.pack()
