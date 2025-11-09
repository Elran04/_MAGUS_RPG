"""
Application-level action orchestration.

Responsibilities:
- Validate and execute actions (MovementAction, AttackAction, ...)
- Apply domain results to entities (AP/FP/EP changes) where appropriate
- Invoke ReactionHandler when actions trigger reactions (e.g., movement enters ZoC)
- Provide a simple facade for the UI/presentation layer
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Tuple

from domain.entities import Unit
from domain.value_objects import Position
from domain.mechanics import (
    AttackAction,
    MovementAction,
)
from domain.mechanics.actions import ActionResult
from .reaction_handler import ReactionHandler


@dataclass
class ActionHandler:
    reaction_handler: ReactionHandler = field(default_factory=ReactionHandler)

    def start_turn(self, units: Iterable[Unit]) -> None:
        self.reaction_handler.start_turn(units)

    # --- Movement ---
    def move_unit(
        self,
        *,
        unit: Unit,
        dest: Position,
        enemy: Optional[Unit] = None,
        ap_available: int = 0,
        blocked: Optional[Iterable[Tuple[int, int]]] = None,
        apply_move: bool = True,
        potential_reactors: Optional[Iterable[Unit]] = None,
        rng_overrides: Optional[dict] = None,
    ) -> dict:
        """Execute movement with optional reactions. Returns a summary dict.

        The summary includes: action_result, reaction_results, final_path, ap_spent.
        """
        move = MovementAction()
        ok, msg = move.can_execute(
            unit=unit,
            start=unit.position,
            dest=dest,
            enemy=enemy,
            ap_available=ap_available,
            blocked=blocked,
        )
        if not ok:
            return {"error": msg}

        ares: ActionResult = move.execute(
            unit=unit,
            start=unit.position,
            dest=dest,
            enemy=enemy,
            ap_available=ap_available,
            blocked=blocked,
        )

        path = ares.data.get("path", [])
        intersects = ares.data.get("intersects_zoc", False)
        ix = ares.data.get("intersection_index")

        reaction_results = []
        final_path = path
        if potential_reactors:
            # Use application-level list of reactors around the path
            reaction_results = self.reaction_handler.handle_opportunity_attacks(
                movers_path=path,
                intersects_zoc=intersects,
                intersection_index=ix,
                mover=unit,
                potential_reactors=potential_reactors,
                mover_shield_ve=0,  # Placeholder: shield VÉ not yet modeled on Unit
                mover_dodge_mod=0,  # Placeholder: dodge skill not yet modeled
                rng_overrides=rng_overrides,
            )
            # If any reaction interrupts, truncate path
            for rr in reaction_results:
                if rr.interrupts_movement and rr.interrupt_index is not None:
                    final_path = path[: rr.interrupt_index + 1]
                    break

        # Apply movement (only the final truncated or full path)
        ap_spent = ares.ap_spent
        if apply_move and final_path:
            end_q, end_r = final_path[-1]
            unit.move_to(Position(end_q, end_r))
            # AP mutations should be handled by game state; we return ap_spent for caller

        return {
            "action_result": ares,
            "reaction_results": reaction_results,
            "final_path": final_path,
            "ap_spent": ap_spent,
        }

    # --- Attack ---
    def attack(
        self,
        *,
        attacker: Unit,
        defender: Unit,
        rng_overrides: Optional[dict] = None,
        **kwargs,
    ) -> ActionResult:
        act = AttackAction()
        ok, msg = act.can_execute(attacker=attacker, defender=defender, **kwargs)
        if not ok:
            return ActionResult(success=False, message=msg)

        ares = act.execute(attacker=attacker, defender=defender, **(rng_overrides or {}), **kwargs)

        # Attack action is pure; application layer applies to defender if desired
        # from domain.mechanics.attack_resolution import apply_attack_result
        # apply_attack_result(ares.data["attack_result"], defender)

        return ares
