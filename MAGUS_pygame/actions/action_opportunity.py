"""
Opportunity attack handling for Zone of Control mechanics.
"""
from typing import Tuple
from core.game_state import GameState
from core.unit_manager import Unit
from systems.reach import compute_reach_hexes
from actions.action_attack import execute_attack


def handle_opportunity_attack(state: GameState, mover: Unit) -> Tuple[bool, str]:
    """
    Execute an opportunity attack when a unit moves through an enemy's zone of control.
    
    Args:
        state: Current game state
        mover: The moving unit (potential target of opportunity attack)
        
    Returns:
        Tuple of (attacked: bool, message: str)
        - attacked=True if opportunity attack was executed
        - attacked=False if opportunity already used this round
    """
    # Determine which enemy can make the opportunity attack
    enemy = state.warrior if mover == state.goblin else state.goblin
    
    # Check if enemy has already used their opportunity attack this round
    if enemy.has_used_opportunity_attack:
        return (False, "")
    
    # Check if mover is in enemy's reach
    eq, er = enemy.get_position()
    enemy_reach = compute_reach_hexes(eq, er, enemy.facing, enemy.size_category)
    mover_pos = mover.get_position()
    
    if mover_pos not in enemy_reach:
        return (False, "")
    
    # Mark opportunity attack as used
    enemy.has_used_opportunity_attack = True
    
    # Execute the attack (no AP cost for opportunity attacks)
    success, attack_msg = execute_attack(state, enemy, mover)
    
    if success and attack_msg:
        msg = f"⚔ OPPORTUNITY ATTACK! {attack_msg}"
        return (True, msg)
    
    return (False, "")
