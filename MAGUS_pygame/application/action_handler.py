"""
Application-level action orchestration.

Responsibilities:
- Validate and execute actions (MovementAction, AttackAction, ...)
- Apply domain results to entities (AP/FP/EP changes) where appropriate
- Invoke ReactionHandler when actions trigger reactions (e.g., movement enters ZoC)
- Provide a simple facade for the UI/presentation layer
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from domain.entities import Unit
from domain.mechanics import (
    AttackAction,
    MovementAction,
)
from domain.mechanics.actions import ActionResult
from domain.mechanics.actions.facing_action import FacingAction
from domain.mechanics.attack_resolution import apply_attack_result
from domain.value_objects import Facing, Position

from .reaction_handler import ReactionHandler


@dataclass
class ActionHandler:
    reaction_handler: ReactionHandler = field(default_factory=ReactionHandler)

    def start_turn(self, units: Iterable[Unit]) -> None:
        self.reaction_handler.start_turn(units)

    # --- Movement ---
    def move_unit(
        self: "ActionHandler",
        *,
        unit: Unit,
        dest: Position,
        enemy: Unit | None = None,
        ap_available: int = 0,
        blocked: Iterable[tuple[int, int]] | None = None,
        apply_move: bool = True,
        potential_reactors: Iterable[Unit] | None = None,
        rng_overrides: dict[str, object] | None = None,
    ) -> dict[str, object]:
        """Execute movement with optional reactions. Returns a summary dict.

        The summary includes: action_result, reaction_results, final_path, ap_spent.
        """
        # Compute combined enemy zones if potential_reactors provided
        enemy_zones: set[tuple[int, int]] = set()
        if potential_reactors:
            from domain.mechanics.reach import compute_reach_hexes

            for reactor in potential_reactors:
                if reactor.is_alive():
                    zone = compute_reach_hexes(reactor, reactor.weapon)
                    enemy_zones.update(zone)

        move = MovementAction()
        ok, msg = move.can_execute(
            unit=unit,
            start=unit.position,
            dest=dest,
            enemy=enemy,
            enemy_zones=enemy_zones if enemy_zones else None,
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
            enemy_zones=enemy_zones if enemy_zones else None,
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
        # Calculate AP spent for the actual path taken (truncated if interrupted)
        if final_path:
            ap_per_hex = move.ap_per_hex if hasattr(move, "ap_per_hex") else 2
            ap_spent = (len(final_path) - 1) * ap_per_hex
        else:
            ap_spent = 0

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
        self: "ActionHandler",
        *,
        attacker: Unit,
        defender: Unit,
        rng_overrides: dict[str, object] | None = None,
        **kwargs: object,
    ) -> ActionResult:
        act = AttackAction()
        ok, msg = act.can_execute(attacker=attacker, defender=defender, **kwargs)
        if not ok:
            return ActionResult(success=False, message=msg)

        ares = act.execute(attacker=attacker, defender=defender, **(rng_overrides or {}), **kwargs)

        # Attack action is pure; application layer applies to defender if desired

        apply_attack_result(ares.data["attack_result"], defender)

        return ares

    # --- Facing ---
    def change_facing(
        self: "ActionHandler",
        *,
        unit: Unit,
        new_facing: Facing,
        ap_available: int = 0,
        apply_rotation: bool = True,
    ) -> dict[str, object]:
        """Execute facing change. Returns a summary dict.

        The summary includes: action_result, ap_spent.

        Args:
            unit: Unit to rotate
            new_facing: Target facing direction
            ap_available: Available action points
            apply_rotation: If True, apply facing change to unit

        Returns:
            Dict with action_result and ap_spent, or error
        """
        action = FacingAction()
        ok, msg = action.can_execute(unit=unit, new_facing=new_facing, ap_available=ap_available)
        if not ok:
            return {"error": msg}

        result = action.execute(unit=unit, new_facing=new_facing)

        # Apply rotation if requested
        if apply_rotation and result.success:
            unit.rotate_to(new_facing)

        return {"action_result": result, "ap_spent": result.ap_spent}
