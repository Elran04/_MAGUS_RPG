import tkinter as tk
from utils.reopen_prevention import WindowSingleton

class DescriptionEditorDialog:
    def __init__(self, parent_editor):
        self.parent_editor = parent_editor
        self.win, created = WindowSingleton.get('description_editor', lambda: tk.Toplevel(parent_editor.win))
        if not created:
            return
        self.win.title("Leírások szerkesztése")
        self.win.geometry("900x700")
        tk.Label(self.win, text="Általános leírás:").pack(anchor="w", padx=10, pady=(10,0))
        self.general_desc_text = tk.Text(self.win, wrap=tk.WORD, font=("Consolas", 12), height=6)
        self.general_desc_text.pack(fill=tk.X, padx=10, pady=5)
        self.general_desc_text.insert(tk.END, parent_editor.general_desc)
        tk.Label(self.win, text="Szintenkénti leírások:").pack(anchor="w", padx=10, pady=(10,0))
        self.level_desc_texts = []
        self.level_text_widgets = []
        for i in range(6):
            frame = tk.Frame(self.win)
            frame.pack(fill=tk.X, padx=10, pady=3)
            tk.Label(frame, text=f"{i+1}. szint:", width=10).pack(side=tk.LEFT)
            text = tk.Text(frame, wrap=tk.WORD, font=("Consolas", 11), height=4, width=80)
            text.pack(side=tk.LEFT, fill=tk.X, expand=True)
            desc = parent_editor.level_desc_texts[i] if i < len(parent_editor.level_desc_texts) else ""
            text.insert(tk.END, desc)
            self.level_text_widgets.append(text)
        btn_frame = tk.Frame(self.win)
        btn_frame.pack(fill=tk.X, pady=15)
        save_btn = tk.Button(btn_frame, text="Mentés", command=self.save_and_close, width=18)
        save_btn.pack(side=tk.LEFT, padx=10)
        cancel_btn = tk.Button(btn_frame, text="Mégse", command=self.win.destroy, width=18)
        cancel_btn.pack(side=tk.LEFT, padx=10)
    def save_and_close(self):
        self.parent_editor.general_desc = self.general_desc_text.get("1.0", tk.END).strip()
        for i, text_widget in enumerate(self.level_text_widgets):
            self.parent_editor.level_desc_texts[i] = text_widget.get("1.0", tk.END).strip()
        self.win.destroy()
