"""
Charge special attack: combines movement (up to 5 hexes) and a melee attack.

Rules implemented:
- Cost: 10 AP, 20 Stamina (fixed for now).
- Must target an enemy unit (cannot charge empty hex).
- Minimum starting distance to target: 5 hexes (cannot charge closer than that).
- Maximum effective range: up to 5 hexes of movement plus weapon reach (forward distance).
- Movement obeys blocking rules (cannot move through blocked hexes or the target hex).
- Landing hex must be within weapon reach of the target after moving.
- Facing auto-adjusts to look at the target from the landing hex.
- Attack uses standard resolve_attack; application layer applies movement/facing/attack results.

Combat Modifiers (charge-specific):
- Attacker TÉ: +20 (applies only to this attack, not subsequent reactions)
- Attacker VÉ: -25 (persists through the round)
- Damage from attacker: 2x multiplier
- Damage to attacker (from opportunity attacks during charge): 2x multiplier

Interruption Mechanic:
- If a successful opportunity attack (at least HIT) occurs during movement, the charge
  attack is cancelled and movement stops as if normal movement occurred.
- Application layer handles OA resolution and movement cancellation.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, replace
from typing import Iterable

from domain.entities import Unit, Weapon
from domain.mechanics.attack_resolution import AttackResult as CoreAttackResult
from domain.mechanics.attack_resolution import resolve_attack
from domain.mechanics.lucky_roll import LuckyRollType, resolve_lucky_roll, should_use_lucky_roll
from domain.mechanics.reach import HEX_DIRECTIONS, get_weapon_reach
from domain.value_objects import Facing, Position

from ..base import Action, ActionCategory, ActionCost, ActionResult
from ..movement_action import bfs_path, path_intersects_zone

# AP per hex is 2 (same as MovementAction); 10 AP -> 5 hexes of movement budget.
AP_COST = 10
STAMINA_COST = 20
AP_PER_HEX = 2
MAX_STEPS = AP_COST // AP_PER_HEX  # 5
MIN_START_DISTANCE = 5  # Cannot charge targets nearer than 5 hexes

# Charge combat modifiers
CHARGE_ATTACK_TE_BONUS = 20  # +20 TÉ for the charge attack
CHARGE_ATTACKER_VE_PENALTY = -25  # -25 VÉ (persists through round)
CHARGE_DAMAGE_MULTIPLIER = 2  # 2x damage dealt by attacker
CHARGE_DAMAGE_MULTIPLIER_TO_ATTACKER = 2  # 2x damage to attacker from opportunity attacks


def _hex_distance(a: tuple[int, int], b: tuple[int, int]) -> int:
    """Hex distance on axial coordinates."""
    aq, ar = a
    bq, br = b
    return (abs(aq - bq) + abs(ar - br) + abs((aq + ar) - (bq + br))) // 2


def _facing_towards(source: tuple[int, int], target: tuple[int, int]) -> Facing:
    """Compute facing that best looks from source to target on hex grid."""
    dq = target[0] - source[0]
    dr = target[1] - source[1]
    if dq == 0 and dr == 0:
        return Facing(0)

    # Exact axial alignment first
    if dq == 0:
        return Facing(2 if dr > 0 else 5)
    if dr == 0:
        return Facing(1 if dq > 0 else 4)
    if dq + dr == 0:
        return Facing(0 if dq > 0 else 3)

    # Otherwise pick direction with maximum dot product (closest bearing)
    best_dir = 0
    best_score = -math.inf
    for idx, (dir_q, dir_r) in enumerate(HEX_DIRECTIONS):
        score = dq * dir_q + dr * dir_r
        if score > best_score:
            best_score = score
            best_dir = idx
    return Facing(best_dir)


def _forward_reach_distance(weapon: Weapon | None) -> int:
    """Forward reach in hexes (matches compute_reach_hexes forward ray length)."""
    reach = get_weapon_reach(weapon)
    return max(1, (reach + 1) // 2)


@dataclass
class ChargeAction(Action):
    """Charge: move then attack with a single special action."""

    @property
    def category(self) -> ActionCategory:
        return ActionCategory.SPECIAL_ATTACK

    @property
    def cost(self) -> ActionCost:
        return ActionCost(ap=AP_COST, stamina=STAMINA_COST)

    def can_execute(
        self,
        *,
        attacker: Unit,
        target: Unit,
        ap_available: int,
        blocked: Iterable[tuple[int, int]] | None = None,
        weapon: Weapon | None = None,
        **_: object,
    ) -> tuple[bool, str]:
        if attacker is None or target is None:
            return (False, "Attacker and target are required")
        if not attacker.is_alive():
            return (False, "Attacker is not alive")
        if not target.is_alive():
            return (False, "Target is not alive")
        if ap_available < AP_COST:
            return (False, "Insufficient AP for charge")

        start = attacker.position
        tgt_pos = target.position
        distance = start.distance_to(tgt_pos)
        if distance < MIN_START_DISTANCE:
            return (False, "Target is too close for a charge")

        weapon_use = weapon or attacker.weapon
        forward_reach = _forward_reach_distance(weapon_use)
        max_range = MAX_STEPS + forward_reach
        if distance > max_range:
            return (False, "Target is out of charge range")

        # Quick path feasibility: ensure there exists some unblocked landing hex within reach
        blocked_set = set(blocked or [])
        blocked_set.add((tgt_pos.q, tgt_pos.r))
        start_xy = (start.q, start.r)

        # Candidate landing hexes are within forward reach of the target
        candidates: list[tuple[int, int]] = []
        for dq in range(-forward_reach, forward_reach + 1):
            for dr in range(-forward_reach, forward_reach + 1):
                cq, cr = tgt_pos.q + dq, tgt_pos.r + dr
                if _hex_distance((cq, cr), (tgt_pos.q, tgt_pos.r)) > forward_reach:
                    continue
                if (cq, cr) in blocked_set:
                    continue
                candidates.append((cq, cr))

        for cand in candidates:
            path = bfs_path(start_xy, cand, blocked_set)
            if path and (len(path) - 1) <= MAX_STEPS:
                return (True, "")

        return (False, "No viable path within charge range")

    def execute(
        self,
        *,
        attacker: Unit,
        target: Unit,
        ap_available: int,
        blocked: Iterable[tuple[int, int]] | None = None,
        enemy_zones: set[tuple[int, int]] | None = None,
        weapon: Weapon | None = None,
        weapon_skill_level: int = 0,
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
        ok, reason = self.can_execute(
            attacker=attacker,
            target=target,
            ap_available=ap_available,
            blocked=blocked,
            weapon=weapon,
        )
        if not ok:
            return ActionResult(success=False, message=reason, ap_spent=0)

        weapon_use = weapon or attacker.weapon
        forward_reach = _forward_reach_distance(weapon_use)

        blocked_set = set(blocked or [])
        # Target hex is blocked for movement (cannot end on target)
        blocked_set.add((target.position.q, target.position.r))

        start_xy = (attacker.position.q, attacker.position.r)
        tgt_xy = (target.position.q, target.position.r)

        # Build candidate landing hexes within forward reach of target
        candidates: list[tuple[int, int]] = []
        for dq in range(-forward_reach, forward_reach + 1):
            for dr in range(-forward_reach, forward_reach + 1):
                cq, cr = tgt_xy[0] + dq, tgt_xy[1] + dr
                if _hex_distance((cq, cr), tgt_xy) > forward_reach:
                    continue
                if (cq, cr) in blocked_set:
                    continue
                candidates.append((cq, cr))

        best_path: list[tuple[int, int]] | None = None
        for cand in candidates:
            path = bfs_path(start_xy, cand, blocked_set)
            if not path:
                continue
            steps = len(path) - 1
            if steps == 0:
                continue  # cannot charge without moving
            if steps > MAX_STEPS:
                continue
            if best_path is None or steps < (len(best_path) - 1):
                best_path = path

        if not best_path:
            return ActionResult(
                success=False, message="No viable path within charge range", ap_spent=0
            )

        landing = best_path[-1]
        new_facing = _facing_towards(landing, tgt_xy)

        # Optional ZoC info
        intersects_zoc, intersection_index = False, None
        if enemy_zones:
            intersects_zoc, intersection_index = path_intersects_zone(best_path, enemy_zones)

        # Prepare temporary attacker at landing with corrected facing
        temp_attacker = replace(
            attacker,
            position=Position(q=landing[0], r=landing[1]),
            facing=new_facing,
        )

        # Rolls
        lucky_attack_rolls = None
        lucky_damage_rolls = None
        if attack_roll is None:
            if should_use_lucky_roll(attacker, LuckyRollType.ATTACK_ROLL, weapon_use, weapon_skill_level):
                roll_1 = random.randint(1, 100)
                roll_2 = random.randint(1, 100)
                attack_roll, _ = resolve_lucky_roll(roll_1, roll_2)
                lucky_attack_rolls = (roll_1, roll_2, attack_roll)
            else:
                attack_roll = random.randint(1, 100)
        if base_damage_roll is None:
            if weapon_use is not None:
                if should_use_lucky_roll(attacker, LuckyRollType.DAMAGE_ROLL, weapon_use, weapon_skill_level):
                    roll_1 = random.randint(weapon_use.damage_min, weapon_use.damage_max)
                    roll_2 = random.randint(weapon_use.damage_min, weapon_use.damage_max)
                    base_damage_roll, _ = resolve_lucky_roll(roll_1, roll_2)
                    lucky_damage_rolls = (roll_1, roll_2, base_damage_roll)
                else:
                    base_damage_roll = random.randint(weapon_use.damage_min, weapon_use.damage_max)
            else:
                base_damage_roll = 1

        core_result: CoreAttackResult = resolve_attack(
            attacker=temp_attacker,
            defender=target,
            attack_roll=attack_roll,
            base_damage_roll=base_damage_roll,
            weapon=weapon_use,
            weapon_skill_level=weapon_skill_level,
            shield_ve=shield_ve,
            dodge_modifier=dodge_modifier,
            attacker_conditions=attacker_conditions + CHARGE_ATTACK_TE_BONUS,  # +20 TÉ for charge
            defender_conditions=defender_conditions,
            overpower_threshold=overpower_threshold,
            stamina_block=stamina_block,
            stamina_parry=stamina_parry,
            stamina_dodge=stamina_dodge,
        )

        msg = (
            f"Charge from {start_xy} to {landing} (cost {AP_COST} AP, {STAMINA_COST} STA) "
            f"and attack {target.name} (roll {attack_roll})"
        )

        data = {
            "path": best_path,
            "landing_hex": landing,
            "new_facing": new_facing.direction,
            "attack_result": core_result,
            "intersects_zoc": intersects_zoc,
            "intersection_index": intersection_index,
            "charge_te_bonus": CHARGE_ATTACK_TE_BONUS,
            "charge_ve_penalty": CHARGE_ATTACKER_VE_PENALTY,
            "charge_damage_multiplier": CHARGE_DAMAGE_MULTIPLIER,
            "charge_damage_multiplier_to_attacker": CHARGE_DAMAGE_MULTIPLIER_TO_ATTACKER,
        }

        if lucky_attack_rolls is not None:
            data["lucky_attack_rolls"] = lucky_attack_rolls
        if lucky_damage_rolls is not None:
            data["lucky_damage_rolls"] = lucky_damage_rolls

        return ActionResult(
            success=True,
            message=msg,
            ap_spent=AP_COST,
            stamina_spent=STAMINA_COST,
            data=data,
        )
