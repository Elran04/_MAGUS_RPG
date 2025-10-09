"""
Character data storage utilities for MAGUS RPG.

This module provides functions for saving and loading character data to/from JSON files.
"""

import json
import os

CHARACTER_DIR = "characters"

def save_character(character, filename):
    """
    Save a character to a JSON file.
    
    Args:
        character (dict): Character data to save
        filename (str): Name of the file to save to
    """
    os.makedirs(CHARACTER_DIR, exist_ok=True)
    path = os.path.join(CHARACTER_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(character, f, ensure_ascii=False, indent=2)

def load_character(filename):
    """
    Load a character from a JSON file.
    
    Args:
        filename (str): Name of the file to load from
        
    Returns:
        dict or None: Character data if found, None otherwise
    """
    path = os.path.join(CHARACTER_DIR, filename)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)