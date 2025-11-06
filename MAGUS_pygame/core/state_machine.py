"""
State machine for turn and phase management in MAGUS Pygame.
Handles transitions between combat phases and turn orders.
"""

from enum import Enum, auto
from typing import Any, Callable


class CombatPhase(Enum):
    """Combat phase states."""
    SETUP = auto()
    INITIATIVE = auto()
    PLAYER_TURN = auto()
    ENEMY_TURN = auto()
    RESOLUTION = auto()
    END_ROUND = auto()


class TurnPhase(Enum):
    """Individual turn phase states."""
    START = auto()
    MOVEMENT = auto()
    ACTION = auto()
    END = auto()


class StateMachine:
    """Manages state transitions for combat flow."""

    def __init__(self) -> None:
        """Initialize state machine."""
        self.combat_phase = CombatPhase.SETUP
        self.turn_phase = TurnPhase.START
        self.current_unit_index = 0
        self.turn_order: list[Any] = []
        self.round_number = 0
        
        # Transition callbacks
        self._on_combat_phase_change: list[Callable[[CombatPhase, CombatPhase], None]] = []
        self._on_turn_phase_change: list[Callable[[TurnPhase, TurnPhase], None]] = []

    def register_combat_phase_callback(
        self, callback: Callable[[CombatPhase, CombatPhase], None]
    ) -> None:
        """Register a callback for combat phase changes.
        
        Args:
            callback: Function called with (old_phase, new_phase)
        """
        self._on_combat_phase_change.append(callback)

    def register_turn_phase_callback(
        self, callback: Callable[[TurnPhase, TurnPhase], None]
    ) -> None:
        """Register a callback for turn phase changes.
        
        Args:
            callback: Function called with (old_phase, new_phase)
        """
        self._on_turn_phase_change.append(callback)

    def set_combat_phase(self, new_phase: CombatPhase) -> None:
        """Transition to a new combat phase.
        
        Args:
            new_phase: The combat phase to transition to
        """
        old_phase = self.combat_phase
        self.combat_phase = new_phase
        
        for callback in self._on_combat_phase_change:
            callback(old_phase, new_phase)

    def set_turn_phase(self, new_phase: TurnPhase) -> None:
        """Transition to a new turn phase.
        
        Args:
            new_phase: The turn phase to transition to
        """
        old_phase = self.turn_phase
        self.turn_phase = new_phase
        
        for callback in self._on_turn_phase_change:
            callback(old_phase, new_phase)

    def next_turn(self) -> None:
        """Advance to the next unit's turn."""
        self.current_unit_index += 1
        if self.current_unit_index >= len(self.turn_order):
            self.end_round()
        else:
            self.set_turn_phase(TurnPhase.START)

    def end_round(self) -> None:
        """End the current round and prepare for next."""
        self.round_number += 1
        self.current_unit_index = 0
        self.set_combat_phase(CombatPhase.END_ROUND)
        # Logic to prepare next round would go here
        self.set_combat_phase(CombatPhase.PLAYER_TURN)

    def get_current_unit(self) -> Any:
        """Get the unit whose turn it currently is.
        
        Returns:
            The current unit, or None if no units in turn order
        """
        if 0 <= self.current_unit_index < len(self.turn_order):
            return self.turn_order[self.current_unit_index]
        return None
