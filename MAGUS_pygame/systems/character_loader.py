"""
Character JSON loader for MAGUS_pygame.
Loads character sheets from the repository-level 'characters' folder
and returns parsed dictionaries.
"""

import json
import os
from typing import Any


def repo_root() -> str:
    # __file__ is in systems/ folder -> parent is MAGUS_pygame -> parent is repo root
    magus_pygame_dir = os.path.dirname(os.path.dirname(__file__))
    return os.path.dirname(magus_pygame_dir)


def load_character_json(filename: str) -> dict[str, Any]:
    """Load a character JSON by filename from the repo's characters folder.

    Args:
        filename: e.g., 'Teszt.json'
    Returns:
        Parsed JSON dict.
    Raises:
        FileNotFoundError if the file doesn't exist.
        json.JSONDecodeError if invalid JSON.
    """
    path = os.path.join(repo_root(), "characters", filename)
    with open(path, encoding="utf-8") as f:
        return json.load(f)
