"""
Game state container to centralize turn and UI state for cleaner module interfaces.
"""
from dataclasses import dataclass, field
from typing import Dict, Set, Tuple
from sprite_manager import Unit


@dataclass
class GameState:
    # Core turn/action
    turn: int = 0  # 0: Player, 1: Enemy
    action_mode: str = "move"  # "move" | "attack"

    # Positions and overlays
    turn_start_pos: Tuple[int, int] = (0, 0)
    reachable_for_active: Set[Tuple[int, int]] = field(default_factory=set)
    attackable_for_active: Set[Tuple[int, int]] = field(default_factory=set)

    # UI and units
    ui_state: Dict[str, object] = field(default_factory=dict)
    warrior: Unit = None
    goblin: Unit = None
