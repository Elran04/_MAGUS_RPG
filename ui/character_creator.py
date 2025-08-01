import tkinter as tk
from tkinter import ttk
from engine.character import generate_character, is_valid_character, GENDER_RESTRICTIONS, RACE_RESTRICTIONS
from data.Class.class_list import ALL_CLASSES
from data.Race.race_list import ALL_RACES
from data.Race.race_age_stat_modifiers import AGE_LIMITS

def open_character_creator(root, on_character_created):
    open_character_wizard(root, on_character_created)
    return
# ...existing code...
    from tkinter import simpledialog, messagebox
    from utils.character_storage import save_character, load_character, CHARACTER_DIR

    # --- Karakter mentése ---
    def save_character_dialog(char):
        default_name = char.get("Név", "karakter").replace(" ", "_")
        filename = simpledialog.askstring("Mentés", "Fájlnév:", initialvalue=default_name, parent=creator)
        if filename:
            if not filename.lower().endswith(".json"):
                filename += ".json"
            save_character(char, filename)
            messagebox.showinfo("Mentés", f"Sikeres mentés: {filename}", parent=creator)

    # --- Karakter betöltése ---
    def load_character_dialog():
        import os
        if not os.path.exists(CHARACTER_DIR):
            messagebox.showinfo("Betöltés", "Nincs elérhető karakter.", parent=creator)
            return
        files = [f for f in os.listdir(CHARACTER_DIR) if f.endswith(".json")]
        if not files:
            messagebox.showinfo("Betöltés", "Nincs elérhető karakter.", parent=creator)
            return
        dialog = tk.Toplevel(creator)
        dialog.title("Karakter betöltése")
        tk.Label(dialog, text="Válassz karaktert:").pack(pady=5)
        listbox = tk.Listbox(dialog, height=10, width=40)
        for f in files:
            listbox.insert(tk.END, f)
        listbox.pack(pady=5)
        def do_load():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("Betöltés", "Nincs kiválasztva karakter.", parent=dialog)
                return
            filename = files[selection[0]]
            char = load_character(filename)
            if char:
                on_character_created(char)
                messagebox.showinfo("Betöltés", f"Sikeres betöltés: {filename}", parent=dialog)
                dialog.destroy()
                creator.destroy()
            else:
                messagebox.showerror("Betöltés", "Nem található ilyen karakterfájl.", parent=dialog)
        listbox.bind('<Double-1>', lambda event: do_load())
        tk.Button(dialog, text="Betöltés", command=do_load).pack(pady=10)
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

        # --- Karakterlap megjelenítése ---
        try:
            from ui.character_page import open_character_page
            open_character_page(root, char)
        except Exception as e:
            import tkinter.messagebox as messagebox
            messagebox.showerror("Hiba", f"Nem sikerült megnyitni a karakterlapot:\n{e}")

    # --- KONFIGURÁCIÓS ADATOK ---
    # ALL_RACES és ALL_CLASSES importálva külön modulból

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

    # --- Létrehozás, Mentés, Betöltés gombok és eredmény label ---
    btn_frame = tk.Frame(creator)
    btn_frame.pack(pady=10)
    tk.Button(btn_frame, text="Létrehozás", command=create, width=12).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="Mentés", command=lambda: save_character_dialog({
        "Név": name_entry.get(),
        "Nem": gender_var.get(),
        "Kor": age_entry.get(),
        "Faj": race_var.get(),
        "Kaszt": class_var.get()
    }), width=12).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="Betöltés", command=load_character_dialog, width=12).pack(side=tk.LEFT, padx=5)
    result_label = tk.Label(creator, text="")
    result_label.pack()

class CharacterWizard:
    def __init__(self, root, on_character_created):
        self.root = root
        self.on_character_created = on_character_created
        self.data = {}
        self.step = 0
        self.win = tk.Toplevel(root)
        self.win.title("Karakteralkotás varázsló")
        self.frame = tk.Frame(self.win)
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.specializations = ["Nincs"]
        self.show_step()

    def show_step(self):
        for widget in self.frame.winfo_children():
            widget.destroy()
        if self.step == 0:
            self.show_basic_data()
        elif self.step == 1:
            self.show_specialization()
        elif self.step == 2:
            self.show_skills()
        elif self.step == 3:
            self.show_equipment()
        elif self.step == 4:
            self.show_summary()

    def show_basic_data(self):
        tk.Label(self.frame, text="Név:").pack()
        self.name_var = tk.StringVar()
        tk.Entry(self.frame, textvariable=self.name_var).pack()
        tk.Label(self.frame, text="Nem:").pack()
        self.gender_var = tk.StringVar()
        gender_combo = ttk.Combobox(self.frame, textvariable=self.gender_var, values=["Férfi", "Nő"], state="readonly")
        gender_combo.current(0)
        gender_combo.pack()
        tk.Label(self.frame, text="Kor:").pack()
        self.age_var = tk.StringVar()
        tk.Entry(self.frame, textvariable=self.age_var).pack()
        # --- Korhatár label ---
        self.age_limits_label = tk.Label(self.frame, text="")
        self.age_limits_label.pack()
        tk.Label(self.frame, text="Faj:").pack()
        self.race_var = tk.StringVar()
        race_combo = ttk.Combobox(self.frame, textvariable=self.race_var, values=ALL_RACES, state="readonly")
        race_combo.current(0)
        race_combo.pack()
        tk.Label(self.frame, text="Kaszt:").pack()
        self.class_var = tk.StringVar()
        self.class_combo = ttk.Combobox(self.frame, textvariable=self.class_var, state="readonly")
        self.class_combo.pack()
        self.result_label = tk.Label(self.frame, text="")
        self.result_label.pack()
        btn_frame = tk.Frame(self.frame)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Vissza", command=self.prev_step, state=tk.DISABLED).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Következő", command=self.validate_basic_data).pack(side=tk.LEFT, padx=5)

        # --- Dinamikus frissítés: faj és nem változásakor ---
        def update_age_limits(*args):
            race = self.race_var.get()
            from data.Race.race_age_stat_modifiers import AGE_LIMITS
            limits = AGE_LIMITS.get(race, (13, 100))
            self.age_limits_label.config(text=f"Engedélyezett kor: {limits[0]} - {limits[1]}")

        def update_class_options(*args):
            race = self.race_var.get()
            gender = self.gender_var.get()
            from engine.character import GENDER_RESTRICTIONS, RACE_RESTRICTIONS
            restricted_by_gender = GENDER_RESTRICTIONS.get(gender, set())
            restricted_by_race = RACE_RESTRICTIONS.get(race, set())
            allowed_classes = [k for k in ALL_CLASSES if k not in restricted_by_gender and k not in restricted_by_race]
            self.class_combo['values'] = allowed_classes
            # Ha az aktuális kaszt már nem engedélyezett, állítsd át az elsőre
            if self.class_var.get() not in allowed_classes:
                self.class_var.set(allowed_classes[0] if allowed_classes else "")

        # Trace-ek beállítása
        self.race_var.trace_add("write", lambda *args: [update_age_limits(), update_class_options()])
        self.gender_var.trace_add("write", lambda *args: update_class_options())
        # Kezdeti frissítés
        update_age_limits()
        update_class_options()

    def validate_basic_data(self):
        name = self.name_var.get()
        gender = self.gender_var.get()
        age = self.age_var.get()
        race = self.race_var.get()
        klass = self.class_var.get()
        if not name:
            self.result_label.config(text="Adj meg egy nevet!")
            return
        if not age:
            self.result_label.config(text="Add meg a karakter korát!")
            return
        if not is_valid_character(gender, race, klass):
            self.result_label.config(text=f"A(z) {race.lower()} {gender.lower()} nem lehet {klass.lower()}!")
            return
        try:
            age_int = int(age)
        except ValueError:
            self.result_label.config(text="A kor csak szám lehet.")
            return

        limits = AGE_LIMITS.get(race, (13, 100))
        if age_int < limits[0] or age_int > limits[1]:
            self.result_label.config(text=f"A(z) {race} kora {limits[0]} és {limits[1]} között kell legyen.")
            return
        # Minden oké, adatokat mentjük
        self.data = {
            "Név": name,
            "Nem": gender,
            "Kor": age,
            "Faj": race,
            "Kaszt": klass
        }
        self.step += 1
        self.show_step()

    def show_specialization(self):
        tk.Label(self.frame, text="Specializáció:").pack()
        self.spec_var = tk.StringVar()
        spec_combo = ttk.Combobox(self.frame, textvariable=self.spec_var, values=self.specializations, state="readonly")
        spec_combo.current(0)
        spec_combo.pack()
        tk.Label(self.frame, text="Leírás:").pack()
        self.spec_desc = tk.Text(self.frame, height=4, width=40)
        self.spec_desc.insert("1.0", "")
        self.spec_desc.pack()
        btn_frame = tk.Frame(self.frame)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Vissza", command=self.prev_step).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Következő", command=self.save_specialization).pack(side=tk.LEFT, padx=5)

    def save_specialization(self):
        self.data["Specializáció"] = self.spec_var.get()
        self.data["Spec_leírás"] = self.spec_desc.get("1.0", tk.END).strip()
        self.step += 1
        self.show_step()

    def show_skills(self):
        tk.Label(self.frame, text="Képzettségek szerkesztése (később)").pack(pady=30)
        btn_frame = tk.Frame(self.frame)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Vissza", command=self.prev_step).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Következő", command=self.next_step).pack(side=tk.LEFT, padx=5)

    def show_equipment(self):
        tk.Label(self.frame, text="Felszerelések szerkesztése (később)").pack(pady=30)
        btn_frame = tk.Frame(self.frame)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Vissza", command=self.prev_step).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Következő", command=self.next_step).pack(side=tk.LEFT, padx=5)

    def show_summary(self):
        tk.Label(self.frame, text="Karakter összegzés").pack()
        summary = "\n".join(f"{k}: {v}" for k, v in self.data.items())
        tk.Label(self.frame, text=summary, justify=tk.LEFT).pack(pady=10)
        btn_frame = tk.Frame(self.frame)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Vissza", command=self.prev_step).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Mentés", command=self.finish).pack(side=tk.LEFT, padx=5)

    def next_step(self):
        self.step += 1
        self.show_step()

    def prev_step(self):
        if self.step > 0:
            self.step -= 1
            self.show_step()

    def finish(self):
        # Karakter generálás, mentés, karakterlap megjelenítés
        char = generate_character(
            self.data["Név"], self.data["Nem"], self.data["Kor"], self.data["Faj"], self.data["Kaszt"]
        )
        # Itt bővíthető a char a specializációval, képzettségekkel, felszereléssel
        self.on_character_created(char)
        self.win.destroy()
        try:
            from ui.character_page import open_character_page
            open_character_page(self.root, char)
        except Exception as e:
            import tkinter.messagebox as messagebox
            messagebox.showerror("Hiba", f"Nem sikerült megnyitni a karakterlapot:\n{e}")

# --- Új karakter vagy betöltés wizard indítása ---
def open_character_wizard(root, on_character_created):
    def start_new():
        CharacterWizard(root, on_character_created)
    def load_existing():
        from utils.character_storage import load_character, CHARACTER_DIR
        import os
        from tkinter import messagebox
        if not os.path.exists(CHARACTER_DIR):
            messagebox.showinfo("Betöltés", "Nincs elérhető karakter.", parent=root)
            return
        files = [f for f in os.listdir(CHARACTER_DIR) if f.endswith(".json")]
        if not files:
            messagebox.showinfo("Betöltés", "Nincs elérhető karakter.", parent=root)
            return
        dialog = tk.Toplevel(root)
        dialog.title("Karakter betöltése")
        tk.Label(dialog, text="Válassz karaktert:").pack(pady=5)
        listbox = tk.Listbox(dialog, height=10, width=40)
        for f in files:
            listbox.insert(tk.END, f)
        listbox.pack(pady=5)
        def do_load():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("Betöltés", "Nincs kiválasztva karakter.", parent=dialog)
                return
            filename = files[selection[0]]
            char = load_character(filename)
            if char:
                on_character_created(char)
                messagebox.showinfo("Betöltés", f"Sikeres betöltés: {filename}", parent=dialog)
                dialog.destroy()
            else:
                messagebox.showerror("Betöltés", "Nem található ilyen karakterfájl.", parent=dialog)
        listbox.bind('<Double-1>', lambda event: do_load())
        tk.Button(dialog, text="Betöltés", command=do_load).pack(pady=10)
    # Indító ablak
    start_win = tk.Toplevel(root)
    start_win.title("Karakteralkotás indítása")
    tk.Label(start_win, text="Mit szeretnél?").pack(pady=10)
    tk.Button(start_win, text="Új karakter", command=lambda: [start_win.destroy(), start_new()]).pack(pady=5)
    tk.Button(start_win, text="Meglévő karakter betöltése", command=lambda: [start_win.destroy(), load_existing()]).pack(pady=5)
