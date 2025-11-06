"""
Stamina and fatigue system for MAGUS Pygame.
Manages action costs, stamina recovery, and fatigue penalties.
"""

from typing import Optional, Callable


class StaminaSystem:
    """Manages stamina for a character or unit."""

    def __init__(self, max_stamina: int = 100) -> None:
        """Initialize the stamina system.
        
        Args:
            max_stamina: Maximum stamina points
        """
        self.max_stamina = max_stamina
        self.current_stamina = max_stamina
        self.fatigue_level = 0  # 0-100, higher = more tired
        
        # Stamina costs for actions
        self.action_costs = {
            'move': 5,
            'attack': 15,
            'charge': 25,
            'defend': 10,
            'dodge': 20,
            'sprint': 30,
            'skill_basic': 20,
            'skill_advanced': 40,
            'skill_master': 60,
        }
        
        # Recovery rates
        self.passive_recovery = 5  # Stamina recovered per round
        self.rest_recovery = 20  # Stamina recovered when resting
        
        # Callbacks
        self._on_stamina_changed: list[Callable[[int, int], None]] = []
        self._on_exhausted: list[Callable[[], None]] = []

    def can_afford(self, action: str) -> bool:
        """Check if unit has enough stamina for an action.
        
        Args:
            action: The action name
            
        Returns:
            True if action can be afforded
        """
        cost = self.action_costs.get(action, 0)
        return self.current_stamina >= cost

    def spend(self, action: str) -> bool:
        """Spend stamina for an action.
        
        Args:
            action: The action name
            
        Returns:
            True if stamina was spent, False if insufficient
        """
        cost = self.action_costs.get(action, 0)
        
        if self.current_stamina >= cost:
            old_stamina = self.current_stamina
            self.current_stamina -= cost
            
            # Increase fatigue slightly
            self.fatigue_level = min(100, self.fatigue_level + cost // 10)
            
            self._notify_stamina_changed(old_stamina, self.current_stamina)
            
            if self.current_stamina == 0:
                self._notify_exhausted()
            
            return True
        
        return False

    def recover(self, amount: Optional[int] = None) -> None:
        """Recover stamina.
        
        Args:
            amount: Amount to recover (None = passive recovery)
        """
        if amount is None:
            amount = self.passive_recovery
            
        old_stamina = self.current_stamina
        self.current_stamina = min(self.max_stamina, self.current_stamina + amount)
        
        # Reduce fatigue slightly
        if amount > 0:
            self.fatigue_level = max(0, self.fatigue_level - amount // 5)
        
        if old_stamina != self.current_stamina:
            self._notify_stamina_changed(old_stamina, self.current_stamina)

    def rest(self) -> None:
        """Take a rest action to recover more stamina."""
        self.recover(self.rest_recovery)

    def get_stamina_percentage(self) -> float:
        """Get current stamina as a percentage.
        
        Returns:
            Stamina percentage (0.0 to 1.0)
        """
        return self.current_stamina / self.max_stamina if self.max_stamina > 0 else 0.0

    def get_fatigue_penalty(self) -> int:
        """Get penalty to actions from fatigue.
        
        Returns:
            Penalty value (0-10)
        """
        # Every 20 fatigue = -1 penalty
        return min(10, self.fatigue_level // 20)

    def is_exhausted(self) -> bool:
        """Check if unit is exhausted (no stamina).
        
        Returns:
            True if current stamina is 0
        """
        return self.current_stamina == 0

    def is_fatigued(self) -> bool:
        """Check if unit is significantly fatigued.
        
        Returns:
            True if fatigue level is high
        """
        return self.fatigue_level >= 60

    def set_action_cost(self, action: str, cost: int) -> None:
        """Set the stamina cost for an action.
        
        Args:
            action: The action name
            cost: Stamina cost
        """
        self.action_costs[action] = cost

    def get_action_cost(self, action: str) -> int:
        """Get the stamina cost for an action.
        
        Args:
            action: The action name
            
        Returns:
            Stamina cost (0 if action not found)
        """
        return self.action_costs.get(action, 0)

    def reset(self) -> None:
        """Reset stamina and fatigue to initial values."""
        old_stamina = self.current_stamina
        self.current_stamina = self.max_stamina
        self.fatigue_level = 0
        
        if old_stamina != self.current_stamina:
            self._notify_stamina_changed(old_stamina, self.current_stamina)

    def register_on_changed(self, callback: Callable[[int, int], None]) -> None:
        """Register a callback for stamina changes.
        
        Args:
            callback: Function called with (old_stamina, new_stamina)
        """
        self._on_stamina_changed.append(callback)

    def register_on_exhausted(self, callback: Callable[[], None]) -> None:
        """Register a callback for when stamina reaches 0.
        
        Args:
            callback: Function called when exhausted
        """
        self._on_exhausted.append(callback)

    def _notify_stamina_changed(self, old_value: int, new_value: int) -> None:
        """Notify listeners of stamina change.
        
        Args:
            old_value: Previous stamina value
            new_value: New stamina value
        """
        for callback in self._on_stamina_changed:
            callback(old_value, new_value)

    def _notify_exhausted(self) -> None:
        """Notify listeners that unit is exhausted."""
        for callback in self._on_exhausted:
            callback()

    def get_state_description(self) -> str:
        """Get a text description of stamina state.
        
        Returns:
            Description string
        """
        percentage = self.get_stamina_percentage() * 100
        
        if percentage >= 80:
            return "Energized"
        elif percentage >= 60:
            return "Fresh"
        elif percentage >= 40:
            return "Tiring"
        elif percentage >= 20:
            return "Tired"
        elif percentage > 0:
            return "Exhausted"
        else:
            return "Completely Drained"
