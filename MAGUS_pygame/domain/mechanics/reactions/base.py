"""
Reaction abstractions for the domain reaction system (Phase 2).

Reactions are pure computations that evaluate triggers and compute results
(similar to actions) but are invoked by events (e.g., entering ZoC).

They should not mutate application state; instead they return ReactionResult
objects for the application layer to apply.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol


class ReactionCategory(Enum):
    """High-level reaction categories for UI/logging."""

    OPPORTUNITY = "opportunity"
    COUNTER = "counter"
    DEFENSE = "defense"
    UTILITY = "utility"


@dataclass
class ReactionResult:
    """Result of executing a reaction.

    Mirrors ActionResult shape where useful and adds interruption hints
    for the application (e.g., stopping movement).
    """

    success: bool
    message: str = ""
    ap_spent: int = 0
    stamina_spent: int = 0
    data: dict[str, Any] = field(default_factory=dict)

    # Whether this reaction suggests interrupting the triggering action (e.g., movement)
    interrupts_movement: bool = False
    # Index in path to stop at (inclusive) if movement should be interrupted
    interrupt_index: int | None = None

    # Accounting flags
    consumes_reaction: bool = True
    triggered_by: str = ""


class Reaction(Protocol):
    """Protocol implemented by all reactions."""

    @property
    def category(self) -> ReactionCategory:  # pragma: no cover - trivial
        ...

    @property
    def name(self) -> str:  # pragma: no cover - trivial
        ...

    def should_trigger(self, **context) -> tuple[bool, str]:
        """Evaluate if reaction should trigger given context.
        Context is intentionally flexible to avoid tight coupling.
        """
        ...

    def execute(self, **context) -> ReactionResult:
        """Execute reaction and return a pure ReactionResult."""
        ...
