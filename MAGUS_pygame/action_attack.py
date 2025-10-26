"""
Attack action handling: range checking, attack rolls, and damage resolution.
"""
import random
from typing import Tuple, Optional, Set
from hex_grid import hex_distance
from config import ATTACK_RANGE, AP_COST_ATTACK_DEFAULT
from game_state import GameState
from unit_manager import Unit


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


class AttackResult:
    """Encapsulates the result of an attack."""
    def __init__(self, hit: bool, damage: int = 0, is_critical: bool = False, 
                 is_critical_fail: bool = False, is_overpower: bool = False,
                 attack_roll: int = 0, total_attack: int = 0):
        self.hit = hit
        self.damage = damage
        self.is_critical = is_critical
        self.is_critical_fail = is_critical_fail
        self.is_overpower = is_overpower
        self.attack_roll = attack_roll  # The d100 roll
        self.total_attack = total_attack  # d100 + TÉ


def check_attack_range(attacker: Unit, defender: Unit) -> bool:
    """Check if defender is within attack range of attacker."""
    aq, ar = attacker.get_position()
    dq, dr = defender.get_position()
    distance = hex_distance(aq, ar, dq, dr)
    return distance <= ATTACK_RANGE


def roll_attack(attacker: Unit, defender: Unit) -> AttackResult:
    """
    Roll an attack from attacker against defender.
    
    Rules:
    - Roll d100 (1-100)
    - Attack succeeds if d100 + TÉ > VÉ
    - Special cases:
      - d100 = 1: Critical failure (automatic miss)
      - d100 = 100: Critical hit (automatic hit, +3 ÉP damage)
      - d100 + TÉ > VÉ + 50: Overpower strike (damage goes directly to ÉP)
    
    Returns:
        AttackResult with hit status and damage info
    """
    d100 = random.randint(1, 100)
    attacker_te = attacker.TE
    defender_ve = defender.VE
    total_attack = d100 + attacker_te
    
    # Critical failure on 1
    if d100 == 1:
        return AttackResult(
            hit=False,
            is_critical_fail=True,
            attack_roll=d100,
            total_attack=total_attack
        )
    
    # Critical hit on 100
    if d100 == 100:
        base_damage = random.randint(1, 6)
        return AttackResult(
            hit=True,
            damage=base_damage,
            is_critical=True,
            attack_roll=d100,
            total_attack=total_attack
        )
    
    # Normal attack resolution
    if total_attack > defender_ve:
        base_damage = random.randint(1, 6)
        is_overpower = total_attack > (defender_ve + 50)
        return AttackResult(
            hit=True,
            damage=base_damage,
            is_overpower=is_overpower,
            attack_roll=d100,
            total_attack=total_attack
        )
    
    # Miss
    return AttackResult(
        hit=False,
        attack_roll=d100,
        total_attack=total_attack
    )


def apply_damage(defender: Unit, damage: int, is_critical: bool = False, is_overpower: bool = False) -> dict:
    """
    Apply damage to defender.
    
    Rules:
    - Normal damage: reduces FP first, overflow to ÉP
    - Overpower strike: damage goes directly to ÉP
    - Critical hit: deals +3 ÉP damage regardless of FP
    - If ÉP damage occurs and defender still has FP: lose 2x ÉP damage as FP
    - Max damage (6): automatically deals +1 ÉP (which also triggers 2 FP loss)
    
    Args:
        defender: The unit receiving damage
        damage: Base damage amount
        is_critical: Whether this is a critical hit
        is_overpower: Whether this is an overpower strike
    
    Returns:
        dict with damage breakdown: {'fp_damage': int, 'ep_damage': int, 'max_damage_bonus': bool}
    """
    fp_damage = 0
    ep_damage = 0
    max_damage_bonus = False
    
    # Check for max damage (6) - adds +1 ÉP
    if damage == 6:
        max_damage_bonus = True
        ep_damage += 1
        # If defender has FP, lose 2 FP per ÉP damage
        if defender.current_fp > 0:
            fp_loss = min(2, defender.current_fp)
            fp_damage += fp_loss
            defender.current_fp -= fp_loss
    
    # Critical hit: +3 ÉP damage directly (ignores FP)
    if is_critical:
        ep_damage += damage + 3
        defender.current_ep = max(0, defender.current_ep - (damage + 3))
        # If defender still has FP, lose 2x ÉP damage as FP
        if defender.current_fp > 0:
            fp_loss = min((damage + 3) * 2, defender.current_fp)
            fp_damage += fp_loss
            defender.current_fp -= fp_loss
    
    # Overpower strike: damage goes directly to ÉP
    elif is_overpower:
        ep_damage += damage
        defender.current_ep = max(0, defender.current_ep - damage)
        # If defender still has FP, lose 2x ÉP damage as FP
        if defender.current_fp > 0:
            fp_loss = min(damage * 2, defender.current_fp)
            fp_damage += fp_loss
            defender.current_fp -= fp_loss
    
    # Normal damage: FP first, then overflow to ÉP
    else:
        if defender.current_fp > 0:
            if damage <= defender.current_fp:
                # All damage absorbed by FP
                fp_damage += damage
                defender.current_fp -= damage
            else:
                # Damage exceeds FP - overflow to ÉP
                overflow_ep = damage - defender.current_fp
                fp_damage += defender.current_fp
                defender.current_fp = 0
                ep_damage += overflow_ep
                defender.current_ep = max(0, defender.current_ep - overflow_ep)
                # Note: No additional FP loss here since FP was depleted by normal damage
        else:
            # No FP left - all damage to ÉP
            ep_damage += damage
            defender.current_ep = max(0, defender.current_ep - damage)
    
    return {
        'fp_damage': fp_damage,
        'ep_damage': ep_damage,
        'max_damage_bonus': max_damage_bonus
    }


def execute_attack(state: GameState, attacker: Unit, defender: Unit) -> Tuple[bool, str]:
    """
    Execute a complete attack sequence: range check, attack roll, damage application.
    
    Args:
        state: Current game state
        attacker: The attacking unit
        defender: The defending unit
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    # Check range
    if not check_attack_range(attacker, defender):
        return (False, f"{attacker.name} is too far to attack!")
    
    # Roll attack
    result = roll_attack(attacker, defender)
    
    # Critical failure
    if result.is_critical_fail:
        return (True, f"{attacker.name} rolled a critical failure (1)! Attack missed.")
    
    # Miss
    if not result.hit:
        return (True, f"{attacker.name} missed! (Rolled {result.attack_roll}, total {result.total_attack} vs VÉ {defender.VE})")
    
    # Hit - apply damage
    damage_breakdown = apply_damage(defender, result.damage, result.is_critical, result.is_overpower)
    
    # Build message
    if result.is_critical:
        msg = f"{attacker.name} CRITICAL HIT (100)! Dealt {result.damage + 3} ÉP damage"
        if damage_breakdown['fp_damage'] > 0:
            msg += f" + {damage_breakdown['fp_damage']} FP damage (2x ÉP)"
        msg += f" to {defender.name}!"
    elif result.is_overpower:
        msg = f"{attacker.name} OVERPOWER STRIKE! (Total {result.total_attack} vs VÉ {defender.VE}) Dealt {result.damage} ÉP damage"
        if damage_breakdown['fp_damage'] > 0:
            msg += f" + {damage_breakdown['fp_damage']} FP damage (2x ÉP)"
        msg += f" to {defender.name}!"
    else:
        msg = f"{attacker.name} hits! (Rolled {result.attack_roll}, total {result.total_attack} vs VÉ {defender.VE}) "
        if damage_breakdown['fp_damage'] > 0 and damage_breakdown['ep_damage'] > 0:
            msg += f"Dealt {damage_breakdown['fp_damage']} FP + {damage_breakdown['ep_damage']} ÉP damage to {defender.name}!"
        elif damage_breakdown['fp_damage'] > 0:
            msg += f"Dealt {damage_breakdown['fp_damage']} FP damage to {defender.name}!"
        else:
            msg += f"Dealt {damage_breakdown['ep_damage']} ÉP damage to {defender.name}!"
    
    # Add max damage bonus note
    if damage_breakdown.get('max_damage_bonus'):
        msg += " [MAX DAMAGE: +1 ÉP, +2 FP]"
    
    return (True, msg)


def handle_attack_click(state: GameState, q: int, r: int) -> bool:
    """
    Attempt an attack if clicking enemy in range. 
    Deducts AP_COST_ATTACK action points.
    On success, advance turn if no AP left, otherwise allow more actions.
    Returns True if attacked.
    """
    from action_movement import next_turn, compute_reachable
    from game_state import check_defeat
    
    enemy_unit = state.goblin if state.active_unit == state.warrior else state.warrior
    eq, er = enemy_unit.get_position()
    if (q, r) == (eq, er):
        # Check if unit has enough action points
        # TODO: Get actual weapon AP cost from unit equipment when implemented
        attack_ap_cost = AP_COST_ATTACK_DEFAULT
        
        if state.active_unit.current_action_points < attack_ap_cost:
            print(f"{state.active_unit.name} doesn't have enough AP to attack! (Need {attack_ap_cost}, have {state.active_unit.current_action_points})")
            return False
        
        # Execute the attack with full combat mechanics
        success, message = execute_attack(state, state.active_unit, enemy_unit)
        if success:
            # Deduct AP for the attack
            state.active_unit.current_action_points -= attack_ap_cost
            print(message)  # Print the detailed attack result
            print(f"{state.active_unit.name} AP remaining: {state.active_unit.current_action_points}/{state.active_unit.max_action_points}")
            
            # Check if the defender was defeated
            if check_defeat(state):
                print(f"\n{state.winner.name} is victorious! {enemy_unit.name} has been defeated!")
                return True
            
            # If no AP left, end turn automatically
            if state.active_unit.current_action_points <= 0:
                next_turn(state)
                state.action_mode = "move"
                state.attackable_for_active = set()
                compute_reachable(state)
            else:
                # Recalculate what's attackable (still in range?)
                compute_attackable(state)
            
            return True
    return False
