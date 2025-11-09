"""
Weapon reach mechanics for MAGUS combat.

Handles:
- Directional attack hexes based on weapon size_category (reach) and facing
- Mandatory EP loss based on reach and FP damage dealt
- Attack range validation

Reach interpretation:
- size_category (reach) defines three rays from unit: forward, left, right
- Forward distance F = (size_category + 1) // 2   # 1,1,2,2,3,3,...
- Side distance    S = size_category // 2         # 0,1,1,2,2,3,...
- Unit can attack ALL intermediate hexes along these rays up to those distances

Examples:
- size 1 => F=1, S=0 -> forward(1) only -> 1 hex
- size 2 => F=1, S=1 -> forward(1) + left(1) + right(1) -> 3 hexes
- size 3 => F=2, S=1 -> forward(1,2) + left(1) + right(1) -> 4 hexes
- size 4 => F=2, S=2 -> forward(1,2) + left(1,2) + right(1,2) -> 6 hexes
- size 5 => F=3, S=2 -> forward(1,2,3) + left(1,2) + right(1,2) -> 7 hexes
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from domain.value_objects import Position

if TYPE_CHECKING:
    from domain.entities import Unit, Weapon


# Axial directions for hexes (q, r) - clockwise from NE
# 0=NE, 1=E, 2=SE, 3=SW, 4=W, 5=NW
HEX_DIRECTIONS = (
    (1, -1),  # facing 0: NE
    (1, 0),  # facing 1: E
    (0, 1),  # facing 2: SE
    (-1, 1),  # facing 3: SW
    (-1, 0),  # facing 4: W
    (0, -1),  # facing 5: NW
)


def get_weapon_reach(weapon: Weapon | None) -> int:
    """
    Get effective reach (size_category) of a weapon.

    Args:
        weapon: Weapon entity (None = unarmed)

    Returns:
        Reach value (1-5 typically, can be higher with martial arts)
    """
    if weapon is None:
        return 1  # Unarmed default

    return weapon.size_category


def _get_direction_vector(facing: int) -> tuple[int, int]:
    """Get axial direction vector for given facing."""
    return HEX_DIRECTIONS[facing % 6]


def _scale_direction(q: int, r: int, dq: int, dr: int, distance: int) -> tuple[int, int]:
    """Scale direction vector by distance and add to position."""
    return q + dq * distance, r + dr * distance


def compute_reach_hexes(unit: Unit, weapon: Weapon | None = None) -> set[tuple[int, int]]:
    """
    Compute all attackable hexes from unit's position given facing and weapon reach.

    Returns set of (q, r) hex coordinates including all intermediate tiles along:
    - Forward ray: distances 1..F
    - Left and right rays: distances 1..S (if S > 0)

    Args:
        unit: Attacking unit (provides position and facing)
        weapon: Weapon (provides size_category/reach), defaults to unit's weapon

    Returns:
        Set of attackable hex coordinates (q, r)
    """
    if weapon is None:
        weapon = unit.weapon

    size_category = get_weapon_reach(weapon)

    if size_category < 1:
        size_category = 1

    # Calculate distances
    forward_distance = (size_category + 1) // 2
    side_distance = size_category // 2

    result: set[tuple[int, int]] = set()
    q, r = unit.position.q, unit.position.r
    facing = unit.facing.direction

    # Forward ray: include all distances 1..F
    fwd_dq, fwd_dr = _get_direction_vector(facing)
    for k in range(1, forward_distance + 1):
        result.add(_scale_direction(q, r, fwd_dq, fwd_dr, k))

    # Left and right rays: include all distances 1..S
    if side_distance > 0:
        left_dq, left_dr = _get_direction_vector(facing - 1)
        right_dq, right_dr = _get_direction_vector(facing + 1)

        for k in range(1, side_distance + 1):
            result.add(_scale_direction(q, r, left_dq, left_dr, k))
            result.add(_scale_direction(q, r, right_dq, right_dr, k))

    return result


def can_attack_target(
    attacker: Unit, target_position: Position, weapon: Weapon | None = None
) -> bool:
    """
    Check if attacker can reach target position with current weapon and facing.

    Args:
        attacker: Attacking unit
        target_position: Target hex position
        weapon: Weapon to use (defaults to attacker's weapon)

    Returns:
        True if target is within reach
    """
    attackable_hexes = compute_reach_hexes(attacker, weapon)
    return (target_position.q, target_position.r) in attackable_hexes


def calculate_mandatory_ep_loss(weapon: Weapon | None, fp_damage_dealt: int) -> int:
    """
    Calculate mandatory EP loss based on weapon reach and FP damage dealt.

    Rules:
    - Reach > 3: Every 10 FP damage → 1 EP loss
    - Reach > 1: Every 8 FP damage → 1 EP loss
    - Reach = 1: Every 6 FP damage → 1 EP loss

    Args:
        weapon: Attacking weapon
        fp_damage_dealt: Amount of FP damage actually dealt to defender

    Returns:
        Additional EP damage to apply
    """
    if fp_damage_dealt <= 0:
        return 0

    reach = get_weapon_reach(weapon)

    # Determine threshold based on reach
    if reach > 3:
        threshold = 10
    elif reach > 1:
        threshold = 8
    else:  # reach == 1
        threshold = 6

    # Calculate EP loss: FP damage / threshold (integer division)
    ep_loss = fp_damage_dealt // threshold

    return ep_loss
