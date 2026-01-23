"""
Weapon switch action: swap between equipped and quickslot weapons.

Pure domain action that validates weapon switching feasibility and returns
the new weapon configuration. Application layer is responsible for applying
the changes to the unit's equipment and deducting AP cost.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.entities import Unit
from domain.value_objects import Position

from .base import Action, ActionCategory, ActionCost, ActionResult


@dataclass
class SwitchWeaponAction(Action):
    """Swap equipped weapons with quickslot weapons (5 AP cost)."""

    ap_cost: int = 5

    @property
    def category(self) -> ActionCategory:
        return ActionCategory.EQUIPMENT

    @property
    def cost(self) -> ActionCost:
        return ActionCost(ap=self.ap_cost)

    def can_execute(
        self,
        *,
        unit: Unit,
        new_main_hand: str | None,
        new_off_hand: str | None,
        ap_available: int,
        **_: object,
    ) -> tuple[bool, str]:
        """Validate that weapon switch is possible.

        Args:
            unit: Unit performing the weapon switch
            new_main_hand: New main hand weapon ID
            new_off_hand: New off hand weapon ID
            ap_available: Available action points

        Returns:
            Tuple of (can_execute, error_message)
        """
        if unit is None:
            return (False, "Unit is required")

        if not unit.is_alive():
            return (False, "Unit is not alive")

        if unit.is_exhausted():
            return (False, "Unit is exhausted")

        # Check AP cost
        if ap_available < self.ap_cost:
            return (False, f"Insufficient AP (need {self.ap_cost}, have {ap_available})")

        # Check equipment data exists
        if not unit.character_data or "equipment" not in unit.character_data:
            return (False, "Unit has no equipment data")

        equipment = unit.character_data["equipment"]

        # Get available weapons from all slots
        available_weapons = {
            equipment.get("main_hand", ""),
            equipment.get("off_hand", ""),
            equipment.get("weapon_quick_1", ""),
            equipment.get("weapon_quick_2", ""),
            equipment.get("weapon_quick_3", ""),
            equipment.get("weapon_quick_4", ""),
        }
        available_weapons.discard("")  # Remove empty slots

        # Validate new weapons are available
        if new_main_hand and new_main_hand not in available_weapons:
            return (False, f"Weapon {new_main_hand} not available")

        if new_off_hand and new_off_hand not in available_weapons:
            return (False, f"Weapon {new_off_hand} not available")

        # Check if at least one weapon changed
        current_main = equipment.get("main_hand", "")
        current_off = equipment.get("off_hand", "")

        if new_main_hand == current_main and new_off_hand == current_off:
            return (False, "No weapon change")

        return (True, "")

    def execute(
        self,
        *,
        unit: Unit,
        new_main_hand: str | None,
        new_off_hand: str | None,
        **_: object,
    ) -> ActionResult:
        """Execute weapon switch.

        Note: This is a pure function that doesn't mutate the unit's equipment.
        The application layer must apply the changes to unit.character_data["equipment"]
        by setting main_hand and off_hand values.

        Args:
            unit: Unit switching weapons
            new_main_hand: New main hand weapon ID
            new_off_hand: New off hand weapon ID

        Returns:
            ActionResult with success and weapon swap details
        """
        equipment = unit.character_data["equipment"]
        old_main = equipment.get("main_hand", "")
        old_off = equipment.get("off_hand", "")

        # Create descriptive message
        msg_parts = []
        if new_main_hand != old_main:
            msg_parts.append(f"main hand: {old_main or '(empty)'} → {new_main_hand or '(empty)'}")
        if new_off_hand != old_off:
            msg_parts.append(f"off hand: {old_off or '(empty)'} → {new_off_hand or '(empty)'}")

        message = f"Switched weapons ({', '.join(msg_parts)})"

        return ActionResult(
            success=True,
            message=message,
            ap_spent=self.ap_cost,
            data={
                "old_main_hand": old_main,
                "old_off_hand": old_off,
                "new_main_hand": new_main_hand or "",
                "new_off_hand": new_off_hand or "",
            },
        )
