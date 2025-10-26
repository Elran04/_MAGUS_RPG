"""
Movement action helpers: range computation and movement resolution.
"""
from typing import Set, Tuple
from hex_grid import hexes_in_range
from config import MOVEMENT_RANGE
from game_state import GameState


def compute_reachable(state: GameState) -> Set[Tuple[int, int]]:
    """Compute movement range from start, excluding enemy-occupied hex to prevent stacking.
    Updates and returns state.reachable_for_active.
    """
    reachable = hexes_in_range(state.turn_start_pos[0], state.turn_start_pos[1], MOVEMENT_RANGE)
    enemy_unit = state.goblin if state.active_unit == state.warrior else state.warrior
    enemy_pos = enemy_unit.get_position()
    if enemy_pos in reachable:
        reachable.remove(enemy_pos)
    state.reachable_for_active = reachable
    return reachable


def _set_turn_start_to_active(state: GameState) -> None:
    """Set the turn start position to the current active unit's position."""
    state.turn_start_pos = state.active_unit.get_position()


def next_turn(state: GameState) -> None:
    """
    End current unit's turn and switch to next unit.
    If both units have acted, start a new round with fresh initiative.
    """
    from action_handling import roll_initiative
    
    # Mark current unit as having acted
    state.units_acted_this_round.add(state.active_unit.name)
    
    # Check if both units have acted this round
    if len(state.units_acted_this_round) >= 2:
        # Round complete - roll new initiative for next round
        state.round += 1
        roll_initiative(state)
    else:
        # Switch to next unit in turn order
        current_idx = state.turn_order.index(state.active_unit)
        next_idx = (current_idx + 1) % len(state.turn_order)
        state.active_unit = state.turn_order[next_idx]
        state.turn = 0 if state.active_unit == state.warrior else 1
    
    _set_turn_start_to_active(state)


def apply_move_if_valid(state: GameState, q: int, r: int) -> bool:
    """Attempt to move active unit to (q,r). On success, advance turn and refresh reachable. Returns True if moved."""
    if state.action_mode != "move" or (q, r) not in state.reachable_for_active:
        return False
    enemy_unit = state.goblin if state.active_unit == state.warrior else state.warrior
    enemy_pos = enemy_unit.get_position()
    if (q, r) == enemy_pos:
        return False
    state.active_unit.move_to(q, r)
    # Advance turn and reset mode/overlays
    next_turn(state)
    state.action_mode = "move"
    state.attackable_for_active = set()
    compute_reachable(state)
    return True


def skip_turn(state: GameState) -> None:
    """Skip current turn and prepare next turn state."""
    next_turn(state)
    state.action_mode = "move"
    state.attackable_for_active = set()
    compute_reachable(state)
