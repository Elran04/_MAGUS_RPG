import os
from typing import Any, cast

from config.paths import CHARACTERS_DIR

from utils.data.json_io import load_json, save_json
from utils.log.logger import get_logger

logger = get_logger(__name__)
CHARACTER_DIR = str(CHARACTERS_DIR)


def save_character(character: dict[str, Any], filename: str) -> bool:
    """Save character data to JSON file.

    Args:
        character: Character data dictionary
        filename: Target filename

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        path = os.path.join(CHARACTER_DIR, filename)
        save_json(path, character)
        logger.info(f"Character saved successfully: {filename}")
        return True
    except (OSError, TypeError) as e:
        logger.error(f"Failed to save character {filename}: {e}")
        return False


def load_character(filename: str) -> dict[str, Any] | None:
    """Load character data from JSON file.

    Args:
        filename: Source filename

    Returns:
        dict: Character data or None if file doesn't exist or is invalid
    """
    path = os.path.join(CHARACTER_DIR, filename)
    if not os.path.exists(path):
        logger.warning(f"Character file not found: {filename}")
        return None

    try:
        raw = load_json(path, default=None)
        if isinstance(raw, dict):
            # Best-effort typing; JSON loader returns Any, guard to dict
            return cast(dict[str, Any], raw)
        return None
    except Exception as e:
        logger.error(f"Failed to load character {filename}: {e}")
        return None
