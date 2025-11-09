"""
Application-level reaction orchestration.

Responsibilities:
- Track per-unit reaction budget (default: 1 per turn)
- Evaluate should_trigger for relevant reactions
- Execute eligible reactions (e.g., opportunity attack) and collect results
- Apply domain results to entities (EP/FP changes) where appropriate

This handler is intentionally thin: pure computations remain in domain.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Iterable, Tuple

from domain.entities import Unit
from domain.mechanics import (
    OpportunityAttackReaction,
    apply_attack_result,
)
from domain.mechanics.actions import ActionResult
from domain.mechanics.reactions import ReactionResult


@dataclass
class ReactionBudget:
    """Tracks remaining reactions per unit for the current turn."""
    max_reactions_per_turn: int = 1
    remaining: Dict[str, int] = field(default_factory=dict)

    def reset_for_units(self, units: Iterable[Unit]) -> None:
        self.remaining = {u.id: self.max_reactions_per_turn for u in units}

    def can_react(self, unit: Unit) -> bool:
        return self.remaining.get(unit.id, self.max_reactions_per_turn) > 0

    def consume(self, unit: Unit) -> bool:
        if not self.can_react(unit):
            return False
        self.remaining[unit.id] = self.remaining.get(unit.id, self.max_reactions_per_turn) - 1
        return True


@dataclass
class ReactionHandler:
    """Coordinates reaction evaluation and execution."""
    budget: ReactionBudget = field(default_factory=ReactionBudget)

    def start_turn(self, units: Iterable[Unit]) -> None:
        """Reset budget for all units at turn start."""
        self.budget.reset_for_units(units)

    def handle_opportunity_attacks(
        self,
        *,
        movers_path: List[Tuple[int, int]],
        intersects_zoc: bool,
        intersection_index: Optional[int],
        mover: Unit,
        potential_reactors: Iterable[Unit],
        mover_shield_ve: int = 0,
        mover_dodge_mod: int = 0,
        rng_overrides: Optional[dict] = None,
    ) -> List[ReactionResult]:
        """Evaluate and execute opportunity attacks from potential reactors.

        Returns a list of ReactionResult in the order they are resolved.
        Stops early if a reaction interrupts movement.
        """
        results: List[ReactionResult] = []

        if not intersects_zoc or intersection_index is None:
            return results

        for reactor in potential_reactors:
            if reactor.id == mover.id:
                continue
            if not self.budget.can_react(reactor):
                continue

            reaction = OpportunityAttackReaction()
            should, _ = reaction.should_trigger(
                path=movers_path,
                intersects_zoc=intersects_zoc,
                intersection_index=intersection_index,
                attacker=reactor,
                mover=mover,
            )
            if not should:
                continue

            rkwargs = {}
            if rng_overrides:
                if "attack_roll" in rng_overrides:
                    rkwargs["attack_roll"] = rng_overrides["attack_roll"]
                if "base_damage_roll" in rng_overrides:
                    rkwargs["base_damage_roll"] = rng_overrides["base_damage_roll"]

            result = reaction.execute(
                attacker=reactor,
                mover=mover,
                intersection_index=intersection_index,
                path=movers_path,
                shield_ve=mover_shield_ve,
                dodge_modifier=mover_dodge_mod,
                **rkwargs,
            )
            # Apply effects (mutating mover) from domain result payload
            attack_result = result.data.get("attack_result")
            if attack_result is not None:
                apply_attack_result(attack_result, mover)

            # Consume budget after a fired reaction
            self.budget.consume(reactor)
            results.append(result)

            if result.interrupts_movement:
                break

        return results
