import tkinter as tk
from tkinter import ttk
import os
from utils.json_manager import JsonManager

# --- JSON MANAGER ---
class GeneralEquipmentJsonManager(JsonManager):
    def validate(self, item):
        required = ["id", "name", "description", "weight", "price", "category"]
        for field in required:
            if field not in item or item[field] in (None, ""):
                return False
        # Kategóriafüggő mezők
        cat = item.get("category", "")
        if cat in ["eszköz", "élelem", "speciális"] and "space" not in item:
            return False
        if cat == "tároló" and "capacity" not in item:
            return False
        if cat == "élelem" and ("freshness" not in item or "durability" not in item):
            return False
        return True

GENERAL_JSON = os.path.join(os.path.dirname(__file__), "..", "..", "data", "equipment", "general_equipment.json")

# --- FŐ SZERKESZTŐ ---

class GeneralEquipmentEditor:
    CATEGORIES = ["eszköz", "élelem", "tároló", "speciális"]
    SPECIAL_SUBCATEGORIES = ["Alkímia"]

    def __init__(self):
        from utils.reopen_prevention import WindowSingleton
        self.win, created = WindowSingleton.get('general_equipment_editor', lambda: tk.Toplevel())
        if not created:
            return
        self.win.title("Általános felszerelés szerkesztő")
        self.win.geometry("1100x700")
        self.manager = GeneralEquipmentJsonManager(GENERAL_JSON)
        self.items = self.manager.load()
        self.selected_idx = None
        self.create_widgets()

    def create_widgets(self):
        main_frame = tk.Frame(self.win)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- BAL OLDALI TREEVIEW ---
        list_frame = tk.Frame(main_frame)
        list_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        tk.Label(list_frame, text="Felszerelések kategóriák szerint", font=("Arial", 14, "bold")).pack(pady=5)
        self.tree = ttk.Treeview(list_frame, show="tree", selectmode="browse", height=30)
        self.tree.pack(pady=5, fill=tk.Y, expand=True, ipadx=80)
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        self.tree_nodes = {}
        self.populate_treeview()
        tk.Button(list_frame, text="Új felszerelés", command=self.new_item).pack(pady=5)
        tk.Button(list_frame, text="Törlés", command=self.delete_item).pack(pady=5)

        # --- JOBB OLDALI SZERKESZTŐ PANEL ---
        self.edit_frame = tk.Frame(main_frame)
        self.edit_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.edit_vars = {}
        self.edit_frame_widgets = []
        self.populate_edit_panel()

    def populate_treeview(self):
        self.tree.delete(*self.tree.get_children())
        self.tree_nodes = {}
        cat_map = {cat: [] for cat in self.CATEGORIES}
        for idx, item in enumerate(self.items):
            cat = item.get('category', 'egyéb')
            cat_map.setdefault(cat, []).append((idx, item))
        for cat in self.CATEGORIES:
            cat_id = self.tree.insert('', 'end', text=cat.capitalize(), open=True)
            self.tree_nodes[cat] = cat_id
            if cat == "speciális":
                # Alkategóriák
                subcat_map = {}
                for idx, item in cat_map.get(cat, []):
                    subcat = item.get('subcategory', 'Egyéb')
                    subcat_map.setdefault(subcat, []).append((idx, item))
                for subcat in sorted(subcat_map.keys()):
                    subcat_id = self.tree.insert(cat_id, 'end', text=subcat, open=True)
                    for idx, item in subcat_map[subcat]:
                        node = self.tree.insert(subcat_id, 'end', text=f"{item.get('name', '-')}", open=False)
                        self.tree_nodes[(cat, subcat, idx)] = node
            else:
                for idx, item in cat_map.get(cat, []):
                    node = self.tree.insert(cat_id, 'end', text=f"{item.get('name', '-')}", open=False)
                    self.tree_nodes[(cat, idx)] = node

    def populate_edit_panel(self, item=None):
        for w in getattr(self, 'edit_frame_widgets', []):
            w.destroy()
        self.edit_frame_widgets = []
        ef = self.edit_frame
        row = 0
        # --- Alap mezők ---
        fields = [
            ("Azonosító:", 'id'),
            ("Név:", 'name'),
            ("Leírás:", 'description'),
            ("Súly (kg):", 'weight'),
        ]
        for label, key in fields:
            tk.Label(ef, text=label).grid(row=row, column=0, sticky="w")
            self.edit_vars[key] = tk.StringVar()
            e = tk.Entry(ef, textvariable=self.edit_vars[key], width=40)
            e.grid(row=row, column=1, sticky="w")
            self.edit_frame_widgets.append(e)
            row += 1
        # --- Ár mezők (currency manager) ---
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
        # --- Kategória választó ---
        tk.Label(ef, text="Kategória:").grid(row=row, column=0, sticky="w")
        self.edit_vars['category'] = tk.StringVar()
        om = tk.OptionMenu(ef, self.edit_vars['category'], *self.CATEGORIES, command=self.update_category_fields)
        om.grid(row=row, column=1, sticky="w")
        self.edit_frame_widgets.append(om)
        row += 1
        # --- Speciális alkategória mező ---
        self.special_subcat_label = tk.Label(ef, text="Alkategória:")
        self.special_subcat_om = tk.OptionMenu(ef, tk.StringVar(), *self.SPECIAL_SUBCATEGORIES)
        # --- Kategóriafüggő mezők helye ---
        self.category_fields_frame = tk.Frame(ef)
        self.category_fields_frame.grid(row=row, column=0, columnspan=3, sticky="w")
        self.category_fields_widgets = []
        self.edit_frame_widgets.append(self.category_fields_frame)
        row += 1
        # --- Mentés gomb ---
        btn = tk.Button(ef, text="Mentés", command=self.save_item)
        btn.grid(row=row, column=1, pady=15, sticky="w")
        self.edit_frame_widgets.append(btn)
        # Ha van item, töltsd be az értékeket
        if item:
            # Alap mezők
            for key in self.edit_vars:
                self.edit_vars[key].set(str(item.get(key, "")))
            # Ár szétbontása
            try:
                from engine.currency_manager import CurrencyManager
                price_raw = item.get('price', 0)
                try:
                    price = int(price_raw)
                except Exception:
                    try:
                        price = int(float(price_raw))
                    except Exception:
                        price = 0
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
            self.edit_vars['category'].set(item.get('category', ''))
            self.update_category_fields(item.get('category', ''))
            # Kategóriafüggő mezők értékeinek betöltése
            cat = item.get('category', '')
            if cat == 'speciális':
                if 'subcategory' not in self.edit_vars:
                    self.edit_vars['subcategory'] = tk.StringVar()
                self.edit_vars['subcategory'].set(item.get('subcategory', self.SPECIAL_SUBCATEGORIES[0]))
            if cat in ['eszköz', 'élelem', 'speciális']:
                if 'space' not in self.edit_vars:
                    self.edit_vars['space'] = tk.StringVar()
                self.edit_vars['space'].set(str(item.get('space', '')))
            if cat == 'tároló':
                if 'capacity' not in self.edit_vars:
                    self.edit_vars['capacity'] = tk.StringVar()
                self.edit_vars['capacity'].set(str(item.get('capacity', '')))
            if cat == 'élelem':
                if 'freshness' not in self.edit_vars:
                    self.edit_vars['freshness'] = tk.StringVar()
                if 'durability' not in self.edit_vars:
                    self.edit_vars['durability'] = tk.StringVar()
                if 'nutritional_value' not in self.edit_vars:
                     self.edit_vars['nutritional_value'] = tk.StringVar()
                self.edit_vars['freshness'].set(str(item.get('freshness', '')))
                self.edit_vars['durability'].set(str(item.get('durability', '')))
                self.edit_vars['nutritional_value'].set(str(item.get('nutritional_value', '')))
        else:
            self.update_category_fields(self.edit_vars['category'].get())

    def update_category_fields(self, selected_category):
        # Töröld a régi mezőket
        for w in getattr(self, 'category_fields_widgets', []):
            w.destroy()
        self.category_fields_widgets = []
        f = self.category_fields_frame
        row = 0
        cat = self.edit_vars['category'].get()
        # Speciális: alkategória
        if cat == "speciális":
            tk.Label(f, text="Alkategória:").grid(row=row, column=0, sticky="w")
            if 'subcategory' not in self.edit_vars:
                self.edit_vars['subcategory'] = tk.StringVar()
            om = tk.OptionMenu(f, self.edit_vars['subcategory'], *self.SPECIAL_SUBCATEGORIES)
            om.grid(row=row, column=1, sticky="w")
            self.category_fields_widgets.append(om)
            row += 1
        # Eszköz, Élelem, Speciális: helyigény
        if cat in ["eszköz", "élelem", "speciális"]:
            tk.Label(f, text="Helyigény:").grid(row=row, column=0, sticky="w")
            self.edit_vars['space'] = tk.StringVar()
            e = tk.Entry(f, textvariable=self.edit_vars['space'], width=10)
            e.grid(row=row, column=1, sticky="w")
            self.category_fields_widgets.append(e)
            row += 1
        # Tároló: kapacitás
        if cat == "tároló":
            tk.Label(f, text="Kapacitás:").grid(row=row, column=0, sticky="w")
            self.edit_vars['capacity'] = tk.StringVar()
            e = tk.Entry(f, textvariable=self.edit_vars['capacity'], width=10)
            e.grid(row=row, column=1, sticky="w")
            self.category_fields_widgets.append(e)
            row += 1
        # Élelem: frissesség, tartósság, tápérték
        if cat == "élelem":
            tk.Label(f, text="Frissesség:").grid(row=row, column=0, sticky="w")
            self.edit_vars['freshness'] = tk.StringVar()
            e = tk.Entry(f, textvariable=self.edit_vars['freshness'], width=10)
            e.grid(row=row, column=1, sticky="w")
            self.category_fields_widgets.append(e)
            row += 1
            tk.Label(f, text="Tartósság:").grid(row=row, column=0, sticky="w")
            self.edit_vars['durability'] = tk.StringVar()
            e = tk.Entry(f, textvariable=self.edit_vars['durability'], width=10)
            e.grid(row=row, column=1, sticky="w")
            self.category_fields_widgets.append(e)
            row += 1
            tk.Label(f, text="Tápérték:").grid(row=row, column=0, sticky="w")
            self.edit_vars['nutritional_value'] = tk.StringVar()
            e = tk.Entry(f, textvariable=self.edit_vars['nutritional_value'], width=10)
            e.grid(row=row, column=1, sticky="w")
            self.category_fields_widgets.append(e)
            row += 1

    def on_tree_select(self, event):
        selected = self.tree.focus()
        if not selected:
            return
        parent = self.tree.parent(selected)
        if not parent:
            return
        # Kikeressük az indexet
        cat = self.tree.item(parent, 'text').lower()
        name = self.tree.item(selected, 'text')
        idx = None
        for i, item in enumerate(self.items):
            if item.get('category', '').lower() == cat and item.get('name', '') == name:
                idx = i
                break
        if idx is None:
            return
        self.selected_idx = idx
        item = self.items[idx]
        self.populate_edit_panel(item)

    def save_item(self):
        # Ár összerakása
        try:
            from engine.currency_manager import CurrencyManager
            price_total = 0
            for curr in getattr(CurrencyManager, 'ORDER', ['réz', 'ezüst', 'arany', 'mithrill']):
                val = self.edit_vars.get(f'price_{curr}')
                try:
                    v = int(val.get() or 0)
                except Exception:
                    try:
                        v = int(float(val.get() or 0))
                    except Exception:
                        v = 0
                price_total += CurrencyManager().to_base(v, curr)
        except Exception:
            price_total = 0
        item = {
            'id': self.edit_vars['id'].get(),
            'name': self.edit_vars['name'].get(),
            'description': self.edit_vars['description'].get(),
            'weight': float(self.edit_vars['weight'].get() or 0),
            'price': price_total,
            'category': self.edit_vars['category'].get()
        }
        cat = item['category']
        if cat == "speciális":
            item['subcategory'] = self.edit_vars['subcategory'].get() or self.SPECIAL_SUBCATEGORIES[0]
        if cat in ["eszköz", "élelem", "speciális"]:
            item['space'] = int(self.edit_vars['space'].get() or 0)
        if cat == "tároló":
            item['capacity'] = int(self.edit_vars['capacity'].get() or 0)
        if cat == "élelem":
            item['freshness'] = int(self.edit_vars['freshness'].get() or 0)
            item['durability'] = int(self.edit_vars['durability'].get() or 0)
            try:
                item['nutritional_value'] = int(self.edit_vars['nutritional_value'].get() or 0)
            except Exception:
                item['nutritional_value'] = 0
        # Validáció
        if not self.manager.validate(item):
            tk.messagebox.showerror("Hiba", "Hiányzó vagy hibás mezők!")
            return
        # Mentés
        if self.selected_idx is not None:
            self.items[self.selected_idx] = item
        else:
            self.items.append(item)
        self.manager.save(self.items)
        self.populate_treeview()
        tk.messagebox.showinfo("Mentés", "Felszerelés mentve!")

    def new_item(self):
        self.selected_idx = None
        for key in ["id", "name", "description", "weight", "category", "space", "capacity", "freshness", "durability"]:
            self.edit_vars[key] = tk.StringVar()
        self.edit_vars['price_réz'].set("")
        self.edit_vars['price_ezüst'].set("")
        self.edit_vars['price_arany'].set("")
        self.edit_vars['price_mithrill'].set("")
        self.populate_edit_panel()

    def delete_item(self):
        selected = self.tree.focus()
        if not selected:
            return
        parent = self.tree.parent(selected)
        if not parent:
            return
        cat = self.tree.item(parent, 'text').lower()
        name = self.tree.item(selected, 'text')
        idx = None
        for i, item in enumerate(self.items):
            if item.get('category', '').lower() == cat and item.get('name', '') == name:
                idx = i
                break
        if idx is None:
            return
        answer = tk.messagebox.askyesno("Törlés", f"Biztosan törlöd ezt?\n{name}")
        if answer:
            del self.items[idx]
            self.manager.save(self.items)
            self.populate_treeview()
            self.populate_edit_panel()

if __name__ == "__main__":
    GeneralEquipmentEditor()
