"""
Status conditions and effects system for MAGUS Pygame.
Handles buffs, debuffs, and temporary status effects on units.
"""

from enum import Enum, auto
from typing import Any, Optional, Callable


class ConditionType(Enum):
    """Types of status conditions."""
    # Negative conditions
    STUNNED = auto()
    POISONED = auto()
    BLEEDING = auto()
    WEAKENED = auto()
    SLOWED = auto()
    BLINDED = auto()
    
    # Positive conditions
    BLESSED = auto()
    HASTED = auto()
    PROTECTED = auto()
    REGENERATING = auto()
    INSPIRED = auto()
    
    # Special conditions
    DEFENDING = auto()
    CHARGING = auto()
    CONCENTRATING = auto()


class Condition:
    """Represents a status condition on a unit."""

    def __init__(
        self,
        condition_type: ConditionType,
        duration: int,
        strength: int = 1,
        source: Optional[str] = None
    ) -> None:
        """Initialize a condition.
        
        Args:
            condition_type: The type of condition
            duration: Duration in rounds (0 = permanent until removed)
            strength: Strength/intensity of the condition
            source: Optional description of the condition source
        """
        self.condition_type = condition_type
        self.duration = duration
        self.strength = strength
        self.source = source
        self.rounds_active = 0

    def tick(self) -> bool:
        """Process one round of the condition.
        
        Returns:
            True if condition is still active, False if expired
        """
        if self.duration == 0:
            return True  # Permanent condition
            
        self.rounds_active += 1
        return self.rounds_active < self.duration

    def get_description(self) -> str:
        """Get a description of the condition.
        
        Returns:
            Description string
        """
        desc = self.condition_type.name.title()
        if self.duration > 0:
            rounds_left = self.duration - self.rounds_active
            desc += f" ({rounds_left} rounds)"
        if self.strength > 1:
            desc += f" (Strength {self.strength})"
        return desc


class ConditionsManager:
    """Manages status conditions for a unit."""

    def __init__(self) -> None:
        """Initialize the conditions manager."""
        self.conditions: dict[ConditionType, Condition] = {}
        
        # Callbacks for condition events
        self._on_condition_added: list[Callable[[Condition], None]] = []
        self._on_condition_removed: list[Callable[[ConditionType], None]] = []

    def add_condition(self, condition: Condition) -> None:
        """Add a condition to the unit.
        
        Args:
            condition: The condition to add
        """
        # If condition already exists, use the stronger/longer one
        if condition.condition_type in self.conditions:
            existing = self.conditions[condition.condition_type]
            if condition.strength > existing.strength or condition.duration > existing.duration:
                self.conditions[condition.condition_type] = condition
        else:
            self.conditions[condition.condition_type] = condition
            
        # Notify listeners
        for callback in self._on_condition_added:
            callback(condition)

    def remove_condition(self, condition_type: ConditionType) -> None:
        """Remove a condition from the unit.
        
        Args:
            condition_type: The type of condition to remove
        """
        if condition_type in self.conditions:
            del self.conditions[condition_type]
            
            # Notify listeners
            for callback in self._on_condition_removed:
                callback(condition_type)

    def has_condition(self, condition_type: ConditionType) -> bool:
        """Check if unit has a specific condition.
        
        Args:
            condition_type: The condition type to check
            
        Returns:
            True if the unit has the condition
        """
        return condition_type in self.conditions

    def get_condition(self, condition_type: ConditionType) -> Optional[Condition]:
        """Get a specific condition.
        
        Args:
            condition_type: The condition type to get
            
        Returns:
            The condition if present, None otherwise
        """
        return self.conditions.get(condition_type)

    def tick_conditions(self) -> None:
        """Process one round for all conditions."""
        expired: list[ConditionType] = []
        
        for condition_type, condition in self.conditions.items():
            if not condition.tick():
                expired.append(condition_type)
        
        # Remove expired conditions
        for condition_type in expired:
            self.remove_condition(condition_type)

    def get_all_conditions(self) -> list[Condition]:
        """Get all active conditions.
        
        Returns:
            List of all active conditions
        """
        return list(self.conditions.values())

    def clear_all(self) -> None:
        """Remove all conditions."""
        condition_types = list(self.conditions.keys())
        for condition_type in condition_types:
            self.remove_condition(condition_type)

    def register_on_added(self, callback: Callable[[Condition], None]) -> None:
        """Register a callback for when a condition is added.
        
        Args:
            callback: Function called with the added condition
        """
        self._on_condition_added.append(callback)

    def register_on_removed(self, callback: Callable[[ConditionType], None]) -> None:
        """Register a callback for when a condition is removed.
        
        Args:
            callback: Function called with the removed condition type
        """
        self._on_condition_removed.append(callback)

    def is_incapacitated(self) -> bool:
        """Check if unit is incapacitated (cannot act).
        
        Returns:
            True if unit cannot take actions
        """
        incapacitating = {ConditionType.STUNNED}
        return any(ct in self.conditions for ct in incapacitating)

    def get_move_modifier(self) -> float:
        """Get movement speed modifier from conditions.
        
        Returns:
            Movement multiplier (1.0 = normal, 0.5 = half speed, etc.)
        """
        modifier = 1.0
        
        if ConditionType.SLOWED in self.conditions:
            modifier *= 0.5
        if ConditionType.HASTED in self.conditions:
            modifier *= 1.5
        if ConditionType.STUNNED in self.conditions:
            modifier = 0.0
            
        return modifier

    def get_attack_modifier(self) -> int:
        """Get attack bonus/penalty from conditions.
        
        Returns:
            Attack modifier (positive or negative)
        """
        modifier = 0
        
        if ConditionType.WEAKENED in self.conditions:
            modifier -= 2
        if ConditionType.BLESSED in self.conditions:
            modifier += 2
        if ConditionType.BLINDED in self.conditions:
            modifier -= 4
            
        return modifier

    def get_defense_modifier(self) -> int:
        """Get defense bonus/penalty from conditions.
        
        Returns:
            Defense modifier (positive or negative)
        """
        modifier = 0
        
        if ConditionType.PROTECTED in self.conditions:
            modifier += 2
        if ConditionType.DEFENDING in self.conditions:
            modifier += 4
        if ConditionType.STUNNED in self.conditions:
            modifier -= 4
            
        return modifier
