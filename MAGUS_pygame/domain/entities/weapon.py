"""
Weapon entity for MAGUS combat system.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Weapon:
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

    # Requirements
    strength_required: int = 0
    dexterity_required: int = 0

    # Metadata
    damage_types: list[str] = field(default_factory=list)
    # Attributes that can add damage bonuses (e.g., ["erő", "ügyesség"])
    damage_bonus_attributes: list[str] = field(default_factory=list)
    can_disarm: bool = False
    can_break_weapon: bool = False

    def __str__(self) -> str:
        return f"{self.name} (KÉ+{self.ke_modifier} TÉ+{self.te_modifier} VÉ+{self.ve_modifier})"
