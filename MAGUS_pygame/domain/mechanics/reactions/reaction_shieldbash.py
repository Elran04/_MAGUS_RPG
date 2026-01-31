"""
Reaction Shield Bash

Triggered after a successful block with a shield.
This is a free reaction attack using the shield as a weapon.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from domain.entities.weapon import Weapon
from domain.mechanics.actions.special.usability_special_attacks import can_use_reaction_bash
from domain.mechanics.attack_resolution import AttackOutcome
from domain.mechanics.attack_resolution import AttackResult as CoreAttackResult
from domain.mechanics.attack_resolution import resolve_attack
from domain.mechanics.reach import compute_reach_hexes

from .base import Reaction, ReactionCategory, ReactionResult

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
class ReactionShieldBash(Reaction):
	"""Reaction shield bash after a successful block."""

	name: str = "reaction_shieldbash"
	ap_cost: int = 0
	stamina_cost: int = 0

	@property
	def category(self) -> ReactionCategory:
		return ReactionCategory.COUNTER

	def should_trigger(
		self,
		*,
		attacker: Unit,
		defender: Unit,
		last_attack_result: CoreAttackResult | None,
		reactions_used: int = 0,
		**_: object,
	) -> tuple[bool, str]:
		if attacker is None or defender is None:
			return (False, "Attacker and defender are required")
		if last_attack_result is None:
			return (False, "Missing last attack result")
		if last_attack_result.outcome != AttackOutcome.BLOCKED:
			return (False, "Last attack was not blocked")

		if not can_use_reaction_bash(defender, reactions_used):
			return (False, "Reaction shield bash not available")

		# Must be within defender's zone of control (adjacent for shield bash)
		attacker_pos = getattr(attacker, "position", None)
		if attacker_pos is None:
			return (False, "Attacker position missing")

		defender_zone = compute_reach_hexes(defender, defender.weapon)
		if attacker_pos not in defender_zone:
			return (False, "Attacker not in defender's zone of control")

		return (True, "Reaction shield bash available")

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
	) -> ReactionResult:
		# Defender is the reactor; they perform the bash on the original attacker
		reactor = defender
		target = attacker

		bash_weapon = _build_shield_bash_weapon()
		shield_skill_level = 0
		if getattr(reactor, "skills", None):
			shield_skill_level = reactor.skills.get_rank("shieldskill", 0)

		if attack_roll is None:
			attack_roll = random.randint(1, 100)
		if base_damage_roll is None:
			base_damage_roll = random.randint(
				SHIELD_BASH_DAMAGE_MIN, SHIELD_BASH_DAMAGE_MAX
			)

		core_result: CoreAttackResult = resolve_attack(
			attacker=reactor,
			defender=target,
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

		outcome_str = core_result.outcome.value.replace("_", " ").title()
		msg = (
			f"Reaction Bash!: TÉ {core_result.all_te} ({core_result.attack_roll}) "
			f"vs VÉ {core_result.all_ve} | {outcome_str}"
		)

		data = {
			"attack_result": core_result,
			"special_attack": "reaction_shieldbash",
		}

		return ReactionResult(
			success=True,
			message=msg,
			ap_spent=self.ap_cost,
			stamina_spent=0,
			data=data,
			triggered_by=self.name,
		)
