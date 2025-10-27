"""
Game state container to centralize turn and UI state for cleaner module interfaces.
"""
from dataclasses import dataclass, field
from typing import Dict, Set, Tuple, List
from core.unit_manager import Unit
from config import ActionMode


@dataclass
class GameState:
    # Core turn/action
    round: int = 1  # Round counter
    turn: int = 0  # Turn counter (increments each action)
    active_unit: Unit = None  # The unit currently taking their turn
    units_acted_this_round: Set[str] = field(default_factory=set)  # Track who has acted
    action_mode: str = ActionMode.MOVE  # ActionMode.MOVE | ActionMode.ATTACK | ActionMode.CHANGE_FACING

    # Game over tracking
    game_over: bool = False
    winner: Unit = None

    # Initiative tracking
    initiative_rolls: Dict[str, int] = field(default_factory=dict)  # unit_name -> d100+KÉ
    turn_order: list = field(default_factory=list)  # Ordered list of units for this round

    # Positions and overlays
    turn_start_pos: Tuple[int, int] = (0, 0)
    reachable_for_active: Set[Tuple[int, int]] = field(default_factory=set)
    attackable_for_active: Set[Tuple[int, int]] = field(default_factory=set)
    charge_targets: Set[Tuple[int, int]] = field(default_factory=set)  # Valid charge targets
    enemy_zone_hexes: Set[Tuple[int, int]] = field(default_factory=set)  # Enemy's zone of control
    preview_path: List[Tuple[int, int]] = field(default_factory=list)  # Path preview for movement
    
    # Combat messages
    combat_message: str = ""  # Display combat events (attacks, opportunity attacks, etc.)
    message_timer: int = 0  # Frame counter for message display
    
    # Charge attack state
    charge_damage_multiplier: int = 1  # Damage multiplier for charge attacks

    # UI and units
    ui_state: Dict[str, object] = field(default_factory=dict)
    warrior: Unit = None
    goblin: Unit = None


def check_defeat(state: GameState) -> bool:
    """
    Check if any unit has been defeated (ÉP <= 0).
    If so, set game_over flag and winner.
    
    Returns:
        True if game is over, False otherwise
    """
    if state.warrior.current_ep <= 0:
        state.game_over = True
        state.winner = state.goblin
        return True
    
    if state.goblin.current_ep <= 0:
        state.game_over = True
        state.winner = state.warrior
        return True
    
    return False


def next_turn(state: GameState) -> None:
    """
    End current unit's turn and switch to next unit.
    If both units have acted, start a new round with fresh initiative.
    Resets action points when switching to a new unit.
    """
    from actions.action_handling import roll_initiative
    
    # Mark current unit as having acted
    state.units_acted_this_round.add(state.active_unit.name)
    
    # Check if both units have acted this round
    if len(state.units_acted_this_round) >= 2:
        # Round complete - roll new initiative for next round
        state.round += 1
        roll_initiative(state)  # This resets AP for both units
        # Reset ZOC opportunity attacks for all units
        state.warrior.has_used_opportunity_attack = False
        state.goblin.has_used_opportunity_attack = False
    else:
        # Switch to next unit in turn order
        current_idx = state.turn_order.index(state.active_unit)
        next_idx = (current_idx + 1) % len(state.turn_order)
        state.active_unit = state.turn_order[next_idx]
        state.turn = 0 if state.active_unit == state.warrior else 1
        
        # Reset action points for the new active unit
        state.active_unit.current_action_points = state.active_unit.max_action_points
    
    # Set turn start position to current active unit's position
    state.turn_start_pos = state.active_unit.get_position()
