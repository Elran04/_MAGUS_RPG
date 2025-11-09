"""
Domain Entities - Core business objects with identity.
"""

from dataclasses import dataclass, field
from typing import Optional
import pygame

from domain.value_objects import Position, CombatStats, ResourcePool, Attributes, Facing
from domain.mechanics.armor import ArmorSystem


@dataclass
class Unit:
    """
    A combat unit on the battlefield.
    
    Represents a character, creature, or entity engaged in tactical combat.
    Owns its position, facing, combat resources, and reference to character data.
    """
    
    # Identity
    id: str
    name: str
    
    # Tactical state
    position: Position
    
    # Resources
    fp: ResourcePool  # Fatigue Points (Fáradtságpont)
    ep: ResourcePool  # Health Points (Életpont)
    
    # Facing with default
    facing: Facing = field(default_factory=lambda: Facing(0))
    
    # Combat stats
    combat_stats: CombatStats = field(default_factory=CombatStats)
    attributes: Attributes = field(default_factory=Attributes)
    
    # Visual
    sprite: Optional[pygame.Surface] = None
    
    # Character reference (raw data, detailed stats, skills, equipment)
    character_data: Optional[dict] = None
    
    # Weapon (if wielded)
    weapon: Optional["Weapon"] = None

    # Armor system (layered); optional until equipped during loadout
    armor_system: Optional[ArmorSystem] = None
    
    def is_alive(self) -> bool:
        """Check if unit is still alive."""
        return not self.ep.is_depleted()
    
    def is_exhausted(self) -> bool:
        """Check if unit is out of fatigue."""
        return self.fp.is_depleted()
    
    def can_act(self) -> bool:
        """Check if unit can perform actions."""
        return self.is_alive() and not self.is_exhausted()
    
    def move_to(self, new_position: Position) -> None:
        """Move unit to a new position."""
        self.position = new_position
    
    def rotate_to(self, new_facing: Facing) -> None:
        """Change unit facing."""
        self.facing = new_facing
    
    def take_damage(self, damage: int) -> int:
        """
        Apply damage to unit, reducing EP.
        
        Args:
            damage: Amount of damage to apply
            
        Returns:
            Actual damage taken (after bounds checking)
        """
        if damage <= 0:
            return 0
        
        actual_damage = min(damage, self.ep.current)
        self.ep = ResourcePool(
            current=self.ep.current - actual_damage,
            maximum=self.ep.maximum
        )
        return actual_damage
    
    def spend_fatigue(self, amount: int) -> bool:
        """
        Spend fatigue points.
        
        Args:
            amount: FP to spend
            
        Returns:
            True if successfully spent, False if insufficient FP
        """
        if amount > self.fp.current:
            return False
        
        self.fp = ResourcePool(
            current=self.fp.current - amount,
            maximum=self.fp.maximum
        )
        return True
    
    def restore_fp(self, amount: int) -> None:
        """Restore fatigue points (capped at maximum)."""
        new_current = min(self.fp.current + amount, self.fp.maximum)
        self.fp = ResourcePool(current=new_current, maximum=self.fp.maximum)
    
    def restore_ep(self, amount: int) -> None:
        """Restore health points (capped at maximum)."""
        new_current = min(self.ep.current + amount, self.ep.maximum)
        self.ep = ResourcePool(current=new_current, maximum=self.ep.maximum)
    
    def __str__(self) -> str:
        return f"{self.name} at {self.position} facing {self.facing.direction} [{self.ep} EP, {self.fp} FP]"


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
