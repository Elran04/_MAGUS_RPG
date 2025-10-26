"""
Movement and combat helpers: range computation, attackability, and action resolution.
"""
import random
from typing import Set, Tuple
from hex_grid import hex_distance, hexes_in_range
from config import MOVEMENT_RANGE, ATTACK_RANGE
from game_state import GameState


def roll_initiative(state: GameState) -> None:
    """
    Roll initiative for both units (d100 + KÉ).
    Determine turn order for the round and set first active unit.
    In case of tie, higher base KÉ wins. If still tied, reroll.
    """
    warrior_ke = state.warrior.KE
    goblin_ke = state.goblin.KE
    
    while True:
        warrior_d100 = random.randint(1, 100)
        goblin_d100 = random.randint(1, 100)
        
        warrior_init = warrior_d100 + warrior_ke
        goblin_init = goblin_d100 + goblin_ke
        
        # Store the rolls for display
        state.initiative_rolls = {
            state.warrior.name: warrior_init,
            state.goblin.name: goblin_init,
        }
        
        if warrior_init > goblin_init:
            state.turn_order = [state.warrior, state.goblin]
            break
        elif goblin_init > warrior_init:
            state.turn_order = [state.goblin, state.warrior]
            break
        else:
            # Tied - use base KÉ as tiebreaker
            if warrior_ke > goblin_ke:
                state.turn_order = [state.warrior, state.goblin]
                break
            elif goblin_ke > warrior_ke:
                state.turn_order = [state.goblin, state.warrior]
                break
            # Both init and base KÉ are equal - reroll (loop continues)
    
    # Set first active unit and clear acted tracking
    state.active_unit = state.turn_order[0]
    state.units_acted_this_round = set()
    state.turn = 0 if state.active_unit == state.warrior else 1


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


def compute_attackable(state: GameState) -> Set[Tuple[int, int]]:
    """Mark enemy hex if within attack range; updates and returns state.attackable_for_active."""
    active_pos = state.active_unit.get_position()
    enemy_unit = state.goblin if state.active_unit == state.warrior else state.warrior
    enemy_pos = enemy_unit.get_position()
    if hex_distance(active_pos[0], active_pos[1], enemy_pos[0], enemy_pos[1]) <= ATTACK_RANGE:
        state.attackable_for_active = {enemy_pos}
    else:
        state.attackable_for_active = set()
    return state.attackable_for_active


def _set_turn_start_to_active(state: GameState) -> None:
    """Set the turn start position to the current active unit's position."""
    state.turn_start_pos = state.active_unit.get_position()


def next_turn(state: GameState) -> None:
    """
    End current unit's turn and switch to next unit.
    If both units have acted, start a new round with fresh initiative.
    """
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


def handle_attack_click(state: GameState, q: int, r: int) -> bool:
    """Attempt an attack if clicking enemy in range. On success, advance turn and refresh reachable. Returns True if attacked."""
    enemy_unit = state.goblin if state.active_unit == state.warrior else state.warrior
    eq, er = enemy_unit.get_position()
    if (q, r) == (eq, er):
        aq, ar = state.active_unit.get_position()
        if hex_distance(aq, ar, eq, er) <= ATTACK_RANGE:
            print(f"{state.active_unit.name} attacks!")
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
