"""
Skill editor UI for MAGUS RPG.

This module provides a comprehensive editor for creating and modifying skills,
including their costs, prerequisites, descriptions, and level-based properties.
"""

import tkinter as tk
from utils.reopen_prevention import WindowSingleton
from tkinter import messagebox
from utils.skilldata_manager import SkillManager
import re
from ui.skills.skill_prerequisite_editor import SkillPrerequisiteEditorDialog
from ui.skills.dialogs.skill_loader_dialog import SkillLoaderDialog
from utils.skill_prerequisite_manager import PrerequisiteManager


CATEGORIES = {
    "Harci képzettségek": ["Közkeletű", "Szakértő", "Titkos"],
    "Szociális képzettségek": ["Általános", "Nemesi", "Polgári", "Póri", "Művész"],
    "Alvilági képzettségek": ["Álcázó", "Kommunikációs", "Pénzszerző", "Harci", "Behatoló", "Ellenálló"],
    "Túlélő képzettségek": ["Vadonjáró", "Atlétikai"],
    "Elméleti képzettségek": ["Közkeletű", "Szakértő", "Titkos elméleti", "Titkos szervezeti"],
    "Helyfoglaló képzettségek": ["Harci képzettségek", "Szociális képzettségek", "Alvilági képzettségek", "Túlélő képzettségek", "Elméleti képzettségek"]
}
ACQ_METHOD_MAP = {1: "Gyakorlás", 2: "Tapasztalás", 3: "Tanulás"}
ACQ_METHOD_MAP_REV = {v: k for k, v in ACQ_METHOD_MAP.items()}
ACQ_DIFF_MAP = {1: "Egyszerű", 2: "Könnyű", 3: "Közepes", 4: "Nehéz", 5: "Szinte lehetetlen"}
ACQ_DIFF_MAP_REV = {v: k for k, v in ACQ_DIFF_MAP.items()}
TYPE_MAP = {1: "szint", 2: "%"}
TYPE_MAP_REV = {v: k for k, v in TYPE_MAP.items()}

GRID_CFG = {
    "label": {"sticky": "w", "padx": 5, "pady": 2},
    "entry": {"sticky": "w", "padx": 5, "pady": 2},
    "optionmenu": {"sticky": "w", "padx": 5, "pady": 2},
    "text": {"sticky": "w", "padx": 5, "pady": 2},
    "kp_entry": {"sticky": "w", "padx": 25, "pady": 2},
}

class SkillEditor():
    """
    Main skill editor window.
    
    Provides a complete interface for creating and editing skills including:
    - Basic skill information (name, category, type)
    - KP costs for different levels or percentages
    - Prerequisites for each skill level
    - Skill descriptions with Markdown support
    - Parametric skill support
    
    Attributes:
        win (tk.Toplevel): Main editor window
        skill_manager (SkillManager): Manager for skill data
        all_skills (list): List of all skills from database
    """
    def __init__(self):

        self.win, created = WindowSingleton.get('skills_editor', lambda: tk.Toplevel())
        if not created:
            return
        self.skill_manager = SkillManager()
        # Biztonság: ha description_file None, legyen üres string
        self.all_skills = self.skill_manager.load()
        for s in self.all_skills:
            if s.get("description_file") is None:
                s["description_file"] = ""
        self.SKILL_NAMES = [s["name"] for s in self.all_skills]
        self.win.title("Képzettség szerkesztő")
        self.win.geometry("800x600")
        # --- Scrollable frame setup ---
        self.canvas = tk.Canvas(self.win, borderwidth=0, background="#f0f0f0", width=1420, height=880)
        self.scroll_frame = tk.Frame(self.canvas, background="#f0f0f0")
        self.vsb = tk.Scrollbar(self.win, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.create_window((0,0), window=self.scroll_frame, anchor="nw")
        self.scroll_frame.bind("<Configure>", lambda event: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        # --- End scrollable frame setup ---
        self.prereq_manager = PrerequisiteManager(self.scroll_frame, self.SKILL_NAMES, self.all_skills)
        self.create_widgets()
        self.win.mainloop()


    # Egységes hibakezelő metódusok
    def show_error(self, message, title="Hiba"):
        messagebox.showerror(title, message)

    def show_info(self, message, title="Info"):
        messagebox.showinfo(title, message)

    def show_warning(self, message, title="Figyelem"):
        messagebox.showwarning(title, message)

    def ask_yes_no(self, message, title="Megerősítés"):
        return messagebox.askyesno(title, message)

    def create_widgets(self):
        self._init_vars()
        self._create_header()
        self._create_category_selectors()
        # Leírás szekció eltávolítva, a leírás szerkesztő gombot helyezd át az akciógombokhoz, ha szükséges
        self._create_acquisition_section()
        self._create_type_section()
        self._create_level_sections()
        self._create_action_buttons()

    def _init_vars(self):
        if not hasattr(self, "id_var"):
            self.id_var = tk.StringVar()
        if not hasattr(self, "name_var"):
            self.name_var = tk.StringVar()
        if not hasattr(self, "param_var"):
            self.param_var = tk.StringVar()
        if not hasattr(self, "main_cat_var"):
            self.main_cat_var = tk.StringVar()
        if not hasattr(self, "sub_cat_var"):
            self.sub_cat_var = tk.StringVar()
        if not hasattr(self, "acq_method_var"):
            self.acq_method_var = tk.StringVar(value=ACQ_METHOD_MAP[1])
        if not hasattr(self, "acq_diff_var"):
            self.acq_diff_var = tk.StringVar(value=ACQ_DIFF_MAP[3])
        if not hasattr(self, "type_var"):
            self.type_var = tk.StringVar(value=TYPE_MAP[1])
        if not hasattr(self, "kp_per_3_var"):
            self.kp_per_3_var = tk.StringVar()
        if not hasattr(self, "general_desc"):
            self.general_desc = ""
        if not hasattr(self, "level_desc_texts") or not self.level_desc_texts:
            self.level_desc_texts = ["" for _ in range(6)]
        if not hasattr(self, "kp_cost_vars") or not self.kp_cost_vars:
            self.kp_cost_vars = [tk.StringVar() for _ in range(6)]
        if not hasattr(self, "kp_cost_labels") or not self.kp_cost_labels:
            self.kp_cost_labels = []
        if not hasattr(self, "kp_cost_entries") or not self.kp_cost_entries:
            self.kp_cost_entries = []

    def _create_header(self):
        row = 0
        # Név
        tk.Label(self.scroll_frame, text="Név:").grid(row=row, column=0, **GRID_CFG["label"])
        tk.Entry(self.scroll_frame, textvariable=self.name_var, width=30).grid(row=row, column=1, columnspan=4, **GRID_CFG["entry"])
        row += 1
        # Azonosító
        tk.Label(self.scroll_frame, text="Azonosító:").grid(row=row, column=0, **GRID_CFG["label"])
        tk.Entry(self.scroll_frame, textvariable=self.id_var, width=30).grid(row=row, column=1, columnspan=4, **GRID_CFG["entry"])
        row += 1
        # Paraméter
        tk.Label(self.scroll_frame, text="Paraméter:").grid(row=row, column=0, **GRID_CFG["label"])
        tk.Entry(self.scroll_frame, textvariable=self.param_var, width=30).grid(row=row, column=1, columnspan=4, **GRID_CFG["entry"])
        tk.Label(self.scroll_frame, text="Rövid kardok, Elf nyelv, Dobótőr stb...").grid(row=row, column=2, **GRID_CFG["label"])
    def _create_category_selectors(self):
        row = 3
        tk.Label(self.scroll_frame, text="Főkategória:").grid(row=row, column=0, **GRID_CFG["label"])
        main_cat_menu = tk.OptionMenu(self.scroll_frame, self.main_cat_var, *CATEGORIES.keys())
        main_cat_menu.grid(row=row, column=1, **GRID_CFG["optionmenu"])
        self.main_cat_menu = main_cat_menu
        self.main_cat_var.set(list(CATEGORIES.keys())[0])
        row += 1
        tk.Label(self.scroll_frame, text="Alkategória:").grid(row=row, column=0, **GRID_CFG["label"])
        self.sub_cat_menu = tk.OptionMenu(self.scroll_frame, self.sub_cat_var, *CATEGORIES[self.main_cat_var.get()])
        self.sub_cat_menu.grid(row=row, column=1, **GRID_CFG["optionmenu"])
        self.sub_cat_var.set(CATEGORIES[self.main_cat_var.get()][0])
        self.main_cat_var.trace_add("write", self._on_main_category_change)
        self.main_cat_var.trace_add("write", self.update_subcategories)

    def _on_main_category_change(self, *args):
        selected_main = self.main_cat_var.get()
        is_placeholder = selected_main == "Helyfoglaló képzettségek"
        # Elsajátítás módja
        for child in self.scroll_frame.winfo_children():
            if isinstance(child, tk.OptionMenu) and child.cget('textvariable') == str(self.acq_method_var):
                child.configure(state=tk.DISABLED if is_placeholder else tk.NORMAL)
            if isinstance(child, tk.OptionMenu) and child.cget('textvariable') == str(self.acq_diff_var):
                child.configure(state=tk.DISABLED if is_placeholder else tk.NORMAL)
            if isinstance(child, tk.OptionMenu) and child.cget('textvariable') == str(self.type_var):
                child.configure(state=tk.DISABLED if is_placeholder else tk.NORMAL)
        # KP/3% mező
        if hasattr(self, "kp_per_3_label") and hasattr(self, "kp_per_3_entry"):
            state = tk.DISABLED if is_placeholder else tk.NORMAL
            self.kp_per_3_label.configure(state=state)
            self.kp_per_3_entry.configure(state=state)
        # Szintenkénti KP mezők
        if hasattr(self, "kp_cost_entries"):
            for entry in self.kp_cost_entries:
                entry.configure(state=tk.DISABLED if is_placeholder else tk.NORMAL)
        if hasattr(self, "kp_cost_labels"):
            for label in self.kp_cost_labels:
                label.configure(state=tk.DISABLED if is_placeholder else tk.NORMAL)
        self._update_editor_buttons_state()

    def _create_acquisition_section(self):
        row = 5
        tk.Label(self.scroll_frame, text="Elsajátítás módja:").grid(row=row, column=0, **GRID_CFG["label"])
        tk.OptionMenu(self.scroll_frame, self.acq_method_var, *ACQ_METHOD_MAP.values()).grid(row=row, column=1, **GRID_CFG["optionmenu"])
        row += 1
        tk.Label(self.scroll_frame, text="Elsajátítás nehézsége:").grid(row=row, column=0, **GRID_CFG["label"])
        tk.OptionMenu(
            self.scroll_frame, self.acq_diff_var,
            *ACQ_DIFF_MAP.values()
        ).grid(row=row, column=1, **GRID_CFG["optionmenu"])

    def _create_type_section(self):
        row = 7
        tk.Label(self.scroll_frame, text="Típus:").grid(row=row, column=0, **GRID_CFG["label"])
        tk.OptionMenu(self.scroll_frame, self.type_var, *TYPE_MAP.values()).grid(row=row, column=1, **GRID_CFG["optionmenu"])
        self.row_kp_percent = row + 1
        self.kp_per_3_label = tk.Label(self.scroll_frame, text="KP/3%:")
        self.kp_per_3_entry = tk.Entry(self.scroll_frame, textvariable=self.kp_per_3_var)
        if self.type_var.get() == TYPE_MAP[2]:
            self.kp_per_3_label.grid(row=self.row_kp_percent, column=0, **GRID_CFG["label"])
            self.kp_per_3_entry.grid(row=self.row_kp_percent, column=1, **GRID_CFG["entry"])
        self.type_var.trace_add("write", lambda *args: self.update_kp_fields(self.row_kp_percent))
        self.update_kp_fields(self.row_kp_percent)

    def _create_level_sections(self):
        row = self.row_kp_percent
        self.level_frames = []
        for i in range(1, 7):
            row += 1
            level_frame = tk.Frame(self.scroll_frame)
            level_frame.grid(row=row, column=0, columnspan=5, sticky="w", pady=2)
            self.level_frames.append(level_frame)
            kp_label = tk.Label(level_frame, text=f"{i}. szint KP:")
            kp_label.grid(row=0, column=0, sticky="nw", padx=5)
            self.kp_cost_labels.append(kp_label)
            kp_entry = tk.Entry(level_frame, textvariable=self.kp_cost_vars[i-1], width=8)
            kp_entry.grid(row=0, column=1, sticky="nw", padx=5)
            self.kp_cost_entries.append(kp_entry)
            prereq_summary = tk.Label(level_frame, text="", anchor="nw", justify="left", font=("Consolas", 10), fg="#444")
            prereq_summary.grid(row=0, column=2, sticky="nw", padx=5)
            if not hasattr(self, "prereq_summary_labels"):
                self.prereq_summary_labels = []
            self.prereq_summary_labels.append(prereq_summary)
        # 6. szint frame tiltása/engedélyezése tickbox alapján (ha már létezik a var)
        if hasattr(self, "level_six_available_var") and len(self.level_frames) >= 6:
            state = tk.NORMAL if self.level_six_available_var.get() else tk.DISABLED
            for widget in self.level_frames[5].winfo_children():
                try:
                    widget.configure(state=state)
                except Exception:
                    pass

    def _create_action_buttons(self):
        row = self.row_kp_percent + 7
        # Tickbox a gombok fölé
        # 6. szint tickbox és logika eltávolítva
        row += 1
        button_frame = tk.Frame(self.scroll_frame)
        button_frame.grid(row=row, column=0, columnspan=5, pady=20)
        load_btn = tk.Button(button_frame, text="Szerkesztés", width=18, command=self.open_skill_loader)
        load_btn.pack(side=tk.LEFT, padx=10)
        self.prereq_btn = tk.Button(button_frame, text="Előfeltételek szerkesztése", width=22, command=self.open_prerequisite_editor)
        self.prereq_btn.pack(side=tk.LEFT, padx=10)
        self.desc_btn = tk.Button(button_frame, text="Leírások szerkesztése", width=22, command=self.open_all_description_editor)
        self.desc_btn.pack(side=tk.LEFT, padx=10)
        save_btn = tk.Button(button_frame, text="Mentés", width=18, command=self.save_skill)
        save_btn.pack(side=tk.LEFT, padx=10)
        self._update_editor_buttons_state()

    def _update_editor_buttons_state(self):
        selected_main = self.main_cat_var.get() if hasattr(self, "main_cat_var") else ""
        is_placeholder = selected_main == "Helyfoglaló képzettségek"
        if hasattr(self, "prereq_btn"):
            self.prereq_btn.configure(state=tk.DISABLED if is_placeholder else tk.NORMAL)
        if hasattr(self, "desc_btn"):
            self.desc_btn.configure(state=tk.DISABLED if is_placeholder else tk.NORMAL)

    def open_all_description_editor(self):
        self.open_description_editor()

    def update_subcategories(self, *args):
        menu = self.sub_cat_menu["menu"]
        menu.delete(0, 'end')
        selected_main = self.main_cat_var.get()
        for sub in CATEGORIES.get(selected_main, []):
            menu.add_command(label=sub, command=tk._setit(self.sub_cat_var, sub))
        if CATEGORIES.get(selected_main):
            self.sub_cat_var.set(CATEGORIES[selected_main][0])
        else:
            self.sub_cat_var.set("")



    def update_prereq_summary(self):
        """
        Frissíti a főablakban lévő tömör előfeltétel listákat minden szinthez.
        """
        for i in range(6):
            stat_list = []
            skill_list = []
            for prereq in self.prereq_manager.prereq_vars[i]:
                if prereq["type"] == "stat":
                    stat = prereq["name_var"].get()
                    value = prereq["value_var"].get()
                    if stat and value:
                        stat_list.append(f"{stat} {value}+")
                elif prereq["type"] == "skill":
                    skillname = prereq["name_var"].get()
                    level = prereq["level_var"].get() if "level_var" in prereq else ""
                    param = prereq.get("param_var", tk.StringVar()).get() if "param_var" in prereq else ""
                    # Ha a skillname placeholder, nincs szint, csak név és paraméter
                    m = re.match(r"(.+?)(?: \((.+?)\))?$", skillname)
                    base_name = m.group(1) if m else skillname
                    param_in_name = m.group(2) if m and m.group(2) else ""
                    if param:
                        display_text = f"{base_name} ({param})"
                    elif param_in_name:
                        display_text = f"{base_name} ({param_in_name})"
                    else:
                        display_text = base_name
                    if skillname:
                        # Mindig jelenjen meg a szint, ha van (placeholdernél is)
                        if level:
                            skill_list.append(f"{display_text} {level}. szint")
                        else:
                            skill_list.append(display_text)
            summary = ""
            if stat_list:
                summary += "Tulajdonság: " + ", ".join(stat_list) + "\n"
            if skill_list:
                summary += "Képzettség: " + ", ".join(skill_list)
            self.prereq_summary_labels[i].config(text=summary.strip())

    def validate_skill_levels(self, level_kp_dict):
        if not level_kp_dict:
            return False, "Nem adtál meg egy szintet sem."
        valid_levels = sorted(int(lvl) for lvl in level_kp_dict.keys())
        expected_levels = list(range(1, max(valid_levels) + 1))
        if valid_levels != expected_levels:
            return False, f"Hibás szintfelépítés: hiányzó szintek észlelve: {valid_levels}"
        return True, None

 
    def open_prerequisite_editor(self):
        SkillPrerequisiteEditorDialog(self)


    def save_and_close(self):
        # Itt kell visszaírni az adatokat az editor.prereq_manager-be
        self.win.destroy()

    def open_level_description_editor(self, idx):
        """
        Megnyit egy új ablakot a szintenkénti leírás szerkesztéséhez (Markdown támogatott).
        idx: 0-alapú index a szinthez
        """
        editor_win = tk.Toplevel(self.win)
        editor_win.title(f"{idx+1}. szint leírás szerkesztése")
        editor_win.geometry("800x600")
        tk.Label(editor_win, text="Használhatsz Markdown szintaxist: **félkövér**, *dőlt*, - lista, stb.").pack(pady=5)
        desc_text = tk.Text(editor_win, wrap=tk.WORD, font=("Consolas", 12))
        desc_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        # Betöltjük a jelenlegi leírást (stringből)
        current_desc = self.level_desc_texts[idx] if idx < len(self.level_desc_texts) else ""
        desc_text.insert(tk.END, current_desc)
        def save_and_close():
            self.level_desc_texts[idx] = desc_text.get("1.0", tk.END).strip()
            editor_win.destroy()
        tk.Button(editor_win, text="Mentés", command=save_and_close).pack(pady=10)

    def open_description_editor(self):
        editor_win = tk.Toplevel(self.win)
        editor_win.title("Leírás szerkesztése")
        editor_win.geometry("800x600")
        tk.Label(editor_win, text="Használhatsz Markdown szintaxist: **félkövér**, *dőlt*, - lista, stb.").pack(pady=5)
        desc_text = tk.Text(editor_win, wrap=tk.WORD, font=("Consolas", 12))
        desc_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        desc_text.insert(tk.END, self.general_desc)
        def save_and_close():
            self.general_desc = desc_text.get("1.0", tk.END).strip()
            editor_win.destroy()
        tk.Button(editor_win, text="Mentés", command=save_and_close).pack(pady=10)

    def update_kp_fields(self, row_kp_percent):
        if self.type_var.get() == TYPE_MAP[2]:
            self.kp_per_3_label.grid(row=row_kp_percent, column=0, sticky="w", padx=5, pady=2)
            self.kp_per_3_entry.grid(row=row_kp_percent, column=1, sticky="w", padx=5, pady=2)
            # Ne állítsd újra a kp_per_3_var értékét, csak ha skillt töltünk be!
            for lbl, entry in zip(self.kp_cost_labels, self.kp_cost_entries):
                lbl.grid_remove()
                entry.grid_remove()
        else:
            self.kp_per_3_label.grid_remove()
            self.kp_per_3_entry.grid_remove()
            for lbl, entry in zip(self.kp_cost_labels, self.kp_cost_entries):
                lbl.grid()
                entry.grid()

    def save_skill(self):
        # UI adatok összegyűjtése
        ui_data = {
            "id": self.id_var.get().strip(),
            "name": self.name_var.get(),
            "main_category": self.main_cat_var.get(),
            "sub_category": self.sub_cat_var.get(),
            "description": self.general_desc,
            "acquisition_method": ACQ_METHOD_MAP_REV.get(self.acq_method_var.get(), 1),
            "acquisition_difficulty": ACQ_DIFF_MAP_REV.get(self.acq_diff_var.get(), 3),
            "skill_type": TYPE_MAP_REV.get(self.type_var.get(), 1),
            "kp_per_3_percent": self.kp_per_3_var.get() if self.type_var.get() == TYPE_MAP[2] else None,
            "kp_costs": {},
            "level_descriptions": {},
            "is_parametric": bool(self.param_var.get().strip()),
            "parameter": self.param_var.get().strip(),
        # "level_six_available" mező eltávolítva
        }
        # Szintleírások
        for i, desc_text in enumerate(self.level_desc_texts):
            desc = desc_text.strip()
            if desc:
                ui_data["level_descriptions"][str(i+1)] = desc
        # KP költségek
        valid_levels = []
        if self.type_var.get() != TYPE_MAP[2]:
            for i, kp_var in enumerate(self.kp_cost_vars):
                kp = kp_var.get().strip()
                if kp:
                    try:
                        if int(kp) > 0:
                            ui_data["kp_costs"][str(i+1)] = kp
                            valid_levels.append(i+1)
                    except ValueError:
                        continue
        # Validáció: csak szint-alapú skilleknél, de ne ellenőrizzük helyfoglaló képzettségnél
        if ui_data.get("skill_type", 1) == 1 and ui_data.get("main_category", "") != "Helyfoglaló képzettségek":
            is_valid, err_msg = self.validate_skill_levels(ui_data["kp_costs"])
            if not is_valid:
                self.show_error(err_msg)
                return
        # Előfeltételek
        ui_data["prerequisites"] = self.skill_manager.prereq_to_string(self.prereq_manager.prereq_vars)

        # Skill szerializálása
        skill = self.skill_manager.serialize_skill(ui_data)
        if not self.skill_manager.validate(skill):
            self.show_error("Hiányzó vagy hibás mező a képzettségben!")
            return
        # Csak az aktuális skillt mentsük, ne az összeset!
        valid_levels_dict = None
        if skill.get("skill_type", 1) == 1:
            valid_levels_dict = {skill.get("id"): valid_levels}
        self.skill_manager.save([skill], valid_levels_dict=valid_levels_dict)
        self.show_info("Képzettség mentve!", "Siker")

    def open_skill_loader(self):
        SkillLoaderDialog(self)

    def load_skill_to_ui(self, skill):
        """
        Betölt egy skill dict-et az editor UI-ba, a megfelelő szöveges értékekkel.
        """
        self.id_var.set(skill.get("id", ""))
        self.name_var.set(skill.get("name", ""))
        self.param_var.set(skill.get("parameter", ""))
        self.main_cat_var.set(skill.get("main_category", list(CATEGORIES.keys())[0]))
        self.sub_cat_var.set(skill.get("sub_category", ""))
        # Map integer to string for enums and recreate OptionMenus
        acq_method_val = skill.get("acquisition_method", 1)
        self.acq_method_var.set(ACQ_METHOD_MAP.get(acq_method_val, "Gyakorlás"))
        self._recreate_optionmenu("acq_method_var", self.acq_method_var, list(ACQ_METHOD_MAP.values()))

        acq_diff_val = skill.get("acquisition_difficulty", 3)
        self.acq_diff_var.set(ACQ_DIFF_MAP.get(acq_diff_val, "Közepes"))
        self._recreate_optionmenu("acq_diff_var", self.acq_diff_var, list(ACQ_DIFF_MAP.values()))

        type_val = skill.get("skill_type", 1)
        self.type_var.set(TYPE_MAP.get(type_val, "szint"))
        self._recreate_optionmenu("type_var", self.type_var, list(TYPE_MAP.values()))
        self.kp_per_3_var.set(skill.get("kp_per_3_percent", ""))
        self.general_desc = skill.get("description", "")
        # Biztonság: ha description_file None, legyen üres string
        if skill.get("description_file") is None:
            skill["description_file"] = ""
        # 6. szint elérhetőség logika eltávolítva
        # Szintleírások
        self.level_desc_texts = [skill.get("level_descriptions", {}).get(str(i+1), "") for i in range(6)]
        # KP költségek
        for i in range(6):
            kp_val = skill.get("kp_costs", {}).get(str(i+1), "")
            self.kp_cost_vars[i].set(kp_val)
        # Előfeltételek
        if hasattr(self, "prereq_manager"):
            self.prereq_manager.load_from_string(skill.get("prerequisites", ""))
        self.update_kp_fields(self.row_kp_percent)
        self.update_prereq_summary()
        self._update_editor_buttons_state()

    def _recreate_optionmenu(self, var_name, var, values):
        """
        Teljesen újraépíti az OptionMenu-t, hogy a helyes szöveg jelenjen meg.
        """
        # Find and destroy the old OptionMenu
        for child in self.scroll_frame.winfo_children():
            if isinstance(child, tk.OptionMenu) and child.cget('textvariable') == str(var):
                child.destroy()
        # Find the row for this OptionMenu
        if var_name == "acq_method_var":
            row = 5
        elif var_name == "acq_diff_var":
            row = 6
        elif var_name == "type_var":
            row = 7
        else:
            return
        # Recreate OptionMenu
        new_menu = tk.OptionMenu(self.scroll_frame, var, *values)
        new_menu.grid(row=row, column=1, **GRID_CFG["optionmenu"])

    # _refresh_optionmenu removed, replaced by _recreate_optionmenu

# --- Futtatható fő rész ---
if __name__ == "__main__":
    editor = SkillEditor()
