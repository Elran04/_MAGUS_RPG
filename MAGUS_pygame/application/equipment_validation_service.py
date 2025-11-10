"""Equipment Validation Service - Validates equipment slot assignments.

Handles:
- Main/off-hand weapon compatibility (two-handed vs one-handed)
- Armor piece compatibility validation
- Quick access slot validation
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from logger.logger import get_logger
from domain.mechanics.armor import ArmorPiece, ArmorSystem

if TYPE_CHECKING:
    from infrastructure.repositories import EquipmentRepository

logger = get_logger(__name__)


class EquipmentValidationService:
    """Service for validating equipment configurations.
    
    Responsibilities:
    - Check weapon hand requirements (one-handed vs two-handed)
    - Validate off-hand eligibility based on main hand weapon
    - Provide human-readable validation messages
    """
    
    def __init__(self, equipment_repo: "EquipmentRepository"):
        """Initialize equipment validation service.
        
        Args:
            equipment_repo: Equipment repository for looking up item data
        """
        self.equipment_repo = equipment_repo
    
    def is_one_handed_weapon(self, weapon_id: str) -> bool:
        """Check if a weapon is one-handed.
        
        Args:
            weapon_id: Weapon identifier
            
        Returns:
            True if weapon is one-handed, False otherwise
        """
        weapon = self.equipment_repo.find_weapon_by_id(weapon_id)
        if not weapon:
            logger.warning(f"Weapon not found: {weapon_id}")
            return False
        
        wield_mode = weapon.get("wield_mode", "").lower()
        return wield_mode in ["egykezes", "one-handed", "1h"]
    
    def is_two_handed_weapon(self, weapon_id: str) -> bool:
        """Check if a weapon is two-handed.
        
        Args:
            weapon_id: Weapon identifier
            
        Returns:
            True if weapon is two-handed, False otherwise
        """
        weapon = self.equipment_repo.find_weapon_by_id(weapon_id)
        if not weapon:
            return False
        
        wield_mode = weapon.get("wield_mode", "").lower()
        return wield_mode in ["kétkezes", "two-handed", "2h"]
    
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
        
        # Check if main hand is two-handed
        if self.is_two_handed_weapon(main_hand_id):
            return False, "Main hand weapon is two-handed"
        
        # Check if main hand is ranged
        if self.is_ranged_weapon(main_hand_id):
            return False, "Ranged weapons cannot be dual-wielded"
        
        # Main hand is one-handed melee, check off-hand
        if not (self.is_one_handed_weapon(offhand_id) or self.is_shield(offhand_id)):
            return False, "Off-hand must be one-handed weapon or shield"
        
        return True, "OK"
    
    def validate_armor_compatibility(self, armor_ids: list[str]) -> tuple[bool, list[str], dict[str, list[tuple[str, str]]]]:
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
            can_equip, reason = self.can_equip_offhand(main_hand if isinstance(main_hand, str) else None, off_hand)
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
