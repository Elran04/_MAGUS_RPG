import tkinter as tk
from tkinter import messagebox
import os
from utils.skill_manager import SkillManager
from tkinter import ttk
import re

# Ensure SkillManager uses the correct path to skills.json
SKILLS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "skills", "skills.json")

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
        # Új: minden szinthez egy közös előfeltétel-lista (dict-ek)
        self.prereq_vars = [[] for _ in range(6)]  # [{"type":..., ...}, ...]
        self.frames = []
        self.create_frames()

    def create_stat_row_widget(self, frame, prereq_dict):
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
        row = len([w for w in frame.grid_slaves() if isinstance(w, ttk.Combobox) or isinstance(w, tk.Entry) or isinstance(w, tk.Label)]) // 2 + 1
        skill_var = prereq_dict["name_var"]
        level_var = prereq_dict["level_var"]
        param_var = prereq_dict.get("param_var", None)
        # Egységes skill/paraméter feldolgozás
        def parse_skill_name(name):
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
        prereq_dict = {
            "type": "stat",
            "name_var": tk.StringVar(value=STAT_NAMES[0]),
            "value_var": tk.StringVar(),
        }
        self.create_stat_row_widget(frame, prereq_dict)
        self.prereq_vars[level_idx].append(prereq_dict)

    def add_skill_row(self, level_idx, frame):
        dialog = tk.Toplevel(frame)
        dialog.title("Képzettség keresése")
        dialog.geometry("400x250")
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
        param_var = tk.StringVar()
        skill_combo = ttk.Combobox(dialog, textvariable=skill_var, values=filtered_skills, state="readonly", width=35)
        skill_combo.pack(pady=5)
        param_label = tk.Label(dialog, text="Paraméter (pl. Rövid kardok, Elf nyelv):")
        param_label.pack()
        param_entry = tk.Entry(dialog, textvariable=param_var, width=30)
        param_entry.pack()
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
        def update_param_field(*args):
            # Egységes skill/paraméter feldolgozás
            m = re.match(r"(.+?)(?: \((.+?)\))?$", skill_var.get())
            param_in_name = m.group(2) if m and m.group(2) else ""
            param_var.set(param_in_name)
        skill_var.trace_add("write", update_param_field)
        def add_skill():
            skill = skill_var.get()
            level = level_var.get()
            param = param_var.get().strip()
            if skill and level:
                base_name, _ = re.match(r"(.+?)(?: \((.+?)\))?$", skill).groups() if re.match(r"(.+?)(?: \((.+?)\))?$", skill) else (skill, "")
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
        for idx in range(6):
            for prereq in self.prereq_vars[idx][:]:
                for w in prereq.get("widgets", []):
                    w.destroy()
            self.prereq_vars[idx].clear()

    def load_prerequisites(self, prerequisites):
        self.clear_all()
        for idx in range(6):
            prereq = prerequisites.get(str(idx+1), {})
            frame = self.frames[idx]
            # Tulajdonságok
            for stat_str in prereq.get("képesség", []):
                parts = stat_str.split()
                if len(parts) >= 2:
                    prereq_dict = {
                        "type": "stat",
                        "name_var": tk.StringVar(value=parts[0]),
                        "value_var": tk.StringVar(value=parts[1].replace("+", "")),
                    }
                    self.create_stat_row_widget(frame, prereq_dict)
                    self.prereq_vars[idx].append(prereq_dict)
            # Képzettségek
            for skill_str in prereq.get("képzettség", []):
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
                    self.create_skill_row_widget(frame, prereq_dict)
                    self.prereq_vars[idx].append(prereq_dict)

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
        # Mindig a paraméter mező aktuális értékét mentsük, ne a régit vagy automatikusan generáltat
        param_value = self.param_var.get().strip()
        if param_value:
            skill["is_parametric"] = True
            skill["parameter"] = param_value
        else:
            skill["is_parametric"] = False
            skill["parameter"] = ""
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
            skill_list = []
            for prereq in self.prereq_manager.prereq_vars[i-1]:
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
                    # Ha van paraméter, csak egyszer fűzzük hozzá
                    if param:
                        display_text = f"{base_name} ({param})"
                    elif param_in_name:
                        display_text = f"{base_name} ({param_in_name})"
                    else:
                        display_text = base_name
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
        # Egységes név és paraméter összehasonlítás (zárójelek nélkül)
        def get_clean_name_and_param(s):
            name = s.get("name", "")
            param = s.get("parameter", "")
            # Ha a névben van zárójel, szedjük szét
            m = re.match(r"(.+?)(?: \((.+?)\))?$", name)
            base_name = m.group(1) if m else name
            param_in_name = m.group(2) if m and m.group(2) else ""
            # Ha van külön paraméter, az a mérvadó
            if param:
                return base_name.strip().lower(), param.strip().lower()
            elif param_in_name:
                return base_name.strip().lower(), param_in_name.strip().lower()
            else:
                return base_name.strip().lower(), ""

        # Mentés előtt egységesítsük a skill nevét és paraméterét
        # Ha van paraméter, a név legyen tiszta, a paraméter külön mezőben
        if skill.get("is_parametric") and skill.get("parameter"):
            m = re.match(r"(.+?)(?: \((.+?)\))?$", skill["name"])
            base_name = m.group(1) if m else skill["name"]
            skill["name"] = base_name

        # Egységes név+paraméter összehasonlítás: lower, strip, zárójelek nélkül
        def normalize(name, param):
            name = name.strip().lower()
            param = param.strip().lower() if param else ""
            # Ha a névben van zárójel, szedjük ki
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
        self.win.destroy()

    def delete_skill(self):
        # Frissítsük az all_skills-t minden dialógus megnyitásakor
        self.all_skills = self.skill_manager.load()
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
            # Törlés a kiválasztott index alapján
            del self.all_skills[idx[0]]
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
        SkillLoaderDialog(self)

    def delete_skill(self):
        SkillDeleteDialog(self)

# --- ÚJ: SkillLoaderDialog osztály ---
class SkillLoaderDialog:
    def __init__(self, editor):
        self.editor = editor
        self.all_skills = editor.skill_manager.load()
        skills_display = []
        for s in self.all_skills:
            if s.get("is_parametric") and s.get("parameter"):
                skills_display.append(f"{s['name']} ({s['parameter']})")
            else:
                skills_display.append(s['name'])
        self.loader = tk.Toplevel(editor.win)
        self.loader.title("Képzettség betöltése")
        self.loader.geometry("500x300")
        self.listbox = tk.Listbox(self.loader, width=60, height=15)
        for item in skills_display:
            self.listbox.insert(tk.END, item)
        self.listbox.pack(pady=10)
        button_frame = tk.Frame(self.loader)
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="Betöltés", command=self.load_selected).pack(side=tk.LEFT, padx=20)
        tk.Button(button_frame, text="Törlés", command=self.delete_selected).pack(side=tk.LEFT, padx=20)

    def load_selected(self):
        idx = self.listbox.curselection()
        if not idx:
            self.editor.show_warning("Nincs kiválasztva képzettség.", "Betöltés")
            return
        skill_obj = self.all_skills[idx[0]]
        self.editor.name_var.set(skill_obj["name"])
        self.editor.param_var.set(skill_obj.get("parameter", ""))
        self.editor.general_desc_text.delete("1.0", tk.END)
        self.editor.general_desc_text.insert(tk.END, skill_obj.get("description", ""))
        self.editor.main_cat_var.set(skill_obj.get("main_category", ""))
        self.editor.sub_cat_var.set(skill_obj.get("sub_category", ""))
        self.editor.acq_method_var.set(skill_obj.get("acquisition_method", ""))
        self.editor.acq_diff_var.set(skill_obj.get("acquisition_difficulty", ""))
        self.editor.type_var.set(skill_obj.get("skill_type", "%"))
        for i, desc_text in enumerate(self.editor.level_desc_texts):
            desc_text.delete("1.0", tk.END)
            desc = skill_obj.get("level_descriptions", {}).get(str(i+1), "")
            desc_text.insert(tk.END, desc)
        if skill_obj.get("skill_type", "%") == "%":
            self.editor.kp_per_3_var.set(skill_obj.get("kp_per_3_percent", ""))
            for kp_var in self.editor.kp_cost_vars:
                kp_var.set("")
        else:
            self.editor.kp_per_3_var.set("")
            for i, kp_var in enumerate(self.editor.kp_cost_vars):
                kp_var.set(skill_obj.get("kp_costs", {}).get(str(i+1), ""))
        self.editor.prereq_manager.load_prerequisites(skill_obj.get("prerequisites", {}))
        self.loader.destroy()

    def delete_selected(self):
        idx = self.listbox.curselection()
        if not idx:
            self.editor.show_warning("Nincs kiválasztva képzettség.", "Törlés")
            return
        skill_obj = self.all_skills[idx[0]]
        skills_display = self.listbox.get(0, tk.END)
        answer = self.editor.ask_yes_no(f"Biztosan törlöd ezt a képzettséget?\n{skills_display[idx[0]]}", "Törlés")
        if answer:
            self.all_skills.pop(idx[0])
            self.editor.skill_manager.save(self.all_skills)
            self.editor.show_info("Képzettség törölve!", "Törlés")
            self.loader.destroy()

# --- ÚJ: SkillDeleteDialog osztály ---
class SkillDeleteDialog:
    def __init__(self, editor):
        self.editor = editor
        self.all_skills = editor.skill_manager.load()
        skills_display = []
        for s in self.all_skills:
            if s.get("is_parametric") and s.get("parameter"):
                skills_display.append(f"{s['name']} ({s['parameter']})")
            else:
                skills_display.append(s['name'])
        self.loader = tk.Toplevel(editor.win)
        self.loader.title("Képzettség törlése")
        self.loader.geometry("500x300")
        self.listbox = tk.Listbox(self.loader, width=60, height=15)
        for item in skills_display:
            self.listbox.insert(tk.END, item)
        self.listbox.pack(pady=10)
        tk.Button(self.loader, text="Törlés", command=self.do_delete).pack(pady=10)

    def do_delete(self):
        idx = self.listbox.curselection()
        if not idx:
            self.editor.show_warning("Nincs kiválasztva képzettség.", "Törlés")
            return
        self.all_skills.pop(idx[0])
        self.editor.skill_manager.save(self.all_skills)
        self.editor.show_info("Képzettség törölve!", "Törlés")
        self.loader.destroy()

# --- Futtatható fő rész ---
if __name__ == "__main__":
    editor = SkillEditor()
