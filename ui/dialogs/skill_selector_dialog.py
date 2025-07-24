import tkinter as tk
from tkinter import ttk
from utils.reopen_prevention import WindowSingleton

class SkillSelectorDialog:
    def __init__(self, parent, skill_list, callback):
        self.parent = parent
        self.callback = callback
        self.win, created = WindowSingleton.get('skill_selector_dialog', lambda: tk.Toplevel(parent))
        if not created:
            return
        self.win.title("Képzettség kiválasztása")
        self.win.geometry("500x600")
        tk.Label(self.win, text="Válassz egy képzettséget előfeltételként:", font=("Arial", 12)).pack(pady=10)
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(self.win, textvariable=self.search_var, width=40)
        search_entry.pack(pady=(0,5))
        self.tree = ttk.Treeview(self.win)
        self.tree.pack(fill="both", expand=True, pady=10)
        self.tree.heading("#0", text="Képzettség neve", anchor="w")
        self.skill_items = []
        self.populate_tree(skill_list)
        btn_frame = tk.Frame(self.win)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Kiválasztás", command=self.select_skill).pack(side=tk.LEFT, padx=20)
        tk.Button(btn_frame, text="Mégse", command=self.win.destroy).pack(side=tk.LEFT, padx=20)
        self.search_var.trace_add("write", lambda *args: self.filter_tree(skill_list))

    def populate_tree(self, skill_list):
        self.tree.delete(*self.tree.get_children())
        self.skill_items = []
        # Csoportosítás főkategória és alkategória szerint
        main_nodes = {}
        sub_nodes = {}
        for skill in skill_list:
            main_cat = skill.get("main_category", "Egyéb")
            sub_cat = skill.get("sub_category", "Egyéb")
            if skill.get("is_parametric") and skill.get("parameter"):
                display_name = f"{skill['name']} ({skill['parameter']})"
            else:
                display_name = skill['name']
            # Főkategória node
            if main_cat not in main_nodes:
                main_id = self.tree.insert("", "end", text=main_cat, open=True)  # open=True: alapból lenyitva
                main_nodes[main_cat] = main_id
            else:
                main_id = main_nodes[main_cat]
            # Alkategória node
            sub_key = (main_cat, sub_cat)
            if sub_key not in sub_nodes:
                sub_id = self.tree.insert(main_id, "end", text=sub_cat, open=True)
                sub_nodes[sub_key] = sub_id
            else:
                sub_id = sub_nodes[sub_key]
            # Skill node
            item_id = self.tree.insert(sub_id, "end", text=display_name)
            self.skill_items.append((item_id, skill))

    def filter_tree(self, skill_list):
        text = self.search_var.get().lower()
        filtered = []
        for skill in skill_list:
            if skill.get("is_parametric") and skill.get("parameter"):
                display_name = f"{skill['name']} ({skill['parameter']})"
            else:
                display_name = skill['name']
            if text in display_name.lower():
                filtered.append(skill)
        self.populate_tree(filtered)

    def select_skill(self):
        selected = self.tree.focus()
        if not selected:
            return
        for item_id, skill in self.skill_items:
            if item_id == selected:
                self.callback(skill)
                self.win.destroy()
                return
