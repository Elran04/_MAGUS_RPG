"""Scenario selection phases.

Modular phase-based architecture for scenario selection:
- MapSelectionPhase: Choose scenario/map
- TeamCompositionPhase: Build team roster (reusable for both teams)
- EquipmentPhase: Equip characters (TODO)

Each phase implements SelectionPhaseBase for consistent interface.
"""

from .equipment_phase import EquipmentPhase
from .map_phase import MapSelectionPhase
from .phase_base import SelectionPhaseBase
from .team_phase import TeamCompositionPhase

__all__ = [
    "SelectionPhaseBase",
    "MapSelectionPhase",
    "TeamCompositionPhase",
    "EquipmentPhase",
]
