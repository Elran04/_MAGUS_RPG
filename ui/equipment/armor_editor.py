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
        self.win.geometry("1100x700")
        self.manager = ArmorJsonManager(ARMOR_JSON)
        self.armors = self.manager.load()
        self.selected_idx = None
        self.create_widgets()

    def create_widgets(self):
        main_frame = tk.Frame(self.win)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Bal oldali lista
        list_frame = tk.Frame(main_frame)
        list_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        tk.Label(list_frame, text="Páncélok listája", font=("Arial", 14, "bold")).pack(pady=5)
        self.listbox = tk.Listbox(list_frame, width=35, height=30)
        for armor in self.armors:
            self.listbox.insert(tk.END, f"{armor['name']} (ID: {armor.get('id', '-')})")
        self.listbox.pack(pady=5)
        self.listbox.bind('<<ListboxSelect>>', self.on_select)

        tk.Button(list_frame, text="Új páncél", command=self.new_armor).pack(pady=5)
        tk.Button(list_frame, text="Törlés", command=self.delete_armor).pack(pady=5)

        # Jobb oldali szerkesztő panel
        edit_frame = tk.Frame(main_frame)
        edit_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.edit_vars = {}
        row = 0
        tk.Label(edit_frame, text="Név:").grid(row=row, column=0, sticky="w")
        self.edit_vars['name'] = tk.StringVar()
        tk.Entry(edit_frame, textvariable=self.edit_vars['name'], width=40).grid(row=row, column=1, sticky="w")
        row += 1
        tk.Label(edit_frame, text="Azonosító:").grid(row=row, column=0, sticky="w")
        self.edit_vars['id'] = tk.StringVar()
        tk.Entry(edit_frame, textvariable=self.edit_vars['id'], width=40).grid(row=row, column=1, sticky="w")
        row += 1
        # Protection főzónák
        tk.Label(edit_frame, text="SFÉ főzónák:", font=("Arial", 11, "bold")).grid(row=row, column=0, sticky="w", pady=5)
        row += 1
        self.edit_vars['protection'] = {}
        zones = ["fej", "torzó", "kar_jobb", "kar_bal", "láb_jobb", "láb_bal"]
        for z in zones:
            tk.Label(edit_frame, text=f"{z}").grid(row=row, column=0, sticky="w")
            var = tk.StringVar()
            self.edit_vars['protection'][z] = var
            tk.Entry(edit_frame, textvariable=var, width=8).grid(row=row, column=1, sticky="w")
            row += 1
        # Protection overrides - interaktív panel
        from engine.armor_manager import ArmorManager
        tk.Label(edit_frame, text="SFÉ override-ok (alzónák):", font=("Arial", 11, "bold")).grid(row=row, column=0, sticky="w", pady=5)
        row += 1
        self.override_frame = tk.Frame(edit_frame)
        self.override_frame.grid(row=row, column=0, columnspan=3, sticky="w")
        self.override_vars = []  # list of dicts: {main, sub, value, widgets}

        # Add override controls
        self.ov_main_var = tk.StringVar()
        self.ov_sub_var = tk.StringVar()
        self.ov_value_var = tk.StringVar()
        main_zones = list(ArmorManager.MAIN_ZONES.keys())
        tk.Label(self.override_frame, text="Főzóna:").grid(row=0, column=0)
        main_menu = tk.OptionMenu(self.override_frame, self.ov_main_var, *main_zones, command=self.update_subzone_menu)
        main_menu.grid(row=0, column=1)
        tk.Label(self.override_frame, text="Alzóna:").grid(row=0, column=2)
        self.subzone_menu = tk.OptionMenu(self.override_frame, self.ov_sub_var, "")
        self.subzone_menu.grid(row=0, column=3)
        tk.Label(self.override_frame, text="SFÉ:").grid(row=0, column=4)
        tk.Entry(self.override_frame, textvariable=self.ov_value_var, width=6).grid(row=0, column=5)
        tk.Button(self.override_frame, text="Hozzáadás", command=self.add_override).grid(row=0, column=6, padx=5)
        self.ov_main_var.set(main_zones[0])
        self.update_subzone_menu(main_zones[0])
        row += 1
        # List of current overrides
        self.ov_list_frame = tk.Frame(edit_frame)
        self.ov_list_frame.grid(row=row, column=0, columnspan=3, sticky="w")
        row += 1
        # ...existing code for MGT, súly, ár, leírás, mentés gomb...
        for label, key in [("MGT:", "mgt"), ("Súly (kg):", "weight"), ("Ár:", "price")]:
            tk.Label(edit_frame, text=label).grid(row=row, column=0, sticky="w")
            self.edit_vars[key] = tk.StringVar()
            tk.Entry(edit_frame, textvariable=self.edit_vars[key], width=12).grid(row=row, column=1, sticky="w")
            row += 1
        tk.Label(edit_frame, text="Leírás:").grid(row=row, column=0, sticky="nw")
        self.edit_vars['description'] = tk.Text(edit_frame, width=50, height=4)
        self.edit_vars['description'].grid(row=row, column=1, columnspan=2, sticky="w")
        row += 1

        tk.Button(edit_frame, text="Mentés", command=self.save_armor).grid(row=row, column=1, pady=15, sticky="w")

    def update_subzone_menu(self, main):
        from engine.armor_manager import ArmorManager
        menu = self.subzone_menu["menu"]
        menu.delete(0, "end")
        subs = ArmorManager.MAIN_ZONES.get(main, [])
        if subs:
            self.ov_sub_var.set(subs[0])
        else:
            self.ov_sub_var.set("")
        for sub in subs:
            menu.add_command(label=sub, command=lambda value=sub: self.ov_sub_var.set(value))

    def add_override(self):
        main = self.ov_main_var.get()
        sub = self.ov_sub_var.get()
        value = self.ov_value_var.get()
        if not sub or not value:
            tk.messagebox.showwarning("Hiba", "Válassz alzónát és adj meg SFÉ értéket!")
            return
        # Ellenőrizd, hogy már van-e ilyen override
        for ov in self.override_vars:
            if ov['sub'] == sub:
                tk.messagebox.showwarning("Hiba", "Ez az alzóna már szerepel az override-ok között!")
                return
        # Hozzáadás
        ov_dict = {'main': main, 'sub': sub, 'value': int(value)}
        self.override_vars.append(ov_dict)
        self.refresh_override_list()
        self.ov_value_var.set("")

    def refresh_override_list(self):
        for w in getattr(self, 'ov_list_widgets', []):
            w.destroy()
        self.ov_list_widgets = []
        for idx, ov in enumerate(self.override_vars):
            txt = f"{ov['sub']} ({ov['main']}): {ov['value']}"
            lbl = tk.Label(self.ov_list_frame, text=txt)
            lbl.grid(row=idx, column=0, sticky="w")
            btn = tk.Button(self.ov_list_frame, text="Törlés", command=lambda i=idx: self.delete_override(i))
            btn.grid(row=idx, column=1, padx=5)
            self.ov_list_widgets.extend([lbl, btn])

    def delete_override(self, idx):
        self.override_vars.pop(idx)
        self.refresh_override_list()

    def on_select(self, event):
        idxs = self.listbox.curselection()
        if not idxs:
            return
        idx = idxs[0]
        self.selected_idx = idx
        armor = self.armors[idx]
        self.edit_vars['name'].set(armor.get('name', ''))
        self.edit_vars['id'].set(armor.get('id', ''))
        for z in self.edit_vars['protection']:
            self.edit_vars['protection'][z].set(str(armor.get('protection', {}).get(z, '')))
        # overrides: dict -> interactive list
        overrides = armor.get('protection_overrides', {})
        self.override_vars = []
        from engine.armor_manager import ArmorManager
        for main, subs in ArmorManager.MAIN_ZONES.items():
            for sub in subs:
                if sub in overrides:
                    self.override_vars.append({'main': main, 'sub': sub, 'value': overrides[sub]})
        self.refresh_override_list()
        self.edit_vars['mgt'].set(str(armor.get('mgt', '')))
        self.edit_vars['weight'].set(str(armor.get('weight', '')))
        self.edit_vars['price'].set(str(armor.get('price', '')))
        self.edit_vars['description'].delete("1.0", tk.END)
        self.edit_vars['description'].insert(tk.END, armor.get('description', ''))

    def save_armor(self):
        # Gyűjtés
        armor = {
            'name': self.edit_vars['name'].get(),
            'id': self.edit_vars['id'].get(),
            'protection': {z: int(self.edit_vars['protection'][z].get() or 0) for z in self.edit_vars['protection']},
            'protection_overrides': {},
            'mgt': int(self.edit_vars['mgt'].get() or 0),
            'weight': float(self.edit_vars['weight'].get() or 0),
            'price': int(self.edit_vars['price'].get() or 0),
            'description': self.edit_vars['description'].get("1.0", tk.END).strip()
        }
        # override list -> dict
        for ov in self.override_vars:
            armor['protection_overrides'][ov['sub']] = ov['value']
        # Validáció
        if not self.manager.validate(armor):
            tk.messagebox.showerror("Hiba", "Hiányzó vagy hibás mező!")
            return
        # Mentés
        if self.selected_idx is not None:
            self.armors[self.selected_idx] = armor
        else:
            self.armors.append(armor)
        self.manager.save(self.armors)
        self.refresh_list()
        tk.messagebox.showinfo("Mentés", "Páncél mentve!")

    def refresh_list(self):
        self.listbox.delete(0, tk.END)
        for armor in self.armors:
            self.listbox.insert(tk.END, f"{armor['name']} (ID: {armor.get('id', '-')})")

    def new_armor(self):
        self.selected_idx = None
        self.edit_vars['name'].set("")
        self.edit_vars['id'].set("")
        for z in self.edit_vars['protection']:
            self.edit_vars['protection'][z].set("")
        self.override_vars = []
        self.refresh_override_list()
        self.edit_vars['mgt'].set("")
        self.edit_vars['weight'].set("")
        self.edit_vars['price'].set("")
        self.edit_vars['description'].delete("1.0", tk.END)

    def delete_armor(self):
        idxs = self.listbox.curselection()
        if not idxs:
            tk.messagebox.showwarning("Törlés", "Nincs kiválasztva páncél.")
            return
        idx = idxs[0]
        answer = tk.messagebox.askyesno("Törlés", f"Biztosan törlöd ezt a páncélt?\n{self.armors[idx]['name']}")
        if answer:
            self.armors.pop(idx)
            self.manager.save(self.armors)
            self.refresh_list()

if __name__ == "__main__":
    ArmorEditor()
