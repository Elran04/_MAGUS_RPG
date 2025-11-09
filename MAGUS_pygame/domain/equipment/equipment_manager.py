"""
Equipment Manager - manages equipped armor sets and validation.

Interfaces kept minimal for now; integrates with ArmorSystem for layering rules.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from domain.mechanics.armor import ArmorPiece, ArmorSystem


@dataclass
class EquipmentManager:
    """Handles equipping armor pieces and exposing aggregate properties."""

    armor_system: ArmorSystem = field(default_factory=ArmorSystem)

    def equip_armor(self, piece: ArmorPiece) -> tuple[bool, str]:
        """Attempt to equip a new armor piece; validate overlapping zones on same layer."""
        candidate = ArmorSystem(self.armor_system.pieces + [piece])
        ok, msg = candidate.validate_no_overlap_same_layer()
        if not ok:
            return False, msg
        self.armor_system = candidate
        return True, ""

    def set_armor_set(self, pieces: list[ArmorPiece]) -> tuple[bool, str]:
        system = ArmorSystem(list(pieces))
        ok, msg = system.validate_no_overlap_same_layer()
        if not ok:
            return False, msg
        self.armor_system = system
        return True, ""

    def get_total_mgt(self) -> int:
        return self.armor_system.get_total_mgt()

    def get_armor_system(self) -> ArmorSystem:
        return self.armor_system
