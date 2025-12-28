"""

BattleService - orchestrates turn order, action points, and victory checks.

AP model:
- Base AP per unit per turn = 10
- For each point of Gyorsaság (Attributes.speed) above 15, gain +1 AP.

This AP computation is domain logic, but lightweight enough to live here; if it
expands (skills, conditions), extract to domain.mechanics.ap or similar.
"""

from __future__ import annotations

import random
from collections import deque
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field

from config import AP_COST_MOVEMENT
from domain.entities import Unit
from domain.mechanics.actions.movement_action import NEIGHBORS
from domain.mechanics.initiation import (
    InitiativeOrder,
    calculate_initiative,
    initiative_sort_key_factory,
)
from domain.mechanics.reach import can_attack_target, compute_reach_hexes
from domain.value_objects import Facing, Position
from logger.logger import get_logger

from .action_handler import ActionHandler


def compute_unit_ap(unit: Unit) -> int:
    base = 10
    speed = getattr(unit.attributes, "speed", 10)
    bonus = max(0, speed - 15)
    return base + bonus


@dataclass
class BattleService:
    units: list[Unit]
    action_handler: ActionHandler = field(default_factory=ActionHandler)
    initiative_sort: Callable[[Unit], int] | None = None
    initiative_order: InitiativeOrder | None = None
    _rng_seed: int | None = None  # For deterministic testing if provided
    _rng: object | None = None  # random.Random when initiative enabled

    turn_index: int = 0
    round: int = 1
    ap_pool: dict[str, int] = field(default_factory=dict)

    # Victory tracking (simple placeholder: teams distinguished externally)
    team_a_ids: list[str] = field(default_factory=list)
    team_b_ids: list[str] = field(default_factory=list)

    battle_active: bool = True

    def start_battle(self) -> None:
        """Initialize battle: perform initiative (if enabled), sort units, compute AP, reset reactions."""
        if self.initiative_order is not None and self.initiative_sort is None:
            # Initiative was computed but key not yet set (edge case)
            self.initiative_sort = initiative_sort_key_factory(self.initiative_order)
        self._sort_units()
        self._init_ap()
        self.action_handler.start_turn(self.units)

    # ------------------------------------------------------------------
    # Initiative Integration
    # ------------------------------------------------------------------
    def enable_initiative(self, *, seed: int | None = None) -> None:
        """Activate initiative system before calling start_battle.

        Args:
            seed: Optional RNG seed for deterministic rolls (tests).
        """

        self._rng_seed = seed
        self._rng = random.Random(seed) if seed is not None else random.Random()
        self.initiative_order = calculate_initiative(self.units, rng=self._rng)
        self.initiative_sort = initiative_sort_key_factory(self.initiative_order)
        # Sort immediately so presentation can inspect order prior to start_battle if needed
        self._sort_units()

        # Log initiative table
        logger = get_logger(__name__)
        table = self.get_initiative_table()
        logger.info("Initiative order (unit_id, total, base_ke, roll): %s", table)

    def refresh_initiative_for_new_round(self) -> None:
        """Re-roll initiative at the start of a new round unless persistent order is set."""
        if not self.initiative_order:
            return
        # Only re-roll if not persistent
        re_roll = not getattr(self.initiative_order, "persistent", False)
        self.initiative_order.refresh_for_new_round(self.units, re_roll=re_roll, rng=self._rng)
        self.initiative_sort = initiative_sort_key_factory(self.initiative_order)
        self._sort_units()
        # Log initiative table
        logger = get_logger(__name__)
        table = self.get_initiative_table()
        logger.info("Initiative order (unit_id, total, base_ke, roll): %s", table)

    def _sort_units(self) -> None:
        if self.initiative_sort:
            # Sort descending by provided key (higher initiative first)
            self.units.sort(key=self.initiative_sort, reverse=True)
        else:
            # Default: use KE (initiative modifier) descending
            self.units.sort(key=lambda u: u.combat_stats.KE, reverse=True)

    def _init_ap(self) -> None:
        self.ap_pool = {u.id: compute_unit_ap(u) for u in self.units if u.is_alive()}

    def current_unit(self) -> Unit:
        return self.units[self.turn_index]

    def remaining_ap(self, unit: Unit) -> int:
        return self.ap_pool.get(unit.id, 0)

    def spend_ap(self, unit: Unit, amount: int) -> bool:
        if self.remaining_ap(unit) < amount:
            return False
        self.ap_pool[unit.id] -= amount
        return True

    def end_turn(self) -> None:
        """Advance to next alive unit; on wrap, start new round and refresh AP + reactions.

        Skips dead units. If all units are dead, ends the battle.
        """
        num_units = len(self.units)
        for _ in range(num_units):
            self.turn_index += 1
            if self.turn_index >= num_units:
                self.turn_index = 0
                self.round += 1
                # Refresh initiative ordering first (if enabled) then AP and reactions
                self.refresh_initiative_for_new_round()
                self._init_ap()
                self.action_handler.start_turn(self.units)
            # Skip dead units
            if self.units[self.turn_index].is_alive():
                break
        else:
            # All units are dead
            self.battle_active = False
        self._cleanup_dead_units()
        self._check_victory()

    # ------------------------------------------------------------------
    # Initiative inspection helpers
    # ------------------------------------------------------------------
    def get_initiative_table(self) -> list[tuple[str, int, int, int]]:
        """Return debug table of current initiative entries.

        Returns rows: (unit_id, total, base_ke, roll)
        """
        if not self.initiative_order:
            return []
        table = self.initiative_order.to_debug_table()
        return list(table)

    def _cleanup_dead_units(self) -> None:
        # Remove units that are dead from AP pool (keep in list for history; optional removal strategy)
        for u in self.units:
            if not u.is_alive() and u.id in self.ap_pool:
                del self.ap_pool[u.id]

    def _check_victory(self) -> None:
        if not self.team_a_ids or not self.team_b_ids:
            return  # Teams not set yet
        alive_a = any(u.is_alive() for u in self.units if u.id in self.team_a_ids)
        alive_b = any(u.is_alive() for u in self.units if u.id in self.team_b_ids)
        if not alive_a or not alive_b:
            self.battle_active = False

    def is_victory(self) -> bool:
        return not self.battle_active

    # --- Action wrappers integrating AP economy ---
    def move_current_unit(
        self,
        dest: Position,
        enemy: Unit | None = None,
        blocked: Iterable[tuple[int, int]] | None = None,
        potential_reactors: Iterable[Unit] | None = None,
    ) -> dict[str, object]:
        unit = self.current_unit()
        summary = self.action_handler.move_unit(
            unit=unit,
            dest=dest,
            enemy=enemy,
            ap_available=self.remaining_ap(unit),
            blocked=blocked,
            potential_reactors=potential_reactors,
        )
        if "error" in summary:
            return summary
        ap_spent_obj = summary.get("ap_spent", 0)
        if isinstance(ap_spent_obj, int):
            ap_spent = ap_spent_obj
        elif isinstance(ap_spent_obj, str):
            try:
                ap_spent = int(ap_spent_obj)
            except ValueError:
                ap_spent = 0
        else:
            ap_spent = 0
        if not self.spend_ap(unit, ap_spent):
            summary["error"] = "Insufficient AP after movement"
        return summary

    def attack_current_unit(self, defender: Unit, **kwargs: object) -> dict[str, object]:
        unit = self.current_unit()

        # Validate target is in attack range

        if not can_attack_target(unit, defender.position, unit.weapon):
            return {"error": f"{defender.name} is not in attack range"}

        # AttackAction has fixed AP cost inside result.ap_spent
        # Separate rng_overrides if present in kwargs
        rng_overrides = None
        if isinstance(kwargs, dict) and "rng_overrides" in kwargs:
            candidate = kwargs.pop("rng_overrides")
            if isinstance(candidate, dict):
                rng_overrides = candidate
            else:
                rng_overrides = None
        result = self.action_handler.attack(
            attacker=unit, defender=defender, rng_overrides=rng_overrides, **kwargs
        )
        ap_spent_obj = getattr(result, "ap_spent", 0)
        if isinstance(ap_spent_obj, int):
            ap_spent = ap_spent_obj
        elif isinstance(ap_spent_obj, str):
            try:
                ap_spent = int(ap_spent_obj)
            except ValueError:
                ap_spent = 0
        else:
            ap_spent = 0
        if result.success and not self.spend_ap(unit, ap_spent):
            return {"error": "Insufficient AP after attack", "action_result": result}
        return {"action_result": result}

    def rotate_current_unit(self, new_facing: Facing) -> dict[str, object]:
        """Rotate current unit to face a new direction.

        Args:
            new_facing: Target facing direction (0-5)

        Returns:
            Dict with action_result and ap_spent, or error
        """
        unit = self.current_unit()
        summary = self.action_handler.change_facing(
            unit=unit, new_facing=new_facing, ap_available=self.remaining_ap(unit)
        )
        ap_spent_obj = summary.get("ap_spent", 0)
        if isinstance(ap_spent_obj, int):
            ap_spent = ap_spent_obj
        elif isinstance(ap_spent_obj, str):
            try:
                ap_spent = int(ap_spent_obj)
            except ValueError:
                ap_spent = 0
        else:
            ap_spent = 0
        if "error" not in summary and not self.spend_ap(unit, ap_spent):
            summary["error"] = "Insufficient AP after rotation"
        return summary

    def set_teams(self, team_a: Iterable[Unit], team_b: Iterable[Unit]) -> None:
        self.team_a_ids = [u.id for u in team_a]
        self.team_b_ids = [u.id for u in team_b]
        self._check_victory()

    # --- Query methods for presentation layer ---
    def get_enemies(self, unit: Unit) -> list[Unit]:
        """Get all enemy units relative to the given unit.

        Args:
            unit: Unit to get enemies for

        Returns:
            List of enemy units
        """
        if unit.id in self.team_a_ids:
            return [u for u in self.units if u.id in self.team_b_ids]
        elif unit.id in self.team_b_ids:
            return [u for u in self.units if u.id in self.team_a_ids]
        return []

    def get_unit_at_position(self, pos: Position) -> Unit | None:
        """Find unit at given hex position.

        Args:
            pos: Position to check

        Returns:
            Unit at position, or None
        """
        for unit in self.units:
            if unit.position.q == pos.q and unit.position.r == pos.r:
                return unit
        return None

    def get_winner(self) -> str | None:
        """Determine battle winner.

        Returns:
            "team_a" if Team A won
            "team_b" if Team B won
            "draw" if both teams eliminated
            None if battle still active
        """
        if self.battle_active:
            return None

        team_a_alive = any(u.is_alive() for u in self.units if u.id in self.team_a_ids)
        team_b_alive = any(u.is_alive() for u in self.units if u.id in self.team_b_ids)

        if team_a_alive and not team_b_alive:
            return "team_a"
        elif team_b_alive and not team_a_alive:
            return "team_b"
        else:
            return "draw"

    # --- Helper methods for UI highlighting ---
    def compute_reachable_hexes(self, unit: Unit) -> set[tuple[int, int]]:
        """Calculate hexes reachable by unit based on remaining AP.

        Uses BFS flood fill to find all hexes within movement range,
        accounting for AP cost per hex and blocked positions.

        Args:
            unit: Unit to calculate reachable hexes for

        Returns:
            Set of (q, r) hex coordinates the unit can reach
        """

        ap_available = self.remaining_ap(unit)
        max_distance = ap_available // AP_COST_MOVEMENT

        if max_distance <= 0:
            return set()

        start = (unit.position.q, unit.position.r)
        visited = {start}
        queue = deque([(start, 0)])
        reachable = set()

        # Get all occupied positions to block (can't move through other units)
        blocked = {(u.position.q, u.position.r) for u in self.units if u.id != unit.id}

        while queue:
            (q, r), dist = queue.popleft()

            # Add to reachable if beyond start position and within range
            if 0 < dist <= max_distance:
                reachable.add((q, r))

            # Continue exploring if not at max distance
            if dist < max_distance:
                for dq, dr in NEIGHBORS:
                    nxt = (q + dq, r + dr)
                    if nxt not in visited and nxt not in blocked:
                        visited.add(nxt)
                        queue.append((nxt, dist + 1))

        return reachable

    def compute_attackable_hexes(self: BattleService, unit: Unit) -> set[tuple[int, int]]:
        """Calculate hexes attackable by unit based on weapon reach and facing.

        Uses the domain reach mechanics to determine which hexes are in
        the unit's attack range based on weapon size and facing direction.

        Args:
            unit: Unit to calculate attackable hexes for

        Returns:
            Set of (q, r) hex coordinates the unit can attack
        """
        result = compute_reach_hexes(unit, unit.weapon)
        return set(result)

    def compute_enemy_zones(self: BattleService, unit: Unit) -> set[tuple[int, int]]:
        """Calculate combined zone of control for all enemies of the given unit.

        Useful for visual warning when planning movement paths.

        Args:
            unit: Unit to calculate enemy zones for

        Returns:
            Set of (q, r) hex coordinates covered by enemy zones of control
        """
        enemies = self.get_enemies(unit)
        enemy_zones: set[tuple[int, int]] = set()
        for enemy in enemies:
            if enemy.is_alive():
                zone = compute_reach_hexes(enemy, enemy.weapon)
                enemy_zones.update(set(zone))
        return enemy_zones
