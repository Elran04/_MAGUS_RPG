"""
Configuration package for MAGUS Pygame.
Contains game configuration and centralized path management.
"""

# Explicit imports from config.py
from config.config import (
    AP_COST_ATTACK_DAGGER,
    AP_COST_ATTACK_DEFAULT,
    AP_COST_ATTACK_SWORD,
    AP_COST_FACING,
    AP_COST_MOVEMENT,
    ATTACK_RANGE,
    ATTACKABLE_TINT,
    BG_COLOR,
    CHARGE_AREA_TINT,
    CHARGE_TINT,
    ENEMY_ZONE_TINT,
    HEIGHT,
    HEX_BORDER,
    HEX_COLOR,
    HEX_SIZE,
    HIGHLIGHT_BORDER_WIDTH,
    HIGHLIGHT_COLOR,
    HOVER_TINT,
    MOVEMENT_RANGE,
    PATH_DOT_COLOR,
    PATH_DOT_RADIUS,
    PATH_LINE_COLOR,
    PATH_LINE_WIDTH,
    PATH_ZONE_OVERLAP_COLOR,
    PATH_ZONE_OVERLAP_RADIUS,
    PLAY_AREA_WIDTH,
    REACHABLE_TINT,
    SIDEBAR_WIDTH,
    UI_ACTIVE,
    UI_BG,
    UI_BORDER,
    UI_INACTIVE,
    UI_TEXT,
    WIDTH,
    ActionMode,
)

# Explicit imports from paths.py
from config.paths import (
    ASSETS_DIR,
    BACKGROUND_SPRITES_DIR,
    BASE_DIR,
    CHARACTER_SPRITES_DIR,
    CHARACTERS_DIR,
    DATA_DIR,
    DEJAVU_FONT_PATH,
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

# Font utilities
from utils.font_manager import load_font

__all__ = [
    # Display & Grid Configuration
    "WIDTH",
    "HEIGHT",
    "SIDEBAR_WIDTH",
    "PLAY_AREA_WIDTH",
    "HEX_SIZE",
    # Colors
    "BG_COLOR",
    "HEX_COLOR",
    "HEX_BORDER",
    "HIGHLIGHT_COLOR",
    "HIGHLIGHT_BORDER_WIDTH",
    # Game Modes
    "ActionMode",
    # Gameplay Constants
    "MOVEMENT_RANGE",
    "ATTACK_RANGE",
    # Action Costs
    "AP_COST_MOVEMENT",
    "AP_COST_FACING",
    "AP_COST_ATTACK_DAGGER",
    "AP_COST_ATTACK_SWORD",
    "AP_COST_ATTACK_DEFAULT",
    # UI Colors
    "UI_BG",
    "UI_BORDER",
    "UI_TEXT",
    "UI_ACTIVE",
    "UI_INACTIVE",
    # Visual Tints
    "REACHABLE_TINT",
    "HOVER_TINT",
    "ATTACKABLE_TINT",
    "CHARGE_AREA_TINT",
    "CHARGE_TINT",
    "ENEMY_ZONE_TINT",
    # Path Visualization
    "PATH_LINE_COLOR",
    "PATH_LINE_WIDTH",
    "PATH_DOT_COLOR",
    "PATH_DOT_RADIUS",
    "PATH_ZONE_OVERLAP_COLOR",
    "PATH_ZONE_OVERLAP_RADIUS",
    # Directory Paths
    "BASE_DIR",
    "ASSETS_DIR",
    "CHARACTER_SPRITES_DIR",
    "CHARACTERS_DIR",
    "BACKGROUND_SPRITES_DIR",
    "DATA_DIR",
    "SCENARIOS_DIR",
    "EQUIPMENT_DATA_DIR",
    "LOGS_DIR",
    # Asset Paths
    "MENU_BACKGROUND",
    "HUMANOID_SILHOUETTE",
    "WARRIOR_SPRITE",
    "GOBLIN_SPRITE",
    "GRASS_BACKGROUND",
    "DEJAVU_FONT_PATH",
    # Path Helper Functions
    "get_character_json_path",
    "get_character_sprite_path",
    "get_ui_asset_path",
    "get_equipment_json_path",
    "get_scenario_json_path",
    # Font Utilities
    "load_font",
]
