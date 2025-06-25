# ui/character_creator.py

import tkinter as tk
from engine.character import generate_character , is_valid_character

def open_character_creator(root, on_character_created):
    def create():
        result_label.config(text="")
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
        try:
            age_int = int(age)
        except ValueError:
            result_label.config(text="A kor csak szám lehet.")
            return

        # Fajfüggő korhatárok dictionary-ben
        AGE_LIMITS = {
            "Ember": (13, 100),
            "Elf": (30, 3000),
            "Félelf": (16, 200),
            "Törpe": (25, 800),
            "Udvari ork": (9, 80),
            "Amund": (30, 120),
            "Dzsenn": (15, 250),
            "Khál": (1, 50),
            "Wier": (10, 130),
            # ide jöhetnek még a többi fajok
        }

        if race in AGE_LIMITS:
            min_age, max_age = AGE_LIMITS[race]
            if age_int < min_age or age_int > max_age:
                result_label.config(text=f"A(z) {race} kora {min_age} és {max_age} között kell legyen.")
                return
        else:
            # Ha nincs megadva korhatár a fajhoz, az általános tartományt lép érvénybe
            if age_int < 13 or age_int > 100:
                result_label.config(text="A kor 10 és 100 között kell legyen.")
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
