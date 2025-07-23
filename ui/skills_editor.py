import tkinter as tk
from tkinter import messagebox
import os
from utils.skill_manager import SkillManager
import re
from ui.prerequisite_editor import PrerequisiteEditorDialog
from ui.skill_dialogs.skill_loader_dialog import SkillLoaderDialog
from utils.prerequisite_manager import PrerequisiteManager

# Ensure SkillManager uses the correct path to skills.json
SKILLS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "skills", "skills.json")

CATEGORIES = {
    "Harci képzettségek": ["Közkeletű", "Szakértő", "Titkos"],
    "Szociális képzettségek": ["Általános", "Nemesi", "Polgári", "Póri", "Művész"],
    "Alvilági képzettségek": ["Álcázó", "Kommunikációs", "Pénzszerző", "Harci", "Behatoló", "Ellenálló"],
    "Túlélő képzettségek": ["Vadonjáró", "Atlétikai"],
    "Elméleti képzettségek": ["Közkeletű", "Szakértő", "Titkos elméleti", "Titkos szervezeti"]
}

GRID_CFG = {
    "label": {"sticky": "w", "padx": 5, "pady": 2},
    "entry": {"sticky": "w", "padx": 5, "pady": 2},
    "optionmenu": {"sticky": "w", "padx": 5, "pady": 2},
    "text": {"sticky": "w", "padx": 5, "pady": 2},
    "kp_entry": {"sticky": "w", "padx": 25, "pady": 2},
}

class SkillEditor():
    def __init__(self):
        self.skill_manager = SkillManager()
        self.all_skills = self.skill_manager.load()
        self.SKILL_NAMES = [s["name"] for s in self.all_skills]
        self.win = tk.Tk()
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
        self._create_description_section()
        self._create_acquisition_section()
        self._create_type_section()
        self._create_level_sections()
        self._create_action_buttons()

    def _init_vars(self):
        if not hasattr(self, "name_var"):
            self.name_var = tk.StringVar()
        if not hasattr(self, "param_var"):
            self.param_var = tk.StringVar()
        if not hasattr(self, "main_cat_var"):
            self.main_cat_var = tk.StringVar()
        if not hasattr(self, "sub_cat_var"):
            self.sub_cat_var = tk.StringVar()
        if not hasattr(self, "acq_method_var"):
            self.acq_method_var = tk.StringVar(value="Gyakorlás")
        if not hasattr(self, "acq_diff_var"):
            self.acq_diff_var = tk.StringVar(value="3 - Közepes")
        if not hasattr(self, "type_var"):
            self.type_var = tk.StringVar(value="szint")
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
        tk.Label(self.scroll_frame, text="Név:").grid(row=row, column=0, **GRID_CFG["label"])
        tk.Entry(self.scroll_frame, textvariable=self.name_var).grid(row=row, column=1, **GRID_CFG["entry"])
        tk.Label(self.scroll_frame, text="Paraméter (pl. Rövid kardok, Elf nyelv, stb.):").grid(row=row, column=2, **GRID_CFG["label"])
        tk.Entry(self.scroll_frame, textvariable=self.param_var, width=20).grid(row=row, column=3, **GRID_CFG["entry"])

    def _create_category_selectors(self):
        row = 1
        tk.Label(self.scroll_frame, text="Főkategória:").grid(row=row, column=0, **GRID_CFG["label"])
        tk.OptionMenu(self.scroll_frame, self.main_cat_var, *CATEGORIES.keys()).grid(row=row, column=1, **GRID_CFG["optionmenu"])
        self.main_cat_var.set(list(CATEGORIES.keys())[0])
        row += 1
        tk.Label(self.scroll_frame, text="Alkategória:").grid(row=row, column=0, **GRID_CFG["label"])
        self.sub_cat_menu = tk.OptionMenu(self.scroll_frame, self.sub_cat_var, *CATEGORIES[self.main_cat_var.get()])
        self.sub_cat_menu.grid(row=row, column=1, **GRID_CFG["optionmenu"])
        self.sub_cat_var.set(CATEGORIES[self.main_cat_var.get()][0])
        self.main_cat_var.trace_add("write", self.update_subcategories)

    def _create_description_section(self):
        row = 3
        tk.Label(self.scroll_frame, text="Általános leírás:").grid(row=row, column=0, **GRID_CFG["label"])
        edit_desc_btn = tk.Button(self.scroll_frame, text="Leírás szerkesztése", command=self.open_description_editor)
        edit_desc_btn.grid(row=row, column=1, padx=5, pady=2, sticky="w")

    def _create_acquisition_section(self):
        row = 4
        tk.Label(self.scroll_frame, text="Elsajátítás módja:").grid(row=row, column=0, **GRID_CFG["label"])
        tk.OptionMenu(self.scroll_frame, self.acq_method_var, "Gyakorlás", "Tapasztalás", "Tanulás").grid(row=row, column=1, **GRID_CFG["optionmenu"])
        row += 1
        tk.Label(self.scroll_frame, text="Elsajátítás nehézsége:").grid(row=row, column=0, **GRID_CFG["label"])
        tk.OptionMenu(
            self.scroll_frame, self.acq_diff_var,
            "1 - Egyszerű", "2 - Könnyű", "3 - Közepes", "4 - Nehéz", "5 - Szinte lehetetlen"
        ).grid(row=row, column=1, **GRID_CFG["optionmenu"])

    def _create_type_section(self):
        row = 6
        tk.Label(self.scroll_frame, text="Típus:").grid(row=row, column=0, **GRID_CFG["label"])
        tk.OptionMenu(self.scroll_frame, self.type_var, "%", "szint").grid(row=row, column=1, **GRID_CFG["optionmenu"])
        self.row_kp_percent = row + 1
        self.kp_per_3_label = tk.Label(self.scroll_frame, text="KP/3%:")
        self.kp_per_3_entry = tk.Entry(self.scroll_frame, textvariable=self.kp_per_3_var)
        if self.type_var.get() == "%":
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
            tk.Label(level_frame, text=f"{i}. szint leírás:").grid(row=0, column=0, sticky="nw", padx=5)
            edit_btn = tk.Button(level_frame, text="Leírás szerkesztése", command=lambda idx=i-1: self.open_level_description_editor(idx))
            edit_btn.grid(row=0, column=1, sticky="ne", padx=(5, 0))
            kp_label = tk.Label(level_frame, text=f"{i}. szint KP:")
            kp_label.grid(row=0, column=2, sticky="nw", padx=5)
            self.kp_cost_labels.append(kp_label)
            kp_entry = tk.Entry(level_frame, textvariable=self.kp_cost_vars[i-1], width=8)
            kp_entry.grid(row=0, column=3, sticky="nw", padx=5)
            self.kp_cost_entries.append(kp_entry)
            prereq_summary = tk.Label(level_frame, text="", anchor="nw", justify="left", font=("Consolas", 10), fg="#444")
            prereq_summary.grid(row=0, column=4, sticky="nw", padx=5)
            if not hasattr(self, "prereq_summary_labels"):
                self.prereq_summary_labels = []
            self.prereq_summary_labels.append(prereq_summary)

    def _create_action_buttons(self):
        row = self.row_kp_percent + 7
        button_frame = tk.Frame(self.scroll_frame)
        button_frame.grid(row=row, column=0, columnspan=5, pady=20)
        load_btn = tk.Button(button_frame, text="Szerkesztés", width=18, command=self.open_skill_loader)
        load_btn.pack(side=tk.LEFT, padx=10)
        prereq_btn = tk.Button(button_frame, text="Előfeltételek szerkesztése", width=22, command=self.open_prerequisite_editor)
        prereq_btn.pack(side=tk.LEFT, padx=10)
        save_btn = tk.Button(button_frame, text="Mentés", width=18, command=self.save_skill)
        save_btn.pack(side=tk.LEFT, padx=10)
        # Delete button removed

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
                    level = prereq["level_var"].get()
                    param = prereq.get("param_var", tk.StringVar()).get()
                    m = re.match(r"(.+?)(?: \((.+?)\))?$", skillname)
                    base_name = m.group(1) if m else skillname
                    param_in_name = m.group(2) if m and m.group(2) else ""
                    if param:
                        display_text = f"{base_name} ({param})"
                    elif param_in_name:
                        display_text = f"{base_name} ({param_in_name})"
                    else:
                        display_text = base_name
                    if skillname and level:
                        skill_list.append(f"{display_text} {level}. szint")
            summary = ""
            if stat_list:
                summary += "Tulajdonság: " + ", ".join(stat_list) + "\n"
            if skill_list:
                summary += "Képzettség: " + ", ".join(skill_list)
            self.prereq_summary_labels[i].config(text=summary.strip())

 
    def open_prerequisite_editor(self):
        PrerequisiteEditorDialog(self)


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
        if self.type_var.get() == "%":
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
            "name": self.name_var.get(),
            "main_category": self.main_cat_var.get(),
            "sub_category": self.sub_cat_var.get(),
            "description": self.general_desc,
            "acquisition_method": self.acq_method_var.get(),
            "acquisition_difficulty": self.acq_diff_var.get(),
            "skill_type": self.type_var.get(),
            "kp_per_3_percent": self.kp_per_3_var.get() if self.type_var.get() == "%" else None,
            "kp_costs": {},
            "level_descriptions": {},
            "is_parametric": bool(self.param_var.get().strip()),
            "parameter": self.param_var.get().strip()
        }
        # Szintleírások
        for i, desc_text in enumerate(self.level_desc_texts):
            desc = desc_text.strip()
            if desc:
                ui_data["level_descriptions"][str(i+1)] = desc
        # KP költségek
        if self.type_var.get() != "%":
            for i, kp_var in enumerate(self.kp_cost_vars):
                kp = kp_var.get().strip()
                if kp:
                    ui_data["kp_costs"][str(i+1)] = kp
        # Előfeltételek
        ui_data["prerequisites"] = self.skill_manager.prereq_to_string(self.prereq_manager.prereq_vars)

        # Skill szerializálása
        skill = self.skill_manager.serialize_skill(ui_data)
        if not self.skill_manager.validate(skill):
            self.show_error("Hiányzó vagy hibás mező a képzettségben!")
            return
        try:
            skills = self.skill_manager.load()
        except Exception:
            skills = []
        # Egységes név+paraméter összehasonlítás
        def normalize(name, param):
            name = name.strip().lower()
            param = param.strip().lower() if param else ""
            m = re.match(r"(.+?)(?: \((.+?)\))?$", name)
            base_name = m.group(1) if m else name
            return base_name, param
        skill_name, skill_param = normalize(skill.get("name", ""), skill.get("parameter", ""))
        found_idx = None
        for idx, s in enumerate(skills):
            s_name, s_param = normalize(s.get("name", ""), s.get("parameter", ""))
            if skill_name == s_name and skill_param == s_param:
                found_idx = idx
                break
        if found_idx is not None:
            answer = self.ask_yes_no("Az adott képzettség már létezik. Felülírja?", "Felülírás")
            if not answer:
                return
            del skills[found_idx]
        skills.append(skill)
        self.skill_manager.save(skills)
        self.show_info("Képzettség mentve!", "Siker")
        #self.win.destroy()

    def open_skill_loader(self):
        SkillLoaderDialog(self)

# --- Futtatható fő rész ---
if __name__ == "__main__":
    editor = SkillEditor()
