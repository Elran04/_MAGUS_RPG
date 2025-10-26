"""
Movement and combat helpers: range computation, attackability, and action resolution.
"""
from typing import Set, Tuple
from hex_grid import hex_distance, hexes_in_range
from config import MOVEMENT_RANGE, ATTACK_RANGE
from game_state import GameState


def compute_reachable(state: GameState) -> Set[Tuple[int, int]]:
    """Compute movement range from start, excluding enemy-occupied hex to prevent stacking.
    Updates and returns state.reachable_for_active.
    """
    reachable = hexes_in_range(state.turn_start_pos[0], state.turn_start_pos[1], MOVEMENT_RANGE)
    enemy_pos = state.goblin.get_position() if state.turn == 0 else state.warrior.get_position()
    if enemy_pos in reachable:
        reachable.remove(enemy_pos)
    state.reachable_for_active = reachable
    return reachable


def compute_attackable(state: GameState) -> Set[Tuple[int, int]]:
    """Mark enemy hex if within attack range; updates and returns state.attackable_for_active."""
    active_pos = state.warrior.get_position() if state.turn == 0 else state.goblin.get_position()
    enemy_pos = state.goblin.get_position() if state.turn == 0 else state.warrior.get_position()
    if hex_distance(active_pos[0], active_pos[1], enemy_pos[0], enemy_pos[1]) <= ATTACK_RANGE:
        state.attackable_for_active = {enemy_pos}
    else:
        state.attackable_for_active = set()
    return state.attackable_for_active


def _set_turn_start_to_active(state: GameState) -> None:
    """Set the turn start position to the current active unit's position."""
    state.turn_start_pos = state.warrior.get_position() if state.turn == 0 else state.goblin.get_position()


def next_turn(state: GameState) -> None:
    state.turn = (state.turn + 1) % 2
    _set_turn_start_to_active(state)


def apply_move_if_valid(state: GameState, q: int, r: int) -> bool:
    """Attempt to move active unit to (q,r). On success, advance turn and refresh reachable. Returns True if moved."""
    if state.action_mode != "move" or (q, r) not in state.reachable_for_active:
        return False
    enemy_pos = state.goblin.get_position() if state.turn == 0 else state.warrior.get_position()
    if (q, r) == enemy_pos:
        return False
    if state.turn == 0:
        state.warrior.move_to(q, r)
    else:
        state.goblin.move_to(q, r)
    # Advance turn and reset mode/overlays
    next_turn(state)
    state.action_mode = "move"
    state.attackable_for_active = set()
    compute_reachable(state)
    return True


def handle_attack_click(state: GameState, q: int, r: int) -> bool:
    """Attempt an attack if clicking enemy in range. On success, advance turn and refresh reachable. Returns True if attacked."""
    active_unit = state.warrior if state.turn == 0 else state.goblin
    enemy_unit = state.goblin if state.turn == 0 else state.warrior
    eq, er = enemy_unit.get_position()
    if (q, r) == (eq, er):
        aq, ar = active_unit.get_position()
        if hex_distance(aq, ar, eq, er) <= ATTACK_RANGE:
            print(f"{'Player' if state.turn == 0 else 'Enemy'} attacks!")
            # Advance turn and reset mode/overlays
            next_turn(state)
            state.action_mode = "move"
            state.attackable_for_active = set()
            compute_reachable(state)
            return True
    return False


def skip_turn(state: GameState) -> None:
    """Skip current turn and prepare next turn state."""
    next_turn(state)
    state.action_mode = "move"
    state.attackable_for_active = set()
    compute_reachable(state)
