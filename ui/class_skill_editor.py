"""
Class skill editor UI for MAGUS RPG.

This module provides an editor for managing class-specific skill assignments,
including skill levels and percentages per class level.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

DB_CLASS = "d:/_Projekt/_MAGUS_RPG/data/Class/class_data.db"
DB_SKILL = "d:/_Projekt/_MAGUS_RPG/data/skills/skills_data.db"

def get_classes():
    """
    Get all classes from the database.
    
    Returns:
        list: List of (id, name) tuples for all classes
    """
    with sqlite3.connect(DB_CLASS) as conn:
        return conn.execute("SELECT id, name FROM classes").fetchall()

def get_skills():
    """
    Get all skills from the database.
    
    Returns:
        list: List of skill data tuples
    """
    with sqlite3.connect(DB_SKILL) as conn:
        return conn.execute("SELECT id, name, category, subcategory, parameter FROM skills").fetchall()

def get_class_skills(class_id, spec_id=None):
    """
    Get skills assigned to a specific class.
    
    Args:
        class_id: Class ID
        spec_id: Specialization ID (optional)
        
    Returns:
        list: List of skill assignments for the class
    """
    with sqlite3.connect(DB_CLASS) as conn:
        return conn.execute(
            "SELECT skill_id, class_level, skill_level, skill_percent FROM class_skills WHERE class_id=? AND (specialisation_id=? OR specialisation_id IS NULL)",
            (class_id, spec_id)
        ).fetchall()

def add_class_skill(class_id, spec_id, class_level, skill_id, skill_level, skill_percent):
    with sqlite3.connect(DB_CLASS) as conn:
        conn.execute(
            "INSERT INTO class_skills (class_id, specialisation_id, class_level, skill_id, skill_level, skill_percent) VALUES (?, ?, ?, ?, ?, ?)",
            (class_id, spec_id, class_level, skill_id, skill_level, skill_percent)
        )
        conn.commit()

def update_class_skill(class_id, spec_id, skill_id, class_level, skill_level, skill_percent):
    with sqlite3.connect(DB_CLASS) as conn:
        conn.execute(
            "UPDATE class_skills SET class_level=?, skill_level=?, skill_percent=? WHERE class_id=? AND specialisation_id=? AND skill_id=?",
            (class_level, skill_level, skill_percent, class_id, spec_id, skill_id)
        )
        conn.commit()

def delete_class_skill(class_id, spec_id, skill_id):
    with sqlite3.connect(DB_CLASS) as conn:
        conn.execute(
            "DELETE FROM class_skills WHERE class_id=? AND specialisation_id=? AND skill_id=?",
            (class_id, spec_id, skill_id)
        )
        conn.commit()

def ensure_table():
    with sqlite3.connect(DB_CLASS) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS class_skills (
            class_id TEXT,
            specialisation_id TEXT,
            class_level INTEGER,
            skill_id TEXT,
            skill_level INTEGER,
            skill_percent INTEGER,
            PRIMARY KEY (class_id, specialisation_id, skill_id)
        )
        """)
        conn.commit()

class ClassSkillEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Class Skill Editor")
        self.geometry("900x500")
        ensure_table()
        self.create_widgets()
        self.populate_classes()
        self.populate_skills()
        self.selected_class = None
        self.selected_spec = None

    def create_widgets(self):
        # Top: class & spec selector
        top_frame = tk.Frame(self)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=8, pady=4)

        tk.Label(top_frame, text="Kaszt:").pack(side=tk.LEFT)
        self.class_cb = ttk.Combobox(top_frame, state="readonly")
        self.class_cb.pack(side=tk.LEFT, padx=4)
        self.class_cb.bind("<<ComboboxSelected>>", self.on_class_selected)

        tk.Label(top_frame, text="Specializáció:").pack(side=tk.LEFT)
        self.spec_cb = ttk.Combobox(top_frame, state="readonly", values=["(nincs)", "(placeholder)"])
        self.spec_cb.pack(side=tk.LEFT, padx=4)
        self.spec_cb.current(0)
        self.spec_cb.bind("<<ComboboxSelected>>", self.on_spec_selected)

        # Main layout
        main_frame = tk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        # Left: available skills
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tk.Label(left_frame, text="Elérhető képzettségek").pack()
        self.skill_tree = ttk.Treeview(left_frame, columns=("skill_id", "skill_name"), show="tree headings")
        self.skill_tree.heading("#0", text="Kategória / Alkategória")
        self.skill_tree.heading("skill_id", text="Azonosító")
        self.skill_tree.heading("skill_name", text="Név")
        self.skill_tree.pack(fill=tk.BOTH, expand=True)
        self.skill_tree.bind("<<TreeviewSelect>>", self.on_skill_select)

        # Right: assigned skills
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        tk.Label(right_frame, text="Hozzárendelt képzettségek").pack()
        self.class_skill_tree = ttk.Treeview(right_frame, columns=("skill_id", "skill_name", "class_level", "skill_level", "skill_percent"), show="headings")
        for col, txt in zip(self.class_skill_tree["columns"], ["Azonosító", "Név", "Szint", "Képzettség szint", "Képzettség %"]):
            self.class_skill_tree.heading(col, text=txt)
        self.class_skill_tree.pack(fill=tk.BOTH, expand=True)
        self.class_skill_tree.bind("<<TreeviewSelect>>", self.on_class_skill_select)

        # Bottom: CRUD buttons
        btn_frame = tk.Frame(self)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=8, pady=4)
        self.btn_add = tk.Button(btn_frame, text="Hozzáadás", command=self.add_skill)
        self.btn_add.pack(side=tk.LEFT, padx=4)
        self.btn_edit = tk.Button(btn_frame, text="Szerkesztés", command=self.edit_skill)
        self.btn_edit.pack(side=tk.LEFT, padx=4)
        self.btn_delete = tk.Button(btn_frame, text="Törlés", command=self.delete_skill)
        self.btn_delete.pack(side=tk.LEFT, padx=4)

    def populate_classes(self):
        classes = get_classes()
        self.class_cb["values"] = [f"{cid} - {name}" for cid, name in classes]
        if classes:
            self.class_cb.current(0)
            self.on_class_selected()

    def populate_skills(self):
        self.skill_tree.delete(*self.skill_tree.get_children())
        skills = get_skills()
        cats = {}
        for skill_id, skill_name, cat, subcat, parameter in skills:
            if cat not in cats:
                cats[cat] = self.skill_tree.insert("", "end", text=cat)
            if subcat:
                if (cat, subcat) not in cats:
                    cats[(cat, subcat)] = self.skill_tree.insert(cats[cat], "end", text=subcat)
                parent = cats[(cat, subcat)]
            else:
                parent = cats[cat]
            display_name = f"{skill_name} ({parameter})" if parameter else skill_name
            self.skill_tree.insert(parent, "end", text="", values=(skill_id, display_name))

    def on_class_selected(self, event=None):
        sel = self.class_cb.get()
        if not sel:
            return
        self.selected_class = sel.split(" - ")[0]
        self.populate_class_skills()

    def on_spec_selected(self, event=None):
        self.selected_spec = self.spec_cb.get()
        self.populate_class_skills()

    def populate_class_skills(self):
        self.class_skill_tree.delete(*self.class_skill_tree.get_children())
        skills = get_class_skills(self.selected_class, None)
        for skill_id, class_level, skill_level, skill_percent in skills:
            # Skill name lookup
            with sqlite3.connect(DB_SKILL) as conn:
                res = conn.execute("SELECT skill_name FROM skills WHERE skill_id=?", (skill_id,)).fetchone()
                skill_name = res[0] if res else ""
            self.class_skill_tree.insert("", "end", values=(skill_id, skill_name, class_level, skill_level, skill_percent))

    def on_skill_select(self, event=None):
        pass  # Implement if needed for UI feedback

    def on_class_skill_select(self, event=None):
        pass  # Implement if needed for UI feedback

    def add_skill(self):
        sel = self.skill_tree.selection()
        if not sel:
            messagebox.showwarning("Nincs kiválasztva", "Válassz ki egy képzettséget!")
            return
        item = self.skill_tree.item(sel[0])
        skill_id = item["values"][0]
        skill_name = item["values"][1]
        # Dialog for input
        dlg = SkillAssignDialog(self, skill_id, skill_name)
        self.wait_window(dlg)
        if dlg.result:
            class_level, skill_level, skill_percent = dlg.result
            # Csak az egyik lehet kitöltve!
            if skill_level and skill_percent:
                messagebox.showerror("Hiba", "Csak az egyik mezőt töltsd ki: szint vagy százalék!")
                return
            add_class_skill(self.selected_class, None, class_level, skill_id, skill_level, skill_percent)
            self.populate_class_skills()

    def edit_skill(self):
        sel = self.class_skill_tree.selection()
        if not sel:
            messagebox.showwarning("Nincs kiválasztva", "Válassz ki egy hozzárendelt képzettséget!")
            return
        item = self.class_skill_tree.item(sel[0])
        skill_id = item["values"][0]
        skill_name = item["values"][1]
        class_level = item["values"][2]
        skill_level = item["values"][3]
        skill_percent = item["values"][4]
        dlg = SkillAssignDialog(self, skill_id, skill_name, class_level, skill_level, skill_percent)
        self.wait_window(dlg)
        if dlg.result:
            class_level, skill_level, skill_percent = dlg.result
            if skill_level and skill_percent:
                messagebox.showerror("Hiba", "Csak az egyik mezőt töltsd ki: szint vagy százalék!")
                return
            update_class_skill(self.selected_class, None, skill_id, class_level, skill_level, skill_percent)
            self.populate_class_skills()

    def delete_skill(self):
        sel = self.class_skill_tree.selection()
        if not sel:
            messagebox.showwarning("Nincs kiválasztva", "Válassz ki egy hozzárendelt képzettséget!")
            return
        item = self.class_skill_tree.item(sel[0])
        skill_id = item["values"][0]
        delete_class_skill(self.selected_class, None, skill_id)
        self.populate_class_skills()

class SkillAssignDialog(tk.Toplevel):
    def __init__(self, master, skill_id, skill_name, class_level=None, skill_level=None, skill_percent=None):
        super().__init__(master)
        self.title(f"Képzettség hozzárendelése: {skill_name}")
        self.result = None
        tk.Label(self, text=f"Képzettség: {skill_name} ({skill_id})").pack(pady=4)
        frm = tk.Frame(self)
        frm.pack(padx=8, pady=4)
        tk.Label(frm, text="Szint (class_level):").grid(row=0, column=0, sticky="e")
        self.ent_class_level = tk.Entry(frm)
        self.ent_class_level.grid(row=0, column=1)
        if class_level:
            self.ent_class_level.insert(0, str(class_level))
        tk.Label(frm, text="Képzettség szint:").grid(row=1, column=0, sticky="e")
        self.ent_skill_level = tk.Entry(frm)
        self.ent_skill_level.grid(row=1, column=1)
        if skill_level:
            self.ent_skill_level.insert(0, str(skill_level))
        tk.Label(frm, text="Képzettség %:").grid(row=2, column=0, sticky="e")
        self.ent_skill_percent = tk.Entry(frm)
        self.ent_skill_percent.grid(row=2, column=1)
        if skill_percent:
            self.ent_skill_percent.insert(0, str(skill_percent))
        btn_ok = tk.Button(self, text="OK", command=self.on_ok)
        btn_ok.pack(pady=8)
        btn_cancel = tk.Button(self, text="Mégsem", command=self.destroy)
        btn_cancel.pack()

    def on_ok(self):
        try:
            class_level = int(self.ent_class_level.get())
        except ValueError:
            messagebox.showerror("Hiba", "A szint (class_level) kötelező és számnak kell lennie!")
            return
        skill_level = self.ent_skill_level.get()
        skill_percent = self.ent_skill_percent.get()
        skill_level = int(skill_level) if skill_level else None
        skill_percent = int(skill_percent) if skill_percent else None
        self.result = (class_level, skill_level, skill_percent)
        self.destroy()

if __name__ == "__main__":
    app = ClassSkillEditor()
    app.mainloop()