"""
Game state container to centralize turn and UI state for cleaner module interfaces.
"""
from dataclasses import dataclass, field
from typing import Dict, Set, Tuple
from sprite_manager import Unit


@dataclass
class GameState:
    # Core turn/action
    round: int = 1  # Round counter
    turn: int = 0  # Turn counter (increments each action)
    active_unit: Unit = None  # The unit currently taking their turn
    units_acted_this_round: Set[str] = field(default_factory=set)  # Track who has acted
    action_mode: str = "move"  # "move" | "attack"

    # Initiative tracking
    initiative_rolls: Dict[str, int] = field(default_factory=dict)  # unit_name -> d100+KÉ
    turn_order: list = field(default_factory=list)  # Ordered list of units for this round

    # Positions and overlays
    turn_start_pos: Tuple[int, int] = (0, 0)
    reachable_for_active: Set[Tuple[int, int]] = field(default_factory=set)
    attackable_for_active: Set[Tuple[int, int]] = field(default_factory=set)

    # UI and units
    ui_state: Dict[str, object] = field(default_factory=dict)
    warrior: Unit = None
    goblin: Unit = None
