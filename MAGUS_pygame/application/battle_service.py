"""

BattleService - orchestrates turn order, action points, and victory checks.

AP model:
- Base AP per unit per turn = 10
- For each point of effective Gyorsaság (Attributes.speed - equipment MGT) above 15, gain +1 AP.
- Equipment MGT (armor, shields) reduces speed; certain skills (heavy armor level 4+, shieldskill level 4+) negate this.

This AP computation is domain logic, but lightweight enough to live here; if it
expands (skills, conditions), extract to domain.mechanics.ap or similar.
"""

from __future__ import annotations

import random
from collections import deque
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field

from config import AP_COST_MOVEMENT
from domain.entities import Unit
from domain.mechanics.actions.movement_action import NEIGHBORS
from domain.mechanics.attack_resolution import apply_attack_result
from domain.mechanics.equipment import get_effective_speed
from domain.mechanics.initiation import (
    InitiativeOrder,
    calculate_initiative,
    initiative_sort_key_factory,
)
from domain.mechanics.reach import can_attack_target, compute_reach_hexes
from domain.value_objects import Facing, Position
from logger.logger import get_logger

from .action_handler import ActionHandler
from .special_attack_handler import SpecialAttackHandler


def compute_unit_ap(unit: Unit) -> int:
    base = 10
    effective_speed = get_effective_speed(unit)
    bonus = max(0, effective_speed - 15)
    return base + bonus


@dataclass
class BattleService:
    units: list[Unit]
    action_handler: ActionHandler = field(default_factory=ActionHandler)
    special_attack_handler: SpecialAttackHandler = field(init=False)
    initiative_sort: Callable[[Unit], int] | None = None
    initiative_order: InitiativeOrder | None = None
    _rng_seed: int | None = None  # For deterministic testing if provided
    _rng: object | None = None  # random.Random when initiative enabled
    equipment_repo: object | None = None  # EquipmentRepository for shield extraction
    blocked_hexes: frozenset[tuple[int, int]] | None = (
        None  # Scenario obstacles that restrict movement
    )

    turn_index: int = 0
    round: int = 1
    ap_pool: dict[str, int] = field(default_factory=dict)

    # Victory tracking (simple placeholder: teams distinguished externally)
    team_a_ids: list[str] = field(default_factory=list)
    team_b_ids: list[str] = field(default_factory=list)

    battle_active: bool = True

    def __post_init__(self) -> None:
        self.special_attack_handler = SpecialAttackHandler(self)

    def start_battle(self) -> None:
        """Initialize battle: perform initiative (if enabled), sort units, compute AP, reset reactions."""
        if self.initiative_order is not None and self.initiative_sort is None:
            # Initiative was computed but key not yet set (edge case)
            self.initiative_sort = initiative_sort_key_factory(self.initiative_order)
        self._sort_units()
        self._init_ap()
        self.action_handler.start_turn(self.units)

    # ------------------------------------------------------------------
    # Initiative Integration
    # ------------------------------------------------------------------
    def enable_initiative(self, *, seed: int | None = None) -> None:
        """Activate initiative system before calling start_battle.

        Args:
            seed: Optional RNG seed for deterministic rolls (tests).
        """

        self._rng_seed = seed
        self._rng = random.Random(seed) if seed is not None else random.Random()
        self.initiative_order = calculate_initiative(self.units, rng=self._rng)
        self.initiative_sort = initiative_sort_key_factory(self.initiative_order)
        # Sort immediately so presentation can inspect order prior to start_battle if needed
        self._sort_units()

        # Log initiative table
        logger = get_logger(__name__)
        table = self.get_initiative_table()
        logger.info("Initiative order (unit_id, total, base_ke, roll): %s", table)

    def refresh_initiative_for_new_round(self) -> None:
        """Re-roll initiative at the start of a new round unless persistent order is set."""
        if not self.initiative_order:
            return
        # Only re-roll if not persistent
        re_roll = not getattr(self.initiative_order, "persistent", False)
        self.initiative_order.refresh_for_new_round(self.units, re_roll=re_roll, rng=self._rng)
        self.initiative_sort = initiative_sort_key_factory(self.initiative_order)
        self._sort_units()
        # Log initiative table
        logger = get_logger(__name__)
        table = self.get_initiative_table()
        logger.info("Initiative order (unit_id, total, base_ke, roll): %s", table)

    def _sort_units(self) -> None:
        if self.initiative_sort:
            # Sort descending by provided key (higher initiative first)
            self.units.sort(key=self.initiative_sort, reverse=True)
        else:
            # Default: use KE (initiative modifier) descending
            self.units.sort(key=lambda u: u.combat_stats.KE, reverse=True)

    def _init_ap(self) -> None:
        self.ap_pool = {u.id: compute_unit_ap(u) for u in self.units if u.is_alive()}

    @property
    def current_unit(self) -> Unit:
        return self.units[self.turn_index]

    def remaining_ap(self, unit: Unit) -> int:
        return self.ap_pool.get(unit.id, 0)

    def spend_ap(self, unit: Unit, amount: int) -> bool:
        if self.remaining_ap(unit) < amount:
            return False
        self.ap_pool[unit.id] -= amount
        return True

    def _extract_ap_cost(self, ap_obj: object) -> int:
        """Convert AP cost from various types to int.

        Args:
            ap_obj: AP cost (int, str, float, or other)

        Returns:
            AP cost as int, or 0 if unable to parse
        """
        if isinstance(ap_obj, (int, float)):
            return int(ap_obj)
        elif isinstance(ap_obj, str):
            try:
                return int(ap_obj)
            except ValueError:
                return 0
        return 0

    def end_turn(self) -> None:
        """Advance to next alive and conscious unit; on wrap, start new round and refresh AP + reactions.

        Skips dead and unconscious units. If all units are dead or unconscious, ends the battle.
        """
        num_units = len(self.units)
        for _ in range(num_units):
            self.turn_index += 1
            if self.turn_index >= num_units:
                self.turn_index = 0
                self.round += 1
                # Refresh initiative ordering first (if enabled) then AP and reactions
                self.refresh_initiative_for_new_round()
                self._init_ap()
                self.action_handler.start_turn(self.units)
            # Skip dead or unconscious units
            u = self.units[self.turn_index]
            if not u.is_alive():
                # Dead unit - skip to next
                continue
            if hasattr(u, "stamina") and u.stamina and u.stamina.is_unconscious():
                # Unconscious unit - skip to next
                continue
            # Found an alive and conscious unit
            break
        else:
            # All units are dead or unconscious
            self.battle_active = False
        self._cleanup_dead_units()
        self._check_victory()

    # ------------------------------------------------------------------
    # Initiative inspection helpers
    # ------------------------------------------------------------------
    def get_initiative_table(self) -> list[tuple[str, int, int, int]]:
        """Return debug table of current initiative entries.

        Returns rows: (unit_id, total, base_ke, roll)
        """
        if not self.initiative_order:
            return []
        table = self.initiative_order.to_debug_table()
        return list(table)

    def _cleanup_dead_units(self) -> None:
        # Remove units that are dead from AP pool (keep in list for history; optional removal strategy)
        for u in self.units:
            if not u.is_alive() and u.id in self.ap_pool:
                del self.ap_pool[u.id]

    def _check_victory(self) -> None:
        if not self.team_a_ids or not self.team_b_ids:
            return  # Teams not set yet
        alive_a = any(u.is_alive() for u in self.units if u.id in self.team_a_ids)
        alive_b = any(u.is_alive() for u in self.units if u.id in self.team_b_ids)
        if not alive_a or not alive_b:
            self.battle_active = False

    def is_victory(self) -> bool:
        return not self.battle_active

    # --- Action wrappers integrating AP economy ---
    def move_current_unit(
        self,
        dest: Position,
        enemy: Unit | None = None,
        blocked: Iterable[tuple[int, int]] | None = None,
        potential_reactors: Iterable[Unit] | None = None,
    ) -> dict[str, object]:
        unit = self.current_unit
        # Prevent actions for unconscious units
        if hasattr(unit, "stamina") and unit.stamina and unit.stamina.is_unconscious():
            return {"error": "Unit is unconscious and cannot act"}

        # Extract mover's shield VÉ for opportunity attack defense
        mover_shield_ve = self._extract_shield_ve(unit)

        summary = self.action_handler.move_unit(
            unit=unit,
            dest=dest,
            enemy=enemy,
            ap_available=self.remaining_ap(unit),
            blocked=blocked,
            potential_reactors=potential_reactors,
            mover_shield_ve=mover_shield_ve,
        )
        if "error" in summary:
            return summary
        ap_spent = self._extract_ap_cost(summary.get("ap_spent", 0))
        if not self.spend_ap(unit, ap_spent):
            summary["error"] = "Insufficient AP after movement"
        return summary

    def _extract_shield_ve(self, unit: Unit) -> int:
        """Extract shield VE bonus from unit's off-hand equipment.

        Args:
            unit: Unit to extract shield VE from

        Returns:
            Shield VE value (0 if no shield equipped)
        """
        if not self.equipment_repo or not unit.character_data:
            return 0

        equipment = unit.character_data.get("equipment", {})
        off_hand_id = equipment.get("off_hand", "")
        if not off_hand_id:
            return 0

        shield_data = self.equipment_repo.find_weapon_by_id(off_hand_id)
        if not shield_data:
            return 0

        return shield_data.get("VE", 0)

    def attack_current_unit(self, defender: Unit, **kwargs: object) -> dict[str, object]:
        unit = self.current_unit

        # Validate target is in attack range

        if not can_attack_target(unit, defender.position, unit.weapon):
            return {"error": f"{defender.name} is not in attack range"}

        # Prevent actions for unconscious units
        if hasattr(unit, "stamina") and unit.stamina and unit.stamina.is_unconscious():
            return {"error": "Unit is unconscious and cannot act"}

        # Extract defender's shield VE bonus from equipment
        shield_ve = self._extract_shield_ve(defender)

        # AttackAction has fixed AP cost inside result.ap_spent
        # Separate rng_overrides if present in kwargs
        rng_overrides = None
        if isinstance(kwargs, dict) and "rng_overrides" in kwargs:
            candidate = kwargs.pop("rng_overrides")
            if isinstance(candidate, dict):
                rng_overrides = candidate
            else:
                rng_overrides = None

        # Add shield_ve to kwargs if not already present
        if "shield_ve" not in kwargs:
            kwargs["shield_ve"] = shield_ve

        # Determine correct weapon skill level for AP cost and other effects
        weapon_skill_level = 0
        if getattr(unit, "weapon", None) is not None:
            skill_id = getattr(unit.weapon, "skill_id", "") or ""
            if skill_id and getattr(unit, "skills", None):
                try:
                    weapon_skill_level = unit.skills.get_rank(skill_id, 0)
                except Exception:
                    weapon_skill_level = 0

        result = self.action_handler.attack(
            attacker=unit,
            defender=defender,
            rng_overrides=rng_overrides,
            weapon_skill_level=weapon_skill_level,
            **kwargs,
        )

        # If action failed, bubble up without applying effects
        if not getattr(result, "success", False):
            return {"action_result": result}

        # Extract AP cost and ensure we can spend before applying any effects
        ap_spent = self._extract_ap_cost(getattr(result, "ap_spent", 0))
        if not self.spend_ap(unit, ap_spent):
            return {"error": "Insufficient AP after attack", "action_result": result}

        # Apply effects only after AP was successfully spent (atomic behavior)
        attack_result = None
        attack_results = None
        if hasattr(result, "data") and result.data:
            attack_result = result.data.get("attack_result")
            attack_results = result.data.get("attack_results")

        reaction_results = []

        if attack_results:
            applied_results = []
            for combo_result in attack_results:
                apply_attack_result(combo_result, defender)
                applied_results.append(combo_result)

                # Spend attacker stamina per attack
                if hasattr(unit, "stamina") and unit.stamina:
                    if getattr(combo_result, "stamina_spent_attacker", 0) > 0:
                        unit.stamina.spend_action_points(combo_result.stamina_spent_attacker)

                # Spend defender stamina (block/parry/dodge) per attack
                if hasattr(defender, "stamina") and defender.stamina:
                    if getattr(combo_result, "stamina_spent_defender", 0) > 0:
                        defender.stamina.spend_action_points(combo_result.stamina_spent_defender)

                if not defender.is_alive():
                    if result.data is not None:
                        result.data["attack_results"] = applied_results
                        result.data["combo_stopped_early"] = True
                        result.data["combo_stop_reason"] = "defender_defeated"
                    break

                # After each attack in combo, trigger post-attack reactions
                if combo_result is not None:
                    ca_results = self.action_handler.reaction_handler.handle_counterattacks(
                        attacker=unit,
                        defender=defender,
                        last_attack_result=combo_result,
                    )
                    reaction_results.extend(ca_results)

                    sb_results = self.action_handler.reaction_handler.handle_reaction_shieldbash(
                        attacker=unit,
                        defender=defender,
                        last_attack_result=combo_result,
                    )
                    reaction_results.extend(sb_results)

        elif attack_result is not None:
            # Apply FP/EP damage to defender
            apply_attack_result(attack_result, defender)

            # Spend attacker stamina
            if hasattr(unit, "stamina") and unit.stamina:
                if getattr(attack_result, "stamina_spent_attacker", 0) > 0:
                    unit.stamina.spend_action_points(attack_result.stamina_spent_attacker)

            # Spend defender stamina (block/parry/dodge)
            if hasattr(defender, "stamina") and defender.stamina:
                if getattr(attack_result, "stamina_spent_defender", 0) > 0:
                    defender.stamina.spend_action_points(attack_result.stamina_spent_defender)

            # After single attack, trigger post-attack reactions
            ca_results = self.action_handler.reaction_handler.handle_counterattacks(
                attacker=unit,
                defender=defender,
                last_attack_result=attack_result,
            )
            reaction_results.extend(ca_results)

            sb_results = self.action_handler.reaction_handler.handle_reaction_shieldbash(
                attacker=unit,
                defender=defender,
                last_attack_result=attack_result,
            )
            reaction_results.extend(sb_results)

        return_dict = {"action_result": result}
        if reaction_results:
            return_dict["reaction_results"] = reaction_results
        return return_dict

    def attack_combination_current_unit(self, defender: Unit, **kwargs: object) -> dict[str, object]:
        """Execute dagger attack combination with the current unit."""
        return self.special_attack_handler.attack_combination_current_unit(defender, **kwargs)

    def charge_current_unit(self, defender: Unit, potential_reactors: Iterable[Unit] | None = None, **kwargs: object) -> dict[str, object]:
        """Execute charge special attack with the current unit."""
        return self.special_attack_handler.charge_current_unit(defender, potential_reactors, **kwargs)

    def shield_bash_current_unit(self, defender: Unit, **kwargs: object) -> dict[str, object]:
        """Execute shield bash special attack with the current unit."""
        return self.special_attack_handler.shield_bash_current_unit(defender, **kwargs)

    def rotate_current_unit(self, new_facing: Facing) -> dict[str, object]:
        """Rotate current unit to face a new direction.

        Args:
            new_facing: Target facing direction (0-5)
        Returns:
            Dict with action_result and ap_spent, or error
        """
        unit = self.current_unit
        summary = self.action_handler.change_facing(
            unit=unit, new_facing=new_facing, ap_available=self.remaining_ap(unit)
        )
        ap_spent = self._extract_ap_cost(summary.get("ap_spent", 0))
        if "error" not in summary and not self.spend_ap(unit, ap_spent):
            summary["error"] = "Insufficient AP after rotation"
        return summary

    def switch_weapon(
        self, unit: Unit, new_main_hand: str | None, new_off_hand: str | None
    ) -> dict[str, object]:
        """Switch the active weapons for a unit.

        Weapon switching costs 5 AP. Swaps weapons between main_hand/off_hand
        and the quickslot weapons (weapon_quick_1, weapon_quick_2).

        Args:
            unit: Unit switching weapons
            new_main_hand: New main hand weapon ID (from equipment or quickslot)
            new_off_hand: New off hand weapon ID (from equipment or quickslot)

        Returns:
            Dict with success, message, ap_spent, or error
        """
        logger = get_logger(__name__)

        # Delegate to ActionHandler
        summary = self.action_handler.switch_weapon(
            unit=unit,
            new_main_hand=new_main_hand,
            new_off_hand=new_off_hand,
            ap_available=self.remaining_ap(unit),
            apply_switch=True,
        )

        # Handle AP spending
        if "error" not in summary:
            ap_spent = summary.get("ap_spent", 5)
            if not self.spend_ap(unit, ap_spent):
                # Rollback on AP spend failure
                equipment = unit.character_data["equipment"]
                old_main = summary.get("action_result").data.get("old_main_hand", "")
                old_off = summary.get("action_result").data.get("old_off_hand", "")
                equipment["main_hand"] = old_main
                equipment["off_hand"] = old_off
                return {"error": f"Failed to spend {ap_spent} AP"}

            # Reload unit's weapon object from new main_hand equipment
            # This ensures reach, combat stats, and all weapon-dependent calculations use updated weapon
            if self.equipment_repo:
                equipment = unit.character_data["equipment"]
                new_main_id = equipment.get("main_hand", "")
                if new_main_id:
                    weapon_data = self.equipment_repo.find_weapon_by_id(new_main_id)
                    if weapon_data:
                        # Build weapon entity using UnitFactory's method for consistency
                        from domain.services import UnitFactory
                        factory = UnitFactory(None, self.equipment_repo)
                        unit.weapon = factory._build_weapon_entity(weapon_data)
                        logger.debug(f"{unit.name} equipped {new_main_id}")
                else:
                    unit.weapon = None
                    logger.debug(f"{unit.name} unequipped main hand weapon")

        return summary

    def set_teams(self, team_a: Iterable[Unit], team_b: Iterable[Unit]) -> None:
        self.team_a_ids = [u.id for u in team_a]
        self.team_b_ids = [u.id for u in team_b]
        self._check_victory()

    # --- Query methods for presentation layer ---
    def get_enemies(self, unit: Unit) -> list[Unit]:
        """Get all enemy units relative to the given unit.

        Args:
            unit: Unit to get enemies for

        Returns:
            List of enemy units
        """
        if unit.id in self.team_a_ids:
            return [u for u in self.units if u.id in self.team_b_ids]
        elif unit.id in self.team_b_ids:
            return [u for u in self.units if u.id in self.team_a_ids]
        return []

    def get_unit_at_position(self, pos: Position) -> Unit | None:
        """Find unit at given hex position.

        Args:
            pos: Position object to check

        Returns:
            Unit at position, or None
        """
        for unit in self.units:
            if unit.position.q == pos.q and unit.position.r == pos.r:
                return unit
        return None

    def get_unit_at_hex(self, q: int, r: int) -> Unit | None:
        """Find unit at given hex coordinates (convenience wrapper).

        Args:
            q, r: Hex coordinates

        Returns:
            Unit at position or None
        """
        return self.get_unit_at_position(Position(q, r))

    def is_enemy(self, unit_a: Unit, unit_b: Unit) -> bool:
        """Check if unit_b is an enemy of unit_a.

        Args:
            unit_a: First unit
            unit_b: Second unit

        Returns:
            True if units are on different teams
        """
        return (unit_a.id in self.team_a_ids) != (unit_b.id in self.team_a_ids)

    # --- Action execution (business logic) ---
    def can_move(self, unit: Unit) -> tuple[bool, str]:
        """Check if unit can perform movement action.

        Args:
            unit: Unit to check

        Returns:
            Tuple of (can_move, error_message)
        """
        if not unit.is_alive():
            return False, "Unit is not alive"
        if self.remaining_ap(unit) < 1:
            return False, "Insufficient AP to move"
        return True, ""

    def can_attack(self, unit: Unit) -> tuple[bool, str]:
        """Check if unit can perform attack action.

        Args:
            unit: Unit to check

        Returns:
            Tuple of (can_attack, error_message)
        """
        if not unit.is_alive():
            return False, "Unit is not alive"
        if not unit.weapon:
            return False, "No weapon equipped"

        attack_ap = unit.weapon.attack_time
        remaining_ap = self.remaining_ap(unit)
        if remaining_ap < attack_ap:
            return False, f"Insufficient AP to attack (need {attack_ap}, have {remaining_ap})"
        return True, ""

    def validate_move_target(self, unit: Unit, target_pos: Position) -> tuple[bool, str]:
        """Check if target hex is valid for movement.

        Args:
            unit: Unit to move
            target_pos: Target position

        Returns:
            Tuple of (is_valid, error_message)
        """
        reachable = self.compute_reachable_hexes(unit)
        if (target_pos.q, target_pos.r) not in reachable:
            return False, "Hex not in movement range"
        return True, ""

    def validate_attack_target(self, unit: Unit, target_pos: Position) -> tuple[bool, str]:
        """Check if target hex is valid for attack.

        Args:
            unit: Unit attacking
            target_pos: Target position

        Returns:
            Tuple of (is_valid, error_message)
        """
        # First check if unit has AP to attack
        if not unit.weapon:
            return False, "No weapon equipped"

        attack_ap = unit.weapon.attack_time
        remaining_ap = self.remaining_ap(unit)
        if remaining_ap < attack_ap:
            return False, f"Insufficient AP to attack (need {attack_ap}, have {remaining_ap})"

        # Then check if target is valid
        attackable = self.compute_attackable_hexes(unit)
        if (target_pos.q, target_pos.r) not in attackable:
            return False, "Hex not in attack range"

        target = self.get_unit_at_position(target_pos)
        if not target:
            return False, "No target at selected hex"
        if not target.is_alive():
            return False, "Target is already defeated"
        return True, ""

    def validate_charge_target(self, unit: Unit, target_pos: Position) -> tuple[bool, str]:
        """Check if target hex is valid for a charge special attack."""
        return self.special_attack_handler.validate_charge_target(unit, target_pos)

    def validate_attack_combination_target(self, unit: Unit, target_pos: Position) -> tuple[bool, str]:
        """Check if target hex is valid for dagger attack combination."""
        return self.special_attack_handler.validate_attack_combination_target(unit, target_pos)

    def validate_shield_bash_target(self, unit: Unit, target_pos: Position) -> tuple[bool, str]:
        """Check if target hex is valid for shield bash."""
        return self.special_attack_handler.validate_shield_bash_target(unit, target_pos)

    # --- Helper methods for UI highlighting ---
    def compute_reachable_hexes(self, unit: Unit) -> set[tuple[int, int]]:
        """Calculate hexes reachable by unit based on remaining AP.

        Uses BFS flood fill to find all hexes within movement range,
        accounting for AP cost per hex and blocked positions.

        Args:
            unit: Unit to calculate reachable hexes for

        Returns:
            Set of (q, r) hex coordinates the unit can reach
        """
        # Unconscious units cannot move
        if hasattr(unit, "stamina") and unit.stamina and unit.stamina.is_unconscious():
            return set()
        ap_available = self.remaining_ap(unit)
        max_distance = ap_available // AP_COST_MOVEMENT

        if max_distance <= 0:
            return set()

        start = (unit.position.q, unit.position.r)
        visited = {start}
        queue = deque([(start, 0)])
        reachable = set()

        # Get all occupied positions to block (can't move through other units)
        blocked = {(u.position.q, u.position.r) for u in self.units if u.id != unit.id}

        while queue:
            (q, r), dist = queue.popleft()

            # Add to reachable if beyond start position and within range
            if 0 < dist <= max_distance:
                reachable.add((q, r))

            # Continue exploring if not at max distance
            if dist < max_distance:
                for dq, dr in NEIGHBORS:
                    nxt = (q + dq, r + dr)
                    if nxt not in visited and nxt not in blocked:
                        visited.add(nxt)
                        queue.append((nxt, dist + 1))

        return reachable

    def compute_attackable_hexes(self, unit: Unit) -> set[tuple[int, int]]:
        """Calculate hexes attackable by unit based on weapon reach and facing.

        Uses the domain reach mechanics to determine which hexes are in
        the unit's attack range based on weapon size and facing direction.

        Args:
            unit: Unit to calculate attackable hexes for

        Returns:
            Set of (q, r) hex coordinates the unit can attack
        """
        # Unconscious units cannot attack
        if hasattr(unit, "stamina") and unit.stamina and unit.stamina.is_unconscious():
            return set()
        result = compute_reach_hexes(unit, unit.weapon)
        return set(result)

    def compute_enemy_zones(self, unit: Unit) -> set[tuple[int, int]]:
        """Calculate combined zone of control for all enemies of the given unit.

        Useful for visual warning when planning movement paths.

        Args:
            unit: Unit to calculate enemy zones for

        Returns:
            Set of (q, r) hex coordinates covered by enemy zones of control
        """
        enemies = self.get_enemies(unit)
        enemy_zones: set[tuple[int, int]] = set()
        for enemy in enemies:
            if enemy.is_alive():
                zone = compute_reach_hexes(enemy, enemy.weapon)
                enemy_zones.update(set(zone))
        return enemy_zones

    def get_winner(self) -> str | None:
        """Determine battle winner.

        Returns:
            "team_a" if Team A won
            "team_b" if Team B won
            "draw" if both teams eliminated
            None if battle still active
        """
        if self.battle_active:
            return None

        team_a_alive = any(u.is_alive() for u in self.units if u.id in self.team_a_ids)
        team_b_alive = any(u.is_alive() for u in self.units if u.id in self.team_b_ids)

        if team_a_alive and not team_b_alive:
            return "team_a"
        elif team_b_alive and not team_a_alive:
            return "team_b"
        else:
            return "draw"
