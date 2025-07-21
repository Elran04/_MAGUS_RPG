# --- IMPORTOK ÉS KONFIGURÁCIÓ ---
import tkinter as tk
from tkinter import simpledialog, messagebox
from ui.character_creator import open_character_creator
from utils.storage import save_character, load_character
import subprocess
import sys

last_character = {}

# --- KARAKTER ADATOK MEGJELENÍTÉSE ---
def display_character(char):
    global last_character
    last_character = char
    text_area.insert(tk.END, f"\nKarakter létrehozva:\n")
    text_area.insert(tk.END, f"Név: {char['Név']}\nNem: {char['Nem']}\nKor: {char['Kor']}\n")
    text_area.insert(tk.END, f"Faj: {char['Faj']}\nKaszt: {char['Kaszt']}\n")

    text_area.insert(tk.END, "Tulajdonságok:\n")
    for stat, value in char["Tulajdonságok"].items():
        marker = " [✓]" if stat in char.get("Fejleszthető", []) else ""
        text_area.insert(tk.END, f"  {stat}: {value}{marker}\n")

    text_area.insert(tk.END, "\nHarci értékek:\n")
    for key, value in char.get("Harci értékek", {}).items():
        if key == "HM/szint":
            text_area.insert(tk.END, f"  Harci Módosítók / szint: {value['total']}, Kötelező: {value['mandatory']}\n")
        else:
            text_area.insert(tk.END, f"  {key}: {value}\n")

    text_area.insert(tk.END, "\nKépzettségpontok:\n")
    kp = char.get("Képzettségpontok", {})
    text_area.insert(tk.END, f"  Alap: {kp.get('Alap', 0)}\n")
    text_area.insert(tk.END, f"  Szintenként: {kp.get('Szintenként', 0)}\n")
    text_area.insert(tk.END, "-" * 40 + "\n")

# --- KARAKTER MENTÉSE ---
def save_last_character():
    if not last_character:
        messagebox.showinfo("Mentés", "Nincs menthető karakter.")
        return
    # Alapértelmezett fájlnév a karakter neve (szóközök helyett _)
    default_name = last_character.get("Név", "karakter").replace(" ", "_")
    filename = simpledialog.askstring("Mentés", "Fájlnév:", initialvalue=default_name)
    if filename:
        if not filename.lower().endswith(".json"):
            filename += ".json"
        save_character(last_character, filename)
        messagebox.showinfo("Mentés", f"Sikeres mentés: {filename}")

# --- KARAKTER BETÖLTÉSE ---
def load_character_dialog():
    import os
    from utils.storage import CHARACTER_DIR

    if not os.path.exists(CHARACTER_DIR):
        messagebox.showinfo("Betöltés", "Nincs elérhető karakter.")
        return
    files = [f for f in os.listdir(CHARACTER_DIR) if f.endswith(".json")]
    if not files:
        messagebox.showinfo("Betöltés", "Nincs elérhető karakter.")
        return

    dialog = tk.Toplevel(root)
    dialog.title("Karakter betöltése")
    tk.Label(dialog, text="Válassz karaktert:").pack(pady=5)

    listbox = tk.Listbox(dialog, height=10, width=40)
    for f in files:
        listbox.insert(tk.END, f)
    listbox.pack(pady=5)

    def do_load():
        selection = listbox.curselection()
        if not selection:
            messagebox.showwarning("Betöltés", "Nincs kiválasztva karakter.")
            return
        filename = files[selection[0]]
        char = load_character(filename)
        if char:
            display_character(char)
            messagebox.showinfo("Betöltés", f"Sikeres betöltés: {filename}")
            dialog.destroy()
        else:
            messagebox.showerror("Betöltés", "Nem található ilyen karakterfájl.")

    listbox.bind('<Double-1>', lambda event: do_load())
    tk.Button(dialog, text="Betöltés", command=do_load).pack(pady=10)

# --- KÉPZETTSÉG SZERKESZTŐ ABLAK MEGNYITÁSA ---
def open_skill_editor():
    subprocess.Popen([sys.executable, "-m", "ui.skills_editor"])
# --- FELSZERELÉS SZERKESZTŐ ABLAK MEGNYITÁSA ---
def open_equipment_editor():
    subprocess.Popen([sys.executable, "-m", "ui.equipment_editor"])

# --- FŐABLAK ÉS WIDGETEK LÉTREHOZÁSA ---
root = tk.Tk()
root.title("M.A.G.U.S. Szöveges RPG")
root.geometry("800x500")

# --- Fő szövegterület ---
text_area = tk.Text(root, wrap=tk.WORD, height=18, width=90)
text_area.pack(pady=15)

# --- Gombok elrendezése egy külön frame-ben, egymás alatt ---
button_frame = tk.Frame(root)
button_frame.pack(pady=10)

# 1. sor: Játék indítása
start_button = tk.Button(button_frame, text="Játék indítása", width=30, command=lambda: text_area.insert(tk.END, "\nJáték indítása...\n"))
start_button.grid(row=0, column=0, pady=5)

# 2. sor: Karaktergenerálás, Mentés, Betöltés
char_frame = tk.Frame(button_frame)
char_frame.grid(row=1, column=0, pady=5)
create_char_button = tk.Button(char_frame, text="Karaktergenerálás", width=20, command=lambda: open_character_creator(root, display_character))
create_char_button.pack(side=tk.LEFT, padx=5)
save_button = tk.Button(char_frame, text="Mentés", width=12, command=save_last_character)
save_button.pack(side=tk.LEFT, padx=5)
load_button = tk.Button(char_frame, text="Betöltés", width=12, command=load_character_dialog)
load_button.pack(side=tk.LEFT, padx=5)

# 3. sor: Képzettség szerkesztő
skill_editor_button = tk.Button(button_frame, text="Képzettség szerkesztő", width=30, command=open_skill_editor)
skill_editor_button.grid(row=2, column=0, pady=5)

# 4. sor: Felszerelés szerkesztő (Új)
equipment_editor_button = tk.Button(button_frame, text="Felszerelés szerkesztő", width=30, command=open_equipment_editor)
equipment_editor_button.grid(row=3, column=0, pady=5)

# --- FŐABLAK FUTTATÁSA ---
root.mainloop()
