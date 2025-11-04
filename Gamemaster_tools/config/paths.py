"""
Central path configuration for the Gamemaster Tools application.
All file and directory paths should be defined here to avoid hardcoding throughout the codebase.
"""

from pathlib import Path

# Base directory - root of the Gamemaster_tools module
BASE_DIR = Path(__file__).parent.parent.absolute()
# Project root directory (repository root)
PROJECT_ROOT = BASE_DIR.parent

# ============================================================================
# DATA DIRECTORIES
# ============================================================================

# Main data directory
DATA_DIR = BASE_DIR / "data"

# Equipment data
EQUIPMENT_DIR = DATA_DIR / "equipment"
ARMOR_JSON = EQUIPMENT_DIR / "armor.json"
WEAPONS_SHIELDS_JSON = EQUIPMENT_DIR / "weapons_and_shields.json"
GENERAL_EQUIPMENT_JSON = EQUIPMENT_DIR / "general_equipment.json"

# Skills data
SKILLS_DIR = DATA_DIR / "skills"
SKILLS_DB = SKILLS_DIR / "skills_data.db"
SKILLS_DESCRIPTIONS_DIR = SKILLS_DIR / "descriptions"

# Classes data
CLASSES_DIR = DATA_DIR / "classes"
CLASSES_DB = CLASSES_DIR / "class_data.db"
CLASSES_DESCRIPTIONS_DIR = CLASSES_DIR / "descriptions"

# Races data
RACES_DIR = DATA_DIR / "races"
RACES_DESCRIPTIONS_DIR = RACES_DIR / "descriptions"
SPECIAL_ABILITIES_JSON = RACES_DIR / "special_abilities.json"

# ============================================================================
# CHARACTER DATA
# ============================================================================

# Character storage directory (user-created characters)
# Store characters at the repository root: <repo>/characters
CHARACTERS_DIR = PROJECT_ROOT / "characters"

# ============================================================================
# ASSETS
# ============================================================================

# Assets directory
ASSETS_DIR = BASE_DIR / "assets"
ICONS_DIR = ASSETS_DIR / "icons"

# ============================================================================
# CONFIG
# ============================================================================

# Config directory
CONFIG_DIR = BASE_DIR / "config"
SETTINGS_JSON = CONFIG_DIR / "settings.json"

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def ensure_directories() -> None:
    """Create all necessary directories if they don't exist."""
    directories = [
        DATA_DIR,
        EQUIPMENT_DIR,
        SKILLS_DIR,
        SKILLS_DESCRIPTIONS_DIR,
        CLASSES_DIR,
        CLASSES_DESCRIPTIONS_DIR,
        RACES_DIR,
        RACES_DESCRIPTIONS_DIR,
        CHARACTERS_DIR,
        ASSETS_DIR,
        ICONS_DIR,
        CONFIG_DIR,
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def get_relative_path(path: Path) -> str:
    """
    Get a path relative to BASE_DIR as a string.

    Args:
        path: Absolute Path object

    Returns:
        Relative path as string
    """
    try:
        return str(path.relative_to(BASE_DIR))
    except ValueError:
        # If path is not relative to BASE_DIR, return absolute path
        return str(path)


# Legacy compatibility - provide string versions for older code
def get_str_paths() -> dict[str, str]:
    """
    Returns a dictionary of all paths as strings for backward compatibility.
    Use Path objects directly in new code.
    """
    return {
        "BASE_DIR": str(BASE_DIR),
        "PROJECT_ROOT": str(PROJECT_ROOT),
        "DATA_DIR": str(DATA_DIR),
        "EQUIPMENT_DIR": str(EQUIPMENT_DIR),
        "ARMOR_JSON": str(ARMOR_JSON),
        "WEAPONS_SHIELDS_JSON": str(WEAPONS_SHIELDS_JSON),
        "GENERAL_EQUIPMENT_JSON": str(GENERAL_EQUIPMENT_JSON),
        "SKILLS_DIR": str(SKILLS_DIR),
        "SKILLS_DB": str(SKILLS_DB),
        "SKILLS_DESCRIPTIONS_DIR": str(SKILLS_DESCRIPTIONS_DIR),
        "CLASSES_DIR": str(CLASSES_DIR),
        "CLASSES_DB": str(CLASSES_DB),
        "CLASSES_DESCRIPTIONS_DIR": str(CLASSES_DESCRIPTIONS_DIR),
        "RACES_DIR": str(RACES_DIR),
        "RACES_DESCRIPTIONS_DIR": str(RACES_DESCRIPTIONS_DIR),
        "SPECIAL_ABILITIES_JSON": str(SPECIAL_ABILITIES_JSON),
        "CHARACTERS_DIR": str(CHARACTERS_DIR),
        "ASSETS_DIR": str(ASSETS_DIR),
        "ICONS_DIR": str(ICONS_DIR),
        "CONFIG_DIR": str(CONFIG_DIR),
        "SETTINGS_JSON": str(SETTINGS_JSON),
    }


# Initialize directories on module import
ensure_directories()
