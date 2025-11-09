"""
BattleService - orchestrates turn order, action points, and victory checks.

AP model:
- Base AP per unit per turn = 10
- For each point of Gyorsaság (Attributes.speed) above 15, gain +1 AP.

This AP computation is domain logic, but lightweight enough to live here; if it
expands (skills, conditions), extract to domain.mechanics.ap or similar.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field

from domain.entities import Unit
from domain.value_objects import Position

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

    turn_index: int = 0
    round: int = 1
    ap_pool: dict[str, int] = field(default_factory=dict)

    # Victory tracking (simple placeholder: teams distinguished externally)
    team_a_ids: list[str] = field(default_factory=list)
    team_b_ids: list[str] = field(default_factory=list)

    battle_active: bool = True

    def start_battle(self) -> None:
        """Initialize battle: sort units, compute initial AP, reset reactions."""
        self._sort_units()
        self._init_ap()
        self.action_handler.start_turn(self.units)

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
        """Advance to next unit; on wrap, start new round and refresh AP + reactions."""
        self.turn_index += 1
        if self.turn_index >= len(self.units):
            self.turn_index = 0
            self.round += 1
            self._init_ap()
            self.action_handler.start_turn(self.units)
        self._cleanup_dead_units()
        self._check_victory()

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
        self, dest: Position, enemy: Unit | None = None, blocked=None, potential_reactors=None
    ) -> dict:
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
        if not self.spend_ap(unit, summary.get("ap_spent", 0)):
            summary["error"] = "Insufficient AP after movement"
        return summary

    def attack_current_unit(self, defender: Unit, **kwargs) -> dict:
        unit = self.current_unit()
        # AttackAction has fixed AP cost inside result.ap_spent
        result = self.action_handler.attack(attacker=unit, defender=defender, **kwargs)
        if result.success:
            if not self.spend_ap(unit, result.ap_spent):
                return {"error": "Insufficient AP after attack", "action_result": result}
        return {"action_result": result}

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
