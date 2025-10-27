"""
Configuration constants for the MAGUS pygame game.
"""

# --- WINDOW CONFIG ---
WIDTH = 1024
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
ENEMY_ZONE_TINT = (200, 50, 50, 60)  # Red tint for enemy zone of control
