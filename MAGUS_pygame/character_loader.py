"""
Character JSON loader for MAGUS_pygame.
Loads character sheets from the repository-level 'characters' folder
and returns parsed dictionaries.
"""
import json
import os
from typing import Any, Dict


def repo_root() -> str:
    # MAGUS_pygame directory -> parent is repo root
    return os.path.dirname(os.path.dirname(__file__))


def load_character_json(filename: str) -> Dict[str, Any]:
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
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
