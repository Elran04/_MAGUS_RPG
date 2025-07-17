# ui/character_creator.py

# --- IMPORTOK ÉS SEGÉDFÜGGVÉNYEK ---
import tkinter as tk
from tkinter import ttk
from engine.character import generate_character, is_valid_character, GENDER_RESTRICTIONS, RACE_RESTRICTIONS

def open_character_creator(root, on_character_created):
    # --- SEGÉDFÜGGVÉNY: Korhatár label frissítése faj szerint ---
    def update_age_limits(*args):
        race = race_var.get()
        limits = AGE_LIMITS.get(race, (13, 100))
        age_limits_label.config(text=f"Engedélyezett kor: {limits[0]} - {limits[1]}")

    # --- SEGÉDFÜGGVÉNY: Kaszt választó frissítése restrictionök alapján ---
    def update_class_options(*args):
        race = race_var.get()
        gender = gender_var.get()
        restricted_by_gender = GENDER_RESTRICTIONS.get(gender, set())
        restricted_by_race = RACE_RESTRICTIONS.get(race, set())
        allowed_classes = [k for k in ALL_CLASSES if k not in restricted_by_gender and k not in restricted_by_race]
        class_combo['values'] = allowed_classes
        # Ha az aktuális kaszt már nem engedélyezett, állítsd át az elsőre
        if class_var.get() not in allowed_classes:
            class_var.set(allowed_classes[0] if allowed_classes else "")

    # --- SEGÉDFÜGGVÉNY: Karakter létrehozása és validáció ---
    def create():
        result_label.config(text="")
        name = name_entry.get()
        gender = gender_var.get()
        age = age_entry.get()
        race = race_var.get()
        klass = class_var.get()

        # --- Validáció: név, kor, restrictionök ---
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

        limits = AGE_LIMITS.get(race, (13, 100))
        if age_int < limits[0] or age_int > limits[1]:
            result_label.config(text=f"A(z) {race} kora {limits[0]} és {limits[1]} között kell legyen.")
            return

        # --- Karakter generálás és visszaadás a főablaknak ---
        char = generate_character(name, gender, age, race, klass)
        on_character_created(char)
        creator.destroy()

    # --- KONFIGURÁCIÓS ADATOK ---
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
    }
    ALL_RACES = list(AGE_LIMITS.keys())
    ALL_CLASSES = [
        "Harcos", "Gladiátor", "Fejvadász", "Lovag", "Bajvívó", "Amazon", "Barbár",
        "Tolvaj", "Bárd", "Harcművész", "Kardművész", "Pap", "Szerzetes", "Sámán",
        "Paplovag", "Boszorkány", "Boszorkánymester", "Tűzvarázsló",
        "Varázsló", "Pszi mester"
    ]

    # --- FŐABLAK LÉTREHOZÁSA ---
    creator = tk.Toplevel(root)
    creator.title("Karaktergenerálás")
    creator.geometry("400x400")

    # --- Név mező ---
    tk.Label(creator, text="Név:").pack()
    name_entry = tk.Entry(creator)
    name_entry.pack()

    # --- Nem választó (legördülő) ---
    tk.Label(creator, text="Nem:").pack()
    gender_var = tk.StringVar(creator)
    gender_combo = ttk.Combobox(creator, textvariable=gender_var, state="readonly")
    gender_combo['values'] = ["Férfi", "Nő"]
    gender_combo.current(0)
    gender_combo.pack()

    # --- Kor mező és korhatár label ---
    tk.Label(creator, text="Kor:").pack()
    age_entry = tk.Entry(creator)
    age_entry.pack()
    age_limits_label = tk.Label(creator, text="")
    age_limits_label.pack()

    # --- Faj választó (legördülő) ---
    tk.Label(creator, text="Faj:").pack()
    race_var = tk.StringVar(creator)
    race_combo = ttk.Combobox(creator, textvariable=race_var, values=ALL_RACES, state="readonly")
    race_combo.current(0)
    race_combo.pack()

    # --- Kaszt választó (legördülő, restrictionök alapján szűrve) ---
    tk.Label(creator, text="Kaszt:").pack()
    class_var = tk.StringVar(creator)
    class_combo = ttk.Combobox(creator, textvariable=class_var, state="readonly")
    class_combo.pack()

    # --- Dinamikus frissítés: faj és nem változásakor ---
    race_var.trace_add("write", lambda *args: [update_age_limits(), update_class_options()])
    gender_var.trace_add("write", lambda *args: update_class_options())
    update_age_limits()
    update_class_options()

    # --- Létrehozás gomb és eredmény label ---
    tk.Button(creator, text="Létrehozás", command=create).pack(pady=10)
    result_label = tk.Label(creator, text="")
    result_label.pack()
