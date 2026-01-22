"""
Weapon entity for MAGUS combat system.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Weapon:
    def set_wield_state(self, main_hand: bool, off_hand_equipped: bool) -> None:
        """
        Set current wield state for variable wield mode weapons.
        If equipped in main hand and no off-hand weapon, set to two-handed.
        If off-hand weapon is equipped, set to one-handed.
        Only applies if wield_mode is 'variable'.
        """
        if self.wield_mode == "variable":
            if main_hand and not off_hand_equipped:
                self.current_wield_state = "two_handed"
            elif main_hand and off_hand_equipped:
                self.current_wield_state = "one_handed"
            else:
                self.current_wield_state = None

    """Weapon definition with combat modifiers."""

    id: str
    name: str

    # Combat modifiers
    ke_modifier: int = 0
    te_modifier: int = 0
    ve_modifier: int = 0

    # Damage
    damage_dice: str = "1d6"  # e.g., "2d6+3"
    damage_min: int = 1
    damage_max: int = 6

    # Special properties
    armor_penetration: int = 0
    attack_time: int = 5  # Initiative cost
    size_category: int = 1
    wield_mode: str = "one_handed"  # one_handed, two_handed, dual

    # For variable wield mode weapons, track current state
    current_wield_state: str = None  # None, "one_handed", "two_handed"

    # Requirements
    strength_required: int = 0
    dexterity_required: int = 0

    # Metadata
    damage_types: list[str] = field(default_factory=list)
    # Attributes that can add damage bonuses (e.g., ["erő", "ügyesség"])
    damage_bonus_attributes: list[str] = field(default_factory=list)
    can_disarm: bool = False
    can_break_weapon: bool = False

    # Weapon classification for skill lookups
    category: str = ""  # e.g., "Hosszú kardok"
    skill_id: str = ""  # e.g., "weaponskill_longswords" (derived from category)

    def __str__(self) -> str:
        return f"{self.name} (KÉ+{self.ke_modifier} TÉ+{self.te_modifier} VÉ+{self.ve_modifier})"
