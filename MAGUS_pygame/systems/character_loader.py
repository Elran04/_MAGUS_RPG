"""
Character JSON loader for MAGUS_pygame.
Loads character sheets from the repository-level 'characters' folder
and returns parsed dictionaries.
"""

import json
from typing import Any
from config import get_character_json_path


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
    path = get_character_json_path(filename)
    with open(path, encoding="utf-8") as f:
        return json.load(f)
