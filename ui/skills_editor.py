import tkinter as tk
from tkinter import messagebox
import os

# Ensure SkillManager uses the correct path to skills.json
SKILLS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "skills", "skills.json")
from utils.skill_manager import SkillManager
from tkinter import ttk
import re

CATEGORIES = {
    "Harci képzettségek": ["Közkeletű", "Szakértő", "Titkos"],
    "Szociális képzettségek": ["Általános", "Nemesi", "Polgári", "Póri", "Művész"],
    "Alvilági képzettségek": ["Álcázó", "Kommunikációs", "Pénzszerző", "Harci", "Behatoló", "Ellenálló"],
    "Túlélő képzettségek": ["Vadonjáró", "Atlétikai"],
    "Elméleti képzettségek": ["Közkeletű", "Szakértő", "Titkos elméleti", "Titkos szervezeti"]
}

STAT_NAMES = [
    "Erő", "Állóképesség", "Gyorsaság", "Ügyesség", "Karizma",
    "Egészség", "Intelligencia", "Akaraterő", "Asztrál", "Érzékelés"
]

class PrerequisiteManager:
    def __init__(self, parent, skill_names, all_skills):
        self.parent = parent
        self.skill_names = skill_names
        self.all_skills = all_skills
        self.stat_vars = [[] for _ in range(6)]
        self.skill_vars = [[] for _ in range(6)]
        self.frames = []
        self.create_frames()

    def create_stat_row_widget(self, frame, stat_var, value_var, remove_callback):
        row = len([w for w in frame.grid_slaves() if isinstance(w, tk.OptionMenu) or isinstance(w, tk.Entry)]) // 2 + 1
        stat_menu = tk.OptionMenu(frame, stat_var, *STAT_NAMES)
        stat_menu.grid(row=row, column=0, padx=(20, 0), sticky="w")
        entry = tk.Entry(frame, textvariable=value_var, width=5)
        entry.grid(row=row, column=1, padx=10, sticky="w")
        btn = tk.Button(frame, text="Törlés", command=remove_callback)
        btn.grid(row=row, column=1, padx=50, sticky="w")
        return stat_menu, entry, btn

    def create_skill_row_widget(self, frame, skill_var, level_var, remove_callback):
        row = len([w for w in frame.grid_slaves() if isinstance(w, ttk.Combobox) or isinstance(w, tk.Entry)]) // 2 + 1
        skill_combo = ttk.Combobox(frame, textvariable=skill_var, values=self.skill_names, state="readonly", width=30)
        skill_combo.grid(row=row, column=2, padx=(5, 0), sticky="w")
        entry = tk.Entry(frame, textvariable=level_var, width=5)
        entry.grid(row=row, column=3, padx=10, sticky="w")
        btn = tk.Button(frame, text="Törlés", command=remove_callback)
        btn.grid(row=row, column=3, padx=50, sticky="w")
        return skill_combo, entry, btn

    def create_frames(self):
        for i in range(1, 7):
            frame = tk.Frame(self.parent)
            frame.grid(row=7+i, column=4, columnspan=2, sticky="w", padx=40)
            tk.Label(frame, text=f"{i}. szint előfeltétel:").grid(row=0, column=0, sticky="w", padx=10)
            tk.Button(
                frame, text="Tulajdonság hozzáadása",
                command=lambda idx=i-1, fr=frame: self.add_stat_row(idx, fr)
            ).grid(row=0, column=1, padx=10)
            tk.Button(
                frame, text="Képzettség hozzáadása",
                command=lambda idx=i-1, fr=frame: self.add_skill_row(idx, fr)
            ).grid(row=0, column=2, padx=10)
            self.frames.append(frame)

    def add_stat_row(self, level_idx, frame):
        stat_var = tk.StringVar(value=STAT_NAMES[0])
        value_var = tk.StringVar()
        def remove():
            stat_menu.destroy()
            entry.destroy()
            btn.destroy()
            self.stat_vars[level_idx].remove((stat_var, value_var))
        stat_menu, entry, btn = self.create_stat_row_widget(frame, stat_var, value_var, remove)
        self.stat_vars[level_idx].append((stat_var, value_var))

    def add_skill_row(self, level_idx, frame):
        dialog = tk.Toplevel(frame)
        dialog.title("Képzettség keresése")
        dialog.geometry("400x250")
        search_var = tk.StringVar()
        tk.Label(dialog, text="Képzettség keresése:").pack()
        search_entry = tk.Entry(dialog, textvariable=search_var, width=40)
        search_entry.pack()
        filtered_skills = self.skill_names.copy()
        skill_var = tk.StringVar()
        skill_combo = ttk.Combobox(dialog, textvariable=skill_var, values=filtered_skills, state="readonly", width=35)
        skill_combo.pack(pady=5)
        param_label = tk.Label(dialog, text="Specializáció / típus (pl. Rövid kardok, Elf nyelv):")
        param_label.pack_forget()
        param_var = tk.StringVar()
        param_menu = None
        def show_param_field(*args):
            nonlocal param_menu
            skill_name = skill_var.get()
            skill_obj = next((s for s in self.all_skills if s["name"] == skill_name), None)
            if param_menu:
                param_menu.destroy()
                param_menu = None
            if skill_obj and skill_obj.get("is_parametric"):
                param_label.pack()
                params = set()
                for s in self.all_skills:
                    if s["name"] == skill_name and s.get("parameter"):
                        params.add(s["parameter"])
                params = sorted(params)
                if params:
                    param_var.set(params[0])
                    param_menu = tk.OptionMenu(dialog, param_var, *params)
                    param_menu.pack()
                else:
                    param_var.set("")
                    param_menu = tk.Entry(dialog, textvariable=param_var, width=30)
                    param_menu.pack()
            else:
                param_label.pack_forget()
                param_var.set("")
                if param_menu:
                    param_menu.destroy()
                    param_menu = None
        skill_var.trace_add("write", show_param_field)
        tk.Label(dialog, text="Szükséges szint:").pack()
        level_var = tk.StringVar()
        level_entry = tk.Entry(dialog, textvariable=level_var, width=5)
        level_entry.pack()
        def update_skill_list(*args):
            text = search_var.get().lower()
            filtered = [s for s in self.skill_names if text in s.lower()]
            skill_combo['values'] = filtered
            if filtered:
                skill_var.set(filtered[0])
            else:
                skill_var.set("")
        search_var.trace_add("write", update_skill_list)
        def add_skill():
            skill = skill_var.get()
            level = level_var.get()
            param = param_var.get().strip()
            if skill and level:
                def remove():
                    skill_combo_widget.destroy()
                    entry_widget.destroy()
                    btn_widget.destroy()
                    self.skill_vars[level_idx].remove((skill_var, level_var, param))
                skill_combo_widget, entry_widget, btn_widget = self.create_skill_row_widget(frame, skill_var, level_var, remove)
                self.skill_vars[level_idx].append((skill_var, level_var, param))
                dialog.destroy()
        tk.Button(dialog, text="Hozzáadás", command=add_skill).pack(pady=5)

    def clear_all(self):
        for idx in range(6):
            for stat_var, value_var in self.stat_vars[idx][:]:
                stat_var.set("")
                value_var.set("")
            self.stat_vars[idx].clear()
            for skill_var, level_var in self.skill_vars[idx][:]:
                skill_var.set("")
                level_var.set("")
            self.skill_vars[idx].clear()

    def load_prerequisites(self, prerequisites):
        self.clear_all()
        for idx in range(6):
            prereq = prerequisites.get(str(idx+1), {})
            frame = self.frames[idx]
            for stat_str in prereq.get("képesség", []):
                parts = stat_str.split()
                if len(parts) >= 2:
                    stat_var = tk.StringVar(value=parts[0])
                    value_var = tk.StringVar(value=parts[1].replace("+", ""))
                    def remove_stat(stat_menu=None, entry=None, btn=None):
                        stat_menu.destroy()
                        entry.destroy()
                        if btn:
                            btn.destroy()
                        self.stat_vars[idx].remove((stat_var, value_var))
                    stat_menu, entry, btn = self.create_stat_row_widget(frame, stat_var, value_var, lambda: remove_stat(stat_menu, entry, btn))
                    self.stat_vars[idx].append((stat_var, value_var))
            for skill_str in prereq.get("képzettség", []):
                m = re.match(r"(.+?)(?: \((.+?)\))? (\d+)\. szint", skill_str)
                if m:
                    skillname = m.group(1)
                    param = m.group(2) or ""
                    level = m.group(3)
                    skill_var = tk.StringVar(value=skillname)
                    level_var = tk.StringVar(value=level)
                    def remove_skill(skill_combo=None, entry=None, btn=None):
                        skill_combo.destroy()
                        entry.destroy()
                        if btn:
                            btn.destroy()
                        self.skill_vars[idx].remove((skill_var, level_var))
                    skill_combo, entry, btn = self.create_skill_row_widget(frame, skill_var, level_var, lambda: remove_skill(skill_combo, entry, btn))
                    self.skill_vars[idx].append((skill_var, level_var))

    def open_frames(self):
        for frame in self.frames:
            frame.grid()
        self.parent.update_idletasks()

    def close_frames(self):
        for frame in self.frames:
            frame.grid_remove()
        self.parent.update_idletasks()

class SkillEditor():
    def __init__(self):
        self.skill_manager = SkillManager()
        self.all_skills = self.skill_manager.load()
        self.SKILL_NAMES = [s["name"] for s in self.all_skills]
        self.win = tk.Tk()
        self.win.title("Képzettség szerkesztő")
        self.win.geometry("1440x900")
        self.prereq_manager = PrerequisiteManager(self.win, self.SKILL_NAMES, self.all_skills)
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
        self.name_var = tk.StringVar()
        self.param_var = tk.StringVar()
        self.main_cat_var = tk.StringVar()
        self.sub_cat_var = tk.StringVar()
        self.general_desc_text = tk.Text(self.win, height=3, width=30)
        self.acq_method_var = tk.StringVar(value="Gyakorlás")
        self.acq_diff_var = tk.StringVar(value="3 - Közepes")
        self.type_var = tk.StringVar(value="szint")
        self.kp_per_3_var = tk.StringVar()
        self.level_desc_texts = []
        self.kp_cost_vars = []
        self.kp_cost_labels = []
        self.kp_cost_entries = []

        # Grid sablon paraméterek
        grid_cfg = {
            "label": {"sticky": "w", "padx": 5, "pady": 2},
            "entry": {"sticky": "w", "padx": 5, "pady": 2},
            "optionmenu": {"sticky": "w", "padx": 5, "pady": 2},
            "text": {"sticky": "w", "padx": 5, "pady": 2},
            "kp_entry": {"sticky": "w", "padx": 25, "pady": 2},  # KP mezőhöz nagyobb bal padding
        }

        # Felső sorok
        row = 0
        tk.Label(self.win, text="Név:").grid(row=row, column=0, **grid_cfg["label"])
        tk.Entry(self.win, textvariable=self.name_var).grid(row=row, column=1, **grid_cfg["entry"])
        tk.Label(self.win, text="Paraméter (pl. Rövid kardok, Elf nyelv, stb.):").grid(row=row, column=2, **grid_cfg["label"])
        tk.Entry(self.win, textvariable=self.param_var, width=20).grid(row=row, column=3, **grid_cfg["entry"])
        row += 1
        tk.Label(self.win, text="Főkategória:").grid(row=row, column=0, **grid_cfg["label"])
        tk.OptionMenu(self.win, self.main_cat_var, *CATEGORIES.keys()).grid(row=row, column=1, **grid_cfg["optionmenu"])
        self.main_cat_var.set(list(CATEGORIES.keys())[0])
        row += 1
        tk.Label(self.win, text="Alkategória:").grid(row=row, column=0, **grid_cfg["label"])
        self.sub_cat_menu = tk.OptionMenu(self.win, self.sub_cat_var, *CATEGORIES[self.main_cat_var.get()])
        self.sub_cat_menu.grid(row=row, column=1, **grid_cfg["optionmenu"])
        self.sub_cat_var.set(CATEGORIES[self.main_cat_var.get()][0])
        self.main_cat_var.trace_add("write", self.update_subcategories)
        row += 1
        tk.Label(self.win, text="Általános leírás:").grid(row=row, column=0, **grid_cfg["label"])
        self.general_desc_text.grid(row=row, column=1, columnspan=3, **grid_cfg["text"])
        row += 1
        tk.Label(self.win, text="Elsajátítás módja:").grid(row=row, column=0, **grid_cfg["label"])
        tk.OptionMenu(self.win, self.acq_method_var, "Gyakorlás", "Tapasztalás", "Tanulás").grid(row=row, column=1, **grid_cfg["optionmenu"])
        row += 1
        tk.Label(self.win, text="Elsajátítás nehézsége:").grid(row=row, column=0, **grid_cfg["label"])
        tk.OptionMenu(
            self.win, self.acq_diff_var,
            "1 - Egyszerű", "2 - Könnyű", "3 - Közepes", "4 - Nehéz", "5 - Szinte lehetetlen"
        ).grid(row=row, column=1, **grid_cfg["optionmenu"])
        row += 1
        tk.Label(self.win, text="Típus:").grid(row=row, column=0, **grid_cfg["label"])
        tk.OptionMenu(self.win, self.type_var, "%", "szint").grid(row=row, column=1, **grid_cfg["optionmenu"])
        row_kp_percent = row + 1  # KP/3% mező mindig a következő sorba kerül

        self.kp_per_3_label = tk.Label(self.win, text="KP/3%:")
        self.kp_per_3_entry = tk.Entry(self.win, textvariable=self.kp_per_3_var)
        # A KP/3% mezőt mindig a row_kp_percent sorba grideljük, update_kp_fields-ben is!
        if self.type_var.get() == "%":
            self.kp_per_3_label.grid(row=row_kp_percent, column=0, **grid_cfg["label"])
            self.kp_per_3_entry.grid(row=row_kp_percent, column=1, **grid_cfg["entry"])
        self.type_var.trace_add("write", lambda *args: self.update_kp_fields(row_kp_percent))
        self.update_kp_fields(row_kp_percent)

        # Szint leírások a KP/3% mező után kezdődnek
        row = row_kp_percent
        for i in range(1, 7):
            row += 1
            tk.Label(self.win, text=f"{i}. szint leírás:").grid(row=row, column=0, **grid_cfg["label"])
            desc_text = tk.Text(self.win, height=4, width=50)
            desc_text.grid(row=row, column=1, columnspan=2, **grid_cfg["text"])
            self.level_desc_texts.append(desc_text)
            kpvar = tk.StringVar()
            self.kp_cost_vars.append(kpvar)
            # KP label és entry egymás mellett, egy columnban, de entry-nek nagyobb bal padding
            kp_label = tk.Label(self.win, text=f"{i}. szint KP:")
            kp_label.grid(row=row, column=3, sticky="w", padx=5, pady=2)
            self.kp_cost_labels.append(kp_label)
            kp_entry = tk.Entry(self.win, textvariable=kpvar, width=8)
            kp_entry.grid(row=row, column=3, sticky="w", padx=75, pady=2)
            self.kp_cost_entries.append(kp_entry)

        # Alsó gombok
        row += 1
        bottom_frame = tk.Frame(self.win)
        bottom_frame.grid(row=row, column=0, columnspan=5, pady=20)
        tk.Button(bottom_frame, text="Szerkesztés", command=self.open_skill_loader).pack(side=tk.LEFT, padx=20)
        tk.Button(bottom_frame, text="Törlés", command=self.delete_skill).pack(side=tk.LEFT, padx=20)
        tk.Button(bottom_frame, text="Mentés", command=self.save_skill).pack(side=tk.LEFT, padx=20)

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

    def update_kp_fields(self, row_kp_percent):
        if self.type_var.get() == "%":
            self.kp_per_3_label.grid(row=row_kp_percent, column=0, sticky="w", padx=5, pady=2)
            self.kp_per_3_entry.grid(row=row_kp_percent, column=1, sticky="w", padx=5, pady=2)
            self.kp_per_3_var.set("")
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
        skill = {
            "name": self.name_var.get(),
            "main_category": self.main_cat_var.get(),
            "sub_category": self.sub_cat_var.get(),
            "description": self.general_desc_text.get("1.0", tk.END).strip(),
            "acquisition_method": self.acq_method_var.get(),
            "acquisition_difficulty": self.acq_diff_var.get(),
            "skill_type": self.type_var.get(),
            "kp_per_3_percent": self.kp_per_3_var.get() if self.type_var.get() == "%" else None,
            "kp_costs": {},
            "level_descriptions": {},
            "prerequisites": {}
        }
        param_value = self.param_var.get().strip()
        if param_value:
            skill["is_parametric"] = True
            skill["parameter"] = param_value
        for i, desc_text in enumerate(self.level_desc_texts):
            desc = desc_text.get("1.0", tk.END).strip()
            if desc:
                skill["level_descriptions"][str(i+1)] = desc
        if self.type_var.get() != "%":
            for i, kp_var in enumerate(self.kp_cost_vars):
                kp = kp_var.get().strip()
                if kp:
                    skill["kp_costs"][str(i+1)] = kp
        for i in range(1, 7):
            stat_list = []
            for stat_var, value_var in self.prereq_manager.stat_vars[i-1]:
                stat = stat_var.get()
                value = value_var.get()
                if stat and value:
                    stat_list.append(f"{stat} {value}+")
            skill_list = []
            for skill_var, level_var, param in self.prereq_manager.skill_vars[i-1]:
                skillname = skill_var.get()
                level = level_var.get()
                display_text = skillname
                if param:
                    display_text += f" ({param})"
                if skillname and level:
                    skill_list.append(f"{display_text} {level}. szint")
            if stat_list or skill_list:
                skill["prerequisites"][str(i)] = {"képesség": stat_list, "képzettség": skill_list}
        if self.type_var.get() == "%":
            skill.pop("kp_costs")
        else:
            skill.pop("kp_per_3_percent")
        if not self.skill_manager.validate(skill):
            self.show_error("Hiányzó vagy hibás mező a képzettségben!")
            return
        try:
            skills = self.skill_manager.load()
        except Exception:
            skills = []
        found_idx = None
        for idx, s in enumerate(skills):
            if s["name"].strip().lower() == skill["name"].strip().lower():
                if skill.get("is_parametric"):
                    if s.get("parameter", "").strip().lower() == skill.get("parameter", "").strip().lower():
                        found_idx = idx
                        break
                else:
                    if not s.get("is_parametric"):
                        found_idx = idx
                        break
        if found_idx is not None:
            answer = self.ask_yes_no("Az adott képzettség már létezik. Felülírja?", "Felülírás")
            if not answer:
                return
            skills[found_idx] = skill
        else:
            skills.append(skill)
        self.skill_manager.save(skills)
        self.show_info("Képzettség mentve!", "Siker")
        self.win.destroy()

    def delete_skill(self):
        loader = tk.Toplevel(self.win)
        loader.title("Képzettség törlése")
        loader.geometry("500x300")
        skills_display = []
        for s in self.all_skills:
            if s.get("is_parametric") and s.get("parameter"):
                skills_display.append(f"{s['name']} ({s['parameter']})")
            else:
                skills_display.append(s['name'])
        listbox = tk.Listbox(loader, width=60, height=15)
        for item in skills_display:
            listbox.insert(tk.END, item)
        listbox.pack(pady=10)
        def do_delete():
            idx = listbox.curselection()
            if not idx:
                self.show_warning("Nincs kiválasztva képzettség.", "Törlés")
                return
            self.all_skills.pop(idx[0])
            self.skill_manager.save(self.all_skills)
            self.show_info("Képzettség törölve!", "Törlés")
            loader.destroy()
        tk.Button(loader, text="Törlés", command=do_delete).pack(pady=10)

    def open_skill_search_dialog(self, level_idx, frame):
        dialog = tk.Toplevel(frame)
        dialog.title("Képzettség keresése")
        dialog.geometry("400x220")
        search_var = tk.StringVar()
        tk.Label(dialog, text="Képzettség keresése:").pack()
        search_entry = tk.Entry(dialog, textvariable=search_var, width=40)
        search_entry.pack()
        filtered_skills = self.SKILL_NAMES.copy()
        skill_var = tk.StringVar()
        skill_combo = ttk.Combobox(dialog, textvariable=skill_var, values=filtered_skills, state="readonly", width=35)
        skill_combo.pack(pady=5)
        param_label = tk.Label(dialog, text="Specializáció / típus (pl. Rövid kardok, Elf nyelv):")
        param_label.pack_forget()
        param_var = tk.StringVar()
        param_menu = None
        def show_param_field(*args):
            nonlocal param_menu
            skill_name = skill_var.get()
            skill_obj = next((s for s in self.all_skills if s["name"] == skill_name), None)
            if param_menu:
                param_menu.destroy()
                param_menu = None
            if skill_obj and skill_obj.get("is_parametric"):
                param_label.pack()
                params = set()
                for s in self.all_skills:
                    if s["name"] == skill_name and s.get("parameter"):
                        params.add(s["parameter"])
                params = sorted(params)
                if params:
                    param_var.set(params[0])
                    param_menu = tk.OptionMenu(dialog, param_var, *params)
                    param_menu.pack()
                else:
                    param_var.set("")
                    param_menu = tk.Entry(dialog, textvariable=param_var, width=30)
                    param_menu.pack()
            else:
                param_label.pack_forget()
                param_var.set("")
                if param_menu:
                    param_menu.destroy()
                    param_menu = None
        skill_var.trace_add("write", show_param_field)
        tk.Label(dialog, text="Szükséges szint:").pack()
        level_var = tk.StringVar()
        level_entry = tk.Entry(dialog, textvariable=level_var, width=5)
        level_entry.pack()
        def update_skill_list(*args):
            text = search_var.get().lower()
            filtered = [s for s in self.SKILL_NAMES if text in s.lower()]
            skill_combo['values'] = filtered
            if filtered:
                skill_var.set(filtered[0])
            else:
                skill_var.set("")
        search_var.trace_add("write", update_skill_list)
        def add_skill():
            skill = skill_var.get()
            level = level_var.get()
            param = param_var.get().strip()
            skill_obj = next((s for s in self.all_skills if s["name"] == skill), None)
            if skill and level:
                row = len(self.prereq_manager.skill_vars[level_idx]) + 1
                display_text = skill
                if skill_obj and skill_obj.get("is_parametric") and param:
                    display_text += f" ({param})"
                skill_label = tk.Label(frame, text=display_text)
                skill_label.grid(row=row, column=2, padx=(5, 0), sticky="w")
                entry = tk.Entry(frame, width=5)
                entry.insert(0, level)
                entry.grid(row=row, column=3, padx=10, sticky="w")
                def remove():
                    skill_label.destroy()
                    entry.destroy()
                    btn.destroy()
                    self.prereq_manager.skill_vars[level_idx].remove((skill_var, level_var, param))
                btn = tk.Button(frame, text="Törlés", command=remove)
                btn.grid(row=row, column=4, padx=10, sticky="w")
                self.prereq_manager.skill_vars[level_idx].append((skill_var, level_var, param))
                dialog.destroy()
        tk.Button(dialog, text="Hozzáadás", command=add_skill).pack(pady=5)

    def open_skill_loader(self):
        loader = tk.Toplevel(self.win)
        loader.title("Képzettség betöltése")
        loader.geometry("500x300")
        skills_display = []
        for s in self.all_skills:
            if s.get("is_parametric") and s.get("parameter"):
                skills_display.append(f"{s['name']} ({s['parameter']})")
            else:
                skills_display.append(s['name'])
        listbox = tk.Listbox(loader, width=60, height=15)
        for item in skills_display:
            listbox.insert(tk.END, item)
        listbox.pack(pady=10)
        def load_selected():
            idx = listbox.curselection()
            if not idx:
                self.show_warning("Nincs kiválasztva képzettség.", "Betöltés")
                return
            skill_obj = self.all_skills[idx[0]]
            self.name_var.set(skill_obj["name"])
            self.param_var.set(skill_obj.get("parameter", ""))
            self.general_desc_text.delete("1.0", tk.END)
            self.general_desc_text.insert(tk.END, skill_obj.get("description", ""))
            self.main_cat_var.set(skill_obj.get("main_category", ""))
            self.sub_cat_var.set(skill_obj.get("sub_category", ""))
            self.acq_method_var.set(skill_obj.get("acquisition_method", ""))
            self.acq_diff_var.set(skill_obj.get("acquisition_difficulty", ""))
            self.type_var.set(skill_obj.get("skill_type", "%"))
            for i, desc_text in enumerate(self.level_desc_texts):
                desc_text.delete("1.0", tk.END)
                desc = skill_obj.get("level_descriptions", {}).get(str(i+1), "")
                desc_text.insert(tk.END, desc)
            if skill_obj.get("skill_type", "%") == "%":
                self.kp_per_3_var.set(skill_obj.get("kp_per_3_percent", ""))
                for kp_var in self.kp_cost_vars:
                    kp_var.set("")
            else:
                self.kp_per_3_var.set("")
                for i, kp_var in enumerate(self.kp_cost_vars):
                    kp_var.set(skill_obj.get("kp_costs", {}).get(str(i+1), ""))
            self.prereq_manager.load_prerequisites(skill_obj.get("prerequisites", {}))
            loader.destroy()
        def delete_selected():
            idx = listbox.curselection()
            if not idx:
                self.show_warning("Nincs kiválasztva képzettség.", "Törlés")
                return
            skill_obj = self.all_skills[idx[0]]
            answer = self.ask_yes_no(f"Biztosan törlöd ezt a képzettséget?\n{skills_display[idx[0]]}", "Törlés")
            if answer:
                self.all_skills.pop(idx[0])
                self.skill_manager.save(self.all_skills)
                self.show_info("Képzettség törölve!", "Törlés")
                loader.destroy()
        button_frame = tk.Frame(loader)
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="Betöltés", command=load_selected).pack(side=tk.LEFT, padx=20)
        tk.Button(button_frame, text="Törlés", command=delete_selected).pack(side=tk.LEFT, padx=20)

# --- Futtatható fő rész ---
if __name__ == "__main__":
    editor = SkillEditor()
