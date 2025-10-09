"""
Skill prerequisite editor dialog for MAGUS RPG.

This module provides a dialog for editing skill prerequisites including
attribute and skill requirements for each skill level.
"""

import tkinter as tk
from utils.skill_prerequisite_manager import STAT_NAMES
from utils.reopen_prevention import WindowSingleton

class SkillPrerequisiteEditorDialog:
    """
    Dialog for editing skill prerequisites.
    
    Provides a UI for managing:
    - Attribute prerequisites (e.g., Strength 12+)
    - Skill prerequisites (e.g., Sword Use level 2)
    
    Prerequisites can be set independently for each of the 6 skill levels.
    
    Attributes:
        editor: Parent skill editor instance
        win (tk.Toplevel): Dialog window
        canvas (tk.Canvas): Scrollable canvas for prerequisite widgets
        scroll_frame (tk.Frame): Frame containing prerequisite widgets
    """
    def __init__(self, editor):
        self.editor = editor
        self.win, created = WindowSingleton.get('prerequisite_editor', lambda: tk.Toplevel(editor.win))
        if not created:
            return
        self.win.title("Előfeltételek szerkesztése")
        self.win.geometry("1024x768")
        tk.Label(self.win, text="Itt szerkesztheted az összes szint előfeltételeit (tulajdonságok és képzettségek)", font=("Arial", 12)).pack(pady=10)
        # Görgethető panel
        self.canvas = tk.Canvas(self.win, borderwidth=0, background="#f0f0f0")
        self.scroll_frame = tk.Frame(self.canvas, background="#f0f0f0")
        self.vsb = tk.Scrollbar(self.win, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.create_window((0,0), window=self.scroll_frame, anchor="nw")
        self.scroll_frame.bind("<Configure>", lambda event: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.prereq_vars = [[] for _ in range(6)]
        self.stat_frames = []
        self.skill_frames = []
        self.frames = []
        # Betöltjük az aktuális előfeltételeket
        for idx in range(6):
            self.prereq_vars[idx] = []
            for prereq in self.editor.prereq_manager.prereq_vars[idx]:
                # Mélymásolat, hogy a szerkesztés ne legyen azonnali
                if prereq["type"] == "stat":
                    self.prereq_vars[idx].append({
                        "type": "stat",
                        "name_var": tk.StringVar(value=prereq["name_var"].get()),
                        "value_var": tk.StringVar(value=prereq["value_var"].get()),
                    })
                elif prereq["type"] == "skill":
                    self.prereq_vars[idx].append({
                        "type": "skill",
                        "name_var": tk.StringVar(value=prereq["name_var"].get()),
                        "level_var": tk.StringVar(value=prereq["level_var"].get()),
                        "param_var": tk.StringVar(value=prereq.get("param_var", tk.StringVar()).get()),
                    })
        # UI: minden szinthez külön frame, gombok, lista
        for i in range(1, 7):
            main_frame = tk.LabelFrame(self.scroll_frame, text=f"{i}. szint előfeltételek", padx=10, pady=5)
            main_frame.pack(fill="x", padx=10, pady=5)
            btn_row = tk.Frame(main_frame)
            btn_row.pack(anchor="w")
            tk.Button(
                btn_row, text="Tulajdonság hozzáadása",
                command=lambda idx=i-1: self.add_stat_row(idx)
            ).pack(side="left", padx=(0,10))
            tk.Button(
                btn_row, text="Képzettség hozzáadása",
                command=lambda idx=i-1: self.add_skill_row(idx)
            ).pack(side="left", padx=(60,10))
            stat_frame = tk.Frame(main_frame)
            stat_frame.pack(side="left", fill="y", padx=5)
            skill_frame = tk.Frame(main_frame)
            skill_frame.pack(side="left", fill="y", padx=5)
            self.stat_frames.append(stat_frame)
            self.skill_frames.append(skill_frame)
            self.frames.append(main_frame)
        self.refresh_all_rows()
        save_btn = tk.Button(self.scroll_frame, text="Mentés", command=self.save_and_close)
        save_btn.pack(pady=20)

    def refresh_all_rows(self):
        for idx in range(6):
            for w in self.stat_frames[idx].winfo_children():
                w.destroy()
            for w in self.skill_frames[idx].winfo_children():
                w.destroy()
            for prereq in self.prereq_vars[idx]:
                if prereq["type"] == "stat":
                    self.create_stat_row_widget(self.stat_frames[idx], prereq, idx)
                elif prereq["type"] == "skill":
                    self.create_skill_row_widget(self.skill_frames[idx], prereq, idx)

    def create_stat_row_widget(self, frame, prereq_dict, level_idx):
        row = len(frame.winfo_children())
        stat_var = prereq_dict["name_var"]
        value_var = prereq_dict["value_var"]
        stat_menu = tk.OptionMenu(frame, stat_var, *STAT_NAMES)
        stat_menu.grid(row=row, column=0, padx=(0, 0), sticky="w")
        entry = tk.Entry(frame, textvariable=value_var, width=5)
        entry.grid(row=row, column=1, padx=10, sticky="w")
        def remove():
            self.prereq_vars[level_idx].remove(prereq_dict)
            self.refresh_all_rows()
        btn = tk.Button(frame, text="Törlés", command=remove)
        btn.grid(row=row, column=2, padx=10, sticky="w")

    def create_skill_row_widget(self, frame, prereq_dict, level_idx):
        row = len(frame.winfo_children())
        skill_var = prereq_dict["name_var"]
        level_var = prereq_dict["level_var"]
        param_var = prereq_dict.get("param_var", None)
        def remove():
            self.prereq_vars[level_idx].remove(prereq_dict)
            self.refresh_all_rows()
        # Skill gomb: kattintásra új skill választható
        def select_new_skill():
            from ui.skills.dialogs.skill_selector_dialog import SkillSelectorDialog
            skill_list = self.editor.skill_manager.load()
            def on_skill_selected(skill):
                skill_var.set(skill["name"])
                if param_var is not None:
                    param_var.set(skill.get("parameter", ""))
                self.refresh_all_rows()
            SkillSelectorDialog(self.win, skill_list, on_skill_selected)
        # Gomb felirata: név (paraméter)
        display_name = skill_var.get()
        param_value = param_var.get() if param_var is not None else ""
        if param_value:
            display_name = f"{display_name} ({param_value})"
        skill_btn = tk.Button(frame, text=display_name or "Képzettség kiválasztása", command=select_new_skill, width=28)
        skill_btn.grid(row=row, column=0, padx=5, sticky="w")
        # Szint választó OptionMenu
        level_choices = [str(i) for i in range(1,7)]
        if level_var.get() not in level_choices:
            level_var.set(level_choices[0])
        level_menu = tk.OptionMenu(frame, level_var, *level_choices)
        level_menu.grid(row=row, column=1, padx=5, sticky="w")
        # Törlés gomb
        btn = tk.Button(frame, text="Törlés", command=remove)
        btn.grid(row=row, column=2, padx=10, sticky="w")

    def add_stat_row(self, level_idx):
        prereq_dict = {
            "type": "stat",
            "name_var": tk.StringVar(value=STAT_NAMES[0]),
            "value_var": tk.StringVar(),
        }
        self.prereq_vars[level_idx].append(prereq_dict)
        self.refresh_all_rows()

    def add_skill_row(self, level_idx):
        # SkillSelectorDialog import csak itt, hogy ne legyen körkörös import
        from ui.skills.dialogs.skill_selector_dialog import SkillSelectorDialog
        # Skill listát az editor.skill_manager-ből vesszük
        skill_list = self.editor.skill_manager.load()
        def on_skill_selected(skill):
            prereq_dict = {
                "type": "skill",
                "name_var": tk.StringVar(value=skill["name"]),
                "level_var": tk.StringVar(),
                "param_var": tk.StringVar(value=skill.get("parameter", "")),
            }
            self.prereq_vars[level_idx].append(prereq_dict)
            self.refresh_all_rows()
        SkillSelectorDialog(self.win, skill_list, on_skill_selected)

    def save_and_close(self):
        # Visszaírjuk az adatokat az editor.prereq_manager-be
        for idx in range(6):
            self.editor.prereq_manager.prereq_vars[idx].clear()
            for prereq in self.prereq_vars[idx]:
                if prereq["type"] == "stat":
                    self.editor.prereq_manager.prereq_vars[idx].append({
                        "type": "stat",
                        "name_var": prereq["name_var"],
                        "value_var": prereq["value_var"],
                    })
                elif prereq["type"] == "skill":
                    self.editor.prereq_manager.prereq_vars[idx].append({
                        "type": "skill",
                        "name_var": prereq["name_var"],
                        "level_var": prereq["level_var"],
                        "param_var": prereq.get("param_var", tk.StringVar()),
                    })
        self.editor.update_prereq_summary()
        self.win.destroy()
