import tkinter as tk
import os
from utils.json_manager import JsonManager

class ArmorJsonManager(JsonManager):
    def validate(self, item):
        required = ["id", "name", "parts", "mgt", "weight", "price", "description"]
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
        # Páncél részegységek (parts) - SFÉ értékekkel
        from engine.armor_manager import ArmorManager
        tk.Label(edit_frame, text="Részegységek és SFÉ:", font=("Arial", 11, "bold")).grid(row=row, column=0, sticky="w", pady=5)
        row += 1
        self.parts_vars = {}
        self.parts_sfe_vars = {}
        parts = list(ArmorManager.PARTS.keys())
        parts_frame = tk.Frame(edit_frame)
        parts_frame.grid(row=row, column=0, columnspan=3, sticky="w")
        for i, part in enumerate(parts):
            var = tk.IntVar()
            sfe_var = tk.StringVar()
            self.parts_vars[part] = var
            self.parts_sfe_vars[part] = sfe_var
            tk.Checkbutton(parts_frame, text=part, variable=var).grid(row=i, column=0, sticky="w")
            tk.Label(parts_frame, text="SFÉ:").grid(row=i, column=1, sticky="e")
            tk.Entry(parts_frame, textvariable=sfe_var, width=6).grid(row=i, column=2, padx=2)
        row += len(parts)
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
        for label, key in [("MGT:", "mgt"), ("Súly (kg):", "weight")]:
            tk.Label(edit_frame, text=label).grid(row=row, column=0, sticky="w")
            self.edit_vars[key] = tk.StringVar()
            tk.Entry(edit_frame, textvariable=self.edit_vars[key], width=12).grid(row=row, column=1, sticky="w")
            row += 1
        # Ár mezők (currency manager alapján) - egy sorban, egy frame-ben
        from engine.currency_manager import CurrencyManager
        tk.Label(edit_frame, text="Ár:").grid(row=row, column=0, sticky="nw")
        price_frame = tk.Frame(edit_frame)
        price_frame.grid(row=row, column=1, columnspan=8, sticky="w", pady=2)
        self.edit_vars['price_réz'] = tk.StringVar()
        self.edit_vars['price_ezüst'] = tk.StringVar()
        self.edit_vars['price_arany'] = tk.StringVar()
        self.edit_vars['price_mithrill'] = tk.StringVar()
        tk.Label(price_frame, text="réz").grid(row=0, column=0)
        tk.Entry(price_frame, textvariable=self.edit_vars['price_réz'], width=4).grid(row=0, column=1)
        tk.Label(price_frame, text="ezüst").grid(row=0, column=2)
        tk.Entry(price_frame, textvariable=self.edit_vars['price_ezüst'], width=4).grid(row=0, column=3)
        tk.Label(price_frame, text="arany").grid(row=0, column=4)
        tk.Entry(price_frame, textvariable=self.edit_vars['price_arany'], width=4).grid(row=0, column=5)
        tk.Label(price_frame, text="mithrill").grid(row=0, column=6)
        tk.Entry(price_frame, textvariable=self.edit_vars['price_mithrill'], width=4).grid(row=0, column=7)
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
        # parts mező kitöltése és SFÉ értékek
        for part in self.parts_vars:
            # SFÉ érték lekérése, ha nincs, akkor 0
            sfe_val = 0
            if part in armor.get('parts', {}):
                sfe_val = armor['parts'][part]
            self.parts_sfe_vars[part].set(str(sfe_val))
            # Tickbox csak akkor checked, ha SFÉ > 0
            self.parts_vars[part].set(1 if sfe_val > 0 else 0)
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
        # Ár felbontása currency managerrel
        from engine.currency_manager import CurrencyManager
        price = int(armor.get('price', 0))
        price_parts = CurrencyManager().from_base(price)
        self.edit_vars['price_réz'].set(str(price_parts.get('réz', 0)))
        self.edit_vars['price_ezüst'].set(str(price_parts.get('ezüst', 0)))
        self.edit_vars['price_arany'].set(str(price_parts.get('arany', 0)))
        self.edit_vars['price_mithrill'].set(str(price_parts.get('mithrill', 0)))
        self.edit_vars['description'].delete("1.0", tk.END)
        self.edit_vars['description'].insert(tk.END, armor.get('description', ''))

    def save_armor(self):
        # Gyűjtés
        from engine.currency_manager import CurrencyManager
        # Ár összerakása
        price_total = 0
        for curr in CurrencyManager.ORDER:
            val = int(self.edit_vars[f'price_{curr}'].get() or 0)
            price_total += CurrencyManager().to_base(val, curr)
        # parts dict: {part: SFÉ} minden parts elemhez, ha nincs tickbox vagy üres SFÉ, akkor 0
        parts_dict = {}
        for part, var in self.parts_vars.items():
            if var.get():
                try:
                    sfe_val = int(self.parts_sfe_vars[part].get() or 0)
                except ValueError:
                    sfe_val = 0
                parts_dict[part] = sfe_val
            else:
                parts_dict[part] = 0
        armor = {
            'name': self.edit_vars['name'].get(),
            'id': self.edit_vars['id'].get(),
            'parts': parts_dict,
            'protection_overrides': {},
            'mgt': int(self.edit_vars['mgt'].get() or 0),
            'weight': float(self.edit_vars['weight'].get() or 0),
            'price': price_total,
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
        for part in self.parts_vars:
            self.parts_vars[part].set(0)
            self.parts_sfe_vars[part].set("")
        self.override_vars = []
        self.refresh_override_list()
        self.edit_vars['mgt'].set("")
        self.edit_vars['weight'].set("")
        self.edit_vars['price_réz'].set("")
        self.edit_vars['price_ezüst'].set("")
        self.edit_vars['price_arany'].set("")
        self.edit_vars['price_mithrill'].set("")
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
