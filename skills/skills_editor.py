import tkinter as tk
from tkinter import messagebox
import json
import os
from skills import load_skills
from tkinter import ttk

SKILLS_PATH = os.path.join(os.path.dirname(__file__), "skills.json")

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

all_skills = load_skills()
SKILL_NAMES = [s["name"] for s in all_skills]

# minden szinthez:
prereq_stat_vars = [[] for _ in range(6)]
prereq_skill_vars = [[] for _ in range(6)]

def add_stat_row(level_idx, frame):
    stat_var = tk.StringVar(value=STAT_NAMES[0])
    value_var = tk.StringVar()
    row = len(prereq_stat_vars[level_idx]) + 1
    stat_menu = tk.OptionMenu(frame, stat_var, *STAT_NAMES)
    stat_menu.grid(row=row, column=0, padx=(20, 0), sticky="w") 
    entry = tk.Entry(frame, textvariable=value_var, width=5)
    entry.grid(row=row, column=1, padx=10, sticky="w")
    def remove():
        stat_menu.destroy()
        entry.destroy()
        btn.destroy()
        prereq_stat_vars[level_idx].remove((stat_var, value_var))
    btn = tk.Button(frame, text="Törlés", command=remove)
    btn.grid(row=row, column=1, padx=50, sticky="w")
    prereq_stat_vars[level_idx].append((stat_var, value_var))

def add_skill_row(level_idx, frame):
    skill_var = tk.StringVar(value=SKILL_NAMES[0])
    level_var = tk.StringVar()
    row = len(prereq_skill_vars[level_idx]) + 1

    # Szűrhető legördülő menü a skillekhez
    skill_combo = ttk.Combobox(frame, textvariable=skill_var, values=SKILL_NAMES, state="readonly", width=30)
    skill_combo.grid(row=row, column=2, padx=(5, 0), sticky="w")

    entry = tk.Entry(frame, textvariable=level_var, width=5)
    entry.grid(row=row, column=3, padx=10, sticky="w")

    def remove():
        skill_combo.destroy()
        entry.destroy()
        btn.destroy()
        prereq_skill_vars[level_idx].remove((skill_var, level_var))

    btn = tk.Button(frame, text="Törlés", command=remove)
    btn.grid(row=row, column=3, padx=50, sticky="w")
    prereq_skill_vars[level_idx].append((skill_var, level_var))

def add_skill_gui():
    def update_subcategories(*args):
        sub_cat_menu['menu'].delete(0, 'end')
        selected_main = main_cat_var.get()
        for sub in CATEGORIES.get(selected_main, []):
            sub_cat_menu['menu'].add_command(label=sub, command=tk._setit(sub_cat_var, sub))
        if CATEGORIES.get(selected_main):
            sub_cat_var.set(CATEGORIES[selected_main][0])
        else:
            sub_cat_var.set("")

    win = tk.Tk()
    win.title("Új képzettség hozzáadása")
    win.geometry("1440x900")  # Nagyobb ablak


    tk.Label(win, text="Név:").grid(row=0, column=0)
    name_var = tk.StringVar()
    name_entry = tk.Entry(win, textvariable=name_var)
    name_entry.grid(row=0, column=1)

    # Paraméterezhetőség input mező a név mellett
    tk.Label(win, text="Paraméter (pl. Rövid kardok, Elf nyelv, stb.):").grid(row=0, column=2)
    param_var = tk.StringVar()
    param_entry = tk.Entry(win, textvariable=param_var, width=20)
    param_entry.grid(row=0, column=3)

    tk.Label(win, text="Főkategória:").grid(row=1, column=0)
    main_cat_var = tk.StringVar()
    main_cat_menu = tk.OptionMenu(win, main_cat_var, *CATEGORIES.keys())
    main_cat_menu.grid(row=1, column=1)
    main_cat_var.set(list(CATEGORIES.keys())[0])

    tk.Label(win, text="Alkategória:").grid(row=2, column=0)
    sub_cat_var = tk.StringVar()
    sub_cat_menu = tk.OptionMenu(win, sub_cat_var, *CATEGORIES[main_cat_var.get()])
    sub_cat_menu.grid(row=2, column=1)
    sub_cat_var.set(CATEGORIES[main_cat_var.get()][0])
    main_cat_var.trace_add("write", update_subcategories)

    # Általános leírás mező - VÁLTOZÓNÉV MÓDOSÍTÁS!
    tk.Label(win, text="Általános leírás:").grid(row=3, column=0)
    general_desc_text = tk.Text(win, height=3, width=30)
    general_desc_text.grid(row=3, column=1)

    # Elsajátítás módja
    acq_method_var = tk.StringVar(value="Gyakorlás")
    tk.Label(win, text="Elsajátítás módja:").grid(row=4, column=0)
    tk.OptionMenu(win, acq_method_var, "Gyakorlás", "Tapasztalás", "Tanulás").grid(row=4, column=1)

    # Nehézség
    acq_diff_var = tk.StringVar(value="3 - Közepes")
    tk.Label(win, text="Elsajátítás nehézsége:").grid(row=5, column=0)
    tk.OptionMenu(
        win, acq_diff_var,
        "1 - Egyszerű", "2 - Könnyű", "3 - Közepes", "4 - Nehéz", "5 - Szinte lehetetlen"
    ).grid(row=5, column=1)

    # Típus választó
    tk.Label(win, text="Típus:").grid(row=6, column=0)
    type_var = tk.StringVar(value="szint")
    type_menu = tk.OptionMenu(win, type_var, "%", "szint")
    type_menu.grid(row=6, column=1)

    # KP/3% csak %-osnál
    kp_per_3_label = tk.Label(win, text="KP/3% (csak %-os):")
    kp_per_3_label.grid(row=7, column=0)
    kp_per_3_var = tk.StringVar()
    kp_per_3_entry = tk.Entry(win, textvariable=kp_per_3_var)
    kp_per_3_entry.grid(row=7, column=1)

    # Szintleírások és KP mezők
    level_desc_texts = []
    kp_cost_vars = []
    kp_cost_labels = []
    kp_cost_entries = []
    for i in range(1, 7):
        tk.Label(win, text=f"{i}. szint leírás:").grid(row=7+i, column=0)
        desc_text = tk.Text(win, height=4, width=50)  # nagyobb leírás mező
        desc_text.grid(row=7+i, column=1)
        level_desc_texts.append(desc_text)

        # KP csak szintnél
        kpvar = tk.StringVar()
        kp_cost_vars.append(kpvar)
        kp_label = tk.Label(win, text=f"{i}. szint KP:")
        kp_label.grid(row=7+i, column=2)
        kp_cost_labels.append(kp_label)
        kp_entry = tk.Entry(win, textvariable=kpvar, width=8)
        kp_entry.grid(row=7+i, column=3)
        kp_cost_entries.append(kp_entry)

    # Dinamikus mezőmegjelenítés
    def update_kp_fields(*args):
        if type_var.get() == "%":
            kp_per_3_label.grid()
            kp_per_3_entry.grid()
            for lbl, entry in zip(kp_cost_labels, kp_cost_entries):
                lbl.grid_remove()
                entry.grid_remove()
        else:
            kp_per_3_label.grid_remove()
            kp_per_3_entry.grid_remove()
            for lbl, entry in zip(kp_cost_labels, kp_cost_entries):
                lbl.grid()
                entry.grid()

    type_var.trace_add("write", update_kp_fields)
    update_kp_fields()

    # minden szinthez:
    for i in range(1, 7):
        prereq_frame = tk.Frame(win)
        prereq_frame.grid(row=7+i, column=4, columnspan=2, sticky="w", padx=40)
        tk.Label(prereq_frame, text=f"{i}. szint előfeltétel:").grid(row=0, column=0, sticky="w", padx=10)
        tk.Button(
            prereq_frame, text="Tulajdonság hozzáadása",
            command=lambda idx=i-1, fr=prereq_frame: add_stat_row(idx, fr)
        ).grid(row=0, column=1, padx=10)
        tk.Button(
            prereq_frame, text="Képzettség hozzáadása",
            command=lambda idx=i-1, fr=prereq_frame: open_skill_search_dialog(idx, fr)
        ).grid(row=0, column=2, padx=10)

    def save_skill():

        skill = {
            "name": name_var.get(),
            "main_category": main_cat_var.get(),
            "sub_category": sub_cat_var.get(),
            "description": general_desc_text.get("1.0", tk.END).strip(),
            "acquisition_method": acq_method_var.get(),
            "acquisition_difficulty": acq_diff_var.get(),
            "skill_type": type_var.get(),
            "kp_per_3_percent": kp_per_3_var.get() if type_var.get() == "%" else None,
            "kp_costs": {},
            "level_descriptions": {},
            "prerequisites": {}
        }
        # Ha van paraméter, akkor paraméteres skillként mentjük
        param_value = param_var.get().strip()
        if param_value:
            skill["is_parametric"] = True
            skill["parameter"] = param_value

        for i in range(1, 7):
            stat_list = []
            for stat_var, value_var in prereq_stat_vars[i-1]:
                stat = stat_var.get()
                value = value_var.get()
                if stat and value:
                    stat_list.append(f"{stat} {value}+")
            skill_list = []
            for skill_var, level_var, param in prereq_skill_vars[i-1]:
                skillname = skill_var.get()
                level = level_var.get()
                if skillname and level:
                    if param:
                        skill_list.append(f"{skillname} ({param}) {level}. szint")
                    else:
                        skill_list.append(f"{skillname} {level}. szint")
            if stat_list or skill_list:
                skill["prerequisites"][str(i)] = {"képesség": stat_list, "képzettség": skill_list}
        
        if type_var.get() == "%":
            skill.pop("kp_costs")
        else:
            skill.pop("kp_per_3_percent")

        try:
            with open(SKILLS_PATH, "r", encoding="utf-8") as f:
                skills = json.load(f)
        except FileNotFoundError:
            skills = []
        skills.append(skill)
        with open(SKILLS_PATH, "w", encoding="utf-8") as f:
            json.dump(skills, f, ensure_ascii=False, indent=2)
        messagebox.showinfo("Siker", "Képzettség hozzáadva!")
        win.destroy()


    tk.Button(win, text="Mentés", command=save_skill).grid(row=14, column=1, pady=10)
    win.mainloop()



def open_skill_search_dialog(level_idx, frame):
    dialog = tk.Toplevel(frame)
    dialog.title("Képzettség keresése")
    dialog.geometry("400x220")

    search_var = tk.StringVar()
    tk.Label(dialog, text="Képzettség keresése:").pack()
    search_entry = tk.Entry(dialog, textvariable=search_var, width=40)
    search_entry.pack()

    filtered_skills = SKILL_NAMES.copy()
    skill_var = tk.StringVar()
    skill_combo = ttk.Combobox(dialog, textvariable=skill_var, values=filtered_skills, state="readonly", width=35)
    skill_combo.pack(pady=5)

    # Paraméter mező csak ha szükséges
    param_label = tk.Label(dialog, text="Specializáció / típus (pl. Rövid kardok, Elf nyelv):")
    param_entry = tk.Entry(dialog, width=30)
    param_label.pack_forget()
    param_entry.pack_forget()

    def show_param_field(*args):
        skill_name = skill_var.get()
        # Megkeressük a skill objektumot
        skill_obj = next((s for s in all_skills if s["name"] == skill_name), None)
        if skill_obj and skill_obj.get("is_parametric"):
            param_label.pack()
            param_entry.pack()
        else:
            param_label.pack_forget()
            param_entry.pack_forget()

    skill_var.trace_add("write", show_param_field)

    tk.Label(dialog, text="Szükséges szint:").pack()
    level_var = tk.StringVar()
    level_entry = tk.Entry(dialog, textvariable=level_var, width=5)
    level_entry.pack()

    def update_skill_list(*args):
        text = search_var.get().lower()
        filtered = [s for s in SKILL_NAMES if text in s.lower()]
        skill_combo['values'] = filtered
        if filtered:
            skill_var.set(filtered[0])
        else:
            skill_var.set("")

    search_var.trace_add("write", update_skill_list)

    def add_skill():
        skill = skill_var.get()
        level = level_var.get()
        param = param_entry.get().strip()
        skill_obj = next((s for s in all_skills if s["name"] == skill), None)
        if skill and level:
            row = len(prereq_skill_vars[level_idx]) + 1
            # Ha paraméterezhető, mutassuk a paramétert is
            if skill_obj and skill_obj.get("is_parametric") and param:
                display_text = f"{skill} ({param})"
            else:
                display_text = skill
            skill_label = tk.Label(frame, text=display_text)
            skill_label.grid(row=row, column=2, padx=(5, 0), sticky="w")
            entry = tk.Entry(frame, width=5)
            entry.insert(0, level)
            entry.grid(row=row, column=3, padx=10, sticky="w")
            def remove():
                skill_label.destroy()
                entry.destroy()
                btn.destroy()
                prereq_skill_vars[level_idx].remove((skill_var, level_var, param))
            btn = tk.Button(frame, text="Törlés", command=remove)
            btn.grid(row=row, column=4, padx=10, sticky="w")
            prereq_skill_vars[level_idx].append((skill_var, level_var, param))
            dialog.destroy()

    tk.Button(dialog, text="Hozzáadás", command=add_skill).pack(pady=5)


# --- Futtatható fő rész ---
if __name__ == "__main__":
    add_skill_gui()