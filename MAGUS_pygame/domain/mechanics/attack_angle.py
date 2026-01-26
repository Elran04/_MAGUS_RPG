"""
Attack angle mechanics for MAGUS combat.

Determines the relative angle of an attack based on attacker and defender positions
and the defender's facing direction. Used for shield protection and facing-dependent
skills.

Hex grid is circular with 6 directions (0=NE, 1=E, 2=SE, 3=SW, 4=W, 5=NW):
```
        0 (NE)
    5 /       \ 1 (E)
   (NW)   U   (SE)
    4 \       / 2
        3 (SW)
```

Attack angles relative to defender's facing:
- FRONT: 0-120° ahead (attack from facing directions 5, 0, 1)
- SIDE:  120-240° perpendicular (attack from facing directions 4, 5 or 1, 2)
- BACK:  240-360° behind (attack from facing directions 3, 4)

Exact classification:
- FRONT: defender_facing ± 1 (3 adjacent hexes including forward)
- SIDE:  defender_facing ± 2 (3 hexes on each flank)
- BACK:  opposite of defender_facing (3 hexes behind)
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from domain.value_objects import Position

if TYPE_CHECKING:
    from domain.entities import Unit


class AttackAngle(Enum):
    """Relative angle of attack to defender (6 directions).

    Relative to defender's facing direction (0-5):
    - 0: FRONT (directly ahead)
    - 1: FRONT_RIGHT (45° right)
    - 2: BACK_RIGHT (135° right)
    - 3: BACK (directly behind)
    - 4: BACK_LEFT (135° left)
    - 5: FRONT_LEFT (45° left)
    """

    FRONT = 0
    FRONT_RIGHT = 1
    BACK_RIGHT = 2
    BACK = 3
    BACK_LEFT = 4
    FRONT_LEFT = 5


def _normalize_direction(direction: int) -> int:
    """Normalize direction to 0-5 range."""
    return direction % 6


def _relative_direction(from_facing: int, to_facing: int) -> int:
    """
    Calculate relative direction from one facing to another.

    Returns a value in range 0-5 representing the angle difference clockwise.

    Args:
        from_facing: Starting direction (0-5)
        to_facing: Target direction (0-5)

    Returns:
        Relative direction (0-5), where 0 means same facing, 3 means opposite
    """
    from_facing = _normalize_direction(from_facing)
    to_facing = _normalize_direction(to_facing)

    # Calculate clockwise difference
    diff = (to_facing - from_facing) % 6
    return diff


def _direction_to_target(source: Position, target: Position) -> int:
    """
    Calculate which hex direction to move from source to reach target (0-5).

    Uses axial coordinates to find the primary direction of the target.
    This is a heuristic for finding the "closest" facing direction.

    Args:
        source: Source position
        target: Target position

    Returns:
        Facing direction (0-5), or 0 if positions are the same
    """
    dq = target.q - source.q
    dr = target.r - source.r

    if dq == 0 and dr == 0:
        return 0

    # Exact axial alignment first
    if dq == 0:
        return 2 if dr > 0 else 5
    if dr == 0:
        return 1 if dq > 0 else 4
    if dq + dr == 0:
        return 0 if dq > 0 else 3

    # Otherwise pick direction with maximum dot product (closest bearing)
    HEX_DIRECTIONS = [
        (1, -1),  # 0: NE
        (1, 0),  # 1: E
        (0, 1),  # 2: SE
        (-1, 1),  # 3: SW
        (-1, 0),  # 4: W
        (0, -1),  # 5: NW
    ]

    best_dir = 0
    best_score = float("-inf")

    for idx, (dir_q, dir_r) in enumerate(HEX_DIRECTIONS):
        score = dq * dir_q + dr * dir_r
        if score > best_score:
            best_score = score
            best_dir = idx

    return best_dir


def get_attack_angle(attacker: Unit, defender: Unit) -> AttackAngle:
    """
    Determine the angle of attack relative to defender's facing (6 directions).

    Calculates which direction the attacker is relative to the defender,
    then returns one of 6 specific angles (0-5).

    Args:
        attacker: Attacking unit
        defender: Defending unit

    Returns:
        AttackAngle (0-5): direct value of relative direction
    """
    # Find direction from defender to attacker
    attack_direction = _direction_to_target(defender.position, attacker.position)

    # Find relative direction from defender's facing
    defender_facing = _normalize_direction(defender.facing.direction)
    relative_dir = _relative_direction(defender_facing, attack_direction)

    # relative_dir is now the angle offset from defender's facing (0-5)
    # Map directly to AttackAngle enum values
    return AttackAngle(relative_dir)


def is_attack_from_front(attacker: Unit, defender: Unit) -> bool:
    """Check if attack is from defender's front (0)."""
    return get_attack_angle(attacker, defender) == AttackAngle.FRONT


def is_attack_from_front_right(attacker: Unit, defender: Unit) -> bool:
    """Check if attack is from defender's front-right (1)."""
    return get_attack_angle(attacker, defender) == AttackAngle.FRONT_RIGHT


def is_attack_from_back_right(attacker: Unit, defender: Unit) -> bool:
    """Check if attack is from defender's back-right (2)."""
    return get_attack_angle(attacker, defender) == AttackAngle.BACK_RIGHT


def is_attack_from_back(attacker: Unit, defender: Unit) -> bool:
    """Check if attack is from defender's back (3)."""
    return get_attack_angle(attacker, defender) == AttackAngle.BACK


def is_attack_from_back_left(attacker: Unit, defender: Unit) -> bool:
    """Check if attack is from defender's back-left (4)."""
    return get_attack_angle(attacker, defender) == AttackAngle.BACK_LEFT


def is_attack_from_front_left(attacker: Unit, defender: Unit) -> bool:
    """Check if attack is from defender's front-left (5)."""
    return get_attack_angle(attacker, defender) == AttackAngle.FRONT_LEFT
