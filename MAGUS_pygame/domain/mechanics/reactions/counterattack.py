"""
Counterattack Reaction

Triggered when an attack misses or is parried against a unit wielding
longswords with skill level 3+.

This reaction performs a free attack similar to an opportunity attack,
but the trigger event is the failed/parried attack.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from domain.mechanics.attack_resolution import AttackOutcome
from domain.mechanics.attack_resolution import AttackResult as CoreAttackResult
from domain.mechanics.attack_resolution import resolve_attack
from domain.mechanics.lucky_unlucky_roll import (
    LuckyRollType,
    resolve_lucky_roll,
    should_use_lucky_roll,
)
from domain.mechanics.reach import compute_reach_hexes
from domain.mechanics.skills import get_weaponskill_modifiers

from .base import Reaction, ReactionCategory, ReactionResult

if TYPE_CHECKING:
	from domain.entities import Unit, Weapon


@dataclass
class CounterattackReaction(Reaction):
	"""Counterattack on miss/parry against skilled longsword user."""

	name: str = "counterattack"
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
		counterattacks_used: int = 0,
		**_: object,
	) -> tuple[bool, str]:
		if attacker is None or defender is None:
			return (False, "Attacker and defender are required")
		if last_attack_result is None:
			return (False, "Missing last attack result")

		if last_attack_result.outcome not in (AttackOutcome.MISS, AttackOutcome.PARRIED):
			return (False, "Attack was not missed or parried")

		weapon = getattr(defender, "weapon", None)
		if weapon is None:
			return (False, "Defender has no weapon")

		skill_id = getattr(weapon, "skill_id", "") or ""
		if skill_id != "weaponskill_longswords":
			return (False, "Defender is not wielding longswords")

		if not getattr(defender, "skills", None):
			return (False, "Defender has no skill data")

		weapon_skill_level = defender.skills.get_rank(skill_id, 0)
		if weapon_skill_level < 3:
			return (False, "Longsword skill level too low")

		mods = get_weaponskill_modifiers(weapon_skill_level, skill_id)
		if not mods.counterattack:
			return (False, "No counterattack effect at this skill level")

		if mods.opportunity_attacks_per_turn > 0 and counterattacks_used >= mods.opportunity_attacks_per_turn:
			return (False, "No counterattacks remaining this turn")

		# Attacker must be in defender's zone of control
		attacker_pos = getattr(attacker, "position", None)
		if attacker_pos is None:
			return (False, "Attacker position missing")

		defender_zone = compute_reach_hexes(defender, weapon)
		if attacker_pos not in defender_zone:
			return (False, "Attacker not in defender's zone of control")

		return (True, "Counterattack available")

	def execute(
		self,
		*,
		attacker: Unit,
		defender: Unit,
		attack_roll: int | None = None,
		base_damage_roll: int | None = None,
		weapon: Weapon | None = None,
		weapon_skill_level: int = 0,
		shield_ve: int = 0,
		dodge_modifier: int = 0,
		attacker_conditions: int = 0,
		defender_conditions: int = 0,
		overpower_threshold: int = 50,
		stamina_block: dict | None = None,
		stamina_parry: dict | None = None,
		stamina_dodge: dict | None = None,
	) -> ReactionResult:
		# Defender is the reactor; they perform the counterattack on the original attacker
		reactor = defender
		target = attacker

		wpn = weapon or reactor.weapon

		if attack_roll is None:
			if should_use_lucky_roll(reactor, LuckyRollType.ATTACK_ROLL, wpn, weapon_skill_level):
				roll_1 = random.randint(1, 100)
				roll_2 = random.randint(1, 100)
				attack_roll, _ = resolve_lucky_roll(roll_1, roll_2)
			else:
				attack_roll = random.randint(1, 100)

		if base_damage_roll is None:
			if wpn is not None:
				if should_use_lucky_roll(reactor, LuckyRollType.DAMAGE_ROLL, wpn, weapon_skill_level):
					roll_1 = random.randint(wpn.damage_min, wpn.damage_max)
					roll_2 = random.randint(wpn.damage_min, wpn.damage_max)
					base_damage_roll, _ = resolve_lucky_roll(roll_1, roll_2)
				else:
					base_damage_roll = random.randint(wpn.damage_min, wpn.damage_max)
			else:
				base_damage_roll = 1

		core_result: CoreAttackResult = resolve_attack(
			attacker=reactor,
			defender=target,
			attack_roll=attack_roll,
			base_damage_roll=base_damage_roll,
			weapon=wpn,
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

		outcome_str = core_result.outcome.value.replace("_", " ").title()
		msg = (
			f"Counterattack!: TÉ {core_result.all_te} ({core_result.attack_roll}) "
			f"vs VÉ {core_result.all_ve} | {outcome_str}"
		)

		data = {
			"attack_result": core_result,
			"special_attack": "counterattack",
		}

		return ReactionResult(
			success=True,
			message=msg,
			ap_spent=self.ap_cost,
			stamina_spent=0,
			data=data,
			triggered_by=self.name,
		)
