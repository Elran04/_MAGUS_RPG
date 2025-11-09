"""
Base action abstractions for the domain action system.

These are framework-agnostic contracts. No pygame, no application state.
All actions should be pure with respect to game rules: they compute results
(ActionResult) that the application layer can apply to mutate state.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol, Optional, Any


class ActionCategory(Enum):
    """High-level action categories for UI grouping and validation."""
    MOVEMENT = "movement"
    ATTACK = "attack"
    SPECIAL_ATTACK = "special"
    EQUIPMENT = "equipment"
    DEFENSE = "defense"
    UTILITY = "utility"


@dataclass(frozen=True)
class ActionCost:
    """Represents the cost to perform an action."""
    ap: int
    stamina: int = 0
    is_free: bool = False
    uses_full_turn: bool = False


@dataclass
class ActionResult:
    """Result of executing an action.

    Application layer should interpret and apply these results to mutate game state.
    """
    success: bool
    message: str = ""
    ap_spent: int = 0
    stamina_spent: int = 0
    # Optional payload for specific actions
    data: dict[str, Any] = field(default_factory=dict)
    # For movement interruption by reactions
    stops_movement: bool = False
    triggered_reactions: list[str] = field(default_factory=list)


class Action(Protocol):
    """Protocol implemented by all actions."""

    @property
    def category(self) -> ActionCategory:  # pragma: no cover - trivial
        ...

    @property
    def cost(self) -> ActionCost:  # pragma: no cover - trivial
        ...

    def can_execute(self, **context) -> tuple[bool, str]:
        """Check if action can be executed with given context.
        Context is intentionally flexible to avoid coupling.
        """
        ...

    def execute(self, **context) -> ActionResult:
        """Execute the action and return a result. Pure computation only.
        Context should contain all required inputs (units, positions, rng, etc.).
        """
        ...
