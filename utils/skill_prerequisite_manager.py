"""
Skill prerequisite management UI for MAGUS RPG.

This module provides the PrerequisiteManager class for managing skill prerequisites
in the UI, including attribute and skill requirements by level.
"""

import tkinter as tk
from tkinter import ttk

STAT_NAMES = [
    "Erő", "Állóképesség", "Gyorsaság", "Ügyesség", "Karizma",
    "Egészség", "Intelligencia", "Akaraterő", "Asztrál", "Érzékelés"
]

class PrerequisiteManager:
    """
    Manages skill prerequisites in the UI.
    
    Handles creation and management of prerequisite widgets for both
    attribute requirements and skill requirements across six skill levels.
    
    Attributes:
        parent: Parent widget
        skill_names (list): List of available skill names
        all_skills (list): List of all skill data
        prereq_vars (list): List of prerequisite variables by level
    """
    def load_from_string(self, prereq_str):
        """
        Parses a prerequisite string and loads it using load_prerequisites.
        """
        # If already dict, just forward
        if isinstance(prereq_str, dict):
            self.load_prerequisites(prereq_str)
            return
        # Otherwise, parse string format
        import re
        result = {str(i+1): {"képesség": [], "képzettség": []} for i in range(6)}
        # Example format: "1: Tulajdonság: Erő 10+, Képzettség: Kardforgatás (Rövid kardok) 2. szint"
        lines = prereq_str.splitlines()
        for line in lines:
            m = re.match(r"(\d+): (.*)", line)
            if not m:
                continue
            idx = m.group(1)
            rest = m.group(2)
            stat_part = re.search(r"Tulajdonság: ([^,]*)", rest)
            skill_part = re.search(r"Képzettség: (.*)", rest)
            if stat_part:
                stats = [s.strip() for s in stat_part.group(1).split(",") if s.strip()]
                result[idx]["képesség"].extend(stats)
            if skill_part:
                skills = [s.strip() for s in skill_part.group(1).split(",") if s.strip()]
                result[idx]["képzettség"].extend(skills)
        self.load_prerequisites(result)
    def __init__(self, parent, skill_names, all_skills):
        """
        Initialize PrerequisiteManager.
        
        Args:
            parent: Parent widget
            skill_names (list): List of available skill names
            all_skills (list): List of all skill data
        """
        self.parent = parent
        self.skill_names = skill_names
        self.all_skills = all_skills
        self.prereq_vars = [[] for _ in range(6)]
    def create_stat_row_widget(self, frame, prereq_dict):
        """
        Create UI widgets for an attribute prerequisite row.
        
        Args:
            frame: Parent frame widget
            prereq_dict (dict): Prerequisite data dictionary
            
        Returns:
            tuple: Widget references (menu, entry, button)
        """
        row = len([w for w in frame.grid_slaves() if isinstance(w, tk.OptionMenu) or isinstance(w, tk.Entry)]) // 2 + 1
        stat_var = prereq_dict["name_var"]
        value_var = prereq_dict["value_var"]
        stat_menu = tk.OptionMenu(frame, stat_var, *STAT_NAMES)
        stat_menu.grid(row=row, column=0, padx=(20, 0), sticky="w")
        entry = tk.Entry(frame, textvariable=value_var, width=5)
        entry.grid(row=row, column=1, padx=10, sticky="w")
        def remove(prereq=prereq_dict):
            for w in prereq["widgets"]:
                w.destroy()
            for idx in range(6):
                if prereq in self.prereq_vars[idx]:
                    self.prereq_vars[idx].remove(prereq)
                    break
        btn = tk.Button(frame, text="Törlés", command=remove)
        btn.grid(row=row, column=1, padx=50, sticky="w")
        prereq_dict["widgets"] = (stat_menu, entry, btn)
        prereq_dict["to_dict"] = lambda: {
            "type": "stat",
            "name": stat_var.get(),
            "param": None,
            "level": value_var.get()
        }
        return stat_menu, entry, btn
    def create_skill_row_widget(self, frame, prereq_dict):
        """
        Create UI widgets for a skill prerequisite row.
        
        Args:
            frame: Parent frame widget
            prereq_dict (dict): Prerequisite data dictionary
            
        Returns:
            tuple: Widget references (label, label, button)
        """
        row = len([w for w in frame.grid_slaves() if isinstance(w, ttk.Combobox) or isinstance(w, tk.Entry) or isinstance(w, tk.Label)]) // 2 + 1
        skill_var = prereq_dict["name_var"]
        level_var = prereq_dict["level_var"]
        param_var = prereq_dict.get("param_var", None)
        def parse_skill_name(name):
            import re
            m = re.match(r"(.+?)(?: \((.+?)\))?$", name)
            base = m.group(1) if m else name
            param = m.group(2) if m and m.group(2) else ""
            return base, param
        base_name, param_in_name = parse_skill_name(skill_var.get())
        param = param_var.get() if param_var is not None else ""
        display_text = base_name
        if param:
            display_text += f" ({param})"
        skill_label = tk.Label(frame, text=display_text, width=30, anchor="w")
        skill_label.grid(row=row, column=2, padx=(5, 0), sticky="w")
        level_label = tk.Label(frame, text=level_var.get(), width=5, anchor="w")
        level_label.grid(row=row, column=3, padx=10, sticky="w")
        def remove(prereq=prereq_dict):
            for w in prereq["widgets"]:
                w.destroy()
            for idx in range(6):
                if prereq in self.prereq_vars[idx]:
                    self.prereq_vars[idx].remove(prereq)
                    break
        btn = tk.Button(frame, text="Törlés", command=remove)
        btn.grid(row=row, column=4, padx=50, sticky="w")
        prereq_dict["widgets"] = (skill_label, level_label, btn)
        prereq_dict["to_dict"] = lambda: {
            "type": "skill",
            "name": base_name,
            "param": param,
            "level": level_var.get()
        }
        return skill_label, level_label, btn
    def add_stat_row(self, level_idx, frame):
        """
        Add a new attribute prerequisite row.
        
        Args:
            level_idx (int): Level index (0-5)
            frame: Parent frame widget
        """
        prereq_dict = {
            "type": "stat",
            "name_var": tk.StringVar(value=STAT_NAMES[0]),
            "value_var": tk.StringVar(),
        }
        self.create_stat_row_widget(frame, prereq_dict)
        self.prereq_vars[level_idx].append(prereq_dict)
    def add_skill_row(self, level_idx, frame):
        """
        Add a new skill prerequisite row with skill search dialog.
        
        Args:
            level_idx (int): Level index (0-5)
            frame: Parent frame widget
        """
        dialog = tk.Toplevel(frame)
        dialog.title("Képzettség keresése")
        dialog.geometry("400x180")
        search_var = tk.StringVar()
        tk.Label(dialog, text="Képzettség keresése:").pack()
        search_entry = tk.Entry(dialog, textvariable=search_var, width=40)
        search_entry.pack()
        skill_names_with_param = []
        for s in self.all_skills:
            if s.get("is_parametric") and s.get("parameter"):
                skill_names_with_param.append(f"{s['name']} ({s['parameter']})")
            else:
                skill_names_with_param.append(s['name'])
        filtered_skills = skill_names_with_param.copy()
        skill_var = tk.StringVar()
        level_var = tk.StringVar()
        skill_combo = ttk.Combobox(dialog, textvariable=skill_var, values=filtered_skills, state="readonly", width=35)
        skill_combo.pack(pady=5)
        tk.Label(dialog, text="Szükséges szint:").pack()
        level_entry = tk.Entry(dialog, textvariable=level_var, width=5)
        level_entry.pack()
        def update_skill_list(*args):
            text = search_var.get().lower()
            filtered = [s for s in skill_names_with_param if text in s.lower()]
            skill_combo['values'] = filtered
            if filtered:
                skill_var.set(filtered[0])
            else:
                skill_var.set("")
        search_var.trace_add("write", update_skill_list)
        def add_skill():
            skill = skill_var.get()
            level = level_var.get()
            if skill and level:
                import re
                m = re.match(r"(.+?)(?: \((.+?)\))?$", skill)
                base_name = m.group(1) if m else skill
                param = m.group(2) if m and m.group(2) else ""
                prereq_dict = {
                    "type": "skill",
                    "name_var": tk.StringVar(value=base_name),
                    "level_var": level_var,
                    "param_var": tk.StringVar(value=param),
                }
                self.create_skill_row_widget(frame, prereq_dict)
                self.prereq_vars[level_idx].append(prereq_dict)
                dialog.destroy()
        tk.Button(dialog, text="Hozzáadás", command=add_skill).pack(pady=5)
    def clear_all(self):
        """Clear all prerequisite widgets and data."""
        for idx in range(6):
            for prereq in self.prereq_vars[idx][:]:
                for w in prereq.get("widgets", []):
                    w.destroy()
            self.prereq_vars[idx].clear()
    def load_prerequisites(self, prerequisites):
        """
        Load prerequisites from dictionary and create UI widgets.
        
        Args:
            prerequisites (dict): Prerequisites organized by level
        """
        self.clear_all()
        for idx in range(6):
            prereq = prerequisites.get(str(idx+1), {})
            frame = self.frames[idx] if hasattr(self, 'frames') and len(self.frames) > idx else None
            # Tulajdonságok
            for stat_str in prereq.get("képesség", []):
                parts = stat_str.split()
                if len(parts) >= 2:
                    prereq_dict = {
                        "type": "stat",
                        "name_var": tk.StringVar(value=parts[0]),
                        "value_var": tk.StringVar(value=parts[1].replace("+", "")),
                    }
                    if frame:
                        self.create_stat_row_widget(frame, prereq_dict)
                    self.prereq_vars[idx].append(prereq_dict)
            # Képzettségek
            for skill_str in prereq.get("képzettség", []):
                import re
                m = re.match(r"(.+?)(?: \((.+?)\))? (\d+)\. szint", skill_str)
                if m:
                    skillname = m.group(1)
                    param = m.group(2) or ""
                    level = m.group(3)
                    prereq_dict = {
                        "type": "skill",
                        "name_var": tk.StringVar(value=skillname),
                        "level_var": tk.StringVar(value=level),
                        "param_var": tk.StringVar(value=param),
                    }
                    if frame:
                        self.create_skill_row_widget(frame, prereq_dict)
                    self.prereq_vars[idx].append(prereq_dict)
