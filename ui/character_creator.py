import tkinter as tk
from tkinter import ttk
from engine.character import generate_character, is_valid_character, GENDER_RESTRICTIONS, RACE_RESTRICTIONS
from data.Class.class_list import ALL_CLASSES
from data.Race.race_list import ALL_RACES
from data.Race.race_age_stat_modifiers import AGE_LIMITS

def open_character_creator(root, on_character_created):
    open_character_wizard(root, on_character_created)

class CharacterWizard:
    def __init__(self, root, on_character_created):
        """Wizard ablak inicializálása."""
        self.root = root
        self.on_character_created = on_character_created
        self.data = {}
        self.step = 0
        self.win = tk.Toplevel(root)
        self.win.title("Karakteralkotás varázsló")
        self.win.geometry("500x500")
        self.frame = tk.Frame(self.win)
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.specializations = ["Nincs"]
        self.show_step()

    def show_step(self):
        """Aktuális lépés UI frissítése."""
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
        """Alapadatok lépés UI és logika."""
        self.name_var = tk.StringVar()
        self.gender_var = tk.StringVar()
        self.age_var = tk.StringVar()
        self.race_var = tk.StringVar()
        self.class_var = tk.StringVar()

        self._add_labeled_entry("Név:", self.name_var)
        self._add_labeled_combobox("Nem:", self.gender_var, ["Férfi", "Nő"])
        self._add_labeled_entry("Kor:", self.age_var)
        self.age_limits_label = tk.Label(self.frame, text="")
        self.age_limits_label.pack()
        self._add_labeled_combobox("Faj:", self.race_var, ALL_RACES)
        self.class_combo = self._add_labeled_combobox("Kaszt:", self.class_var, [])
        self.result_label = tk.Label(self.frame, text="")
        self.result_label.pack()
        btn_frame = tk.Frame(self.frame)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Vissza", command=self.prev_step, state=tk.DISABLED).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Következő", command=self.validate_basic_data).pack(side=tk.LEFT, padx=5)

        # Dinamikus frissítés: faj és nem változásakor
        self.race_var.trace_add("write", lambda *args: [self.update_age_limits(), self.update_class_options()])
        self.gender_var.trace_add("write", lambda *args: self.update_class_options())
        self.update_age_limits()
        self.update_class_options()

    def _add_labeled_entry(self, label, var):
        """Segédfüggvény: címkézett Entry mező létrehozása."""
        tk.Label(self.frame, text=label).pack()
        entry = tk.Entry(self.frame, textvariable=var)
        entry.pack()
        return entry

    def _add_labeled_combobox(self, label, var, values):
        """Segédfüggvény: címkézett Combobox létrehozása."""
        tk.Label(self.frame, text=label).pack()
        combo = ttk.Combobox(self.frame, textvariable=var, values=values, state="readonly")
        if values:
            combo.current(0)
        combo.pack()
        return combo

    def update_age_limits(self, *args):
        """Korhatár label frissítése faj szerint."""
        race = self.race_var.get()
        from data.Race.race_age_stat_modifiers import AGE_LIMITS
        limits = AGE_LIMITS.get(race, (13, 100))
        self.age_limits_label.config(text=f"Engedélyezett kor: {limits[0]} - {limits[1]}")

    def update_class_options(self, *args):
        """Kaszt választó frissítése restrictionök alapján."""
        race = self.race_var.get()
        gender = self.gender_var.get()
        from engine.character import GENDER_RESTRICTIONS, RACE_RESTRICTIONS
        restricted_by_gender = GENDER_RESTRICTIONS.get(gender, set())
        restricted_by_race = RACE_RESTRICTIONS.get(race, set())
        allowed_classes = [k for k in ALL_CLASSES if k not in restricted_by_gender and k not in restricted_by_race]
        self.class_combo['values'] = allowed_classes
        if self.class_var.get() not in allowed_classes:
            self.class_var.set(allowed_classes[0] if allowed_classes else "")

    def validate_basic_data(self):
        """Alapadatok validációja és mentése."""
        name = self.name_var.get()
        gender = self.gender_var.get()
        age = self.age_var.get()
        race = self.race_var.get()
        klass = self.class_var.get()
        error = self._validate_basic_fields(name, gender, age, race, klass)
        if error:
            self.result_label.config(text=error)
            return
        # Minden oké, adatokat mentjük
        self.data = self._collect_basic_data(name, gender, age, race, klass)
        self.step += 1
        self.show_step()

    def _validate_basic_fields(self, name, gender, age, race, klass):
        """Alapadatok validációs logikája, hibaüzenettel."""
        if not name:
            return "Adj meg egy nevet!"
        if not age:
            return "Add meg a karakter korát!"
        if not is_valid_character(gender, race, klass):
            return f"A(z) {race.lower()} {gender.lower()} nem lehet {klass.lower()}!"
        try:
            age_int = int(age)
        except ValueError:
            return "A kor csak szám lehet."
        limits = AGE_LIMITS.get(race, (13, 100))
        if age_int < limits[0] or age_int > limits[1]:
            return f"A(z) {race} kora {limits[0]} és {limits[1]} között kell legyen."
        return None

    def _collect_basic_data(self, name, gender, age, race, klass):
        """Alapadatok összegyűjtése szótárba."""
        return {
            "Név": name,
            "Nem": gender,
            "Kor": age,
            "Faj": race,
            "Kaszt": klass
        }

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
