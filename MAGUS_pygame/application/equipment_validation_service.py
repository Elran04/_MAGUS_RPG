"""Equipment Validation Service - Validates equipment slot assignments.

Handles:
- Main/off-hand weapon compatibility (two-handed vs one-handed)
- Armor piece compatibility validation
- Quick access slot validation
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from domain.mechanics.armor import ArmorPiece, ArmorSystem
from logger.logger import get_logger

if TYPE_CHECKING:
    from infrastructure.repositories import EquipmentRepository

logger = get_logger(__name__)


class EquipmentValidationService:
    def get_wield_mode_hint(self, unit, weapon_id: str, weapon: dict | None = None) -> str:
        """Return wield mode hint for a weapon for a given unit (e.g., '(1h/2h)', '(2h only)'). Accepts cached weapon object."""
        if weapon is None:
            weapon = self.equipment_repo.find_weapon_by_id(weapon_id)
        if not weapon:
            return ""
        wield_mode = weapon.get("wield_mode", "").lower()
        if wield_mode in ["változó", "variable"]:
            can_wield_1h, _ = self.can_wield_variable_one_handed(unit, weapon_id, weapon)
            if can_wield_1h:
                return "(1h/2h)"
            else:
                return "(2h only)"
        elif wield_mode in ["egykezes", "one-handed", "1h"]:
            return "(1h)"
        elif wield_mode in ["kétkezes", "two-handed", "2h"]:
            return "(2h)"
        return ""

    def is_item_eligible(self, unit, slot: str, item_id: str, selected_wield_mode: str | None = None) -> tuple[bool, str]:
        """Check if an item is eligible for a slot for a given unit. Only call weapon logic for weapon/shield items."""
        repo = self.equipment_repo
        # Determine item category
        weapons = repo.load_weapons()
        armor = repo.load_armor()
        is_weapon = any(w.get("id") == item_id for w in weapons)
        is_armor = any(a.get("id") == item_id for a in armor)
        weapon = repo.find_weapon_by_id(item_id) if is_weapon else None
        wield_mode = weapon.get("wield_mode", "") if weapon else ""
        # Weapon slots
        if slot in ["main_hand", "weapon_quick_1", "weapon_quick_2"]:
            if not is_weapon:
                return False, "Not a weapon"
            # Main hand: weapons only
            if slot == "main_hand":
                is_valid_weapon = (
                    self.is_one_handed_weapon(item_id)
                    or self.is_two_handed_weapon(item_id)
                    or self.is_ranged_weapon(item_id)
                )
                if not is_valid_weapon:
                    return False, "Not a weapon"
            # Quick slots: weapons or shields allowed
            elif slot in ["weapon_quick_1", "weapon_quick_2"]:
                is_valid_weapon = (
                    self.is_one_handed_weapon(item_id)
                    or self.is_two_handed_weapon(item_id)
                    or self.is_ranged_weapon(item_id)
                )
                is_shield = self.is_shield(item_id)
                if not (is_valid_weapon or is_shield):
                    return False, "Not a weapon or shield"
            # If variable, check selected wield mode
            if wield_mode in ["variable", "változó"] and selected_wield_mode:
                if selected_wield_mode == "one_handed":
                    can_wield, reason = self.can_wield_variable_one_handed(unit, item_id, weapon)
                    if not can_wield:
                        return False, reason
                    return True, "OK"
                elif selected_wield_mode == "two_handed":
                    return True, "OK"
            return True, "OK"
        # Off-hand slot
        if slot == "off_hand":
            if not is_weapon:
                return False, "Not a weapon/shield"
            main_hand_id = None
            can_equip, reason = self.can_equip_offhand(main_hand_id, item_id)
            return can_equip, reason
        # Armor slot
        if slot == "armor":
            if not is_armor:
                return False, "Not armor"
            return True, "OK"
        # Quick access slots
        if slot in ["quick_access_1", "quick_access_2"]:
            if is_weapon or is_armor:
                return False, "Not general item"
            return True, "OK"
        return False, "Unknown slot"
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

    def is_one_handed_weapon(self, weapon_id: str, off_hand_present: bool = False) -> bool:
        """Check if a weapon is one-handed.

        Args:
            weapon_id: Weapon identifier

            off_hand_present: If True, treat variable wield mode as one-handed

        Returns:
            True if weapon is one-handed, False otherwise
        """
        weapon = self.equipment_repo.find_weapon_by_id(weapon_id)
        if not weapon:
            logger.warning(f"Weapon not found: {weapon_id}")
            return False

        wield_mode = weapon.get("wield_mode", "").lower()
        if wield_mode in ["egykezes", "one-handed", "1h"]:
            return True
        if wield_mode == "változó" and off_hand_present:
            return True
        return False

    def is_two_handed_weapon(self, weapon_id: str, off_hand_present: bool = False) -> bool:
        """Check if a weapon is two-handed.

        Args:
            weapon_id: Weapon identifier

            off_hand_present: If True, treat variable wield mode as one-handed

        Returns:
            True if weapon is two-handed, False otherwise
        """
        weapon = self.equipment_repo.find_weapon_by_id(weapon_id)
        if not weapon:
            return False

        wield_mode = weapon.get("wield_mode", "").lower()
        if wield_mode in ["kétkezes", "two-handed", "2h"]:
            return True
        if wield_mode == "változó" and not off_hand_present:
            return True
        return False

    def is_ranged_weapon(self, weapon_id: str) -> bool:
        """Check if a weapon is ranged.

        Args:
            weapon_id: Weapon identifier

        Returns:
            True if weapon is ranged, False otherwise
        """
        weapon = self.equipment_repo.find_weapon_by_id(weapon_id)
        if not weapon:
            return False

        weapon_type = weapon.get("type", "").lower()
        return weapon_type in ["távolsági", "ranged", "íjászfegyver"]

    def is_shield(self, item_id: str) -> bool:
        """Check if an item is a shield.

        Args:
            item_id: Item identifier

        Returns:
            True if item is a shield, False otherwise
        """
        weapon = self.equipment_repo.find_weapon_by_id(item_id)
        if not weapon:
            return False

        weapon_type = weapon.get("type", "").lower()
        return weapon_type == "pajzs" or weapon_type == "shield"

    def can_equip_offhand(self, main_hand_id: str | None, offhand_id: str) -> tuple[bool, str]:
        """Check if an item can be equipped in the off-hand.

        Args:
            main_hand_id: Currently equipped main hand weapon ID (or None)
            offhand_id: Item to check for off-hand

        Returns:
            Tuple of (can_equip: bool, reason: str)
        """
        # If no main hand weapon, off-hand must be one-handed weapon or shield
        if not main_hand_id:
            if self.is_one_handed_weapon(offhand_id) or self.is_shield(offhand_id):
                return True, "OK"
            return False, "Off-hand requires one-handed weapon or shield"

        # Check if main hand is two-handed (pass off_hand_present)
        if self.is_two_handed_weapon(main_hand_id, off_hand_present=True):
            return False, "Main hand weapon is two-handed"

        # Check if main hand is ranged
        if self.is_ranged_weapon(main_hand_id):
            return False, "Ranged weapons cannot be dual-wielded"

        # Main hand is one-handed melee, check off-hand (pass off_hand_present)
        if not (self.is_one_handed_weapon(offhand_id, off_hand_present=True) or self.is_shield(offhand_id)):
            return False, "Off-hand must be one-handed weapon or shield"

        return True, "OK"

    def can_wield_variable_one_handed(self, unit, weapon_id: str, weapon: dict | None = None) -> tuple[bool, str]:
        """Check if unit meets Erő and Ügyesség requirements for one-handed wielding of variable weapon. Accepts cached weapon object."""
        if weapon is None:
            weapon = self.equipment_repo.find_weapon_by_id(weapon_id)
        if not weapon or weapon.get("wield_mode", "").lower() not in ["variable", "változó"]:
            return False, "Not a variable wield mode weapon"
        # Read requirements from weapon JSON
        str_req = weapon.get("variable_strength_req", 0)
        dex_req = weapon.get("variable_dex_req", 0)
        # Get unit attributes
        unit_str = getattr(unit, "Tulajdonságok", {}).get("Erő", 0)
        unit_dex = getattr(unit, "Tulajdonságok", {}).get("Ügyesség", 0)
        if unit_str < str_req:
            return False, f"Insufficient strength (required: {str_req})"
        if unit_dex < dex_req:
            return False, f"Insufficient dexterity (required: {dex_req})"
        return True, "OK"

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

        main_hand = equipment.get("main_hand")
        off_hand = equipment.get("off_hand")

        # Validate off-hand
        if off_hand and isinstance(off_hand, str):
            can_equip, reason = self.can_equip_offhand(
                main_hand if isinstance(main_hand, str) else None, off_hand
            )
            if not can_equip:
                warnings["off_hand"] = reason

        # Validate armor
        armor_list = equipment.get("armor", [])
        if isinstance(armor_list, list) and armor_list:
            is_valid, armor_warnings, conflicts = self.validate_armor_compatibility(armor_list)
            if armor_warnings:
                # Note: We allow equipping despite conflicts, just warn
                warnings["armor"] = "; ".join(armor_warnings)

        return warnings
