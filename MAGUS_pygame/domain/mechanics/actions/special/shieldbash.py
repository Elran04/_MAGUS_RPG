"""
Shield bash special action.

Unlocked at shieldskill level 3+.
This is a melee attack using a shield as the striking tool.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from domain.entities.weapon import Weapon
from domain.mechanics.actions.base import Action, ActionCategory, ActionCost, ActionResult
from domain.mechanics.attack_resolution import AttackResult as CoreAttackResult
from domain.mechanics.attack_resolution import resolve_attack
from domain.mechanics.skills import can_use_shield_bash

if TYPE_CHECKING:
	from domain.entities import Unit


SHIELD_BASH_DAMAGE_MIN = 1
SHIELD_BASH_DAMAGE_MAX = 3
SHIELD_BASH_AP_COST = 5


def _build_shield_bash_weapon() -> Weapon:
	"""Create a lightweight weapon definition for shield bash."""
	return Weapon(
		id="shield_bash",
		name="Shield Bash",
		ke_modifier=0,
		te_modifier=0,
		ve_modifier=0,
		damage_dice="1d3",
		damage_min=SHIELD_BASH_DAMAGE_MIN,
		damage_max=SHIELD_BASH_DAMAGE_MAX,
		attack_time=SHIELD_BASH_AP_COST,
		size_category=1,
		wield_mode="one_handed",
		skill_id="shieldskill",
	)


@dataclass
class ShieldBashAction(Action):
	"""Execute shield bash special action."""

	ap_cost: int = SHIELD_BASH_AP_COST

	@property
	def category(self) -> ActionCategory:
		return ActionCategory.SPECIAL_ATTACK

	@property
	def cost(self) -> ActionCost:
		return ActionCost(ap=self.ap_cost)

	def can_execute(
		self,
		*,
		attacker: Unit,
		defender: Unit,
		**_: object,
	) -> tuple[bool, str]:
		if attacker is None or defender is None:
			return (False, "Attacker and defender are required")
		if attacker.position.distance_to(defender.position) != 1:
			return (False, "Shield bash requires adjacent target")
		if not can_use_shield_bash(attacker):
			return (False, "Shield bash not available")
		return (True, "")

	def execute(
		self,
		*,
		attacker: Unit,
		defender: Unit,
		attack_roll: int | None = None,
		base_damage_roll: int | None = None,
		shield_ve: int = 0,
		dodge_modifier: int = 0,
		attacker_conditions: int = 0,
		defender_conditions: int = 0,
		overpower_threshold: int = 50,
		stamina_block: dict | None = None,
		stamina_parry: dict | None = None,
		stamina_dodge: dict | None = None,
	) -> ActionResult:
		if not can_use_shield_bash(attacker):
			return ActionResult(success=False, message="Shield bash not available")

		bash_weapon = _build_shield_bash_weapon()
		shield_skill_level = 0
		if getattr(attacker, "skills", None):
			shield_skill_level = attacker.skills.get_rank("shieldskill", 0)

		if attack_roll is None:
			attack_roll = random.randint(1, 100)
		if base_damage_roll is None:
			base_damage_roll = random.randint(
				SHIELD_BASH_DAMAGE_MIN, SHIELD_BASH_DAMAGE_MAX
			)

		core_result: CoreAttackResult = resolve_attack(
			attacker=attacker,
			defender=defender,
			attack_roll=attack_roll,
			base_damage_roll=base_damage_roll,
			weapon=bash_weapon,
			weapon_skill_level=shield_skill_level,
			shield_ve=shield_ve,
			dodge_modifier=dodge_modifier,
			attacker_conditions=attacker_conditions,
			defender_conditions=defender_conditions,
			overpower_threshold=overpower_threshold,
			stamina_block=stamina_block,
			stamina_parry=stamina_parry,
			stamina_dodge=stamina_dodge,
		)

		return ActionResult(
			success=True,
			message="",
			ap_spent=self.ap_cost,
			stamina_spent=0,
			data={"attack_result": core_result, "special_attack": "shield_bash"},
		)
