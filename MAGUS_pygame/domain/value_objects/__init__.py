"""
Value Objects - Immutable data structures for domain concepts.
"""

from dataclasses import dataclass, field
from typing import Optional

from .scenario_config import UnitSetup, ScenarioConfig


@dataclass(frozen=True)
class Position:
    """Hex grid position (cube coordinates)."""
    q: int
    r: int
    
    @property
    def s(self) -> int:
        """Derived s coordinate (q + r + s = 0)."""
        return -self.q - self.r
    
    def distance_to(self, other: "Position") -> int:
        """Calculate hex distance to another position."""
        return (abs(self.q - other.q) + abs(self.r - other.r) + abs(self.s - other.s)) // 2
    
    def __str__(self) -> str:
        return f"({self.q}, {self.r})"


@dataclass(frozen=True)
class CombatStats:
    """Combat statistics (attack/defense values)."""
    KE: int = 0  # Initiative modifier
    TE: int = 0  # Attack value
    VE: int = 0  # Defense value
    CE: int = 0  # Ranged attack value
    
    def __str__(self) -> str:
        return f"KÉ:{self.KE} TÉ:{self.TE} VÉ:{self.VE} CÉ:{self.CE}"


@dataclass(frozen=True)
class ResourcePool:
    """Resource pool with current and maximum values."""
    current: int
    maximum: int
    
    def is_depleted(self) -> bool:
        return self.current <= 0
    
    def is_full(self) -> bool:
        return self.current >= self.maximum
    
    def percentage(self) -> float:
        if self.maximum == 0:
            return 0.0
        return self.current / self.maximum
    
    def __str__(self) -> str:
        return f"{self.current}/{self.maximum}"


@dataclass(frozen=True)
class Attributes:
    """Character attributes (strength, dexterity, etc.)."""
    strength: int = 10  # Erő
    dexterity: int = 10  # Ügyesség
    speed: int = 10  # Gyorsaság
    endurance: int = 10  # Állóképesség
    health: int = 10  # Egészség
    charisma: int = 10  # Karizma
    intelligence: int = 10  # Intelligencia
    willpower: int = 10  # Akaraterő
    astral: int = 10  # Asztrál
    perception: int = 10  # Érzékelés
    
    @staticmethod
    def from_dict(data: dict[str, int]) -> "Attributes":
        """Create from Hungarian keys."""
        return Attributes(
            strength=data.get("Erő", 10),
            dexterity=data.get("Ügyesség", 10),
            speed=data.get("Gyorsaság", 10),
            endurance=data.get("Állóképesség", 10),
            health=data.get("Egészség", 10),
            charisma=data.get("Karizma", 10),
            intelligence=data.get("Intelligencia", 10),
            willpower=data.get("Akaraterő", 10),
            astral=data.get("Asztrál", 10),
            perception=data.get("Érzékelés", 10),
        )


@dataclass(frozen=True)
class Facing:
    """Hex facing direction (0-5, where 0 is North)."""
    direction: int
    
    def __post_init__(self):
        if not 0 <= self.direction <= 5:
            raise ValueError(f"Facing must be 0-5, got {self.direction}")
    
    def rotate_clockwise(self) -> "Facing":
        return Facing((self.direction + 1) % 6)
    
    def rotate_counterclockwise(self) -> "Facing":
        return Facing((self.direction - 1) % 6)
    
    def opposite(self) -> "Facing":
        return Facing((self.direction + 3) % 6)


@dataclass
class DamageResult:
    """Result of a damage calculation."""
    base_damage: int
    final_damage: int
    armor_absorbed: int
    penetrated: bool
    is_critical: bool = False
    overkill: int = 0
    
    def __str__(self) -> str:
        parts = [f"{self.final_damage} damage"]
        if self.armor_absorbed > 0:
            parts.append(f"({self.armor_absorbed} absorbed)")
        if self.is_critical:
            parts.append("CRITICAL")
        if self.penetrated:
            parts.append("PENETRATED")
        return " ".join(parts)
