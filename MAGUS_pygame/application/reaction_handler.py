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
    CounterattackReaction,
    OpportunityAttackReaction,
    ReactionShieldBash,
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
    counterattacks_used: dict[str, int] = field(default_factory=dict)
    reaction_bashes_used: dict[str, int] = field(default_factory=dict)

    def start_turn(self, units: Iterable[Unit]) -> None:
        """Reset budget for all units at turn start."""
        self.budget.reset_for_units(units)
        self.counterattacks_used = {u.id: 0 for u in units}
        self.reaction_bashes_used = {u.id: 0 for u in units}

    def handle_opportunity_attacks(
        self: ReactionHandler,
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

        # Note: we intentionally do not early-return on intersects_zoc here because
        # disengaging (starting inside ZoC and moving out) should still trigger OA.
        # Per-reactor checks below compute their own intersection index.

        # Lazily import to avoid cycles
        from domain.mechanics.reach import compute_reach_hexes

        if not movers_path or len(movers_path) < 2:
            logger.info("Path too short for opportunity attack evaluation.")
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

            # Compute this reactor's zone and first intersection index (including disengage)
            reactor_zone = compute_reach_hexes(reactor, reactor.weapon)
            start_in_zone = movers_path[0] in reactor_zone
            first_idx: int | None = None
            for i, hex_pos in enumerate(movers_path):
                if i == 0:
                    continue  # skip start hex for enter/within checks
                if hex_pos in reactor_zone:
                    first_idx = i
                    break
            if first_idx is None and start_in_zone and len(movers_path) > 1:
                # Disengage: started in zone, leaving on first step
                first_idx = 1

            reaction = OpportunityAttackReaction()
            should, reason = reaction.should_trigger(
                path=movers_path,
                intersects_zoc=first_idx is not None,
                intersection_index=first_idx,
                attacker=reactor,
                mover=mover,
            )
            logger.info(f"should_trigger={should} reason={reason}")
            if not should or first_idx is None:
                continue

            rkwargs = {}
            if rng_overrides:
                if "attack_roll" in rng_overrides:
                    rkwargs["attack_roll"] = rng_overrides["attack_roll"]
                if "base_damage_roll" in rng_overrides:
                    rkwargs["base_damage_roll"] = rng_overrides["base_damage_roll"]

            logger.info(
                f"Triggering opportunity attack from {reactor.name} on {mover.name} at intersection {first_idx}"
            )
            # Determine weapon and skill level for correct stamina cost
            weapon = getattr(reactor, "weapon", None)
            weapon_skill_level = 0
            if weapon is not None:
                skill_id = getattr(weapon, "skill_id", "") or ""
                if skill_id and getattr(reactor, "skills", None):
                    try:
                        weapon_skill_level = reactor.skills.get_rank(skill_id, 0)
                    except Exception:
                        weapon_skill_level = 0
            result = reaction.execute(
                attacker=reactor,
                mover=mover,
                intersection_index=first_idx,
                path=movers_path,
                weapon=weapon,
                weapon_skill_level=weapon_skill_level,
                shield_ve=mover_shield_ve,
                dodge_modifier=mover_dodge_mod,
                **rkwargs,
            )

            # Add unit names to result data for presentation layer
            result.data["attacker_name"] = reactor.name
            result.data["defender_name"] = mover.name

            # Apply effects (mutating mover) from domain result payload
            attack_result = result.data.get("attack_result")
            if attack_result is not None:
                apply_attack_result(attack_result, mover)
                # Spend stamina for attacker and defender (mover) similar to ActionHandler
                if hasattr(reactor, "stamina") and reactor.stamina:
                    if attack_result.stamina_spent_attacker > 0:
                        reactor.stamina.spend_action_points(attack_result.stamina_spent_attacker)
                if hasattr(mover, "stamina") and mover.stamina:
                    if attack_result.stamina_spent_defender > 0:
                        mover.stamina.spend_action_points(attack_result.stamina_spent_defender)

            # Consume budget after a fired reaction
            self.budget.consume(reactor)
            results.append(result)

            if result.interrupts_movement:
                logger.info("Movement interrupted by opportunity attack.")
                break

        logger.info(f"Total opportunity attacks triggered: {len(results)}")
        return results

    def handle_counterattacks(
        self: ReactionHandler,
        *,
        attacker: Unit,
        defender: Unit,
        last_attack_result: object | None,
        rng_overrides: dict[str, object] | None = None,
    ) -> list[ReactionResult]:
        """Evaluate and execute longsword counterattacks after a miss/parry."""
        results: list[ReactionResult] = []

        if attacker is None or defender is None:
            return results

        reaction = CounterattackReaction()
        used = self.counterattacks_used.get(defender.id, 0)
        should, reason = reaction.should_trigger(
            attacker=attacker,
            defender=defender,
            last_attack_result=last_attack_result,
            counterattacks_used=used,
        )
        logger.info(f"Counterattack should_trigger={should} reason={reason}")
        if not should:
            return results

        rkwargs = {}
        if rng_overrides:
            if "attack_roll" in rng_overrides:
                rkwargs["attack_roll"] = rng_overrides["attack_roll"]
            if "base_damage_roll" in rng_overrides:
                rkwargs["base_damage_roll"] = rng_overrides["base_damage_roll"]

        # Determine weapon and skill level for defender (reactor)
        weapon = getattr(defender, "weapon", None)
        weapon_skill_level = 0
        if weapon is not None:
            skill_id = getattr(weapon, "skill_id", "") or ""
            if skill_id and getattr(defender, "skills", None):
                try:
                    weapon_skill_level = defender.skills.get_rank(skill_id, 0)
                except Exception:
                    weapon_skill_level = 0

        result = reaction.execute(
            attacker=attacker,
            defender=defender,
            weapon=weapon,
            weapon_skill_level=weapon_skill_level,
            **rkwargs,
        )

        # Add unit names to result data for presentation layer
        result.data["attacker_name"] = defender.name
        result.data["defender_name"] = attacker.name

        # Apply effects to original attacker
        attack_result = result.data.get("attack_result")
        if attack_result is not None:
            apply_attack_result(attack_result, attacker)
            if hasattr(defender, "stamina") and defender.stamina:
                if attack_result.stamina_spent_attacker > 0:
                    defender.stamina.spend_action_points(attack_result.stamina_spent_attacker)
            if hasattr(attacker, "stamina") and attacker.stamina:
                if attack_result.stamina_spent_defender > 0:
                    attacker.stamina.spend_action_points(attack_result.stamina_spent_defender)

        self.counterattacks_used[defender.id] = used + 1
        results.append(result)
        return results

    def handle_reaction_shieldbash(
        self: ReactionHandler,
        *,
        attacker: Unit,
        defender: Unit,
        last_attack_result: object | None,
        rng_overrides: dict[str, object] | None = None,
    ) -> list[ReactionResult]:
        """Evaluate and execute reaction shield bash after a successful block."""
        results: list[ReactionResult] = []

        if attacker is None or defender is None:
            return results

        reaction = ReactionShieldBash()
        used = self.reaction_bashes_used.get(defender.id, 0)
        should, reason = reaction.should_trigger(
            attacker=attacker,
            defender=defender,
            last_attack_result=last_attack_result,
            reactions_used=used,
        )
        logger.info(f"Reaction shield bash should_trigger={should} reason={reason}")
        if not should:
            return results

        rkwargs = {}
        if rng_overrides:
            if "attack_roll" in rng_overrides:
                rkwargs["attack_roll"] = rng_overrides["attack_roll"]
            if "base_damage_roll" in rng_overrides:
                rkwargs["base_damage_roll"] = rng_overrides["base_damage_roll"]

        result = reaction.execute(
            attacker=attacker,
            defender=defender,
            **rkwargs,
        )

        # Add unit names to result data for presentation layer
        result.data["attacker_name"] = defender.name
        result.data["defender_name"] = attacker.name

        # Apply effects to original attacker
        attack_result = result.data.get("attack_result")
        if attack_result is not None:
            apply_attack_result(attack_result, attacker)
            if hasattr(defender, "stamina") and defender.stamina:
                if attack_result.stamina_spent_attacker > 0:
                    defender.stamina.spend_action_points(attack_result.stamina_spent_attacker)
            if hasattr(attacker, "stamina") and attacker.stamina:
                if attack_result.stamina_spent_defender > 0:
                    attacker.stamina.spend_action_points(attack_result.stamina_spent_defender)

        self.reaction_bashes_used[defender.id] = used + 1
        results.append(result)
        return results
