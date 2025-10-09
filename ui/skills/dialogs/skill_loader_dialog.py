"""
Skill loader dialog for MAGUS RPG skill editor.

This module provides a dialog for loading existing skills from the database,
with search and filtering capabilities.
"""

import tkinter as tk
from tkinter import ttk
from utils.reopen_prevention import WindowSingleton

class SkillLoaderDialog:
    """
    Dialog for loading existing skills.
    
    Provides a searchable tree view of all available skills for loading
    into the editor. Includes filtering and category display.
    
    Attributes:
        editor: Parent skill editor instance
        all_skills (list): List of all skills from database
        loader (tk.Toplevel): Dialog window
        tree (ttk.Treeview): Tree view widget for skill list
    """
    def __init__(self, editor):
        self.editor = editor
        # Betöltjük az összes skilt (a placeholder-eket is tartalmazza)
        self.all_skills = editor.skill_manager.load()
        self.loader, created = WindowSingleton.get('skill_loader_dialog', lambda: tk.Toplevel(editor.win))
        if not created:
            return
        self.loader.title("Képzettség betöltése")
        self.loader.geometry("600x500")
        search_var = tk.StringVar()
        tk.Label(self.loader, text="Képzettség keresése:").pack(pady=(10,0))
        search_entry = tk.Entry(self.loader, textvariable=search_var, width=40)
        search_entry.pack(pady=(0,5))
        self.tree = ttk.Treeview(self.loader)
        self.tree.pack(fill="both", expand=True, pady=10)
        self.tree.heading("#0", text="Kategória / Képzettség", anchor="w")
        # Főkategóriák fix sorrendje
        MAIN_CATEGORY_ORDER = [
            "Harci képzettségek",
            "Szociális képzettségek",
            "Alvilági képzettségek",
            "Túlélő képzettségek",
            "Elméleti képzettségek"
        ]
        from collections import defaultdict
        cat_map = defaultdict(lambda: defaultdict(list))
        for skill in self.all_skills:
            main_cat = skill.get("main_category", "Egyéb")
            sub_cat = skill.get("sub_category", "Egyéb")
            cat_map[main_cat][sub_cat].append(skill)
        all_main_cats = [cat for cat in MAIN_CATEGORY_ORDER if cat in cat_map] + [cat for cat in cat_map if cat not in MAIN_CATEGORY_ORDER]
        self.tree_nodes = {}
        for main_cat in all_main_cats:
            main_id = self.tree.insert("", "end", text=main_cat, open=True)
            self.tree_nodes[main_cat] = main_id
            subcats = sorted(cat_map[main_cat].keys())
            for sub_cat in subcats:
                sub_id = self.tree.insert(main_id, "end", text=sub_cat, open=True)
                self.tree_nodes[(main_cat, sub_cat)] = sub_id
                for skill in cat_map[main_cat][sub_cat]:
                    param = skill.get("parameter", "")
                    if param:
                        skill_name = f"{skill['name']} ({param})"
                    else:
                        skill_name = skill['name']
                    self.tree.insert(sub_id, "end", text=skill_name, open=False)
        button_frame = tk.Frame(self.loader)
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="Betöltés", command=self.load_selected).pack(side=tk.LEFT, padx=20)
        tk.Button(button_frame, text="Törlés", command=self.delete_selected).pack(side=tk.LEFT, padx=20)
        def update_skill_list(*args):
            text = search_var.get().lower()
            for item in self.tree.get_children():
                self.tree.delete(item)
            MAIN_CATEGORY_ORDER = [
                "Harci képzettségek",
                "Szociális képzettségek",
                "Alvilági képzettségek",
                "Túlélő képzettségek",
                "Elméleti képzettségek"
            ]
            from collections import defaultdict
            cat_map = defaultdict(lambda: defaultdict(list))
            for skill in self.all_skills:
                main_cat = skill.get("main_category", "Egyéb")
                sub_cat = skill.get("sub_category", "Egyéb")
                param = skill.get("parameter", "")
                skill_name = f"{skill['name']} ({param})" if param else skill['name']
                if text and text not in skill_name.lower():
                    continue
                cat_map[main_cat][sub_cat].append(skill)
            all_main_cats = [cat for cat in MAIN_CATEGORY_ORDER if cat in cat_map] + [cat for cat in cat_map if cat not in MAIN_CATEGORY_ORDER]
            tree_nodes = {}
            for main_cat in all_main_cats:
                main_id = self.tree.insert("", "end", text=main_cat, open=True)
                tree_nodes[main_cat] = main_id
                subcats = sorted(cat_map[main_cat].keys())
                for sub_cat in subcats:
                    sub_id = self.tree.insert(main_id, "end", text=sub_cat, open=True)
                    tree_nodes[(main_cat, sub_cat)] = sub_id
                    for skill in cat_map[main_cat][sub_cat]:
                        param = skill.get("parameter", "")
                        skill_name = f"{skill['name']} ({param})" if param else skill['name']
                        self.tree.insert(sub_id, "end", text=skill_name, open=False)
        search_var.trace_add("write", update_skill_list)
    def load_selected(self):
        selected = self.tree.focus()
        if not selected:
            self.editor.show_warning("Nincs kiválasztva képzettség.", "Betöltés")
            return
        parent = self.tree.parent(selected)
        grandparent = self.tree.parent(parent)
        if not parent or not grandparent:
            self.editor.show_warning("Csak képzettséget válassz!", "Betöltés")
            return
        skill_name = self.tree.item(selected, "text")
        for skill_obj in self.all_skills:
            param = skill_obj.get("parameter", "")
            name = f"{skill_obj['name']} ({param})" if param else skill_obj['name']
            if name == skill_name:
                # Use SkillEditor's load_skill_to_ui for proper mapping and UI refresh
                self.editor.load_skill_to_ui(skill_obj)
                self.loader.destroy()
                return
        self.editor.show_error("Nem található a kiválasztott képzettség.")
    def delete_selected(self):
        selected = self.tree.focus()
        if not selected:
            self.editor.show_warning("Nincs kiválasztva képzettség.", "Törlés")
            return
        parent = self.tree.parent(selected)
        grandparent = self.tree.parent(parent)
        if not parent or not grandparent:
            self.editor.show_warning("Csak képzettséget válassz!", "Törlés")
            return
        skill_name = self.tree.item(selected, "text")
        for idx, skill_obj in enumerate(self.all_skills):
            param = skill_obj.get("parameter", "")
            name = f"{skill_obj['name']} ({param})" if param else skill_obj['name']
            if name == skill_name:
                answer = self.editor.ask_yes_no(f"Biztosan törlöd ezt a képzettséget?\n{name}", "Törlés")
                if answer:
                    skill_id = skill_obj.get("id")
                    if skill_id:
                        self.editor.skill_manager.delete_skill_by_id(skill_id)
                    # Frissítsük a listát a DB-ből
                    self.all_skills = self.editor.skill_manager.load()
                    self.editor.show_info("Képzettség törölve!", "Törlés")
                    self.loader.destroy()
                return
        self.editor.show_error("Nem található a kiválasztott képzettség.")
