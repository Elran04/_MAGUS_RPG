import tkinter as tk
from tkinter import ttk
from utils.prerequisite_manager import STAT_NAMES

class PrerequisiteEditorDialog:
    def __init__(self, editor):
        self.editor = editor
        self.win = tk.Toplevel(editor.win)
        self.win.title("Előfeltételek szerkesztése")
        self.win.geometry("1024x768")
        tk.Label(self.win, text="Itt szerkesztheted az összes szint előfeltételeit (tulajdonságok és képzettségek)", font=("Arial", 12)).pack(pady=10)
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
            main_frame = tk.LabelFrame(self.win, text=f"{i}. szint előfeltételek", padx=10, pady=5)
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
            ).pack(side="left", padx=(0,10))
            stat_frame = tk.Frame(main_frame)
            stat_frame.pack(side="left", fill="y", padx=5)
            skill_frame = tk.Frame(main_frame)
            skill_frame.pack(side="left", fill="y", padx=5)
            self.stat_frames.append(stat_frame)
            self.skill_frames.append(skill_frame)
            self.frames.append(main_frame)
        self.refresh_all_rows()
        save_btn = tk.Button(self.win, text="Mentés", command=self.save_and_close)
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
        skill_entry = tk.Entry(frame, textvariable=skill_var, width=25)
        skill_entry.grid(row=row, column=0, padx=5, sticky="w")
        param_entry = None
        if param_var is not None:
            param_entry = tk.Entry(frame, textvariable=param_var, width=12)
            param_entry.grid(row=row, column=1, padx=5, sticky="w")
        level_entry = tk.Entry(frame, textvariable=level_var, width=5)
        level_entry.grid(row=row, column=2, padx=5, sticky="w")
        btn = tk.Button(frame, text="Törlés", command=remove)
        btn.grid(row=row, column=3, padx=10, sticky="w")

    def add_stat_row(self, level_idx):
        prereq_dict = {
            "type": "stat",
            "name_var": tk.StringVar(value=STAT_NAMES[0]),
            "value_var": tk.StringVar(),
        }
        self.prereq_vars[level_idx].append(prereq_dict)
        self.refresh_all_rows()

    def add_skill_row(self, level_idx):
        prereq_dict = {
            "type": "skill",
            "name_var": tk.StringVar(),
            "level_var": tk.StringVar(),
            "param_var": tk.StringVar(),
        }
        self.prereq_vars[level_idx].append(prereq_dict)
        self.refresh_all_rows()

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
