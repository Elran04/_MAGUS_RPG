import os

from utils.log.logger import get_logger
from utils.data.json_io import save_json, load_json
from config.paths import CHARACTERS_DIR

logger = get_logger(__name__)
CHARACTER_DIR = str(CHARACTERS_DIR)


def save_character(character, filename):
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
    except (OSError, IOError, TypeError) as e:
        logger.error(f"Failed to save character {filename}: {e}")
        return False


def load_character(filename):
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
        return load_json(path, default=None)
    except Exception as e:
        logger.error(f"Failed to load character {filename}: {e}")
        return None
