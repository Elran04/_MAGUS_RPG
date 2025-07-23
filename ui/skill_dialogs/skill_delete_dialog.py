import tkinter as tk

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
