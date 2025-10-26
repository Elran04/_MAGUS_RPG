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

# --- GAMEPLAY ---
# Max hexes a unit can move in one action
MOVEMENT_RANGE = 5
ATTACK_RANGE = 1

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
