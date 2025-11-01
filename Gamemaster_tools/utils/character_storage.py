import json
import os

from utils.logger import get_logger

logger = get_logger(__name__)
CHARACTER_DIR = "characters"


def save_character(character, filename):
    """Save character data to JSON file.
    
    Args:
        character: Character data dictionary
        filename: Target filename
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        os.makedirs(CHARACTER_DIR, exist_ok=True)
        path = os.path.join(CHARACTER_DIR, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(character, f, ensure_ascii=False, indent=2)
        logger.info(f"Character saved successfully: {filename}")
        return True
    except (OSError, IOError) as e:
        logger.error(f"Failed to save character {filename}: {e}")
        return False
    except TypeError as e:
        logger.error(f"Invalid character data for {filename}: {e}")
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
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {filename}: {e}")
        return None
    except (OSError, IOError) as e:
        logger.error(f"Failed to load character {filename}: {e}")
        return None
