"""Initiative (Turn Order) Mechanics.

Reimplements and generalizes the old system's initiative roll logic:

Old rule (from legacy `old_system.actions.handler.roll_initiative`):
	initiative_total = d100 + KÉ (unit.combat_stats.KE)
	Higher total acts first. Tie-breaker: higher base KÉ. If still tied, reroll.

This module extends it for multi‑unit battles:
	1. Each unit rolls: d100 + KE.
	2. Sort descending by total.
	3. Tie groups are resolved by higher KE.
	4. Remaining perfect ties are re‑rolled only within the tie group until unique
	   ordering achieved (stable against external groups).

The result is an InitiativeOrder object that:
	- Stores per‑unit roll details
	- Tracks current index & round
	- Supports advancing turns, auto‑incrementing rounds
	- Can rebuild a fresh ordering at start of a new round (optional)

API Overview:
	calculate_initiative(units, *, rng=None) -> InitiativeOrder
		Perform a fresh roll and return an InitiativeOrder tracker.

	InitiativeOrder.next_turn()
		Advance to the next living unit, auto‑progress rounds when cycling past end.

	InitiativeOrder.refresh_for_new_round(re_roll: bool = True)
		Optionally re‑roll at the start of a new round (many systems keep order;
		parameter allows both styles).

Determinism:
	Pass a random.Random instance via rng= to produce reproducible sequences in tests.

Extensibility hooks:
	- Modify _roll_formula if later initiative factors (skills, conditions) appear.
	- Add dynamic adjustments mid‑battle by altering .modifiers map and re‑rolling.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Dict, Tuple, Optional
import random

from domain.entities import Unit


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class InitiativeEntry:
	"""Single unit's initiative outcome for a round.

	Attributes:
		unit_id: Stable identifier for the unit.
		total: Final initiative total (d100 + KE + modifiers).
		base_ke: Unit's base KE (for tie breaking).
		roll: Raw d100 roll component.
	"""

	unit_id: str
	total: int
	base_ke: int
	roll: int


@dataclass
class InitiativeOrder:
	"""Tracks ordered initiative sequence across rounds.

	The `order` list stores unit ids in acting sequence. `entries` maps unit id ->
	InitiativeEntry for inspection / UI. Dead units can be skipped by caller or
	via `filter_alive` helper when integrating with battle service.
	"""

	order: List[str]
	entries: Dict[str, InitiativeEntry]
	round: int = 1
	index: int = 0  # Index in order for current acting unit
	persistent: bool = False  # If True, do not re-roll on new rounds unless forced

	def current_unit_id(self) -> str:
		return self.order[self.index]

	def next_turn(self) -> str:
		"""Advance to next unit; increment round when wrapping.

		Returns:
			unit_id of the new active unit.
		"""
		self.index += 1
		if self.index >= len(self.order):
			self.index = 0
			self.round += 1
		return self.current_unit_id()

	def refresh_for_new_round(self, units: Iterable[Unit], *, re_roll: bool = True, rng: random.Random | None = None) -> None:
		"""Optionally re-roll initiative at start of a new round.

		Args:
			units: Iterable of current units (alive ones ideally) to include.
			re_roll: If False and self.persistent=True, keeps existing order.
			rng: Optional RNG for deterministic re-roll.
		"""
		if self.persistent and not re_roll:
			self.round += 1
			self.index = 0
			return
		new_order = calculate_initiative(units, rng=rng)
		# Replace internal state
		self.order = new_order.order
		self.entries = new_order.entries
		self.round += 1
		self.index = 0

	def to_debug_table(self) -> List[Tuple[str, int, int, int]]:
		"""Return debug rows: (unit_id, total, base_ke, roll)."""
		return [
			(uid, self.entries[uid].total, self.entries[uid].base_ke, self.entries[uid].roll)
			for uid in self.order
		]


# ---------------------------------------------------------------------------
# Core calculation
# ---------------------------------------------------------------------------

def _roll_formula(unit: Unit, rng: random.Random) -> Tuple[int, int]:
	"""Compute (roll, total) for unit.

	Current formula: d100 + KE (combat_stats.KE)
	Returns raw d100 roll and final total.
	"""
	d100 = rng.randint(1, 100)
	base_ke = getattr(unit.combat_stats, "KE", 0)
	total = d100 + base_ke
	return d100, total


def _resolve_ties(entries: List[InitiativeEntry], rng: random.Random) -> List[InitiativeEntry]:
	"""Resolve tie groups iteratively until unique ordering.

	Sorting precedence:
		1. higher total
		2. higher base_ke
		3. if still tied: re-roll d100 ONLY for tied group, recompute total
		   (base_ke unchanged) and resort until no exact tie on (total, base_ke).
	"""
	# Initial sort by (total, base_ke) descending
	entries.sort(key=lambda e: (e.total, e.base_ke), reverse=True)

	i = 0
	while i < len(entries):
		j = i + 1
		# Find tie group range where (total, base_ke) identical
		while j < len(entries) and (
			entries[j].total == entries[i].total and entries[j].base_ke == entries[i].base_ke
		):
			j += 1
		group_size = j - i
		if group_size > 1:
			# Re-roll for tie group only
			new_group: List[InitiativeEntry] = []
			for k in range(i, j):
				e = entries[k]
				reroll = rng.randint(1, 100)
				# Recompute total using same base_ke, replace
				new_group.append(
					InitiativeEntry(
						unit_id=e.unit_id,
						total=reroll + e.base_ke,
						base_ke=e.base_ke,
						roll=reroll,
					)
				)
			# Replace slice & resort whole list to keep global ordering consistent
			entries[i:j] = new_group
			entries.sort(key=lambda e: (e.total, e.base_ke), reverse=True)
			# Restart scanning (simpler, small N typical)
			i = 0
			continue
		i = j
	return entries


def calculate_initiative(units: Iterable[Unit], *, rng: random.Random | None = None) -> InitiativeOrder:
	"""Roll initiative for a collection of units.

	Args:
		units: Iterable of Unit objects.
		rng: Optional random.Random for deterministic testable ordering.

	Returns:
		InitiativeOrder tracker.
	"""
	_rng = rng or random.Random()

	entries: List[InitiativeEntry] = []
	for u in units:
		if not u.is_alive():
			continue  # Skip dead units
		roll, total = _roll_formula(u, _rng)
		entries.append(
			InitiativeEntry(
				unit_id=u.id,
				total=total,
				base_ke=getattr(u.combat_stats, "KE", 0),
				roll=roll,
			)
		)

	resolved = _resolve_ties(entries, _rng)
	order = [e.unit_id for e in resolved]
	entry_map = {e.unit_id: e for e in resolved}
	return InitiativeOrder(order=order, entries=entry_map)


# ---------------------------------------------------------------------------
# Convenience helpers for integration
# ---------------------------------------------------------------------------

def initiative_sort_key_factory(order: InitiativeOrder):
	"""Return a key function usable by BattleService._sort_units.

	Example:
		init = calculate_initiative(units)
		battle_service.initiative_sort = initiative_sort_key_factory(init)
		battle_service.start_battle()
	"""

	def _key(unit: Unit) -> int:
		entry = order.entries.get(unit.id)
		# Fallback: units without entry (late spawns) use KE only
		if not entry:
			return getattr(unit.combat_stats, "KE", 0)
		return entry.total

	return _key


__all__ = [
	"InitiativeEntry",
	"InitiativeOrder",
	"calculate_initiative",
	"initiative_sort_key_factory",
]

