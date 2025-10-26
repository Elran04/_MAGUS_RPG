"""
Movement action helpers: range computation and movement resolution.
"""
from typing import Set, Tuple
from hex_grid import hexes_in_range, hex_distance
from config import MOVEMENT_RANGE, AP_COST_MOVEMENT
from game_state import GameState


def compute_reachable(state: GameState) -> Set[Tuple[int, int]]:
    """
    Compute movement range from start, excluding enemy-occupied hex to prevent stacking.
    Range is limited by remaining action points (2 AP per hex).
    Updates and returns state.reachable_for_active.
    """
    # Calculate max distance based on remaining AP
    max_distance = state.active_unit.current_action_points // AP_COST_MOVEMENT
    # Use minimum of MOVEMENT_RANGE and AP-based range
    effective_range = min(MOVEMENT_RANGE, max_distance)
    
    reachable = hexes_in_range(state.turn_start_pos[0], state.turn_start_pos[1], effective_range)
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
    Resets action points when switching to a new unit.
    """
    from action_handling import roll_initiative
    
    # Mark current unit as having acted
    state.units_acted_this_round.add(state.active_unit.name)
    
    # Check if both units have acted this round
    if len(state.units_acted_this_round) >= 2:
        # Round complete - roll new initiative for next round
        state.round += 1
        roll_initiative(state)  # This resets AP for both units
    else:
        # Switch to next unit in turn order
        current_idx = state.turn_order.index(state.active_unit)
        next_idx = (current_idx + 1) % len(state.turn_order)
        state.active_unit = state.turn_order[next_idx]
        state.turn = 0 if state.active_unit == state.warrior else 1
        
        # Reset action points for the new active unit
        state.active_unit.current_action_points = state.active_unit.max_action_points
    
    _set_turn_start_to_active(state)


def apply_move_if_valid(state: GameState, q: int, r: int) -> bool:
    """
    Attempt to move active unit to (q,r). 
    Deducts AP_COST_MOVEMENT (2 AP) per hex distance from turn start position.
    On success, advance turn if no AP left, otherwise allow more actions.
    Returns True if moved.
    """
    if state.action_mode != "move" or (q, r) not in state.reachable_for_active:
        return False
    
    # Calculate hex distance from turn start position
    start_q, start_r = state.turn_start_pos
    distance = hex_distance(start_q, start_r, q, r)
    ap_cost = distance * AP_COST_MOVEMENT
    
    # Check if unit has enough action points
    if state.active_unit.current_action_points < ap_cost:
        print(f"{state.active_unit.name} doesn't have enough AP to move {distance} hexes! (Need {ap_cost}, have {state.active_unit.current_action_points})")
        return False
    
    enemy_unit = state.goblin if state.active_unit == state.warrior else state.warrior
    enemy_pos = enemy_unit.get_position()
    if (q, r) == enemy_pos:
        return False
    
    # Move the unit and deduct AP
    state.active_unit.move_to(q, r)
    state.active_unit.current_action_points -= ap_cost
    print(f"{state.active_unit.name} moved {distance} hex(es) (cost: {ap_cost} AP). AP remaining: {state.active_unit.current_action_points}/{state.active_unit.max_action_points}")
    
    # Update turn start position for further movement calculations
    state.turn_start_pos = state.active_unit.get_position()
    
    # If no AP left, end turn automatically
    if state.active_unit.current_action_points <= 0:
        next_turn(state)
        state.action_mode = "move"
        state.attackable_for_active = set()
        compute_reachable(state)
    else:
        # Recalculate reachable hexes from new position
        compute_reachable(state)
    
    return True


def skip_turn(state: GameState) -> None:
    """Skip current turn and prepare next turn state."""
    next_turn(state)
    state.action_mode = "move"
    state.attackable_for_active = set()
    compute_reachable(state)
