"""
Movement action: compute path and movement feasibility.

Pure domain computation: does not mutate units. Returns instructions in ActionResult.data:
- path: list[(q,r)] from start to dest (inclusive)
- distance: number of hexes
- ap_cost: AP required (distance * ap_per_hex)
- intersects_zoc: whether path intersects enemy zone of control
- intersection_index: index in path where ZoC is first entered (if any)
- final_destination: destination if uninterrupted
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from domain.entities import Unit
from domain.mechanics.reach import compute_reach_hexes
from domain.value_objects import Position

from .base import Action, ActionCategory, ActionCost, ActionResult

# Hex neighbor offsets (axial coordinates)
NEIGHBORS = ((1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1))


def bfs_path(
    start: tuple[int, int], end: tuple[int, int], blocked: set[tuple[int, int]] | None = None
) -> list[tuple[int, int]]:
    """Breadth-first search shortest path on hex grid."""
    if start == end:
        return [start]
    blocked = blocked or set()
    from collections import deque

    q = deque([(start, [start])])
    visited = {start}

    while q:
        current, path = q.popleft()
        for dq, dr in NEIGHBORS:
            nxt = (current[0] + dq, current[1] + dr)
            if nxt in visited or nxt in blocked:
                continue
            new_path = path + [nxt]
            if nxt == end:
                return new_path
            visited.add(nxt)
            q.append((nxt, new_path))
    return []


def path_intersects_zone(
    path: list[tuple[int, int]], zone: set[tuple[int, int]]
) -> tuple[bool, int | None]:
    """Check if path (excluding start) passes through any zone hex. Returns (bool, first_index).

    Triggers on:
    - Entering zone from outside
    - Moving while already inside zone
    Does NOT trigger on:
    - Starting position (even if in zone)
    """
    for i, hex_pos in enumerate(path):
        if i > 0 and hex_pos in zone:
            return True, i
    return False, None


@dataclass
class MovementAction(Action):
    """Compute movement feasibility and path on hex grid."""

    ap_per_hex: int = 2
    max_range: int | None = None  # Optional hard cap independent of AP

    @property
    def category(self) -> ActionCategory:
        return ActionCategory.MOVEMENT

    @property
    def cost(self) -> ActionCost:
        # AP is distance-dependent; report 0 here and include ap_spent in result
        return ActionCost(ap=0)

    def can_execute(
        self,
        *,
        unit: Unit,
        start: Position,
        dest: Position,
        enemy: Unit | None = None,
        enemy_zones: set[tuple[int, int]] | None = None,
        ap_available: int,
        blocked: Iterable[tuple[int, int]] | None = None,
        **_: object,
    ) -> tuple[bool, str]:
        if unit is None:
            return (False, "Unit is required")
        if start is None or dest is None:
            return (False, "Start and destination are required")
        blocked_set = set(blocked or [])
        if (dest.q, dest.r) in blocked_set:
            return (False, "Destination is blocked")
        # Quick AP feasibility (minimum 1 hex -> at least ap_per_hex unless same hex)
        if (start.q, start.r) != (dest.q, dest.r) and ap_available < self.ap_per_hex:
            return (False, "Not enough AP to move at least 1 hex")
        return (True, "")

    def execute(
        self,
        *,
        unit: Unit,
        start: Position,
        dest: Position,
        enemy: Unit | None = None,
        enemy_zones: set[tuple[int, int]] | None = None,
        ap_available: int,
        blocked: Iterable[tuple[int, int]] | None = None,
    ) -> ActionResult:
        # Build blocked set and ensure enemy position is blocked to avoid stacking
        blocked_set: set[tuple[int, int]] = set(blocked or [])
        if enemy is not None:
            blocked_set.add((enemy.position.q, enemy.position.r))

        start_xy = (start.q, start.r)
        dest_xy = (dest.q, dest.r)

        path = bfs_path(start_xy, dest_xy, blocked_set)
        if not path:
            return ActionResult(success=False, message="No valid path", ap_spent=0)

        distance = len(path) - 1
        if self.max_range is not None:
            if distance > self.max_range:
                return ActionResult(success=False, message="Destination out of range", ap_spent=0)

        ap_cost = distance * self.ap_per_hex
        if ap_cost > ap_available:
            return ActionResult(success=False, message="Insufficient AP", ap_spent=0)

        # Compute enemy zone of control for potential reactions
        intersects = False
        intersection_index: int | None = None

        # Use provided enemy_zones if available, otherwise compute from single enemy
        if enemy_zones:
            intersects, intersection_index = path_intersects_zone(path, enemy_zones)
        elif enemy is not None:
            zone = compute_reach_hexes(enemy, enemy.weapon)
            intersects, intersection_index = path_intersects_zone(path, zone)

        data = {
            "path": path,
            "distance": distance,
            "ap_cost": ap_cost,
            "intersects_zoc": intersects,
            "intersection_index": intersection_index,
            "final_destination": dest_xy,
        }

        # We don't deduct AP here; app layer will subtract ap_cost
        msg = f"Move {distance} hex(es) to {dest_xy} (cost {ap_cost} AP)"
        if intersects:
            msg += " - enters enemy zone"

        return ActionResult(success=True, message=msg, ap_spent=ap_cost, data=data)
