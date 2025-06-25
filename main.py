# main.py

import tkinter as tk
from ui.character_creator import open_character_creator

def display_character(char):
    text_area.insert(tk.END, f"\nKarakter létrehozva:\n")
    text_area.insert(tk.END, f"Név: {char['Név']}\nNem: {char['Nem']}\nKor: {char['Kor']}\n")
    text_area.insert(tk.END, f"Faj: {char['Faj']}\nKaszt: {char['Kaszt']}\n")
    text_area.insert(tk.END, "Tulajdonságok:\n")
    for stat, value in char["Tulajdonságok"].items():
        marker = " [✓]" if stat in char.get("Fejleszthető", []) else ""
        text_area.insert(tk.END, f"  {stat}: {value}{marker}\n")
    text_area.insert(tk.END, "-" * 40 + "\n")

root = tk.Tk()
root.title("M.A.G.U.S. Szöveges RPG")
root.geometry("600x400")

text_area = tk.Text(root, wrap=tk.WORD, height=20, width=70)
text_area.pack(pady=10)

start_button = tk.Button(root, text="Játék indítása", command=lambda: text_area.insert(tk.END, "\nJáték indítása...\n"))
start_button.pack(side=tk.LEFT, padx=10)

create_char_button = tk.Button(root, text="Karaktergenerálás", command=lambda: open_character_creator(root, display_character))
create_char_button.pack(side=tk.LEFT, padx=10)

root.mainloop()
