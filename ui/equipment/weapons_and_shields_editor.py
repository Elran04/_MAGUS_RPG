import tkinter as tk
import os
from utils.weapondata_manager import WeaponDataManager

WEAPONS_JSON = os.path.join(os.path.dirname(__file__), "..", "..", "data", "equipment", "weapons_and_shields.json")

class WeaponsAndShieldsEditor:
    # Field definitions from manager (class-level, always available)
    BASE_FIELDS = WeaponDataManager.BASE_FIELDS
    PRICE_FIELDS = WeaponDataManager.PRICE_FIELDS
    TYPE_FIELDS = WeaponDataManager.TYPE_FIELDS
    VARIABLE_FIELDS = WeaponDataManager.VARIABLE_FIELDS
    CHECKBOX_FIELDS = WeaponDataManager.CHECKBOX_FIELDS
    TYPE_FIELD_DEFS = WeaponDataManager.TYPE_FIELD_DEFS
    DAMAGE_TYPES = WeaponDataManager.DAMAGE_TYPES
    DAMAGE_BONUS_ATTRS = WeaponDataManager.DAMAGE_BONUS_ATTRS

    def __init__(self):
        from utils.reopen_prevention import WindowSingleton
        self.win, created = WindowSingleton.get('weapons_and_shields_editor', lambda: tk.Toplevel())
        if not created:
            return
        self.manager = WeaponDataManager(WEAPONS_JSON)
        self.items = self.manager.load()
        self.selected_idx = None
        self.category_options = []
        self.type_fields_widgets = []  # Mindig legyen inicializálva!
        self.type_fields_frame = tk.Frame()  # Inicializáljuk, hogy mindig létezzen
        # Damage types és bonus attributes csak egyszer, managerből!
        self.damage_type_vars = {typ: tk.IntVar() for typ in self.DAMAGE_TYPES}
        self.damage_bonus_attr_vars = {attr: tk.IntVar() for attr in self.DAMAGE_BONUS_ATTRS}
        self.win.title("Fegyverek és pajzsok szerkesztője")
        self.win.geometry("1100x700")
        self.create_widgets()

    def destroy_edit_widgets(self):
        # Egységes widget destroy, csak edit_frame_widgets listából
        for w in self.edit_frame_widgets:
            w.destroy()
        self.edit_frame_widgets = []

    def _init_edit_vars(self):
        # Központi meződefiníciók alapján, csak class-level/managerből
        for key in self.BASE_FIELDS + self.PRICE_FIELDS + self.TYPE_FIELDS + self.VARIABLE_FIELDS:
            if key not in self.edit_vars:
                self.edit_vars[key] = tk.StringVar()
        if 'wield_mode' not in self.edit_vars:
            self.edit_vars['wield_mode'] = tk.StringVar()
        if 'variable_dual_wield' not in self.edit_vars:
            self.edit_vars['variable_dual_wield'] = tk.IntVar()
        for key in self.CHECKBOX_FIELDS:
            if key not in self.edit_vars:
                self.edit_vars[key] = tk.IntVar()

    def _fill_edit_vars(self, item):
        # Alap mezők
        for key in self.BASE_FIELDS:
            self.edit_vars[key].set(str(item.get(key, "")))
        # Ár mezők
        try:
            from engine.currency_manager import CurrencyManager
            price = int(item.get('price', 0))
            price_parts = CurrencyManager().from_base(price)
            for key in self.PRICE_FIELDS:
                curr = key.split('_')[1]  # 'réz', 'ezüst', stb.
                self.edit_vars[key].set(str(price_parts.get(curr, 0)))
        except Exception:
            for key in self.PRICE_FIELDS:
                self.edit_vars[key].set("")
        # Típusfüggő mezők
        t = item.get('type', '')
        if t in ["közelharci"]:
            for key in ["KE", "TE", "VE", "size_category"]:
                self.edit_vars[key].set(str(item.get(key, "")))
        elif t == "hajító":
            for key in ["KE", "TE", "VE", "range"]:
                self.edit_vars[key].set(str(item.get(key, "")))
        elif t == "távolsági":
            for key in ["KE", "CE", "range"]:
                self.edit_vars[key].set(str(item.get(key, "")))
        elif t == "pajzs":
            for key in ["KE", "VE", "MGT"]:
                self.edit_vars[key].set(str(item.get(key, "")))
        # Wield mode
        if t == "közelharci":
            self.edit_vars['wield_mode'].set(item.get('wield_mode', 'Egykezes'))
            if item.get('wield_mode') == "Változó":
                for key in self.VARIABLE_FIELDS:
                    self.edit_vars[key].set(str(item.get(key, 0)))
                self.edit_vars['variable_dual_wield'].set(1 if item.get('variable_dual_wield', False) else 0)
        # Checkboxes
        for key in self.CHECKBOX_FIELDS:
            self.edit_vars[key].set(1 if item.get(key, False) else 0)
        # Damage types
        for typ, var in self.damage_type_vars.items():
            var.set(1 if typ in item.get('damage_types', []) else 0)
        for attr, var in self.damage_bonus_attr_vars.items():
            var.set(1 if attr in item.get('damage_bonus_attributes', []) else 0)
    # ...existing code...

    # nincs szükség külön _on_close metódusra, WindowSingleton kezeli

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
        type_order = self.manager.get_weapon_types()
        type_items = {}
        for idx, item in enumerate(self.items):
            type_val = item.get('type', 'Egyéb')
            cat_val = item.get('category', '') or 'Egyéb'
            type_items.setdefault(type_val, []).append((cat_val, idx, item))
        # Insert types in preferred order, then any others
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
        self.destroy_edit_widgets()
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
        type_options = self.manager.get_weapon_types()
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
        type_cb_frame = tk.Frame(ef)
        type_cb_frame.grid(row=row, column=1, sticky="w")
        for typ, var in self.damage_type_vars.items():
            cb = tk.Checkbutton(type_cb_frame, text=typ.capitalize(), variable=var)
            cb.pack(side=tk.LEFT, padx=(2,2))
            self.edit_frame_widgets.append(cb)
        self.edit_frame_widgets.append(type_cb_frame)
        row += 1
        tk.Label(ef, text="Sebzés bónusz:").grid(row=row, column=0, sticky="w")
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
        options = self.manager.get_weapon_categories(type_value)
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

    def add_labeled_entry(self, parent, label_text, var, row, width=8):
        l = tk.Label(parent, text=label_text)
        l.grid(row=row, column=0, sticky="w")
        e = tk.Entry(parent, textvariable=var, width=width)
        e.grid(row=row, column=1, sticky="w")
        self.type_fields_widgets.extend([l, e])
        return row + 1

    def add_checkbutton(self, parent, text, var, row, col=0, colspan=1):
        cb = tk.Checkbutton(parent, text=text, variable=var)
        cb.grid(row=row, column=col, columnspan=colspan, sticky="w")
        self.type_fields_widgets.append(cb)
        return row + 1

    def update_type_fields(self, selected_type):
        # Töröld a régi mezőket
        for w in self.type_fields_widgets:
            w.destroy()
        self.type_fields_widgets = []
        row = 0
        t = self.edit_vars['type'].get()
        self.update_category_menu(t)

        # Wield mode (csak közelharci)
        if t == "közelharci":
            wield_options = ["Egykezes", "Kétkezes", "Változó"]
            l = tk.Label(self.type_fields_frame, text="Használati mód:")
            l.grid(row=row, column=0, sticky="w")
            om = tk.OptionMenu(self.type_fields_frame, self.edit_vars['wield_mode'], *wield_options, command=lambda _: self.update_type_fields(t))
            om.grid(row=row, column=1, sticky="w")
            self.type_fields_widgets.extend([l, om])
            row += 1

        # Típusfüggő mezők generikusan
        for label, key in self.TYPE_FIELD_DEFS.get(t, []):
            var = self.edit_vars.setdefault(key, tk.StringVar())
            row = self.add_labeled_entry(self.type_fields_frame, label, var, row)

        # Változó extra mezők (csak közelharci, Változó)
        if t == "közelharci" and self.edit_vars['wield_mode'].get() == "Változó":
            for label, key in [
                ("Erő szükséglet:", "variable_strength_req"),
                ("Ügyesség szükséglet:", "variable_dex_req"),
                ("Bonus KÉ:", "variable_bonus_KE"),
                ("Bonus TÉ:", "variable_bonus_TE"),
                ("Bonus VÉ:", "variable_bonus_VE"),
            ]:
                var = self.edit_vars.setdefault(key, tk.StringVar())
                row = self.add_labeled_entry(self.type_fields_frame, label, var, row)
            row = self.add_checkbutton(self.type_fields_frame, "Kétkezes harc lehetséges", self.edit_vars['variable_dual_wield'], row)

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
        self.selected_idx = None
        item = None
        for i, it in enumerate(self.items):
            if item_text.startswith(it['name']):
                self.selected_idx = i
                item = it
                break
        if item is None:
            return
        self._init_edit_vars()
        self._fill_edit_vars(item)
        self.edit_vars['type'].set(item.get('type', ''))
        self.update_type_fields(item.get('type', ''))
        # Régi típusfüggő mezőkitöltés törölve, csak az _fill_edit_vars használatos

    def save_item(self):
        # Collect field values from edit_vars
        fields = {key: var.get() for key, var in self.edit_vars.items()}
        # Collect damage types and bonus attributes
        fields['damage_types'] = [typ for typ, var in self.damage_type_vars.items() if var.get()]
        fields['damage_bonus_attributes'] = [attr for attr, var in self.damage_bonus_attr_vars.items() if var.get()]
        # Build item dict using manager logic
        try:
            item = self.manager.build_item_from_fields(fields)
        except Exception as e:
            tk.messagebox.showerror("Hiba", f"Hibás adat: {e}")
            return
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
        self.reset_edit_vars()
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
