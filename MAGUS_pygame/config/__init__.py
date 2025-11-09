"""
Configuration package for MAGUS Pygame.
Contains game configuration and centralized path management.
"""

from config.config import *  # noqa: F403
from config.paths import (
    ASSETS_DIR,
    BACKGROUND_SPRITES_DIR,
    BASE_DIR,
    CHARACTER_SPRITES_DIR,
    CHARACTERS_DIR,
    DATA_DIR,
    EQUIPMENT_DATA_DIR,
    GOBLIN_SPRITE,
    GRASS_BACKGROUND,
    HUMANOID_SILHOUETTE,
    LOGS_DIR,
    MENU_BACKGROUND,
    SCENARIOS_DIR,
    WARRIOR_SPRITE,
    get_character_json_path,
    get_character_sprite_path,
    get_equipment_json_path,
    get_scenario_json_path,
    get_ui_asset_path,
)

__all__ = [
    # From config.py
    "WIDTH",
    "HEIGHT",
    "FPS",
    "ActionMode",
    # Paths
    "BASE_DIR",
    "ASSETS_DIR",
    "CHARACTER_SPRITES_DIR",
    "CHARACTERS_DIR",
    "BACKGROUND_SPRITES_DIR",
    "DATA_DIR",
    "SCENARIOS_DIR",
    "LOGS_DIR",
    "MENU_BACKGROUND",
    "HUMANOID_SILHOUETTE",
    "WARRIOR_SPRITE",
    "GOBLIN_SPRITE",
    "GRASS_BACKGROUND",
    "get_character_json_path",
    "get_character_sprite_path",
    "get_ui_asset_path",
    "get_equipment_json_path",
    "get_scenario_json_path",
]
