"""
Reach calculation based on facing and weapon size category.

Interpretation (updated per clarification):
- Size category defines three rays from the unit: forward, left, right.
- Distances:
    - forward_distance F = (size_category + 1) // 2   # 1,1,2,2,3,3
    - side_distance    S =  size_category // 2        # 0,1,1,2,2,3
- A unit can attack ALL intermediate hexes along these rays up to those distances:
    - forward: distances 1..F (inclusive)
    - left and right: distances 1..S (inclusive)

Examples:
- size 3 => F=2, S=1 -> forward(1,2) + left(1) + right(1) -> 4 tiles.
- size 2 => F=1, S=1 -> forward(1) + left(1) + right(1) -> 3 tiles.

This can later be extended to a filled wedge/zone-of-control by also including the band
between left/right rays for each depth.
"""
from typing import Set, Tuple

# Axial directions for pointy-top hexes (q, r)
# Ordered clockwise starting from "north" approximated as (0, -1)
# 0=N, 1=NE, 2=SE, 3=S, 4=SW, 5=NW
DIRS: Tuple[Tuple[int, int], ...] = (
    (1, -1),  # facing 0: NE (top-right)
    (1, 0),   # facing 1: E
    (0, 1),   # facing 2: SE (down-right)
    (-1, 1),  # facing 3: SW (down-left)
    (-1, 0),  # facing 4: W
    (0, -1),  # facing 5: NW (top-left)
)


def dir_vec(facing: int) -> Tuple[int, int]:
    f = facing % 6
    return DIRS[f]


def scale_add(q: int, r: int, dq: int, dr: int, k: int) -> Tuple[int, int]:
    return q + dq * k, r + dr * k


def compute_reach_hexes(q: int, r: int, facing: int, size_category: int) -> Set[Tuple[int, int]]:
    """Compute attackable hexes from (q,r) given facing and weapon size category.

    Returns a set of hexes including all intermediate tiles along the forward
    ray (1..F) and along the left/right rays (1..S).
    """
    if size_category < 1:
        size_category = 1
    F = (size_category + 1) // 2
    S = size_category // 2

    result: Set[Tuple[int, int]] = set()
    # Forward ray: include all distances 1..F
    dfq, dfr = dir_vec(facing)
    for k in range(1, F + 1):
        result.add(scale_add(q, r, dfq, dfr, k))
    # Left and right rays: include all distances 1..S
    if S > 0:
        dlq, dlr = dir_vec(facing - 1)
        drq, drr = dir_vec(facing + 1)
        for k in range(1, S + 1):
            result.add(scale_add(q, r, dlq, dlr, k))
            result.add(scale_add(q, r, drq, drr, k))
    return result
