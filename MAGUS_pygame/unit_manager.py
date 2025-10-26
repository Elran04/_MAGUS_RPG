"""
Unit management: Unit class and combat/stat logic.
"""


class Unit:
    """Represents a game unit with combat stats, position, and action points."""
    
    def __init__(self, q, r, sprite, name: str | None = None, combat: dict | None = None):
        """
        Initialize a unit.
        
        Args:
            q, r: hex coordinates
            sprite: pygame.Surface for the unit's sprite
            name: optional display name
            combat: optional dict of combat values (e.g., from character JSON 'Harci értékek')
        """
        self.q = q
        self.r = r
        self.sprite = sprite
        self.name = name or ""
        self.combat = combat or {}
        
        # Action points (10 per turn by default, representing 10 seconds)
        self.max_action_points = 10
        self.current_action_points = 10
        
        # Facing direction (0-5 for hex directions, 0 = north/top)
        # 0 = N, 1 = NE, 2 = SE, 3 = S, 4 = SW, 5 = NW
        self.facing = 0
        
        # Combat state (current HP/FP)
        self.current_ep = 0
        self.current_fp = 0
    
    def move_to(self, q, r):
        """Move the unit to a new hex."""
        self.q = q
        self.r = r
    
    def get_position(self):
        """Get the unit's current hex position."""
        return (self.q, self.r)

    # Convenience getters for common combat values (fallback to 0)
    @property
    def FP(self) -> int:
        return int(self.combat.get("FP", 0))

    @property
    def EP(self) -> int:
        return int(self.combat.get("ÉP", 0))

    @property
    def KE(self) -> int:
        return int(self.combat.get("KÉ", 0))

    @property
    def TE(self) -> int:
        return int(self.combat.get("TÉ", 0))

    @property
    def VE(self) -> int:
        return int(self.combat.get("VÉ", 0))

    @property
    def CE(self) -> int:
        return int(self.combat.get("CÉ", 0))

    def set_combat(self, combat: dict):
        """Set combat stats and initialize current EP/FP to max values."""
        self.combat = combat or {}
        # Initialize current EP to max EP
        try:
            self.current_ep = int(self.combat.get("ÉP", 0))
        except Exception:
            self.current_ep = 0
        # Initialize current FP to max FP
        try:
            self.current_fp = int(self.combat.get("FP", 0))
        except Exception:
            self.current_fp = 0
