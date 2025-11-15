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

from collections.abc import Iterable
from dataclasses import dataclass, field

from domain.entities import Unit
from domain.mechanics import (
    OpportunityAttackReaction,
    apply_attack_result,
)
from domain.mechanics.reactions import ReactionResult
from logger.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ReactionBudget:
    """Tracks remaining reactions per unit for the current turn."""

    max_reactions_per_turn: int = 1
    remaining: dict[str, int] = field(default_factory=dict)

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
        self: "ReactionHandler",
        *,
        movers_path: list[tuple[int, int]],
        intersects_zoc: bool,
        intersection_index: int | None,
        mover: Unit,
        potential_reactors: Iterable[Unit],
        mover_shield_ve: int = 0,
        mover_dodge_mod: int = 0,
        rng_overrides: dict[str, object] | None = None,
    ) -> list[ReactionResult]:
        """Evaluate and execute opportunity attacks from potential reactors.

        Returns a list of ReactionResult in the order they are resolved.
        Stops early if a reaction interrupts movement.
        """

        results: list[ReactionResult] = []

        logger.info(
            f"OpportunityAttack: intersects_zoc={intersects_zoc}, intersection_index={intersection_index}, path={movers_path}"
        )

        if not intersects_zoc or intersection_index is None:
            logger.info("No intersection with ZoC; no opportunity attacks possible.")
            return results

        for reactor in potential_reactors:
            logger.info(
                f"Checking reactor {reactor.name} (id={reactor.id}) at pos={getattr(reactor, 'position', None)} facing={getattr(reactor, 'facing', None)} weapon={getattr(reactor, 'weapon', None)}"
            )
            if reactor.id == mover.id:
                logger.info("Skipping mover itself as reactor.")
                continue
            if not self.budget.can_react(reactor):
                logger.info(f"Reactor {reactor.name} has no remaining reactions this turn.")
                continue

            reaction = OpportunityAttackReaction()
            should, reason = reaction.should_trigger(
                path=movers_path,
                intersects_zoc=intersects_zoc,
                intersection_index=intersection_index,
                attacker=reactor,
                mover=mover,
            )
            logger.info(f"should_trigger={should} reason={reason}")
            if not should:
                continue

            rkwargs = {}
            if rng_overrides:
                if "attack_roll" in rng_overrides:
                    rkwargs["attack_roll"] = rng_overrides["attack_roll"]
                if "base_damage_roll" in rng_overrides:
                    rkwargs["base_damage_roll"] = rng_overrides["base_damage_roll"]

            logger.info(
                f"Triggering opportunity attack from {reactor.name} on {mover.name} at intersection {intersection_index}"
            )
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
                logger.info("Movement interrupted by opportunity attack.")
                break

        logger.info(f"Total opportunity attacks triggered: {len(results)}")
        return results
