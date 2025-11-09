"""
Centralized path management for MAGUS Pygame.
All file and directory paths are defined here for easy maintenance.
"""

from pathlib import Path

# Base directory - MAGUS_pygame root
BASE_DIR = Path(__file__).parent.parent

# Asset directories
ASSETS_DIR = BASE_DIR / "assets"
SPRITES_DIR = ASSETS_DIR / "sprites"
CHARACTER_SPRITES_DIR = SPRITES_DIR / "characters"
BACKGROUND_SPRITES_DIR = SPRITES_DIR / "backgrounds"
UI_SPRITES_DIR = SPRITES_DIR / "ui"
TILESETS_DIR = ASSETS_DIR / "tilesets"

# Data directories
DATA_DIR = BASE_DIR / "data"
CHARACTERS_DIR = BASE_DIR.parent / "characters"  # Goes up to _MAGUS_RPG/characters
GAMEMASTER_DATA_DIR = (
    BASE_DIR.parent / "Gamemaster_tools" / "data"
)  # Goes up to _MAGUS_RPG/Gamemaster_tools/data
EQUIPMENT_DATA_DIR = GAMEMASTER_DATA_DIR / "equipment"
SCENARIOS_DIR = DATA_DIR / "scenarios"

# Logs directory
LOGS_DIR = BASE_DIR / "logger" / "logs"

# Specific asset paths
MENU_BACKGROUND = ASSETS_DIR / "ui" / "MAGUS.png"
HUMANOID_SILHOUETTE = CHARACTER_SPRITES_DIR / "humanoid_silhouette.png"
WARRIOR_SPRITE = CHARACTER_SPRITES_DIR / "warrior.png"
GOBLIN_SPRITE = CHARACTER_SPRITES_DIR / "goblin.png"
GRASS_BACKGROUND = BACKGROUND_SPRITES_DIR / "grass_bg.jpg"  # TODO: Move to backgrounds


def get_character_json_path(filename: str) -> Path:
    """Get path to a character JSON file.

    Args:
        filename: Name of the character file (e.g., "Teszt.json")

    Returns:
        Full path to the character file
    """
    return CHARACTERS_DIR / filename


def get_character_sprite_path(filename: str) -> Path:
    """Get path to a character sprite.

    Args:
        filename: Name of the sprite file (e.g., "warrior.png")

    Returns:
        Full path to the sprite file
    """
    return CHARACTER_SPRITES_DIR / filename


def get_ui_asset_path(filename: str) -> Path:
    """Get path to a UI asset.

    Args:
        filename: Name of the UI asset file

    Returns:
        Full path to the asset file
    """
    return UI_SPRITES_DIR / filename


def get_equipment_json_path(filename: str) -> Path:
    """Get path to an equipment JSON file.

    Args:
        filename: Name of the equipment file (e.g., "weapons_and_shields.json")

    Returns:
        Full path to the equipment file
    """
    return EQUIPMENT_DATA_DIR / filename


def get_scenario_json_path(filename: str) -> Path:
    """Get path to a scenario JSON file.

    Args:
        filename: Name of the scenario file (e.g., "default.json")

    Returns:
        Full path to the scenario file
    """
    return SCENARIOS_DIR / filename


def ensure_dir_exists(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path to ensure exists
    """
    path.mkdir(parents=True, exist_ok=True)


# Ensure critical directories exist
ensure_dir_exists(LOGS_DIR)
ensure_dir_exists(CHARACTER_SPRITES_DIR)
ensure_dir_exists(DATA_DIR)
ensure_dir_exists(SCENARIOS_DIR)
