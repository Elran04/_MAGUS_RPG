# --- IMPORTOK ÉS KONFIGURÁCIÓ ---
import tkinter as tk


last_character = {}

# --- KARAKTER ADATOK MEGJELENÍTÉSE ---


# --- KÉPZETTSÉG SZERKESZTŐ ABLAK MEGNYITÁSA ---
def open_skill_editor():
    from ui.skills_editor import SkillEditor
    SkillEditor()
# --- FELSZERELÉS SZERKESZTŐ ABLAK MEGNYITÁSA ---
def open_equipment_editor():
    from ui.equipment_editor import EquipmentEditor
    EquipmentEditor()

# --- FŐABLAK ÉS WIDGETEK LÉTREHOZÁSA ---
root = tk.Tk()
root.title("M.A.G.U.S. Szöveges RPG")
root.geometry("800x500")
# --- Egyedi ikon beállítása ---

root.iconbitmap("MAGUS.ico")


# --- Fő szövegterület ---
text_area = tk.Text(root, wrap=tk.WORD, height=18, width=90)
text_area.pack(pady=15)

# --- Gombok elrendezése egy külön frame-ben, egymás alatt ---
button_frame = tk.Frame(root)
button_frame.pack(pady=10)

# 1. sor: Játék indítása
start_button = tk.Button(button_frame, text="Játék indítása", width=30, command=lambda: text_area.insert(tk.END, "\nJáték indítása...\n"))
start_button.grid(row=0, column=0, pady=5)

# 2. sor: Karaktergenerálás
def open_character_creator():
    from ui.character_creator import open_character_creator
    open_character_creator(root, lambda char: None)

create_char_button = tk.Button(button_frame, text="Karaktergenerálás", width=30, command=open_character_creator)
create_char_button.grid(row=1, column=0, pady=5)


# 3. sor: Képzettség szerkesztő
skill_editor_button = tk.Button(button_frame, text="Képzettség szerkesztő", width=30, command=open_skill_editor)
skill_editor_button.grid(row=2, column=0, pady=5)

# 4. sor: Felszerelés szerkesztő (Új)
equipment_editor_button = tk.Button(button_frame, text="Felszerelés szerkesztő", width=30, command=open_equipment_editor)
equipment_editor_button.grid(row=3, column=0, pady=5)

# --- FŐABLAK FUTTATÁSA ---
root.mainloop()
