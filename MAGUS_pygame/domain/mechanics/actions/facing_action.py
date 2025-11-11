"""
Facing change action: rotate unit to face a new direction.

Pure domain action that validates and computes the facing change.
Application layer is responsible for applying the facing change to the unit
and deducting AP cost.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.entities import Unit
from domain.value_objects import Facing

from .base import Action, ActionCategory, ActionCost, ActionResult


@dataclass
class FacingAction(Action):
    """Change unit facing direction (free action, 0 AP cost)."""

    @property
    def category(self) -> ActionCategory:
        return ActionCategory.UTILITY

    @property
    def cost(self) -> ActionCost:
        return ActionCost(ap=0)

    def can_execute(
        self,
        *,
        unit: Unit,
        new_facing: Facing,
        ap_available: int = 0,
        **_: object,
    ) -> tuple[bool, str]:
        """Validate that facing change is possible.

        Args:
            unit: Unit to rotate
            new_facing: Target facing direction
            ap_available: Available action points

        Returns:
            Tuple of (can_execute, error_message)
        """
        if unit is None:
            return (False, "Unit is required")

        if not unit.is_alive():
            return (False, "Unit is not alive")

        if new_facing is None:
            return (False, "New facing is required")

        if unit.facing == new_facing:
            return (False, "Already facing that direction")

        # Facing is now a free action (0 AP cost)
        # No AP check needed

        return (True, "")

    def execute(
        self,
        *,
        unit: Unit,
        new_facing: Facing,
        **_: object,
    ) -> ActionResult:
        """Execute facing change.

        Note: This is a pure function that doesn't mutate the unit.
        The application layer must apply the facing change using unit.rotate_to().

        Args:
            unit: Unit to rotate
            new_facing: Target facing direction

        Returns:
            ActionResult with success and facing change details
        """
        old_facing = unit.facing

        message = (
            f"Rotated from facing {old_facing.direction} to {new_facing.direction} (free action)"
        )

        return ActionResult(
            success=True,
            message=message,
            ap_spent=0,  # Free action
            data={
                "old_facing": old_facing.direction,
                "new_facing": new_facing.direction,
            },
        )
