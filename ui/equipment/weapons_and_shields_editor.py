import tkinter as tk
import os
from utils.json_manager import JsonManager

class WeaponsAndShieldsJsonManager(JsonManager):
    def validate(self, item):
        required = ["id", "name", "type", "category", "weight", "price", "stp", "armor_penetration", "can_disarm", "can_break_weapon", "damage_min", "damage_max"]
        for field in required:
            if field not in item:
                return False
        # Típusfüggő mezők
        if item["type"] == "közelharci":
            for f in ["KE", "TE", "VE", "size_category"]:
                if f not in item:
                    return False
        elif item["type"] == "hajító":
            for f in ["KE", "TE", "VE", "range"]:
                if f not in item:
                    return False
        elif item["type"] == "távolsági":
            for f in ["KE", "CE", "range"]:
                if f not in item:
                    return False
        elif item["type"] == "pajzs":
            for f in ["KE", "VE", "MGT"]:
                if f not in item:
                    return False
        return True

WEAPONS_JSON = os.path.join(os.path.dirname(__file__), "..", "..", "data", "equipment", "weapons_and_shields.json")

class WeaponsAndShieldsEditor:
    def __init__(self):
        from utils.reopen_prevention import WindowSingleton
        self.win, created = WindowSingleton.get('weapons_and_shields_editor', lambda: tk.Toplevel())
        if not created:
            return
        self.manager = WeaponsAndShieldsJsonManager(WEAPONS_JSON)
        self.items = self.manager.load()
        self.selected_idx = None
        self.category_options = []
        self.win.title("Fegyverek és pajzsok szerkesztője")
        self.win.geometry("1100x700")
        self.create_widgets()

    # nincs szükség külön _on_close metódusra, WindowSingleton kezeli

    def _get_weapon_categories(self, type_value):
        import json
        skills_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "skills", "skills.json")
        try:
            with open(skills_path, encoding="utf-8") as f:
                skills = json.load(f)
            categories = set()
            if type_value in ["közelharci", "távolsági"]:
                for skill in skills:
                    if skill.get("name") == "Fegyverhasználat" and skill.get("parameter"):
                        categories.add(skill["parameter"])
            elif type_value == "hajító":
                for skill in skills:
                    if skill.get("name") == "Fegyverdobás" and skill.get("parameter"):
                        categories.add(skill["parameter"])
            # pajzs esetén üres
            return sorted(categories)
        except Exception:
            return []

    def create_widgets(self):
        main_frame = tk.Frame(self.win)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Bal oldali Treeview lista
        from tkinter import ttk
        list_frame = tk.Frame(main_frame)
        list_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        tk.Label(list_frame, text="Fegyverek és pajzsok listája", font=("Arial", 14, "bold")).pack(pady=5)
        self.tree = ttk.Treeview(list_frame, show="tree", selectmode="browse", height=30)
        self.tree.pack(pady=5, fill=tk.Y, expand=True, ipadx=100)  # Increase width
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        self.tree_nodes = {}
        # Jobb oldali szerkesztő panel
        self.edit_frame = tk.Frame(main_frame)
        self.edit_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.edit_vars = {}
        self.edit_frame_widgets = []
        self.populate_treeview()
        tk.Button(list_frame, text="Új fegyver/pajzs", command=self.new_item).pack(pady=5)
        tk.Button(list_frame, text="Törlés", command=self.delete_item).pack(pady=5)

    def populate_treeview(self):
        self.tree.delete(*self.tree.get_children())
        self.tree_nodes = {}
        # Collect all types and categories
        type_order = ["közelharci", "hajító", "távolsági", "pajzs"]
        type_items = {}
        for idx, item in enumerate(self.items):
            type_val = item.get('type', 'Egyéb')
            cat_val = item.get('category', '') or 'Egyéb'
            type_items.setdefault(type_val, []).append((cat_val, idx, item))
        # Insert types in preferred order, then any others
        inserted_types = set()
        for t in type_order + [t for t in type_items if t not in type_order]:
            if t not in type_items:
                continue
            type_id = self.tree.insert('', 'end', text=t, open=True)
            self.tree_nodes[t] = type_id
            # Collect categories for this type
            cat_map = {}
            for cat_val, idx, item in type_items[t]:
                cat_map.setdefault(cat_val, []).append((idx, item))
            for cat_val in sorted(cat_map.keys()):
                cat_key = (t, cat_val)
                if cat_val and cat_key not in self.tree_nodes:
                    cat_id = self.tree.insert(type_id, 'end', text=cat_val, open=True)
                    self.tree_nodes[cat_key] = cat_id
                elif cat_val:
                    cat_id = self.tree_nodes[cat_key]
                else:
                    cat_id = type_id
                for idx, item in cat_map[cat_val]:
                    item_text = f"{item['name']} (ID: {item.get('id', '-')})"
                    item_id = self.tree.insert(cat_id, 'end', text=item_text)
        # Szerkesztő panel újrarajzolása
        for w in getattr(self, 'edit_frame_widgets', []):
            w.destroy()
        self.edit_frame_widgets = []
        row = 0
        ef = self.edit_frame
        tk.Label(ef, text="Név:").grid(row=row, column=0, sticky="w")
        self.edit_vars['name'] = tk.StringVar()
        e = tk.Entry(ef, textvariable=self.edit_vars['name'], width=40)
        e.grid(row=row, column=1, sticky="w")
        self.edit_frame_widgets.extend([e])
        row += 1
        tk.Label(ef, text="Azonosító:").grid(row=row, column=0, sticky="w")
        self.edit_vars['id'] = tk.StringVar()
        e = tk.Entry(ef, textvariable=self.edit_vars['id'], width=40)
        e.grid(row=row, column=1, sticky="w")
        self.edit_frame_widgets.extend([e])
        row += 1
        tk.Label(ef, text="Típus:").grid(row=row, column=0, sticky="w")
        self.edit_vars['type'] = tk.StringVar()
        type_options = ["közelharci", "hajító", "távolsági", "pajzs"]
        om = tk.OptionMenu(ef, self.edit_vars['type'], *type_options, command=self.update_type_fields)
        om.grid(row=row, column=1, sticky="w")
        self.edit_frame_widgets.extend([om])
        row += 1
        self.category_label = tk.Label(ef, text="Kategória:")
        self.category_label.grid(row=row, column=0, sticky="w")
        self.edit_vars['category'] = tk.StringVar()
        self.category_menu = tk.OptionMenu(ef, self.edit_vars['category'], "")
        self.category_menu.grid(row=row, column=1, sticky="w")
        self.category_row = row
        self.edit_frame_widgets.extend([self.category_label, self.category_menu])
        row += 1
        tk.Label(ef, text="Támadás ideje (mp):").grid(row=row, column=0, sticky="w")
        self.edit_vars['attack_time'] = tk.StringVar()
        e = tk.Entry(ef, textvariable=self.edit_vars['attack_time'], width=8)
        e.grid(row=row, column=1, sticky="w")
        self.edit_frame_widgets.extend([e])
        row += 1
        tk.Label(ef, text="Sebzés (alsó határ):").grid(row=row, column=0, sticky="w")
        self.edit_vars['damage_min'] = tk.StringVar()
        e = tk.Entry(ef, textvariable=self.edit_vars['damage_min'], width=6)
        e.grid(row=row, column=1, sticky="w")
        self.edit_frame_widgets.extend([e])
        row += 1
        tk.Label(ef, text="Sebzés (felső határ):").grid(row=row, column=0, sticky="w")
        self.edit_vars['damage_max'] = tk.StringVar()
        e = tk.Entry(ef, textvariable=self.edit_vars['damage_max'], width=6)
        e.grid(row=row, column=1, sticky="w")
        self.edit_frame_widgets.extend([e])
        row += 1
        tk.Label(ef, text="Súly (kg):").grid(row=row, column=0, sticky="w")
        self.edit_vars['weight'] = tk.StringVar()
        e = tk.Entry(ef, textvariable=self.edit_vars['weight'], width=8)
        e.grid(row=row, column=1, sticky="w")
        self.edit_frame_widgets.extend([e])
        row += 1
        tk.Label(ef, text="Sebzés típus:").grid(row=row, column=0, sticky="w")
        self.damage_type_vars = {typ: tk.IntVar() for typ in ["szúró", "vágó", "zúzó"]}
        type_cb_frame = tk.Frame(ef)
        type_cb_frame.grid(row=row, column=1, sticky="w")
        for typ, var in self.damage_type_vars.items():
            cb = tk.Checkbutton(type_cb_frame, text=typ.capitalize(), variable=var)
            cb.pack(side=tk.LEFT, padx=(2,2))
            self.edit_frame_widgets.append(cb)
        self.edit_frame_widgets.append(type_cb_frame)
        row += 1
        tk.Label(ef, text="Sebzés bónusz:").grid(row=row, column=0, sticky="w")
        self.damage_bonus_attr_vars = {attr: tk.IntVar() for attr in ["erő", "ügyesség"]}
        bonus_cb_frame = tk.Frame(ef)
        bonus_cb_frame.grid(row=row, column=1, sticky="w")
        for attr, var in self.damage_bonus_attr_vars.items():
            cb = tk.Checkbutton(bonus_cb_frame, text=attr.capitalize(), variable=var)
            cb.pack(side=tk.LEFT, padx=(2,2))
            self.edit_frame_widgets.append(cb)
        self.edit_frame_widgets.append(bonus_cb_frame)
        row += 1
        tk.Label(ef, text="Ár:").grid(row=row, column=0, sticky="nw")
        price_frame = tk.Frame(ef)
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
        self.edit_frame_widgets.append(price_frame)
        row += 1
        tk.Label(ef, text="STP (ellenálló képesség):").grid(row=row, column=0, sticky="w")
        self.edit_vars['stp'] = tk.StringVar()
        e = tk.Entry(ef, textvariable=self.edit_vars['stp'], width=8)
        e.grid(row=row, column=1, sticky="w")
        self.edit_frame_widgets.append(e)
        row += 1
        tk.Label(ef, text="SFÉ átütőképesség:").grid(row=row, column=0, sticky="w")
        self.edit_vars['armor_penetration'] = tk.StringVar()
        e = tk.Entry(ef, textvariable=self.edit_vars['armor_penetration'], width=8)
        e.grid(row=row, column=1, sticky="w")
        self.edit_frame_widgets.append(e)
        row += 1
        self.edit_vars['can_disarm'] = tk.IntVar()
        cb = tk.Checkbutton(ef, text="Alkalmas lefegyverzésre", variable=self.edit_vars['can_disarm'])
        cb.grid(row=row, column=0, sticky="w")
        self.edit_frame_widgets.append(cb)
        self.edit_vars['can_break_weapon'] = tk.IntVar()
        cb = tk.Checkbutton(ef, text="Alkalmas fegyvertörésre", variable=self.edit_vars['can_break_weapon'])
        cb.grid(row=row, column=1, sticky="w")
        self.edit_frame_widgets.append(cb)
        row += 1
        self.type_fields_frame = tk.Frame(ef)
        self.type_fields_frame.grid(row=row, column=0, columnspan=3, sticky="w")
        self.type_fields_widgets = []
        self.edit_frame_widgets.append(self.type_fields_frame)
        row += 1
        btn = tk.Button(ef, text="Mentés", command=self.save_item)
        btn.grid(row=row, column=1, pady=15, sticky="w")
        self.edit_frame_widgets.append(btn)

    def update_category_menu(self, type_value):
        options = self._get_weapon_categories(type_value)
        menu = self.category_menu["menu"]
        menu.delete(0, "end")
        for opt in options:
            menu.add_command(label=opt, command=lambda v=opt: self.edit_vars['category'].set(v))
        if options:
            current = self.edit_vars['category'].get()
            if current in options:
                self.edit_vars['category'].set(current)
            else:
                self.edit_vars['category'].set(options[0])
            self.category_label.grid(row=self.category_row, column=0, sticky="w")
            self.category_menu.grid(row=self.category_row, column=1, sticky="w")
        else:
            self.edit_vars['category'].set("")
            self.category_label.grid_remove()
            self.category_menu.grid_remove()

    def update_type_fields(self, selected_type):
        # Töröld a régi mezőket
        for w in self.type_fields_widgets:
            w.destroy()
        self.type_fields_widgets = []
        row = 0
        t = self.edit_vars['type'].get()
        self.update_category_menu(t)
        if t == "közelharci":
            for label, key in [("KE:", "KE"), ("TE:", "TE"), ("VE:", "VE"), ("Méretkategória:", "size_category")]:
                var = self.edit_vars.setdefault(key, tk.StringVar())
                l = tk.Label(self.type_fields_frame, text=label)
                l.grid(row=row, column=0, sticky="w")
                e = tk.Entry(self.type_fields_frame, textvariable=var, width=8)
                e.grid(row=row, column=1, sticky="w")
                self.type_fields_widgets.extend([l, e])
                row += 1
        elif t == "hajító":
            for label, key in [("KE:", "KE"), ("TE:", "TE"), ("VE:", "VE"), ("Táv (m):", "range")]:
                var = self.edit_vars.setdefault(key, tk.StringVar())
                l = tk.Label(self.type_fields_frame, text=label)
                l.grid(row=row, column=0, sticky="w")
                e = tk.Entry(self.type_fields_frame, textvariable=var, width=8)
                e.grid(row=row, column=1, sticky="w")
                self.type_fields_widgets.extend([l, e])
                row += 1
        elif t == "távolsági":
            for label, key in [("KE:", "KE"), ("CE:", "CE"), ("Táv (m):", "range")]:
                var = self.edit_vars.setdefault(key, tk.StringVar())
                l = tk.Label(self.type_fields_frame, text=label)
                l.grid(row=row, column=0, sticky="w")
                e = tk.Entry(self.type_fields_frame, textvariable=var, width=8)
                e.grid(row=row, column=1, sticky="w")
                self.type_fields_widgets.extend([l, e])
                row += 1
        elif t == "pajzs":
            for label, key in [("KE:", "KE"), ("VE:", "VE"), ("MGT:", "MGT")]:
                var = self.edit_vars.setdefault(key, tk.StringVar())
                l = tk.Label(self.type_fields_frame, text=label)
                l.grid(row=row, column=0, sticky="w")
                e = tk.Entry(self.type_fields_frame, textvariable=var, width=8)
                e.grid(row=row, column=1, sticky="w")
                self.type_fields_widgets.extend([l, e])
                row += 1

    def on_tree_select(self, event):
        selected = self.tree.focus()
        if not selected:
            return
        # Only allow selection of item nodes (not type/category)
        parent = self.tree.parent(selected)
        grandparent = self.tree.parent(parent)
        if not parent or not grandparent:
            return
        item_text = self.tree.item(selected, 'text')
        idx = None
        for i, item in enumerate(self.items):
            if item_text.startswith(item['name']):
                idx = i
                break
        if idx is None:
            return
        self.selected_idx = idx
        item = self.items[idx]
        # Reinitialize edit_vars if needed
        for key in ["name", "id", "type", "category", "attack_time", "weight", "stp", "armor_penetration"]:
            if key not in self.edit_vars:
                self.edit_vars[key] = tk.StringVar()
            self.edit_vars[key].set(str(item.get(key, "")))
        if 'damage_min' not in self.edit_vars:
            self.edit_vars['damage_min'] = tk.StringVar()
        if 'damage_max' not in self.edit_vars:
            self.edit_vars['damage_max'] = tk.StringVar()
        self.edit_vars['damage_min'].set(str(item.get('damage_min', "")))
        self.edit_vars['damage_max'].set(str(item.get('damage_max', "")))
        for typ, var in self.damage_type_vars.items():
            var.set(1 if typ in item.get('damage_types', []) else 0)
        for attr, var in self.damage_bonus_attr_vars.items():
            var.set(1 if attr in item.get('damage_bonus_attributes', []) else 0)
        if 'price_réz' not in self.edit_vars:
            self.edit_vars['price_réz'] = tk.StringVar()
        if 'price_ezüst' not in self.edit_vars:
            self.edit_vars['price_ezüst'] = tk.StringVar()
        if 'price_arany' not in self.edit_vars:
            self.edit_vars['price_arany'] = tk.StringVar()
        if 'price_mithrill' not in self.edit_vars:
            self.edit_vars['price_mithrill'] = tk.StringVar()
        try:
            from engine.currency_manager import CurrencyManager
            price = int(item.get('price', 0))
            price_parts = CurrencyManager().from_base(price)
            self.edit_vars['price_réz'].set(str(price_parts.get('réz', 0)))
            self.edit_vars['price_ezüst'].set(str(price_parts.get('ezüst', 0)))
            self.edit_vars['price_arany'].set(str(price_parts.get('arany', 0)))
            self.edit_vars['price_mithrill'].set(str(price_parts.get('mithrill', 0)))
        except Exception:
            self.edit_vars['price_réz'].set("")
            self.edit_vars['price_ezüst'].set("")
            self.edit_vars['price_arany'].set("")
            self.edit_vars['price_mithrill'].set("")
        if 'can_disarm' not in self.edit_vars:
            self.edit_vars['can_disarm'] = tk.IntVar()
        if 'can_break_weapon' not in self.edit_vars:
            self.edit_vars['can_break_weapon'] = tk.IntVar()
        self.edit_vars['can_disarm'].set(1 if item.get('can_disarm', False) else 0)
        self.edit_vars['can_break_weapon'].set(1 if item.get('can_break_weapon', False) else 0)
        self.edit_vars['type'].set(item.get('type', ''))
        self.update_type_fields(item.get('type', ''))
        t = item.get('type', '')
        for key in ["KE", "TE", "VE", "size_category", "range", "CE", "MGT"]:
            if key not in self.edit_vars:
                self.edit_vars[key] = tk.StringVar()
        if t in ["közelharci", "hajító"]:
            for key in ["KE", "TE", "VE", "size_category"]:
                self.edit_vars[key].set(str(item.get(key, "")))
            if t == "hajító":
                self.edit_vars["range"].set(str(item.get("range", "")))
        elif t == "távolsági":
            for key in ["KE", "CE", "range"]:
                self.edit_vars[key].set(str(item.get(key, "")))
        elif t == "pajzs":
            for key in ["KE", "VE", "MGT"]:
                self.edit_vars[key].set(str(item.get(key, "")))

    def save_item(self):
        # Ár összerakása
        try:
            from engine.currency_manager import CurrencyManager
            price_total = 0
            for curr in CurrencyManager.ORDER:
                val = int(self.edit_vars[f'price_{curr}'].get() or 0)
                price_total += CurrencyManager().to_base(val, curr)
        except Exception:
            price_total = int(self.edit_vars['price_réz'].get() or 0)
        # Sebzés típusok
        damage_types = [typ for typ, var in self.damage_type_vars.items() if var.get()]
        # Sebzés bónusz attribútumok
        damage_bonus_attributes = [attr for attr, var in self.damage_bonus_attr_vars.items() if var.get()]
        item = {
            'name': self.edit_vars['name'].get(),
            'id': self.edit_vars['id'].get(),
            'type': self.edit_vars['type'].get(),
            'category': self.edit_vars['category'].get(),
            'attack_time': int(self.edit_vars['attack_time'].get() or 0),
            'damage_min': int(self.edit_vars['damage_min'].get() or 0),
            'damage_max': int(self.edit_vars['damage_max'].get() or 0),
            'weight': float(self.edit_vars['weight'].get() or 0),
            'price': price_total,
            'stp': int(self.edit_vars['stp'].get() or 0),
            'armor_penetration': int(self.edit_vars['armor_penetration'].get() or 0),
            'can_disarm': bool(self.edit_vars['can_disarm'].get()),
            'can_break_weapon': bool(self.edit_vars['can_break_weapon'].get()),
            'damage_types': damage_types,
            'damage_bonus_attributes': damage_bonus_attributes
        }
        t = self.edit_vars['type'].get()
        if t in ["közelharci", "hajító"]:
            item['KE'] = int(self.edit_vars['KE'].get() or 0)
            item['TE'] = int(self.edit_vars['TE'].get() or 0)
            item['VE'] = int(self.edit_vars['VE'].get() or 0)
            item['size_category'] = int(self.edit_vars['size_category'].get() or 0)
            if t == "hajító":
                item['range'] = int(self.edit_vars['range'].get() or 0)
        elif t == "távolsági":
            item['KE'] = int(self.edit_vars['KE'].get() or 0)
            item['CE'] = int(self.edit_vars['CE'].get() or 0)
            item['range'] = int(self.edit_vars['range'].get() or 0)
        elif t == "pajzs":
            item['KE'] = int(self.edit_vars['KE'].get() or 0)
            item['VE'] = int(self.edit_vars['VE'].get() or 0)
            item['MGT'] = int(self.edit_vars['MGT'].get() or 0)
        # Validáció
        if not self.manager.validate(item):
            tk.messagebox.showerror("Hiba", "Hiányzó vagy hibás mező!")
            return
        # Mentés
        if self.selected_idx is not None:
            self.items[self.selected_idx] = item
        else:
            self.items.append(item)
        self.manager.save(self.items)
        self.refresh_list()
        tk.messagebox.showinfo("Mentés", "Fegyver/pajzs mentve!")

    def refresh_list(self):
        self.populate_treeview()

    def new_item(self):
        self.selected_idx = None
        for key in ["name", "id", "type", "category", "attack_time", "weight", "stp", "armor_penetration", "damage_min", "damage_max"]:
            self.edit_vars[key].set("")
        for key in ["KE", "TE", "VE", "size_category", "range", "CE", "MGT"]:
            if key in self.edit_vars:
                self.edit_vars[key].set("")
        self.edit_vars['price_réz'].set("")
        self.edit_vars['price_ezüst'].set("")
        self.edit_vars['price_arany'].set("")
        self.edit_vars['price_mithrill'].set("")
        self.edit_vars['can_disarm'].set(0)
        self.edit_vars['can_break_weapon'].set(0)
        for var in self.damage_type_vars.values():
            var.set(0)
        for var in self.damage_bonus_attr_vars.values():
            var.set(0)
        self.update_type_fields(self.edit_vars['type'].get())

    def delete_item(self):
        idxs = self.listbox.curselection()
        if not idxs:
            tk.messagebox.showwarning("Törlés", "Nincs kiválasztva fegyver/pajzs.")
            return
        idx = idxs[0]
        answer = tk.messagebox.askyesno("Törlés", f"Biztosan törlöd ezt?\n{self.items[idx]['name']}")
        if answer:
            self.items.pop(idx)
            self.manager.save(self.items)
            self.refresh_list()

if __name__ == "__main__":
    WeaponsAndShieldsEditor()
