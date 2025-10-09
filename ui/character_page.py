"""
Character page UI for MAGUS RPG.

This module provides a detailed character sheet view with tabs for
general info, stats, skills, and equipment.
"""

def open_character_page(root, character):
    """
    Open a character page window.
    
    Args:
        root: Parent window
        character (dict): Character data to display
    """
    CharacterPage(root, character)


# ui/character_page.py
import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedStyle

class CharacterPage:
    """
    Character sheet display window.
    
    Displays character information in a tabbed interface including:
    - General information
    - Character statistics
    - Skills and abilities
    - Equipment and inventory
    
    Attributes:
        win (tk.Toplevel): Character page window
    """
    def __init__(self, root, character):
        self.win = tk.Toplevel(root)
        self.win.title(f"Karakterlap: {character.get('Név', '')}")
        self.win.geometry("700x600")
        # Apply ttkthemes 'keramik' style to this window
        style = ThemedStyle(self.win)
        style.set_theme("keramik")

        notebook = ttk.Notebook(self.win)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Általános fül
        general_frame = ttk.Frame(notebook)
        notebook.add(general_frame, text="Általános")
        self.populate_general_tab(general_frame, character)

        # Felszerelés fül
        equipment_frame = ttk.Frame(notebook)
        notebook.add(equipment_frame, text="Felszerelés")
        self.populate_equipment_tab(equipment_frame, character)

        # Képzettségek fül
        skills_frame = ttk.Frame(notebook)
        notebook.add(skills_frame, text="Képzettségek")
        self.populate_skills_tab(skills_frame, character)

        # Pszi fül
        pszi_frame = ttk.Frame(notebook)
        notebook.add(pszi_frame, text="Pszi (fejlesztés alatt)")
        ttk.Label(pszi_frame, text="Pszi képességek fejlesztés alatt.", font=("Arial", 12, "italic"), foreground="gray").pack(pady=20)

        # Mágia fül
        magic_frame = ttk.Frame(notebook)
        notebook.add(magic_frame, text="Mágia (fejlesztés alatt)")
        ttk.Label(magic_frame, text="Mágia képességek fejlesztés alatt.", font=("Arial", 12, "italic"), foreground="gray").pack(pady=20)

    def populate_general_tab(self, frame, char):
        # Alapadatok
        lf = ttk.LabelFrame(frame, text="Alapadatok")
        lf.pack(fill=tk.X, padx=10, pady=5)
        for label, key in [
            ("Név", "Név"), ("Kaszt", "Kaszt"), ("Kor", "Kor"), ("Nem", "Nem"), ("Faj", "Faj"), ("Szint", "Szint"), ("Jelenlegi TP", "Tapasztalat")
        ]:
            ttk.Label(lf, text=f"{label}: {char.get(key, '')}", font=("Arial", 11)).pack(anchor="w", padx=5)
        # Következő szint TP
        try:
            from engine.character import get_next_level_xp
            next_xp = get_next_level_xp(char.get("Kaszt", ""), char.get("Tapasztalat", 0))
            ttk.Label(lf, text=f"Következő szint TP: {next_xp}", font=("Arial", 11)).pack(anchor="w", padx=5)
        except Exception:
            pass
        # Tulajdonságok
        lf2 = ttk.LabelFrame(frame, text="Tulajdonságok")
        lf2.pack(fill=tk.X, padx=10, pady=5)
        for stat, value in char.get("Tulajdonságok", {}).items():
            marker = " [✓]" if stat in char.get("Fejleszthető", []) else ""
            ttk.Label(lf2, text=f"{stat}: {value}{marker}", font=("Arial", 10)).pack(anchor="w", padx=5)
        # Harci tulajdonságok
        lf3 = ttk.LabelFrame(frame, text="Harci értékek")
        lf3.pack(fill=tk.X, padx=10, pady=5)
        for key, value in char.get("Harci értékek", {}).items():
            if key == "HM/szint":
                ttk.Label(lf3, text=f"Harci Módosítók / szint: {value['total']}, Kötelező: {value['mandatory']}", font=("Arial", 10)).pack(anchor="w", padx=5)
            else:
                ttk.Label(lf3, text=f"{key}: {value}", font=("Arial", 10)).pack(anchor="w", padx=5)
        # ÉP/FP
        lf4 = ttk.LabelFrame(frame, text="ÉP / FP")
        lf4.pack(fill=tk.X, padx=10, pady=5)
        ep = char.get("Harci értékek", {}).get("ÉP", "-")
        fp = char.get("Harci értékek", {}).get("FP", "-")
        ttk.Label(lf4, text=f"ÉP: {ep}", font=("Arial", 11)).pack(anchor="w", padx=5)
        ttk.Label(lf4, text=f"FP: {fp}", font=("Arial", 11)).pack(anchor="w", padx=5)

    def populate_equipment_tab(self, frame, char):
        lf = ttk.LabelFrame(frame, text="Felszerelés")
        lf.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        eq = char.get("Felszerelés", [])
        if not eq:
            ttk.Label(lf, text="Nincs felszerelés.", font=("Arial", 10, "italic"), foreground="gray").pack(pady=10)
        else:
            for item in eq:
                ttk.Label(lf, text=str(item), font=("Arial", 10)).pack(anchor="w", padx=5)
        # Pénz (ha van)
        if "Pénz" in char:
            ttk.Label(lf, text=f"Pénz: {char['Pénz']}", font=("Arial", 10, "bold"), foreground="darkgreen").pack(anchor="w", padx=5, pady=5)

    def populate_skills_tab(self, frame, char):
        lf = ttk.LabelFrame(frame, text="Képzettségek")
        lf.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        skills = char.get("Képzettségek", [])
        if not skills:
            ttk.Label(lf, text="Nincs képzettség.", font=("Arial", 10, "italic"), foreground="gray").pack(pady=10)
        else:
            for skill in skills:
                ttk.Label(lf, text=str(skill), font=("Arial", 10)).pack(anchor="w", padx=5)
