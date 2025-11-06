"""
Charge attack action handling.
A special compound action combining movement and attack with bonuses/penalties.
"""

from config import ActionMode
from core.game_state import GameState, check_defeat, next_turn
from systems.hex_grid import hex_distance, hexes_in_range
from systems.reach import compute_reach_hexes

from actions.attack import apply_damage, roll_attack
from actions.movement import find_path, path_passes_through_zone
from actions.opportunity import handle_opportunity_attack

# Charge attack constants
CHARGE_AP_COST = 10  # Full turn
CHARGE_MIN_DISTANCE = 4  # Minimum hexes away to charge
CHARGE_TE_BONUS = 20  # Attack bonus during charge
CHARGE_VE_PENALTY = 25  # Defense penalty if opportunity attack triggered
CHARGE_DAMAGE_MULTIPLIER = 2  # Damage doubled on charge

# Hex direction vectors (q, r) - same as in reach.py
# 0=NE, 1=E, 2=SE, 3=SW, 4=W, 5=NW
HEX_DIRECTIONS = [
    (1, -1),  # 0: NE (top-right)
    (1, 0),  # 1: E (right)
    (0, 1),  # 2: SE (down-right)
    (-1, 1),  # 3: SW (down-left)
    (-1, 0),  # 4: W (left)
    (0, -1),  # 5: NW (top-left)
]


def calculate_facing_direction(from_q: int, from_r: int, to_q: int, to_r: int) -> int:
    """
    Calculate the facing direction from one hex to another.

    Args:
        from_q, from_r: Starting hex coordinates
        to_q, to_r: Target hex coordinates

    Returns:
        Facing direction (0-5): 0=NE, 1=E, 2=SE, 3=SW, 4=W, 5=NW
    """
    dq = to_q - from_q
    dr = to_r - from_r

    # Normalize to direction vector
    # Find the closest hex direction
    if dq == 0 and dr == 0:
        return 0  # Same hex, default to NE

    # Check each direction and find the best match
    best_facing = 0
    best_dot = -999

    # Normalize the difference vector
    magnitude = max(abs(dq), abs(dr), abs(dq + dr))
    if magnitude > 0:
        norm_dq = dq / magnitude
        norm_dr = dr / magnitude

        for facing, (dir_q, dir_r) in enumerate(HEX_DIRECTIONS):
            # Dot product to find closest direction
            dot = norm_dq * dir_q + norm_dr * dir_r
            if dot > best_dot:
                best_dot = dot
                best_facing = facing

    return best_facing


def compute_charge_targets(state: GameState) -> set[tuple[int, int]]:
    """
    Compute valid charge targets and chargeable area for the active unit.

    Shows all hexes at least 4 hexes away from the unit (chargeable range).
    If enemy is in this range, highlights them as a valid target.

    Args:
        state: Current game state

    Returns:
        Set of (q, r) hex coordinates in chargeable range
    """
    unit = state.active_unit
    uq, ur = unit.get_position()

    # Charge costs 10 AP (full turn), so show max range based on that
    # Maximum distance is limited by the AP cost (10 AP / 2 AP per hex = 5 hexes)
    max_charge_distance = CHARGE_AP_COST // 2  # 10 AP / 2 = 5 hexes max range

    # Get all hexes in range
    all_in_range = hexes_in_range(uq, ur, max_charge_distance)

    # Filter to only hexes at least CHARGE_MIN_DISTANCE away
    chargeable_area = set()
    for hex_pos in all_in_range:
        distance = hex_distance(uq, ur, hex_pos[0], hex_pos[1])
        if distance >= CHARGE_MIN_DISTANCE:
            chargeable_area.add(hex_pos)

    # Get enemy position
    enemy_unit = state.goblin if unit == state.warrior else state.warrior
    enemy_q, enemy_r = enemy_unit.get_position()
    enemy_pos = (enemy_q, enemy_r)

    # Compute enemy's zone of control for visual warning (like in movement mode)
    state.enemy_zone_hexes = compute_reach_hexes(
        enemy_q, enemy_r, enemy_unit.facing, enemy_unit.size_category
    )

    # Remove enemy position from chargeable area display (we'll handle it separately)
    chargeable_area.discard(enemy_pos)

    # Check if enemy is at valid charge distance
    distance_to_enemy = hex_distance(uq, ur, enemy_q, enemy_r)

    if distance_to_enemy >= CHARGE_MIN_DISTANCE:
        print(f"[CHARGE] {unit.name} can charge {enemy_unit.name} (distance: {distance_to_enemy})")
        # Add enemy as valid target (will be rendered differently)
        state.charge_targets = {enemy_pos}
        # Store chargeable area for visualization
        state.reachable_for_active = chargeable_area
        return chargeable_area | {enemy_pos}
    else:
        print(
            f"[CHARGE] {enemy_unit.name} too close to charge (distance: {distance_to_enemy}, need >= {CHARGE_MIN_DISTANCE})"
        )
        state.charge_targets = set()
        # Still show chargeable area even though no valid targets
        state.reachable_for_active = chargeable_area
        return chargeable_area


def execute_charge_attack(state: GameState, target_q: int, target_r: int) -> bool:
    """
    Execute a charge attack from active unit to target position.

    Charge mechanics:
    - Costs 10 AP (full turn)
    - Requires enemy to be >= 4 hexes away
    - Unit automatically moves to best adjacent hex of enemy
    - Unit automatically faces the enemy after charge
    - +20 TÉ bonus for attack roll
    - -25 VÉ penalty if opportunity attack triggered
    - Damage doubled (both for charge attack and opportunity attack)
    - Only stops if charging unit is defeated

    Args:
        state: Current game state
        target_q, target_r: Target hex coordinates (enemy position - clicked by user)

    Returns:
        True if charge was executed, False otherwise
    """
    unit = state.active_unit
    start_q, start_r = unit.get_position()

    # Validate charge is possible
    if state.action_mode != ActionMode.CHARGE:
        return False

    if unit.current_action_points < CHARGE_AP_COST:
        print(
            f"[CHARGE] {unit.name} doesn't have enough AP (need {CHARGE_AP_COST}, have {unit.current_action_points})"
        )
        return False

    # Get enemy unit and validate target is the enemy
    enemy_unit = state.goblin if unit == state.warrior else state.warrior
    enemy_q, enemy_r = enemy_unit.get_position()

    # Validate clicked on enemy position
    if (target_q, target_r) != (enemy_q, enemy_r):
        print(f"[CHARGE] Target {(target_q, target_r)} is not enemy position {(enemy_q, enemy_r)}")
        return False

    # Check minimum distance from start
    distance = hex_distance(start_q, start_r, enemy_q, enemy_r)
    if distance < CHARGE_MIN_DISTANCE:
        print(f"[CHARGE] Target too close (distance: {distance}, need >= {CHARGE_MIN_DISTANCE})")
        return False

    print(f"[CHARGE] {unit.name} charging {enemy_unit.name} from {distance} hexes away!")

    # Find best adjacent hex to charge from (closest path)
    adjacent_hexes = [
        (enemy_q + 1, enemy_r),
        (enemy_q + 1, enemy_r - 1),
        (enemy_q, enemy_r - 1),
        (enemy_q - 1, enemy_r),
        (enemy_q - 1, enemy_r + 1),
        (enemy_q, enemy_r + 1),
    ]

    best_path = None
    best_distance = float("inf")
    best_destination = None
    enemy_pos = (enemy_q, enemy_r)

    for adj_q, adj_r in adjacent_hexes:
        path = find_path((start_q, start_r), (adj_q, adj_r), blocked={enemy_pos})
        if path and len(path) > 1:
            path_distance = len(path) - 1
            if path_distance < best_distance:
                best_distance = path_distance
                best_path = path
                best_destination = (adj_q, adj_r)

    if not best_path or not best_destination:
        print(f"[CHARGE] No valid path found to charge {enemy_unit.name}")
        return False

    print(f"[CHARGE] Path to charge: {best_path}")

    # Check if path passes through enemy zone
    enemy_zone = compute_reach_hexes(enemy_q, enemy_r, enemy_unit.facing, enemy_unit.size_category)
    triggers_opportunity, intersection_index = path_passes_through_zone(best_path, enemy_zone)

    # Track if VÉ penalty should apply
    ve_penalty_active = False
    opportunity_stopped_charge = False

    # Handle opportunity attack if path crosses zone
    if triggers_opportunity and intersection_index is not None:
        print("[CHARGE] Charge path triggers opportunity attack!")

        # Move to intersection hex
        intersection_hex = best_path[intersection_index]
        unit.move_to(intersection_hex[0], intersection_hex[1])

        # Apply VÉ penalty for opportunity attack
        ve_penalty_active = True
        original_ve = unit.VE
        print(f"[CHARGE] Applying VÉ penalty: {original_ve} -> {original_ve - CHARGE_VE_PENALTY}")

        # Temporarily modify combat stats for opportunity attack
        unit.combat["VÉ"] = original_ve - CHARGE_VE_PENALTY

        # Store original damage multiplier state (for opportunity attack damage doubling)
        state.charge_damage_multiplier = CHARGE_DAMAGE_MULTIPLIER

        # Execute opportunity attack with doubled damage
        attacked, opp_msg = handle_opportunity_attack(state, unit, triggers_opportunity=True)

        # Clear damage multiplier
        state.charge_damage_multiplier = 1

        # Restore VÉ (penalty was temporary)
        unit.combat["VÉ"] = original_ve

        if opp_msg:
            print(opp_msg)
            state.combat_message = opp_msg
            state.message_timer = 180

        # Check if charge was stopped by defeat
        if attacked and check_defeat(state):
            print(f"[CHARGE] {unit.name} defeated during charge by opportunity attack!")
            unit.current_action_points -= CHARGE_AP_COST
            return True

        print("[CHARGE] Opportunity attack didn't stop charge - continuing!")

    # Continue movement to final position (adjacent to enemy)
    unit.move_to(best_destination[0], best_destination[1])
    print(f"[CHARGE] {unit.name} reached charge position: {best_destination}")

    # Calculate and set facing direction towards enemy
    new_facing = calculate_facing_direction(
        best_destination[0], best_destination[1], enemy_q, enemy_r
    )
    unit.facing = new_facing
    print(f"[CHARGE] {unit.name} now facing direction {new_facing} towards {enemy_unit.name}")

    # Apply TÉ bonus for charge attack
    original_te = unit.TE
    unit.combat["TÉ"] = original_te + CHARGE_TE_BONUS
    print(f"[CHARGE] Applying TÉ bonus: {original_te} -> {original_te + CHARGE_TE_BONUS}")

    # Set damage multiplier for charge attack
    state.charge_damage_multiplier = CHARGE_DAMAGE_MULTIPLIER

    # Execute charge attack (pass state for damage multiplier)
    result = roll_attack(unit, enemy_unit, state)

    # Build attack message
    if result.is_critical_fail:
        attack_msg = f"⚡ CHARGE ATTACK! {unit.name} rolled a critical failure (1)! Attack missed."
    elif not result.hit:
        attack_msg = f"⚡ CHARGE ATTACK! {unit.name} missed! (Rolled {result.attack_roll}, total {result.total_attack} vs VÉ {enemy_unit.VE})"
    else:
        # Apply damage with charge multiplier
        damage_breakdown = apply_damage(
            unit, enemy_unit, result.damage, result.is_critical, result.is_overpower
        )

        if result.is_critical:
            attack_msg = f"⚡ CHARGE ATTACK - CRITICAL HIT (100)! {unit.name} dealt {result.damage + 3} ÉP damage"
            if damage_breakdown["fp_damage"] > 0:
                attack_msg += f" + {damage_breakdown['fp_damage']} FP damage"
            attack_msg += f" to {enemy_unit.name}! [DOUBLED DAMAGE]"
        elif result.is_overpower:
            attack_msg = f"⚡ CHARGE ATTACK - OVERPOWER! (Total {result.total_attack} vs VÉ {enemy_unit.VE}) {unit.name} dealt {result.damage} ÉP damage"
            if damage_breakdown["fp_damage"] > 0:
                attack_msg += f" + {damage_breakdown['fp_damage']} FP damage"
            attack_msg += f" to {enemy_unit.name}! [DOUBLED DAMAGE]"
        else:
            attack_msg = f"⚡ CHARGE ATTACK! {unit.name} hits! (Rolled {result.attack_roll}, total {result.total_attack} vs VÉ {enemy_unit.VE}) "
            if damage_breakdown["fp_damage"] > 0 and damage_breakdown["ep_damage"] > 0:
                attack_msg += f"Dealt {damage_breakdown['fp_damage']} FP + {damage_breakdown['ep_damage']} ÉP damage [DOUBLED DAMAGE]"
            elif damage_breakdown["fp_damage"] > 0:
                attack_msg += f"Dealt {damage_breakdown['fp_damage']} FP damage [DOUBLED DAMAGE]"
            else:
                attack_msg += f"Dealt {damage_breakdown['ep_damage']} ÉP damage [DOUBLED DAMAGE]"

    # Clear damage multiplier
    state.charge_damage_multiplier = 1

    # Restore TÉ
    unit.combat["TÉ"] = original_te

    print(attack_msg)
    state.combat_message = attack_msg
    state.message_timer = 180

    # Check if enemy was defeated
    if check_defeat(state):
        print(f"[CHARGE] {enemy_unit.name} defeated by charge attack!")

    # Deduct full AP cost
    unit.current_action_points -= CHARGE_AP_COST
    print(
        f"[CHARGE] AP cost: {CHARGE_AP_COST}. Remaining: {unit.current_action_points}/{unit.max_action_points}"
    )

    # End turn (charge uses full AP)
    next_turn(state)
    state.action_mode = ActionMode.MOVE
    state.attackable_for_active = set()

    return True
