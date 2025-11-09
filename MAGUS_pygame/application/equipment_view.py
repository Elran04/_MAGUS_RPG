"""
EquipmentView adapter for presenting armor loadout information without exposing
internal armor structures to the UI.

- Surfaces overlap validation messages
- Lists uncovered main zones (info-only)
- Exposes per-zone current SFÉ and total MGT
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from domain.entities import Unit
from domain.mechanics.armor import ArmorSystem, MAIN_PARTS


@dataclass
class EquipmentView:
    unit: Unit

    def _system(self) -> ArmorSystem | None:
        return getattr(self.unit, "armor_system", None)

    def has_armor(self) -> bool:
        return self._system() is not None and len(self._system().pieces) > 0  # type: ignore[operator]

    def get_overlap_messages(self) -> List[str]:
        sys = self._system()
        if not sys:
            return []
        ok, msg = sys.validate_no_overlap_same_layer()
        return [] if ok or not msg else [msg]

    def get_uncovered_zones(self) -> List[str]:
        sys = self._system()
        if not sys:
            # Without an armor system, treat all zones as uncovered
            return list(MAIN_PARTS)
        missing: List[str] = []
        for part in MAIN_PARTS:
            if sys.get_sfe_for_hit(part) <= 0:
                missing.append(part)
        return missing

    def get_zone_sfe_map(self) -> Dict[str, int]:
        sys = self._system()
        zone_map: Dict[str, int] = {}
        for part in MAIN_PARTS:
            zone_map[part] = sys.get_sfe_for_hit(part) if sys else 0
        return zone_map

    def get_total_mgt(self) -> int:
        sys = self._system()
        return sys.get_total_mgt() if sys else 0
