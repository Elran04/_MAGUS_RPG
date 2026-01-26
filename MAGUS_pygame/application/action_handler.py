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
from domain.mechanics import AttackAction, MovementAction
from domain.mechanics.actions import ActionResult
from domain.mechanics.actions.facing_action import FacingAction
from domain.mechanics.actions.special.charge_action import ChargeAction
from domain.mechanics.actions.switch_weapon_action import SwitchWeaponAction
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
        self: ActionHandler,
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

        if not ares.success:
            return {"error": ares.message or "Movement failed"}

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
        self: ActionHandler,
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
        # Do not mutate game state here. Effects (damage/stamina) are applied
        # by BattleService only after AP spending succeeds to ensure atomicity.
        return ares

    def charge_attack(
        self: ActionHandler,
        *,
        attacker: Unit,
        defender: Unit,
        ap_available: int = 0,
        blocked: Iterable[tuple[int, int]] | None = None,
        enemy_zones: set[tuple[int, int]] | None = None,
        weapon: object | None = None,
        weapon_skill_level: int = 0,
        shield_ve: int = 0,
        dodge_modifier: int = 0,
        attacker_conditions: int = 0,
        defender_conditions: int = 0,
        overpower_threshold: int = 50,
        stamina_block: dict | None = None,
        stamina_parry: dict | None = None,
        stamina_dodge: dict | None = None,
    ) -> dict[str, object]:
        """Execute charge special attack (move + attack)."""

        act = ChargeAction()
        ok, msg = act.can_execute(
            attacker=attacker,
            target=defender,
            ap_available=ap_available,
            blocked=blocked,
            weapon=weapon or attacker.weapon,
        )
        if not ok:
            return {"error": msg}

        ares: ActionResult = act.execute(
            attacker=attacker,
            target=defender,
            ap_available=ap_available,
            blocked=blocked,
            enemy_zones=enemy_zones,
            weapon=weapon or attacker.weapon,
            weapon_skill_level=weapon_skill_level,
            shield_ve=shield_ve,
            dodge_modifier=dodge_modifier,
            attacker_conditions=attacker_conditions,
            defender_conditions=defender_conditions,
            overpower_threshold=overpower_threshold,
            stamina_block=stamina_block,
            stamina_parry=stamina_parry,
            stamina_dodge=stamina_dodge,
        )

        if not ares.success:
            return {"error": ares.message or "Charge failed"}

        data = ares.data or {}
        path = data.get("path") or []
        landing = data.get("landing_hex")
        new_facing_dir = data.get("new_facing")
        attack_result = data.get("attack_result")
        dmg_mult = data.get("charge_damage_multiplier", 1)

        # Apply damage multiplier from charge
        if attack_result:
            attack_result.damage_to_fp = int(attack_result.damage_to_fp * dmg_mult)
            attack_result.damage_to_ep = int(attack_result.damage_to_ep * dmg_mult)
            apply_attack_result(attack_result, defender)
            # Avoid double-charging attacker stamina: charge has a fixed stamina cost already
            attacker_stamina_cost = 0

            # Spend defender stamina from block/parry/dodge
            if hasattr(defender, "stamina") and defender.stamina:
                if attack_result.stamina_spent_defender > 0:
                    defender.stamina.spend_action_points(attack_result.stamina_spent_defender)

            # Optionally spend attacker stamina if we ever choose to stack it (currently zeroed)
            if attacker_stamina_cost > 0 and hasattr(attacker, "stamina") and attacker.stamina:
                attacker.stamina.spend_action_points(attacker_stamina_cost)

        # Apply stamina cost of the charge action itself
        if hasattr(attacker, "stamina") and attacker.stamina and ares.stamina_spent:
            attacker.stamina.spend_action_points(ares.stamina_spent)

        # Apply movement and facing updates
        if landing is not None:
            attacker.move_to(Position(landing[0], landing[1]))
        if new_facing_dir is not None:
            attacker.rotate_to(Facing(new_facing_dir))

        return {"action_result": ares, "path": path}

    # --- Facing ---
    def change_facing(
        self: ActionHandler,
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

    # --- Weapon Switch ---
    def switch_weapon(
        self: ActionHandler,
        *,
        unit: Unit,
        new_main_hand: str | None,
        new_off_hand: str | None,
        ap_available: int = 0,
        apply_switch: bool = True,
    ) -> dict[str, object]:
        """Execute weapon switch. Returns a summary dict.

        The summary includes: action_result, ap_spent.

        Args:
            unit: Unit switching weapons
            new_main_hand: New main hand weapon ID
            new_off_hand: New off hand weapon ID
            ap_available: Available action points
            apply_switch: If True, apply equipment changes to unit

        Returns:
            Dict with action_result and ap_spent, or error
        """
        action = SwitchWeaponAction()
        ok, msg = action.can_execute(
            unit=unit,
            new_main_hand=new_main_hand,
            new_off_hand=new_off_hand,
            ap_available=ap_available,
        )
        if not ok:
            return {"error": msg}

        result = action.execute(
            unit=unit,
            new_main_hand=new_main_hand,
            new_off_hand=new_off_hand,
        )

        # Apply equipment changes if requested
        if apply_switch and result.success:
            equipment = unit.character_data["equipment"]
            equipment["main_hand"] = new_main_hand or ""
            equipment["off_hand"] = new_off_hand or ""

        return {"action_result": result, "ap_spent": result.ap_spent}
