"""
Configuration constants for the MAGUS pygame game.
"""

# --- WINDOW CONFIG ---
SIDEBAR_WIDTH = 250  # Left action panel width
PLAY_AREA_WIDTH = 1024  # Original play area (battle grid)
WIDTH = SIDEBAR_WIDTH + PLAY_AREA_WIDTH  # Total window width: 1274
HEIGHT = 768

# --- HEX GRID CONFIG ---
HEX_SIZE = 40  # Radius of hex

# --- COLORS ---
BG_COLOR = (30, 30, 40)
HEX_COLOR = (80, 120, 180)
HEX_BORDER = (200, 200, 220)

# --- HOVER / HIGHLIGHT ---
HIGHLIGHT_COLOR = (255, 220, 0)  # yellow border for hovered hex
HIGHLIGHT_BORDER_WIDTH = 4


# --- ACTION MODES ---
class ActionMode:
    """Action mode constants for game state."""

    MOVE = "move"
    ATTACK = "attack"
    CHANGE_FACING = "change_facing"
    CHARGE = "charge"
    CHANGE_WIELD = "change_wield"


# --- GAMEPLAY ---
# Max hexes a unit can move in one action
MOVEMENT_RANGE = 5
ATTACK_RANGE = 1

# Action point costs (in game-seconds, 1 AP = 1 second)
AP_COST_MOVEMENT = 2
AP_COST_FACING = 1  # For future implementation
AP_COST_ATTACK_DAGGER = 5
AP_COST_ATTACK_SWORD = 10
# Default weapon cost for now (will be replaced with actual weapon detection)
AP_COST_ATTACK_DEFAULT = 10

# --- ACTION UI ---
UI_BG = (20, 20, 28)
UI_BORDER = (90, 90, 110)
UI_TEXT = (230, 230, 240)
UI_ACTIVE = (70, 150, 220)
UI_INACTIVE = (60, 60, 80)

# --- REACHABLE / HOVER TINTS (RGBA) ---
# Semi-transparent green fills
REACHABLE_TINT = (60, 200, 130, 80)
HOVER_TINT = (60, 220, 150, 130)
ATTACKABLE_TINT = (220, 80, 60, 100)
CHARGE_AREA_TINT = (255, 255, 0, 70)  # Yellow tint for chargeable area (4+ hexes away)
CHARGE_TINT = (255, 165, 0, 100)  # Orange tint for valid charge targets (enemy)
ENEMY_ZONE_TINT = (200, 50, 50, 60)  # Red tint for enemy zone of control

# --- PATH VISUALIZATION ---
PATH_LINE_COLOR = (100, 200, 255)  # Cyan color for movement path
PATH_LINE_WIDTH = 3
PATH_DOT_COLOR = (150, 220, 255)  # Lighter cyan for path nodes
PATH_DOT_RADIUS = 5
PATH_ZONE_OVERLAP_COLOR = (255, 50, 50)  # Red color for path nodes that overlap with enemy zone
PATH_ZONE_OVERLAP_RADIUS = 8  # Larger radius to highlight danger
