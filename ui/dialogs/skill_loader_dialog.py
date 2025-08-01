import tkinter as tk
from tkinter import ttk
from utils.reopen_prevention import WindowSingleton

class SkillLoaderDialog:
    def __init__(self, editor):
        self.editor = editor
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
                    if skill.get("is_parametric") and skill.get("parameter"):
                        skill_name = f"{skill['name']} ({skill['parameter']})"
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
                if text and text not in (f"{skill['name']} ({skill['parameter']})".lower() if skill.get("is_parametric") and skill.get("parameter") else skill['name'].lower()):
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
                        if skill.get("is_parametric") and skill.get("parameter"):
                            skill_name = f"{skill['name']} ({skill['parameter']})"
                        else:
                            skill_name = skill['name']
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
            if skill_obj.get("is_parametric") and skill_obj.get("parameter"):
                name = f"{skill_obj['name']} ({skill_obj['parameter']})"
            else:
                name = skill_obj['name']
            if name == skill_name:
                self.editor.name_var.set(skill_obj["name"])
                self.editor.param_var.set(skill_obj.get("parameter", ""))
                self.editor.general_desc = skill_obj.get("description", "")
                if hasattr(self.editor, "general_desc_label"):
                    self.editor.general_desc_label.config(text=self.editor.general_desc)
                self.editor.main_cat_var.set(skill_obj.get("main_category", ""))
                self.editor.sub_cat_var.set(skill_obj.get("sub_category", ""))
                self.editor.acq_method_var.set(skill_obj.get("acquisition_method", ""))
                self.editor.acq_diff_var.set(skill_obj.get("acquisition_difficulty", ""))
                self.editor.type_var.set(skill_obj.get("skill_type", "%"))
                loaded_level_descs = []
                for i in range(1, 7):
                    desc = skill_obj.get("level_descriptions", {}).get(str(i), "")
                    loaded_level_descs.append(desc)
                self.editor.level_desc_texts = loaded_level_descs
                if skill_obj.get("skill_type", "%") == "%":
                    self.editor.kp_per_3_var.set(skill_obj.get("kp_per_3_percent", ""))
                    for kp_var in self.editor.kp_cost_vars:
                        kp_var.set("")
                else:
                    self.editor.kp_per_3_var.set("")
                    for i, kp_var in enumerate(self.editor.kp_cost_vars):
                        kp_var.set(skill_obj.get("kp_costs", {}).get(str(i+1), ""))
                self.editor.prereq_manager.load_prerequisites(skill_obj.get("prerequisites", {}))
                if hasattr(self.editor, "update_prereq_summary"):
                    self.editor.update_prereq_summary()
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
            if skill_obj.get("is_parametric") and skill_obj.get("parameter"):
                name = f"{skill_obj['name']} ({skill_obj['parameter']})"
            else:
                name = skill_obj['name']
            if name == skill_name:
                answer = self.editor.ask_yes_no(f"Biztosan törlöd ezt a képzettséget?\n{name}", "Törlés")
                if answer:
                    self.all_skills.pop(idx)
                    self.editor.skill_manager.save(self.all_skills)
                    self.editor.show_info("Képzettség törölve!", "Törlés")
                    self.loader.destroy()
                return
        self.editor.show_error("Nem található a kiválasztott képzettség.")
