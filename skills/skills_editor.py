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


    global win, name_var, name_entry, param_var, param_entry, main_cat_var, main_cat_menu, sub_cat_var, sub_cat_menu
    global general_desc_text, acq_method_var, acq_diff_var, type_var, type_menu
    global kp_per_3_label, kp_per_3_var, kp_per_3_entry
    global level_desc_texts, kp_cost_vars, kp_cost_labels, kp_cost_entries

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
        param_value = param_var.get().strip()
        if param_value:
            skill["is_parametric"] = True
            skill["parameter"] = param_value

        for i, desc_text in enumerate(level_desc_texts):
            desc = desc_text.get("1.0", tk.END).strip()
            if desc:
                skill["level_descriptions"][str(i+1)] = desc
        if type_var.get() != "%":
            for i, kp_var in enumerate(kp_cost_vars):
                kp = kp_var.get().strip()
                if kp:
                    skill["kp_costs"][str(i+1)] = kp

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
                display_text = skillname
                if param:
                    display_text += f" ({param})"
                if skillname and level:
                    skill_list.append(f"{display_text} {level}. szint")
            if stat_list or skill_list:
                skill["prerequisites"][str(i)] = {"képesség": stat_list, "képzettség": skill_list}
        
        if type_var.get() == "%":
            skill.pop("kp_costs")
        else:
            skill.pop("kp_per_3_percent")

        # --- DUPLIKÁCIÓ ELLENŐRZÉS ÉS FELÜLÍRÁS ---
        try:
            with open(SKILLS_PATH, "r", encoding="utf-8") as f:
                skills = json.load(f)
        except FileNotFoundError:
            skills = []
        # Keresés név+paraméter alapján
        found_idx = None
        for idx, s in enumerate(skills):
            if s["name"].strip().lower() == skill["name"].strip().lower():
                # Paraméteres skilleknél a paraméter is számít
                if skill.get("is_parametric"):
                    if s.get("parameter", "").strip().lower() == skill.get("parameter", "").strip().lower():
                        found_idx = idx
                        break
                else:
                    # Nem paraméteres skilleknél csak a név számít
                    if not s.get("is_parametric"):
                        found_idx = idx
                        break
        if found_idx is not None:
            answer = messagebox.askyesno("Felülírás", "Az adott képzettség már létezik. Felülírja?")
            if not answer:
                return
            skills[found_idx] = skill
        else:
            skills.append(skill)
        with open(SKILLS_PATH, "w", encoding="utf-8") as f:
            json.dump(skills, f, ensure_ascii=False, indent=2)
        messagebox.showinfo("Siker", "Képzettség mentve!")
        win.destroy()

    # Alsó gombok egy közös frame-ben
    bottom_frame = tk.Frame(win)
    bottom_frame.grid(row=15, column=0, columnspan=6, pady=20)

    def delete_skill():
        loader = tk.Toplevel(win)
        loader.title("Képzettség törlése")
        loader.geometry("500x300")
        skills_display = []
        for s in all_skills:
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
                messagebox.showwarning("Törlés", "Nincs kiválasztva képzettség.")
                return
            skill_obj = all_skills[idx[0]]
            answer = messagebox.askyesno("Törlés", f"Biztosan törlöd ezt a képzettséget?\n{skills_display[idx[0]]}")
            if answer:
                all_skills.pop(idx[0])
                with open(SKILLS_PATH, "w", encoding="utf-8") as f:
                    json.dump(all_skills, f, ensure_ascii=False, indent=2)
                messagebox.showinfo("Törlés", "Képzettség törölve!")
                loader.destroy()
        tk.Button(loader, text="Törlés", command=do_delete).pack(pady=10)

    tk.Button(bottom_frame, text="Szerkesztés", command=open_skill_loader).pack(side=tk.LEFT, padx=20)
    tk.Button(bottom_frame, text="Törlés", command=delete_skill).pack(side=tk.LEFT, padx=20)
    tk.Button(bottom_frame, text="Mentés", command=save_skill).pack(side=tk.LEFT, padx=20)
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
    param_label.pack_forget()
    param_var = tk.StringVar()
    param_menu = None

    def show_param_field(*args):
        nonlocal param_menu
        skill_name = skill_var.get()
        skill_obj = next((s for s in all_skills if s["name"] == skill_name), None)
        # Töröljük a régi menüt, ha van
        if param_menu:
            param_menu.destroy()
            param_menu = None
        if skill_obj and skill_obj.get("is_parametric"):
            param_label.pack()
            # Paraméterek kigyűjtése az összes skillből
            params = set()
            for s in all_skills:
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
        param = param_var.get().strip()
        skill_obj = next((s for s in all_skills if s["name"] == skill), None)
        if skill and level:
            row = len(prereq_skill_vars[level_idx]) + 1
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
                prereq_skill_vars[level_idx].remove((skill_var, level_var, param))
            btn = tk.Button(frame, text="Törlés", command=remove)
            btn.grid(row=row, column=4, padx=10, sticky="w")
            prereq_skill_vars[level_idx].append((skill_var, level_var, param))
            dialog.destroy()

    tk.Button(dialog, text="Hozzáadás", command=add_skill).pack(pady=5)


def open_skill_loader():
    loader = tk.Toplevel()
    loader.title("Képzettség betöltése")
    loader.geometry("500x300")

    # Listázd az összes skillt (név + paraméter, ha van)
    skills_display = []
    for s in all_skills:
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
            messagebox.showwarning("Betöltés", "Nincs kiválasztva képzettség.")
            return
        skill_obj = all_skills[idx[0]]
        # Töltsd be az adatokat a szerkesztő mezőkbe!
        name_var.set(skill_obj["name"])
        param_var.set(skill_obj.get("parameter", ""))
        general_desc_text.delete("1.0", tk.END)
        general_desc_text.insert(tk.END, skill_obj.get("description", ""))
        main_cat_var.set(skill_obj.get("main_category", ""))
        sub_cat_var.set(skill_obj.get("sub_category", ""))
        acq_method_var.set(skill_obj.get("acquisition_method", ""))
        acq_diff_var.set(skill_obj.get("acquisition_difficulty", ""))
        type_var.set(skill_obj.get("skill_type", "%"))

        # Szintleírások betöltése
        for i, desc_text in enumerate(level_desc_texts):
            desc_text.delete("1.0", tk.END)
            desc = skill_obj.get("level_descriptions", {}).get(str(i+1), "")
            desc_text.insert(tk.END, desc)

        # KP-k betöltése
        if skill_obj.get("skill_type", "%") == "%":
            kp_per_3_var.set(skill_obj.get("kp_per_3_percent", ""))
            for kp_var in kp_cost_vars:
                kp_var.set("")
        else:
            kp_per_3_var.set("")
            for i, kp_var in enumerate(kp_cost_vars):
                kp_var.set(skill_obj.get("kp_costs", {}).get(str(i+1), ""))

        # Előfeltételek törlése és újratöltése
        for idx2 in range(6):
            # Stat előfeltételek törlése
            for stat_var, value_var in prereq_stat_vars[idx2][:]:
                stat_var.set("")
                value_var.set("")
            prereq_stat_vars[idx2].clear()
            # Skill előfeltételek törlése
            for skill_var, level_var, param in prereq_skill_vars[idx2][:]:
                skill_var.set("")
                level_var.set("")
            prereq_skill_vars[idx2].clear()

            # Újratöltés
            prereq = skill_obj.get("prerequisites", {}).get(str(idx2+1), {})
            # Stat előfeltételek hozzáadása
            for stat_str in prereq.get("képesség", []):
                parts = stat_str.split()
                if len(parts) >= 2:
                    stat_var = tk.StringVar(value=parts[0])
                    value_var = tk.StringVar(value=parts[1].replace("+", ""))
                    prereq_stat_vars[idx2].append((stat_var, value_var))
                    # Dinamikusan hozzáadjuk a sort a megfelelő frame-hez
                    frame = win.grid_slaves(row=7+idx2, column=4)
                    if frame:
                        stat_menu = tk.OptionMenu(frame[0], stat_var, *STAT_NAMES)
                        stat_menu.grid(row=len(prereq_stat_vars[idx2]), column=0, padx=(20, 0), sticky="w")
                        entry = tk.Entry(frame[0], textvariable=value_var, width=5)
                        entry.grid(row=len(prereq_stat_vars[idx2]), column=1, padx=10, sticky="w")
                        def remove_stat(stat_menu=stat_menu, entry=entry, btn=None):
                            stat_menu.destroy()
                            entry.destroy()
                            if btn:
                                btn.destroy()
                            prereq_stat_vars[idx2].remove((stat_var, value_var))
                        btn = tk.Button(frame[0], text="Törlés", command=remove_stat)
                        btn.grid(row=len(prereq_stat_vars[idx2]), column=1, padx=50, sticky="w")
            # Skill előfeltételek hozzáadása
            for skill_str in prereq.get("képzettség", []):
                import re
                m = re.match(r"(.+?)(?: \((.+?)\))? (\d+)\. szint", skill_str)
                if m:
                    skillname = m.group(1)
                    param = m.group(2) or ""
                    level = m.group(3)
                    skill_var = tk.StringVar(value=skillname)
                    level_var = tk.StringVar(value=level)
                    prereq_skill_vars[idx2].append((skill_var, level_var, param))
                    frame = win.grid_slaves(row=7+idx2, column=4)
                    if frame:
                        skill_combo = ttk.Combobox(frame[0], textvariable=skill_var, values=SKILL_NAMES, state="readonly", width=30)
                        skill_combo.grid(row=len(prereq_skill_vars[idx2]), column=2, padx=(5, 0), sticky="w")
                        entry = tk.Entry(frame[0], textvariable=level_var, width=5)
                        entry.grid(row=len(prereq_skill_vars[idx2]), column=3, padx=10, sticky="w")
                        def remove_skill(skill_combo=skill_combo, entry=entry, btn=None):
                            skill_combo.destroy()
                            entry.destroy()
                            if btn:
                                btn.destroy()
                            prereq_skill_vars[idx2].remove((skill_var, level_var, param))
                        btn = tk.Button(frame[0], text="Törlés", command=remove_skill)
                        btn.grid(row=len(prereq_skill_vars[idx2]), column=4, padx=10, sticky="w")
        loader.destroy()

    def delete_selected():
        idx = listbox.curselection()
        if not idx:
            messagebox.showwarning("Törlés", "Nincs kiválasztva képzettség.")
            return
        skill_obj = all_skills[idx[0]]
        answer = messagebox.askyesno("Törlés", f"Biztosan törlöd ezt a képzettséget?\n{skills_display[idx[0]]}")
        if answer:
            all_skills.pop(idx[0])
            # Írd vissza a JSON-t
            with open(SKILLS_PATH, "w", encoding="utf-8") as f:
                json.dump(all_skills, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Törlés", "Képzettség törölve!")
            loader.destroy()

    # Gombok a loader ablak alján
    button_frame = tk.Frame(loader)
    button_frame.pack(pady=10)
    tk.Button(button_frame, text="Betöltés", command=load_selected).pack(side=tk.LEFT, padx=20)
    tk.Button(button_frame, text="Törlés", command=delete_selected).pack(side=tk.LEFT, padx=20)

# --- Futtatható fő rész ---
if __name__ == "__main__":
    add_skill_gui()