"""
Opportunity attack handling for Zone of Control mechanics.
"""

from core.game_state import GameState
from core.unit_manager import Unit
from systems.reach import compute_reach_hexes

from actions.attack import execute_attack


def handle_opportunity_attack(
    state: GameState, mover: Unit, triggers_opportunity: bool = None
) -> tuple[bool, str]:
    """
    Execute an opportunity attack when a unit moves through an enemy's zone of control.

    Args:
        state: Current game state
        mover: The moving unit (potential target of opportunity attack)
        triggers_opportunity: If True, force trigger the attack; if None, check mover's current position

    Returns:
        Tuple of (attacked: bool, message: str)
        - attacked=True if opportunity attack was executed
        - attacked=False if opportunity already used this round or no trigger
    """
    # Determine which enemy can make the opportunity attack
    enemy = state.warrior if mover == state.goblin else state.goblin

    print(
        f"[OPP ATTACK] Checking opportunity attack. Enemy: {enemy.name}, has_used: {enemy.has_used_opportunity_attack}, triggers: {triggers_opportunity}"
    )

    # Check if enemy has already used their opportunity attack this round
    if enemy.has_used_opportunity_attack:
        print(f"[OPP ATTACK] {enemy.name} already used opportunity attack this round")
        return (False, "")

    # If triggers_opportunity is explicitly provided, use that
    if triggers_opportunity is False:
        print("[OPP ATTACK] No trigger - path doesn't pass through zone")
        return (False, "")

    # If triggers_opportunity is True or None, check position-based trigger
    if triggers_opportunity is None:
        # Fallback: Check if mover is in enemy's reach (for backward compatibility)
        eq, er = enemy.get_position()
        enemy_reach = compute_reach_hexes(eq, er, enemy.facing, enemy.size_category)
        mover_pos = mover.get_position()

        if mover_pos not in enemy_reach:
            print("[OPP ATTACK] Mover not in enemy reach (fallback check)")
            return (False, "")

    print(f"[OPP ATTACK] Triggering opportunity attack from {enemy.name} against {mover.name}")

    # Mark opportunity attack as used
    enemy.has_used_opportunity_attack = True

    # Execute the attack (no AP cost for opportunity attacks)
    # Note: Range check will pass because mover was moved to intersection hex before this call
    success, attack_msg = execute_attack(state, enemy, mover)

    print(f"[OPP ATTACK] Attack execution returned: success={success}, message='{attack_msg}'")

    # Always return message with opportunity attack prefix (hit or miss)
    if success and attack_msg:
        msg = f"⚔ OPPORTUNITY ATTACK! {attack_msg}"
        print(f"[OPP ATTACK] Final message: {msg}")
        return (True, msg)

    print("[OPP ATTACK] No message generated")
    return (False, "")
