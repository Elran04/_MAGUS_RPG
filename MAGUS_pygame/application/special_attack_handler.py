"""
Special attack handling for BattleService.

Keeps special attack logic isolated from the core battle service.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.entities import Unit
from domain.mechanics.actions.special.attack_combination import get_attack_combination_config
from domain.mechanics.actions.special.charge_action import ChargeAction
from domain.mechanics.attack_resolution import apply_attack_result
from domain.mechanics.skills import can_use_shield_bash
from domain.value_objects import Position


@dataclass
class SpecialAttackHandler:
    """Handles special attacks for a battle service instance."""

    battle: "BattleService"

    def validate_attack_combination_target(self, unit: Unit, target_pos: Position) -> tuple[bool, str]:
        if not unit or not unit.weapon:
            return False, "No weapon equipped"

        if getattr(unit.weapon, "skill_id", "") != "weaponskill_daggers":
            return False, "Attack combination requires a dagger"

        weapon_skill_level = 0
        if getattr(unit, "skills", None):
            weapon_skill_level = unit.skills.get_rank("weaponskill_daggers", 0)

        config = get_attack_combination_config(weapon_skill_level)
        if not config:
            return False, "Attack combination requires dagger skill level 3+"

        if self.battle.remaining_ap(unit) < config.ap_cost:
            return False, f"Insufficient AP for attack combination (need {config.ap_cost})"

        target = self.battle.get_unit_at_position(target_pos)
        if not target:
            return False, "No target at selected hex"
        if not target.is_alive():
            return False, "Target is already defeated"

        if unit.position.distance_to(target_pos) != 1:
            return False, "Attack combination requires adjacent target"

        return True, ""

    def validate_charge_target(self, unit: Unit, target_pos: Position) -> tuple[bool, str]:
        """Check if target hex is valid for a charge special attack."""
        if not unit or not unit.weapon:
            return False, "No weapon equipped"

        # Need enough AP for charge (10 AP)
        if self.battle.remaining_ap(unit) < ChargeAction().cost.ap:
            return False, "Insufficient AP to charge"

        target = self.battle.get_unit_at_position(target_pos)
        if not target:
            return False, "No target at selected hex"
        if not target.is_alive():
            return False, "Target is already defeated"

        blocked = {(u.position.q, u.position.r) for u in self.battle.units if u.id != unit.id}
        if self.battle.blocked_hexes:
            blocked |= set(self.battle.blocked_hexes)

        ok, msg = ChargeAction().can_execute(
            attacker=unit,
            target=target,
            ap_available=self.battle.remaining_ap(unit),
            blocked=blocked,
            weapon=unit.weapon,
        )
        return ok, msg

    def validate_shield_bash_target(self, unit: Unit, target_pos: Position) -> tuple[bool, str]:
        """Check if target hex is valid for shield bash."""
        if not unit:
            return False, "No active unit"
        if not can_use_shield_bash(unit):
            return False, "Shield bash not available"

        target = self.battle.get_unit_at_position(target_pos)
        if not target:
            return False, "No target at selected hex"
        if not target.is_alive():
            return False, "Target is already defeated"

        if unit.position.distance_to(target_pos) != 1:
            return False, "Shield bash requires adjacent target"

        return True, ""

    def attack_combination_current_unit(self, defender: Unit, **kwargs: object) -> dict[str, object]:
        unit = self.battle.current_unit

        if not unit or not unit.weapon:
            return {"error": "No weapon equipped"}

        if getattr(unit.weapon, "skill_id", "") != "weaponskill_daggers":
            return {"error": "Attack combination requires a dagger"}

        # Extract defender's shield VE bonus
        shield_ve = self.battle._extract_shield_ve(defender)

        # Determine dagger skill level
        weapon_skill_level = 0
        if getattr(unit, "skills", None):
            try:
                weapon_skill_level = unit.skills.get_rank("weaponskill_daggers", 0)
            except Exception:
                weapon_skill_level = 0

        if "shield_ve" not in kwargs:
            kwargs["shield_ve"] = shield_ve

        result = self.battle.action_handler.attack_combination(
            attacker=unit,
            defender=defender,
            weapon_skill_level=weapon_skill_level,
            **kwargs,
        )

        if not getattr(result, "success", False):
            return {"action_result": result}

        ap_spent = self.battle._extract_ap_cost(getattr(result, "ap_spent", 0))
        if not self.battle.spend_ap(unit, ap_spent):
            return {"error": "Insufficient AP after attack", "action_result": result}

        # Apply effects after AP spending
        attack_results = None
        if hasattr(result, "data") and result.data:
            attack_results = result.data.get("attack_results")

        if attack_results:
            applied_results = []
            for combo_result in attack_results:
                apply_attack_result(combo_result, defender)
                applied_results.append(combo_result)

                if hasattr(unit, "stamina") and unit.stamina:
                    if getattr(combo_result, "stamina_spent_attacker", 0) > 0:
                        unit.stamina.spend_action_points(combo_result.stamina_spent_attacker)

                if hasattr(defender, "stamina") and defender.stamina:
                    if getattr(combo_result, "stamina_spent_defender", 0) > 0:
                        defender.stamina.spend_action_points(combo_result.stamina_spent_defender)

                if not defender.is_alive():
                    if result.data is not None:
                        result.data["attack_results"] = applied_results
                        result.data["combo_stopped_early"] = True
                        result.data["combo_stop_reason"] = "defender_defeated"
                    break

        return {"action_result": result}

    def charge_current_unit(
        self, defender: Unit, potential_reactors: list[Unit] | None = None, **kwargs: object
    ) -> dict[str, object]:
        """Execute charge special attack with the current unit."""
        unit = self.battle.current_unit

        if not unit or not unit.weapon:
            return {"error": "No weapon equipped"}

        # Prepare blocked hexes: other units + scenario obstacles
        blocked = {(u.position.q, u.position.r) for u in self.battle.units if u.id != unit.id}
        if self.battle.blocked_hexes:
            blocked |= set(self.battle.blocked_hexes)

        # Enemy zones for optional reaction handling
        enemy_zones = self.battle.compute_enemy_zones(unit)

        # Extract shield VE bonuses for both defender and attacker (mover)
        shield_ve = self.battle._extract_shield_ve(defender)
        mover_shield_ve = self.battle._extract_shield_ve(unit)

        summary = self.battle.action_handler.charge_attack(
            attacker=unit,
            defender=defender,
            ap_available=self.battle.remaining_ap(unit),
            blocked=blocked,
            enemy_zones=enemy_zones,
            potential_reactors=potential_reactors,
            shield_ve=shield_ve,
            mover_shield_ve=mover_shield_ve,
            **kwargs,
        )

        if "error" in summary:
            return summary

        action_result = summary.get("action_result")
        ap_spent = self.battle._extract_ap_cost(getattr(action_result, "ap_spent", 0))
        if action_result and action_result.success:
            if not self.battle.spend_ap(unit, ap_spent):
                return {"error": "Insufficient AP after charge", "action_result": action_result}
        return summary

    def shield_bash_current_unit(self, defender: Unit, **_: object) -> dict[str, object]:
        """Execute shield bash special attack with the current unit."""
        unit = self.battle.current_unit

        if not unit:
            return {"error": "No active unit"}
        if not can_use_shield_bash(unit):
            return {"error": "Shield bash not available"}

        target = defender
        if not target or not target.is_alive():
            return {"error": "Target is already defeated"}

        shield_ve = self.battle._extract_shield_ve(defender)

        result = self.battle.action_handler.shield_bash(
            attacker=unit,
            defender=defender,
            shield_ve=shield_ve,
        )

        if not getattr(result, "success", False):
            return {"action_result": result}

        ap_spent = self.battle._extract_ap_cost(getattr(result, "ap_spent", 0))
        if not self.battle.spend_ap(unit, ap_spent):
            return {"error": "Insufficient AP after shield bash", "action_result": result}

        attack_result = None
        if hasattr(result, "data") and result.data:
            attack_result = result.data.get("attack_result")

        if attack_result is not None:
            apply_attack_result(attack_result, defender)

            if hasattr(unit, "stamina") and unit.stamina:
                if getattr(attack_result, "stamina_spent_attacker", 0) > 0:
                    unit.stamina.spend_action_points(attack_result.stamina_spent_attacker)

            if hasattr(defender, "stamina") and defender.stamina:
                if getattr(attack_result, "stamina_spent_defender", 0) > 0:
                    defender.stamina.spend_action_points(attack_result.stamina_spent_defender)

        return {"action_result": result}


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from application.battle_service import BattleService
