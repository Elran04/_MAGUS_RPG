"""Equipment Validation Service - Validates equipment slot assignments.

Handles:
- Main/off-hand weapon compatibility (two-handed vs one-handed)
- Armor piece compatibility validation
- Quick access slot validation
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any


# Local result object for validation outcomes
@dataclass
class ValidationResult:
    success: bool
    message: str = ""
    details: Any | None = None


from domain.mechanics.armor import ArmorPiece, ArmorSystem
from domain.value_objects.weapon_type_check import (
    Slot,
    is_one_handed_weapon,
    is_ranged_weapon,
    is_shield,
    is_two_handed_weapon,
)
from logger.logger import get_logger

if TYPE_CHECKING:
    from infrastructure.repositories import EquipmentRepository

logger = get_logger(__name__)


class EquipmentValidationService:
    def get_wield_mode_hint(
        self, unit: Any, weapon_id: str, weapon: dict[str, Any] | None = None
    ) -> str:
        """Return wield mode hint for a weapon for a given unit (e.g., '(1h/2h)', '(2h only)'). Accepts cached weapon object."""
        if weapon is None:
            weapon = self.equipment_repo.find_weapon_by_id(weapon_id)
        if not weapon:
            return ""
        wield_mode = weapon.get("wield_mode", "").lower()
        if wield_mode in ["változó", "variable"]:
            result = self.can_wield_variable_one_handed(unit, weapon_id, weapon)
            if result.success:
                return "(1h/2h)"
            else:
                return "(2h only)"
        elif wield_mode in ["egykezes", "one-handed", "1h"]:
            return "(1h)"
        elif wield_mode in ["kétkezes", "two-handed", "2h"]:
            return "(2h)"
        return ""

    def is_item_eligible(
        self, unit: Any, slot: str, item_id: str, selected_wield_mode: str | None = None
    ) -> ValidationResult:
        """Check if an item is eligible for a slot for a given unit. Only call weapon logic for weapon/shield items."""
        # Normalize slot to Slot enum for all logic
        try:
            slot_enum = Slot(slot) if not isinstance(slot, Slot) else slot
        except Exception:
            return ValidationResult(False, f"Invalid slot: {slot}")

        repo = self.equipment_repo
        # Determine item category
        weapons = repo.load_weapons()
        armor = repo.load_armor()
        is_weapon = any(w.get("id") == item_id for w in weapons)
        is_armor = any(a.get("id") == item_id for a in armor)
        weapon = repo.find_weapon_by_id(item_id) if is_weapon else None
        wield_mode = weapon.get("wield_mode", "") if weapon else ""

        # Weapon slots
        if slot_enum in [Slot.MAIN_HAND, Slot.WEAPON_QUICK_1, Slot.WEAPON_QUICK_2]:
            if not is_weapon:
                return ValidationResult(False, "Not a weapon")

            is_variable = wield_mode.lower() in ["variable", "változó", "valtozo", "1h/2h"]

            # Main hand: weapons only
            if slot_enum == Slot.MAIN_HAND:
                # Variable weapons may be forced to 1h when off-hand is occupied
                if is_variable and selected_wield_mode == "one_handed":
                    result = self.can_wield_variable_one_handed(unit, item_id, weapon)
                    if not result.success:
                        return result
                    return ValidationResult(True, "OK")

                is_1h = is_one_handed_weapon(weapon) if weapon else False
                is_2h = is_two_handed_weapon(weapon) if weapon else False
                is_ranged = is_ranged_weapon(weapon) if weapon else False

                # Variable weapons are allowed even if helper tags them two-handed; rely on selected_wield_mode upstream
                if is_variable:
                    return ValidationResult(True, "OK")

                is_valid_weapon = is_1h or is_2h or is_ranged
                if not is_valid_weapon:
                    return ValidationResult(False, "Not a weapon")
                return ValidationResult(True, "OK")

            # Quick slots: weapons or shields allowed
            elif slot_enum in [Slot.WEAPON_QUICK_1, Slot.WEAPON_QUICK_2]:
                is_1h = is_one_handed_weapon(weapon) if weapon else False
                is_2h = is_two_handed_weapon(weapon) if weapon else False
                is_ranged = is_ranged_weapon(weapon) if weapon else False
                is_shield_item = is_shield(weapon) if weapon else False
                is_valid_weapon = is_1h or is_2h or is_ranged
                if not (is_valid_weapon or is_shield_item):
                    return ValidationResult(False, "Not a weapon or shield")
                return ValidationResult(True, "OK")
        # Off-hand slot
        if slot_enum == Slot.OFF_HAND:
            if not is_weapon:
                return ValidationResult(False, "Not a weapon/shield")
            main_hand_id = None
            result = self.can_equip_offhand(main_hand_id, item_id)
            return result
        # Armor slot
        if slot_enum == Slot.ARMOR:
            if not is_armor:
                return ValidationResult(False, "Not armor")
            return ValidationResult(True, "OK")
        # Quick access slots
        if slot_enum in [Slot.QUICK_ACCESS_1, Slot.QUICK_ACCESS_2]:
            if is_weapon or is_armor:
                return ValidationResult(False, "Not general item")
            return ValidationResult(True, "OK")
        return ValidationResult(False, "Unknown slot")

    """Service for validating equipment configurations.

    Responsibilities:
    - Check weapon hand requirements (one-handed vs two-handed)
    - Validate off-hand eligibility based on main hand weapon
    - Provide human-readable validation messages
    """

    def __init__(self, equipment_repo: EquipmentRepository):
        """Initialize equipment validation service.

        Args:
            equipment_repo: Equipment repository for looking up item data
        """
        self.equipment_repo = equipment_repo

    def can_equip_offhand(self, main_hand_id: str | None, offhand_id: str) -> ValidationResult:
        """Check if an item can be equipped in the off-hand.

        Args:
            main_hand_id: Currently equipped main hand weapon ID (or None)
            offhand_id: Item to check for off-hand

        Returns:
            ValidationResult
        """
        repo = self.equipment_repo
        main_hand_weapon = repo.find_weapon_by_id(main_hand_id) if main_hand_id else None
        offhand_weapon = repo.find_weapon_by_id(offhand_id) if offhand_id else None
        # If no main hand weapon, off-hand must be one-handed weapon or shield
        if not main_hand_weapon:
            if offhand_weapon and (
                is_one_handed_weapon(offhand_weapon) or is_shield(offhand_weapon)
            ):
                return ValidationResult(True, "OK")
            return ValidationResult(False, "Off-hand requires one-handed weapon or shield")
        if is_two_handed_weapon(main_hand_weapon, off_hand_present=True):
            return ValidationResult(False, "Main hand weapon is two-handed")
        if is_ranged_weapon(main_hand_weapon):
            return ValidationResult(False, "Ranged weapons cannot be dual-wielded")
        if not (
            offhand_weapon
            and (
                is_one_handed_weapon(offhand_weapon, off_hand_present=True)
                or is_shield(offhand_weapon)
            )
        ):
            return ValidationResult(False, "Off-hand must be one-handed weapon or shield")
        return ValidationResult(True, "OK")

    def can_wield_variable_one_handed(
        self, unit, weapon_id: str, weapon: dict | None = None
    ) -> ValidationResult:
        """Check if unit meets Erő and Ügyesség requirements for one-handed wielding of variable weapon. Accepts cached weapon object."""
        if weapon is None:
            weapon = self.equipment_repo.find_weapon_by_id(weapon_id)
        if not weapon or weapon.get("wield_mode", "").lower() not in ["variable", "változó"]:
            return ValidationResult(False, "Not a variable wield mode weapon")
        # Read requirements from weapon JSON
        str_req = weapon.get("variable_strength_req", 0)
        dex_req = weapon.get("variable_dex_req", 0)
        # Get unit attributes
        unit_str = getattr(unit, "Tulajdonságok", {}).get("Erő", 0)
        unit_dex = getattr(unit, "Tulajdonságok", {}).get("Ügyesség", 0)
        if unit_str < str_req:
            return ValidationResult(False, f"Insufficient strength (required: {str_req})")
        if unit_dex < dex_req:
            return ValidationResult(False, f"Insufficient dexterity (required: {dex_req})")
        return ValidationResult(True, "OK")

    def validate_armor_compatibility(
        self, armor_ids: list[str]
    ) -> tuple[bool, list[str], dict[str, list[tuple[str, str]]]]:
        """Validate armor pieces for layer/zone conflicts.

        Args:
            armor_ids: List of armor piece IDs to validate

        Returns:
            Tuple of:
            - is_valid: Whether configuration is valid (no same-layer overlaps)
            - warnings: List of warning messages
            - conflicts: Dict mapping armor_id -> list of (conflicting_armor_id, zone) tuples
        """
        if not armor_ids:
            return True, [], {}

        # Load armor pieces and create ArmorPieces
        armor_pieces = []
        for armor_id in armor_ids:
            armor_data = self.equipment_repo.find_armor_by_id(armor_id)
            if not armor_data:
                logger.warning(f"Armor not found: {armor_id}")
                continue

            # Create ArmorPiece from data
            piece = ArmorPiece(
                id=armor_data.get("id", armor_id),
                name=armor_data.get("name", armor_id),
                parts=armor_data.get("parts", {}),
                mgt=armor_data.get("mgt", 0),
                armor_type=armor_data.get("armor_type", "leather"),
                layer=armor_data.get("layer", 3),
                protection_overrides=armor_data.get("protection_overrides", {}),
            )
            armor_pieces.append(piece)

        if not armor_pieces:
            return True, [], {}

        # Create ArmorSystem and validate
        armor_system = ArmorSystem(pieces=armor_pieces)
        is_valid, error_msg = armor_system.validate_no_overlap_same_layer()

        # Build conflict map
        conflicts: dict[str, list[tuple[str, str]]] = {}
        warnings = []

        if not is_valid:
            warnings.append(error_msg)

            # Detect specific conflicts
            seen: dict[tuple[int, str], str] = {}
            for piece in armor_pieces:
                for zone, sfe in piece.parts.items():
                    if sfe <= 0:
                        continue
                    key = (piece.layer, zone)
                    if key in seen:
                        # Conflict found
                        other_id = seen[key]
                        if piece.id not in conflicts:
                            conflicts[piece.id] = []
                        conflicts[piece.id].append((other_id, zone))

                        if other_id not in conflicts:
                            conflicts[other_id] = []
                        conflicts[other_id].append((piece.id, zone))
                    else:
                        seen[key] = piece.id

        return is_valid, warnings, conflicts

    def validate_equipment_slots(self, equipment: dict[str, str | list]) -> dict[str, str]:
        """Validate all equipment slots and return warnings.

        Args:
            equipment: Equipment configuration with slot -> item_id mappings

        Returns:
            Dictionary of slot -> warning message (empty if valid)
        """
        warnings = {}

        # Use enums for slot keys
        main_hand = equipment.get(Slot.MAIN_HAND)
        off_hand = equipment.get(Slot.OFF_HAND)

        # Validate off-hand
        if off_hand and isinstance(off_hand, str):
            result = self.can_equip_offhand(
                main_hand if isinstance(main_hand, str) else None, off_hand
            )
            if not result.success:
                warnings[Slot.OFF_HAND.value] = result.message

        # Validate armor
        armor_list = equipment.get("armor", [])
        if isinstance(armor_list, list) and armor_list:
            is_valid, armor_warnings, conflicts = self.validate_armor_compatibility(armor_list)
            if armor_warnings:
                # Note: We allow equipping despite conflicts, just warn
                warnings["armor"] = "; ".join(armor_warnings)

        return warnings
