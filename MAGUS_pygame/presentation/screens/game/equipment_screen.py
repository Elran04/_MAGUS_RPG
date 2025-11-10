"""
EquipmentScreen: lightweight screen model for viewing unit armor loadouts.

Note: This is a data-only screen for now (no pygame drawing). It builds a report
per unit that a UI layer can render. Uncovered zones are informational only.
"""

from __future__ import annotations

from dataclasses import dataclass

from presentation.adapters.equipment_view import EquipmentView
from domain.entities import Unit


@dataclass
class UnitLoadoutReport:
    unit_id: str
    unit_name: str
    zone_sfe: dict[str, int]
    uncovered_zones: list[str]
    overlap_messages: list[str]
    total_mgt: int


class EquipmentScreen:
    def __init__(self, units: list[Unit]) -> None:
        self._units = units
        self._complete = False

    def is_complete(self) -> bool:
        return self._complete

    def mark_complete(self) -> None:
        self._complete = True

    def build_reports(self) -> list[UnitLoadoutReport]:
        reports: list[UnitLoadoutReport] = []
        for u in self._units:
            view = EquipmentView(u)
            reports.append(
                UnitLoadoutReport(
                    unit_id=u.id,
                    unit_name=u.name,
                    zone_sfe=view.get_zone_sfe_map(),
                    uncovered_zones=view.get_uncovered_zones(),
                    overlap_messages=view.get_overlap_messages(),
                    total_mgt=view.get_total_mgt(),
                )
            )
        return reports
