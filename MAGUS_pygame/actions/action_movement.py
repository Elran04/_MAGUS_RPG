"""
Movement action helpers: range computation and movement resolution.
"""
from typing import Set, Tuple
from systems.hex_grid import hexes_in_range, hex_distance
from systems.reach import compute_reach_hexes
from config import MOVEMENT_RANGE, AP_COST_MOVEMENT, ActionMode
from core.game_state import GameState, next_turn, check_defeat
from actions.action_opportunity import handle_opportunity_attack


def compute_reachable(state: GameState) -> Set[Tuple[int, int]]:
    """
    Compute movement range from start, excluding enemy-occupied hex to prevent stacking.
    Range is limited by remaining action points (2 AP per hex).
    Also computes enemy's zone of control for visual warning.
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
    
    # Compute enemy's zone of control for visual warning
    eq, er = enemy_pos
    state.enemy_zone_hexes = compute_reach_hexes(eq, er, enemy_unit.facing, enemy_unit.size_category)
    
    return reachable


def apply_move_if_valid(state: GameState, q: int, r: int) -> bool:
    """
    Attempt to move active unit to (q,r). 
    Deducts AP_COST_MOVEMENT (2 AP) per hex distance from turn start position.
    Checks for Zone of Control and triggers opportunity attacks if enemy hasn't used theirs yet.
    On success, advance turn if no AP left, otherwise allow more actions.
    Returns True if moved.
    """
    if state.action_mode != ActionMode.MOVE or (q, r) not in state.reachable_for_active:
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
    
    # Check for Zone of Control - opportunity attack
    attacked, opp_msg = handle_opportunity_attack(state, state.active_unit)
    if attacked and opp_msg:
        print(opp_msg)
        # Display message on screen
        state.combat_message = opp_msg
        state.message_timer = 180  # Show for ~3 seconds at 60 FPS
        # Check if the mover was defeated by the opportunity attack
        if check_defeat(state):
            print(f"\n{state.winner.name} is victorious! {state.active_unit.name} was defeated by an opportunity attack!")
            return True
    
    # Update turn start position for further movement calculations
    state.turn_start_pos = state.active_unit.get_position()
    
    # If no AP left, end turn automatically
    if state.active_unit.current_action_points <= 0:
        next_turn(state)
        state.action_mode = ActionMode.MOVE
        state.attackable_for_active = set()
        compute_reachable(state)
    else:
        # Recalculate reachable hexes from new position
        compute_reachable(state)
    
    return True


def skip_turn(state: GameState) -> None:
    """Skip current turn and prepare next turn state."""
    next_turn(state)
    state.action_mode = ActionMode.MOVE
    state.attackable_for_active = set()
    compute_reachable(state)
