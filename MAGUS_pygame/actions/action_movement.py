"""
Movement action helpers: range computation and movement resolution.
"""
from typing import Set, Tuple, List, Optional
from systems.hex_grid import hexes_in_range, hex_distance
from systems.reach import compute_reach_hexes
from config import MOVEMENT_RANGE, AP_COST_MOVEMENT, ActionMode
from core.game_state import GameState, next_turn, check_defeat
from actions.action_opportunity import handle_opportunity_attack


def find_path(start: Tuple[int, int], end: Tuple[int, int], blocked: Optional[Set[Tuple[int, int]]] = None) -> List[Tuple[int, int]]:
    """
    Find the shortest path from start to end hex using breadth-first search.
    
    Args:
        start: Starting hex (q, r)
        end: Destination hex (q, r)
        blocked: Set of hexes that cannot be traversed (optional)
    
    Returns:
        List of hexes representing the path from start to end (inclusive)
        Returns empty list if no path found
    """
    if start == end:
        return [start]
    
    if blocked is None:
        blocked = set()
    
    # Hex neighbor offsets (axial coordinates)
    neighbors = [
        (1, 0), (1, -1), (0, -1),
        (-1, 0), (-1, 1), (0, 1)
    ]
    
    # BFS to find shortest path
    from collections import deque
    queue = deque([(start, [start])])
    visited = {start}
    
    while queue:
        current, path = queue.popleft()
        
        # Check all neighbors
        for dq, dr in neighbors:
            neighbor = (current[0] + dq, current[1] + dr)
            
            # Skip if visited or blocked
            if neighbor in visited or neighbor in blocked:
                continue
            
            new_path = path + [neighbor]
            
            # Found the destination
            if neighbor == end:
                return new_path
            
            visited.add(neighbor)
            queue.append((neighbor, new_path))
    
    # No path found
    return []


def path_passes_through_zone(path: List[Tuple[int, int]], zone: Set[Tuple[int, int]]) -> Tuple[bool, Optional[int]]:
    """
    Check if any hex in the path (excluding start) is in the given zone.
    
    Args:
        path: List of hexes in the movement path
        zone: Set of hexes representing the zone of control
    
    Returns:
        Tuple of (passes_through: bool, first_intersection_index: Optional[int])
        - passes_through: True if path intersects zone
        - first_intersection_index: Index in path where first intersection occurs (None if no intersection)
    """
    # Check all hexes except the starting position
    for i, hex_pos in enumerate(path):
        if i > 0 and hex_pos in zone:  # Skip the starting position (index 0)
            print(f"[ZOC DEBUG] Path intersects zone at index {i}, hex {hex_pos}")
            print(f"[ZOC DEBUG] Full path: {path}")
            print(f"[ZOC DEBUG] Enemy zone: {zone}")
            return (True, i)
    
    return (False, None)


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
    Checks if movement path passes through enemy's zone of control and triggers opportunity attacks.
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
    
    # Find the movement path
    path = find_path((start_q, start_r), (q, r), blocked={enemy_pos})
    
    if not path:
        print(f"No valid path found to ({q}, {r})")
        return False
    
    print(f"[MOVEMENT] Moving from {(start_q, start_r)} to {(q, r)}")
    print(f"[MOVEMENT] Path: {path}")
    
    # Check if path passes through enemy's zone of control
    enemy_zone = state.enemy_zone_hexes
    print(f"[MOVEMENT] Enemy zone: {enemy_zone}")
    triggers_opportunity, intersection_index = path_passes_through_zone(path, enemy_zone)
    print(f"[MOVEMENT] Triggers opportunity: {triggers_opportunity}, intersection at index: {intersection_index}")
    
    # Variables to track actual movement
    final_position = (q, r)  # Intended destination
    actual_distance = distance  # Will be adjusted if stopped by opportunity attack
    
    # If path triggers opportunity attack, move to intersection point and execute attack
    if triggers_opportunity and intersection_index is not None:
        # Move to the hex where zone is entered (the intersection point)
        intersection_hex = path[intersection_index]
        print(f"[MOVEMENT] Moving to intersection hex {intersection_hex} before opportunity attack")
        state.active_unit.move_to(intersection_hex[0], intersection_hex[1])
        
        # Calculate actual distance moved to intersection
        actual_distance = hex_distance(start_q, start_r, intersection_hex[0], intersection_hex[1])
        actual_ap_cost = actual_distance * AP_COST_MOVEMENT
        
        print(f"[MOVEMENT] Moved {actual_distance} hex(es) to intersection point")
        print(f"[MOVEMENT] Executing opportunity attack at {intersection_hex}")
        
        # Execute opportunity attack (no need to skip range check - unit is now in range!)
        attacked, opp_msg = handle_opportunity_attack(state, state.active_unit, triggers_opportunity=True)
        
        # Display message on screen whether hit or miss
        if opp_msg:
            print(opp_msg)
            state.combat_message = opp_msg
            state.message_timer = 180  # Show for ~3 seconds at 60 FPS
        
        # Check if the mover was defeated by the opportunity attack
        if attacked and check_defeat(state):
            print(f"\n{state.winner.name} is victorious! {state.active_unit.name} was defeated by an opportunity attack!")
            # Deduct AP for movement to intersection point
            state.active_unit.current_action_points -= actual_ap_cost
            print(f"AP deducted for {actual_distance} hex(es): {actual_ap_cost}. Remaining: {state.active_unit.current_action_points}/{state.active_unit.max_action_points}")
            return True
        
        # If attack missed or didn't kill, check the attack result to see if movement continues
        # For now, if opportunity attack happens (hit or miss), movement stops at intersection
        if attacked:
            print(f"[MOVEMENT] Opportunity attack occurred - movement interrupted at {intersection_hex}")
            # Deduct AP only for distance to intersection
            state.active_unit.current_action_points -= actual_ap_cost
            print(f"{state.active_unit.name} moved {actual_distance} hex(es) to {intersection_hex} (cost: {actual_ap_cost} AP). AP remaining: {state.active_unit.current_action_points}/{state.active_unit.max_action_points}")
            
            # Update turn start position to intersection
            state.turn_start_pos = state.active_unit.get_position()
            
            # Recalculate reachable hexes from new position
            if state.active_unit.current_action_points > 0:
                compute_reachable(state)
            else:
                next_turn(state)
                state.action_mode = ActionMode.MOVE
                state.attackable_for_active = set()
                compute_reachable(state)
            
            return True
    
    # No opportunity attack or it didn't trigger - complete full movement
    state.active_unit.move_to(q, r)
    state.active_unit.current_action_points -= ap_cost
    print(f"{state.active_unit.name} moved {distance} hex(es) (cost: {ap_cost} AP). AP remaining: {state.active_unit.current_action_points}/{state.active_unit.max_action_points}")
    
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
