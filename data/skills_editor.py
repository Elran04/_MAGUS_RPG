import tkinter as tk
from tkinter import messagebox
import json
import os
from skills import load_skills

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
    skill_menu = tk.OptionMenu(frame, skill_var, *SKILL_NAMES)
    skill_menu.grid(row=row, column=2, padx=(5, 0), sticky="w")  
    entry = tk.Entry(frame, textvariable=level_var, width=5)
    entry.grid(row=row, column=3, padx=10, sticky="w")
    def remove():
        skill_menu.destroy()
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
    win.geometry("1256x978")  # Nagyobb ablak

    tk.Label(win, text="Név:").grid(row=0, column=0)
    name_var = tk.StringVar()
    tk.Entry(win, textvariable=name_var).grid(row=0, column=1)

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

    tk.Label(win, text="Leírás:").grid(row=3, column=0)
    desc_text = tk.Text(win, height=3, width=30)
    desc_text.grid(row=3, column=1)

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
            command=lambda idx=i-1, fr=prereq_frame: add_skill_row(idx, fr)
        ).grid(row=0, column=2, padx=10)

    def save_skill():
        skill = {
            "name": name_var.get(),
            "main_category": main_cat_var.get(),
            "sub_category": sub_cat_var.get(),
            "description": desc_text.get("1.0", tk.END).strip(),
            "acquisition_method": acq_method_var.get(),
            "acquisition_difficulty": acq_diff_var.get(),
            "skill_type": type_var.get(),
            "kp_per_3_percent": kp_per_3_var.get() if type_var.get() == "%" else None,
            "kp_costs": {},
            "level_descriptions": {},
            "prerequisites": {}
        }
        for i in range(1, 7):
            desc = level_desc_texts[i-1].get("1.0", tk.END).strip()
            if desc:
                skill["level_descriptions"][str(i)] = desc
            if type_var.get() == "szint":
                kp = kp_cost_vars[i-1].get()
                if kp:
                    skill["kp_costs"][str(i)] = int(kp)
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

if __name__ == "__main__":
    add_skill_gui()