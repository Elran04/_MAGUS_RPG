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
        self.attributes = {}  # Character attributes (Tulajdonságok)
        self.weapon = {}  # Equipped weapon data
        self.base_combat = {}  # Base combat values before weapon modifiers
        
        # Action points (10 per turn by default, representing 10 seconds)
        self.max_action_points = 10
        self.current_action_points = 10
        
        # Facing direction (0-5 for hex directions, 0 = north/top)
        # 0 = N, 1 = NE, 2 = SE, 3 = S, 4 = SW, 5 = NW
        self.facing = 0
        
        # Combat state (current HP/FP)
        self.current_ep = 0
        self.current_fp = 0
        
        # Zone of Control - opportunity attack tracking
        self.has_used_opportunity_attack = False
    
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
        """Initiative (base + weapon bonus)"""
        base = int(self.combat.get("KÉ", 0))
        weapon_bonus = int(self.weapon.get("KE", 0))
        return base + weapon_bonus

    @property
    def TE(self) -> int:
        """Attack value (base + weapon bonus)"""
        base = int(self.combat.get("TÉ", 0))
        weapon_bonus = int(self.weapon.get("TE", 0))
        return base + weapon_bonus

    @property
    def VE(self) -> int:
        """Defense value (base + weapon bonus)"""
        base = int(self.combat.get("VÉ", 0))
        weapon_bonus = int(self.weapon.get("VE", 0))
        return base + weapon_bonus

    @property
    def CE(self) -> int:
        """Ranged attack value (base + weapon bonus)"""
        base = int(self.combat.get("CÉ", 0))
        weapon_bonus = int(self.weapon.get("CE", 0))
        return base + weapon_bonus

    # Attribute getters (Tulajdonságok)
    @property
    def Ero(self) -> int:
        """Erő (Strength)"""
        return int(self.attributes.get("Erő", 10))

    @property
    def Gyorsasag(self) -> int:
        """Gyorsaság (Speed)"""
        return int(self.attributes.get("Gyorsaság", 10))

    @property
    def Ugyesseg(self) -> int:
        """Ügyesség (Dexterity)"""
        return int(self.attributes.get("Ügyesség", 10))

    @property
    def Allokepesseg(self) -> int:
        """Állóképesség (Endurance)"""
        return int(self.attributes.get("Állóképesség", 10))

    @property
    def Karizma(self) -> int:
        """Karizma (Charisma)"""
        return int(self.attributes.get("Karizma", 10))

    @property
    def Egeszseg(self) -> int:
        """Egészség (Health)"""
        return int(self.attributes.get("Egészség", 10))

    @property
    def Intelligencia(self) -> int:
        """Intelligencia (Intelligence)"""
        return int(self.attributes.get("Intelligencia", 10))

    @property
    def Akaratero(self) -> int:
        """Akaraterő (Willpower)"""
        return int(self.attributes.get("Akaraterő", 10))

    @property
    def Asztral(self) -> int:
        """Asztrál (Astral)"""
        return int(self.attributes.get("Asztrál", 10))

    @property
    def Erzekeles(self) -> int:
        """Érzékelés (Perception)"""
        return int(self.attributes.get("Érzékelés", 10))

    def set_attributes(self, attributes: dict):
        """Set character attributes (Tulajdonságok) from JSON."""
        self.attributes = attributes or {}

    def set_weapon(self, weapon_stats: dict):
        """Set equipped weapon data.
        
        Args:
            weapon_stats: Dictionary with weapon combat stats (KE, TE, VE, damage, etc.)
        """
        self.weapon = weapon_stats or {}

    # Weapon-specific properties (class-level)
    @property
    def attack_time(self) -> int:
        """AP cost of attack (from weapon)"""
        return int(self.weapon.get("attack_time", 10))

    @property
    def damage_min(self) -> int:
        """Minimum weapon damage"""
        return int(self.weapon.get("damage_min", 1))

    @property
    def damage_max(self) -> int:
        """Maximum weapon damage"""
        return int(self.weapon.get("damage_max", 6))

    @property
    def stp(self) -> int:
        """Weapon structure points"""
        return int(self.weapon.get("stp", 10))

    @property
    def armor_penetration(self) -> int:
        """Armor penetration value"""
        return int(self.weapon.get("armor_penetration", 0))

    @property
    def can_disarm(self) -> bool:
        """Whether weapon can disarm"""
        return bool(self.weapon.get("can_disarm", False))

    @property
    def can_break_weapon(self) -> bool:
        """Whether weapon can break other weapons"""
        return bool(self.weapon.get("can_break_weapon", False))

    @property
    def damage_types(self) -> list:
        """List of damage types (szúró, vágó, zúzó)"""
        return self.weapon.get("damage_types", [])

    @property
    def damage_bonus_attributes(self) -> list:
        """List of attributes that give damage bonuses (erő, ügyesség)"""
        return self.weapon.get("damage_bonus_attributes", [])

    @property
    def size_category(self) -> int:
        """Weapon size category (determines attackable squares)"""
        return int(self.weapon.get("size_category", 1))

    @property
    def wield_mode(self) -> str:
        """Weapon wield mode (Egykezes, Kétkezes, Változó)"""
        return self.weapon.get("wield_mode", "Egykezes")

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
