"""
BattleService - orchestrates turn order, action points, and victory checks.

AP model:
- Base AP per unit per turn = 10
- For each point of Gyorsaság (Attributes.speed) above 15, gain +1 AP.

This AP computation is domain logic, but lightweight enough to live here; if it
expands (skills, conditions), extract to domain.mechanics.ap or similar.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Callable, Optional, Iterable

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
    units: List[Unit]
    action_handler: ActionHandler = field(default_factory=ActionHandler)
    initiative_sort: Optional[Callable[[Unit], int]] = None

    turn_index: int = 0
    round: int = 1
    ap_pool: Dict[str, int] = field(default_factory=dict)

    # Victory tracking (simple placeholder: teams distinguished externally)
    team_a_ids: List[str] = field(default_factory=list)
    team_b_ids: List[str] = field(default_factory=list)

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
    def move_current_unit(self, dest: Position, enemy: Optional[Unit] = None, blocked=None, potential_reactors=None) -> dict:
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

