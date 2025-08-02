
import json
import os
import sys
import tkinter as tk
from tkinter import ttk
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from engine.weapon_material_quality_manager import WeaponMaterialQualityManager


def load_melee_weapons(json_path):
    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)
    melee = []
    for item in data:
        if item.get('category', '').lower() == 'közelharci' or item.get('type', '').lower() == 'közelharci':
            melee.append(item)
    return melee

class WeaponNamingStatTestUI:
    def __init__(self, root, weapons):
        self.root = root
        self.weapons = weapons
        self.manager = WeaponMaterialQualityManager()
        self.selected_weapon = None

        main_frame = tk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Bal oldali fegyverlista
        list_frame = tk.Frame(main_frame)
        list_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        tk.Label(list_frame, text="Közelharci fegyverek", font=("Arial", 14, "bold")).pack(pady=5)
        self.weapon_listbox = tk.Listbox(list_frame, height=30, width=40)
        self.weapon_listbox.pack(pady=5, fill=tk.Y, expand=True)
        for w in weapons:
            self.weapon_listbox.insert(tk.END, w.get('name', w.get('id', 'ismeretlen')))
        self.weapon_listbox.bind('<<ListboxSelect>>', self.on_weapon_select)

        # Jobb oldali tesztpanel
        edit_frame = tk.Frame(main_frame)
        edit_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        row = 0
        tk.Label(edit_frame, text="Minőség:").grid(row=row, column=0, sticky="w")
        self.quality_var = tk.StringVar()
        quality_options = ["default"] + list(self.manager.craft_quality_mods.keys())
        om1 = tk.OptionMenu(edit_frame, self.quality_var, *quality_options, command=lambda _: self.update_summary())
        om1.grid(row=row, column=1, sticky="w")
        row += 1
        tk.Label(edit_frame, text="Módosító:").grid(row=row, column=0, sticky="w")
        self.modification_var = tk.StringVar()
        mod_options = ["default"] + [str(k) for k in self.manager.modification_mods.keys() if k != 'default']
        om2 = tk.OptionMenu(edit_frame, self.modification_var, *mod_options, command=lambda _: self.update_summary())
        om2.grid(row=row, column=1, sticky="w")
        row += 1
        tk.Label(edit_frame, text="Alapanyag:").grid(row=row, column=0, sticky="w")
        self.material_var = tk.StringVar()
        material_options = ["default"] + list(self.manager.material_mods.keys())
        om3 = tk.OptionMenu(edit_frame, self.material_var, *material_options, command=lambda _: self.update_summary())
        om3.grid(row=row, column=1, sticky="w")
        row += 1
        tk.Label(edit_frame, text="Kézrekovácsolt:").grid(row=row, column=0, sticky="w")
        self.handforged_var = tk.BooleanVar()
        cb = tk.Checkbutton(edit_frame, variable=self.handforged_var, command=self.update_summary)
        cb.grid(row=row, column=1, sticky="w")
        row += 1
        tk.Label(edit_frame, text="Kovács neve:").grid(row=row, column=0, sticky="w")
        self.handforged_by_var = tk.StringVar()
        e = tk.Entry(edit_frame, textvariable=self.handforged_by_var, width=20)
        e.grid(row=row, column=1, sticky="w")
        row += 1

        # Összesítő panel
        self.summary_frame = tk.Frame(edit_frame)
        self.summary_frame.grid(row=row, column=0, columnspan=2, sticky="nw", pady=10)
        self.summary_labels = {}
        self.update_summary()

    def on_weapon_select(self, event):
        idxs = self.weapon_listbox.curselection()
        if not idxs:
            self.selected_weapon = None
        else:
            self.selected_weapon = self.weapons[idxs[0]]
        self.update_summary()

    def update_summary(self):
        # Töröld a régi összesítő elemeket
        for w in self.summary_labels.values():
            w.destroy()
        self.summary_labels = {}
        # Ha nincs kiválasztott fegyver, ne jeleníts meg semmit
        item = self.selected_weapon
        if not item:
            l = tk.Label(self.summary_frame, text="Nincs kiválasztott fegyver.", font=("Arial", 12, "italic"))
            l.grid(row=0, column=0, sticky="w")
            self.summary_labels['none'] = l
            return
        # Paraméterek összeállítása
        try:
            mod_val = self.modification_var.get()
            modifications = [eval(mod_val)] if mod_val != 'default' else []
        except Exception:
            modifications = []
        params = {
            'craft_quality': self.quality_var.get() if self.quality_var.get() != 'default' else 'default',
            'modifications': modifications,
            'material': self.material_var.get() if self.material_var.get() != 'default' else 'default',
            'handforged': self.handforged_var.get(),
            'handforged_by': self.handforged_by_var.get() if self.handforged_by_var.get() else None
        }
        name = self.manager.generate_weapon_name(item.get('name', 'ismeretlen'), params)
        mods = self.manager.get_total_modifiers(params)
        # Megjelenítés
        l = tk.Label(self.summary_frame, text=f"Végleges név: {name}", font=("Arial", 12, "bold"))
        l.grid(row=0, column=0, columnspan=3, sticky="w")
        self.summary_labels['name'] = l
        row = 1
        # Alapértékek kiolvasása (mapping segítségével)
        l0 = tk.Label(self.summary_frame, text="Alapértékek", font=("Arial", 10, "underline"))
        l0.grid(row=row, column=0, sticky="w")
        self.summary_labels['base_title'] = l0
        row += 1
        # Mapping MODIFIABLE_STATS -> JSON kulcsok
        stat_json_map = {
            "KÉ": "KE",
            "VÉ": "VE",
            "TÉ": "TE",
            "Sebzés": ("damage_min", "damage_max"),
            "Átütőerő": "armor_penetration",
            "Súly": "weight",
            "STP": "stp",
            "Ár": "price"
        }
        # Import CurrencyManager for base price formatting
        try:
            from engine.currency_manager import CurrencyManager
            currency_manager = CurrencyManager()
        except Exception:
            currency_manager = None

        for stat in self.manager.MODIFIABLE_STATS:
            json_key = stat_json_map.get(stat, stat)
            if isinstance(json_key, tuple):
                min_val = item.get(json_key[0], '-')
                max_val = item.get(json_key[1], '-')
                base_val = f"{min_val} - {max_val}"
            elif stat == "Ár":
                price_val = item.get(json_key, '-')
                try:
                    price_val_int = int(float(price_val))
                except Exception:
                    price_val_int = price_val
                if currency_manager and isinstance(price_val_int, int):
                    base_val = currency_manager.format(price_val_int)
                else:
                    base_val = str(price_val)
            else:
                base_val = item.get(json_key, '-')
            l1 = tk.Label(self.summary_frame, text=f"{stat}:", font=("Arial", 10))
            l2 = tk.Label(self.summary_frame, text=str(base_val), font=("Arial", 10))
            l1.grid(row=row, column=0, sticky="w")
            l2.grid(row=row, column=1, sticky="w")
            self.summary_labels[f'base_{stat}'] = l1
            self.summary_labels[f'base_{stat}_v'] = l2
            row += 1
        # Módosított értékek (összegzett statok)
        l0 = tk.Label(self.summary_frame, text="Módosított értékek", font=("Arial", 10, "underline"))
        l0.grid(row=row, column=0, sticky="w")
        self.summary_labels['mod_title'] = l0
        row += 1
        # Import CurrencyManager only when needed
        try:
            from engine.currency_manager import CurrencyManager
            currency_manager = CurrencyManager()
        except Exception:
            currency_manager = None

        for stat in self.manager.MODIFIABLE_STATS:
            json_key = stat_json_map.get(stat, stat)
            mod_val = mods.get(stat, 0)
            # Alapérték
            if isinstance(json_key, tuple):
                min_val = item.get(json_key[0], 1)
                max_val = item.get(json_key[1], 1)
                # Additív módosítás
                min_mod = max(1, int(round(float(min_val) + float(mod_val))))
                max_mod = max(1, int(round(float(max_val) + float(mod_val))))
                mod_display = f"{min_mod} - {max_mod}"
            elif stat == "Súly":
                base_val = item.get(json_key, 0)
                try:
                    mod_display = round(float(base_val) * float(mod_val), 1)
                except Exception:
                    mod_display = base_val
            elif stat == "STP":
                base_val = item.get(json_key, 0)
                try:
                    mod_display = int(round(float(base_val) * float(mod_val)))
                except Exception:
                    mod_display = base_val
            elif stat == "Ár":
                base_val = item.get(json_key, 0)
                try:
                    price_val = int(round(float(base_val) * float(mod_val)))
                except Exception:
                    price_val = base_val
                if currency_manager and isinstance(price_val, int):
                    try:
                        mod_display = currency_manager.format(price_val)
                    except Exception:
                        mod_display = str(price_val)
                else:
                    mod_display = str(price_val)
            elif stat == "Átütőerő":
                base_val = item.get(json_key, 0)
                try:
                    mod_display = max(0, int(round(float(base_val) + float(mod_val))) )
                except Exception:
                    mod_display = base_val
            else:
                base_val = item.get(json_key, 0)
                try:
                    mod_display = int(round(float(base_val) + float(mod_val)))
                except Exception:
                    mod_display = base_val
            l1 = tk.Label(self.summary_frame, text=f"{stat}:", font=("Arial", 10))
            l2 = tk.Label(self.summary_frame, text=str(mod_display), font=("Arial", 10, "bold"))
            l1.grid(row=row, column=0, sticky="w")
            l2.grid(row=row, column=1, sticky="w")
            self.summary_labels[f'mod_{stat}'] = l1
            self.summary_labels[f'mod_{stat}_v'] = l2
            row += 1

if __name__ == "__main__":
    json_path = os.path.join('data', 'equipment', 'weapons_and_shields.json')
    weapons = load_melee_weapons(json_path)
    root = tk.Tk()
    root.title("Fegyver névgenerálás és stat teszt")
    app = WeaponNamingStatTestUI(root, weapons)
    root.mainloop()
