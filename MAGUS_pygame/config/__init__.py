"""
Configuration package for MAGUS Pygame.
Contains game configuration and centralized path management.
"""

# Explicit imports from config.py
from config.config import (
    WIDTH,
    HEIGHT,
    HEX_SIZE,
    BG_COLOR,
    HEX_COLOR,
    HEX_BORDER,
    HIGHLIGHT_COLOR,
    HIGHLIGHT_BORDER_WIDTH,
    ActionMode,
    MOVEMENT_RANGE,
    ATTACK_RANGE,
    AP_COST_MOVEMENT,
    AP_COST_FACING,
    AP_COST_ATTACK_DAGGER,
    AP_COST_ATTACK_SWORD,
    AP_COST_ATTACK_DEFAULT,
    UI_BG,
    UI_BORDER,
    UI_TEXT,
    UI_ACTIVE,
    UI_INACTIVE,
    REACHABLE_TINT,
    HOVER_TINT,
    ATTACKABLE_TINT,
    CHARGE_AREA_TINT,
    CHARGE_TINT,
    ENEMY_ZONE_TINT,
    PATH_LINE_COLOR,
    PATH_LINE_WIDTH,
    PATH_DOT_COLOR,
    PATH_DOT_RADIUS,
    PATH_ZONE_OVERLAP_COLOR,
    PATH_ZONE_OVERLAP_RADIUS,
)

# Explicit imports from paths.py
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
    DEJAVU_FONT_PATH,
    get_character_json_path,
    get_character_sprite_path,
    get_equipment_json_path,
    get_scenario_json_path,
    get_ui_asset_path,
)

__all__ = [
    # Display & Grid Configuration
    "WIDTH",
    "HEIGHT",
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
]
