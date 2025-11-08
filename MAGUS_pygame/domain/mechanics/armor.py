"""
Armor system for MAGUS combat.

Handles:
- Armor entities with SFÉ (Sebzésfelfogó Érték - damage absorption)
- Armor degradation on overpower strikes
- MGT (Mozgásgátló Tényező - movement penalty)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ArmorPiece:
    """
    Single armor piece (vért, sisak, etc.).
    
    Attributes:
        id: Armor identifier
        name: Display name
        sfe: Base damage absorption value
        mgt: Movement penalty
        location: Body part protected
        current_sfe: Current absorption (degrades on overpower)
    """
    id: str
    name: str
    sfe: int  # Base SFÉ
    mgt: int = 0  # Movement penalty
    location: str = "torso"  # Body location
    current_sfe: int = field(init=False)  # Degradable value
    
    def __post_init__(self):
        # Initialize current SFÉ to base value
        if not hasattr(self, 'current_sfe') or self.current_sfe is None:
            self.current_sfe = self.sfe
    
    def degrade(self, amount: int = 1) -> None:
        """
        Degrade armor (reduce current SFÉ).
        Called on overpower strikes.
        
        Args:
            amount: Amount to reduce SFÉ by (default 1)
        """
        self.current_sfe = max(0, self.current_sfe - amount)
    
    def is_broken(self) -> bool:
        """Check if armor is completely degraded."""
        return self.current_sfe <= 0
    
    def repair(self, amount: Optional[int] = None) -> None:
        """
        Repair armor (restore SFÉ).
        
        Args:
            amount: Amount to restore (None = full repair to base)
        """
        if amount is None:
            self.current_sfe = self.sfe
        else:
            self.current_sfe = min(self.sfe, self.current_sfe + amount)


def calculate_total_armor_absorption(armor_pieces: list[ArmorPiece]) -> int:
    """
    Calculate total armor absorption from all equipped armor.
    
    Args:
        armor_pieces: List of equipped armor pieces
        
    Returns:
        Total current SFÉ from all armor
    """
    return sum(piece.current_sfe for piece in armor_pieces if not piece.is_broken())


def calculate_total_mgt(armor_pieces: list[ArmorPiece]) -> int:
    """
    Calculate total movement penalty from armor.
    
    Args:
        armor_pieces: List of equipped armor pieces
        
    Returns:
        Total MGT penalty
    """
    return sum(piece.mgt for piece in armor_pieces)


def apply_overpower_degradation(armor_pieces: list[ArmorPiece]) -> None:
    """
    Apply degradation to all armor pieces on overpower strike.
    Reduces each piece's current_sfe by 1.
    
    Args:
        armor_pieces: List of equipped armor to degrade
    """
    for piece in armor_pieces:
        if not piece.is_broken():
            piece.degrade(1)
