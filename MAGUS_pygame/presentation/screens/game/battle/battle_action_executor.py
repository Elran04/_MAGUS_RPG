"""
Action execution for battle screen.

Handles move, attack, rotation, and other combat actions.
"""

import time
from typing import Callable, Optional

from application.battle_service import BattleService
from application.detailed_battle_log import DetailedBattleLog
from domain.battle_log_entry import (
    BattleLogEntry,
    DetailedActionData,
    DetailedAttackData,
    DetailedMoveData,
)
from domain.entities import Unit
from domain.value_objects import Facing, Position
from infrastructure.rendering.hex_grid import calculate_facing_to_hex
from logger.logger import get_logger

logger = get_logger(__name__)


class BattleActionExecutor:
    """Executes battle actions like move, attack, rotate."""

    def __init__(self, battle_service: BattleService, detailed_log: Optional[DetailedBattleLog] = None):
        """Initialize action executor.

        Args:
            battle_service: Battle service managing combat state
            detailed_log: Optional detailed battle log for event tracking
        """
        self.battle = battle_service
        self.detailed_log = detailed_log
        self.combat_message: Optional[str] = None
        self.combat_message_timer = 0

    def execute_move(self, dest: Position, potential_reactors: list[Unit]) -> dict:
        """Execute movement to destination.

        Args:
            dest: Destination position
            potential_reactors: Enemy units that may react

        Returns:
            Summary dict with move results
        """
        current = self.battle.current_unit
        start_pos = current.position if current else None

        summary = self.battle.move_current_unit(
            dest=dest,
            potential_reactors=potential_reactors,
            blocked=self.battle.blocked_hexes,
        )

        if "error" in summary:
            self.show_message(f"Move failed: {summary['error']}")
        else:
            ap_spent = summary.get("ap_spent", 0)
            self.show_message(f"Moved (AP: -{ap_spent})")

            # Log detailed movement
            if self.detailed_log and current and start_pos:
                # Calculate distance using Position's distance_to method
                distance = start_pos.distance_to(dest)

                # Extract reactions if any
                reactions = []
                if "reactions" in summary:
                    for reaction in summary["reactions"]:
                        reactions.append(f"{reaction.get('type', 'reaction')}: {reaction.get('message', '')}")

                move_data = DetailedMoveData(
                    unit_name=current.name,
                    round_number=self.battle.round,
                    from_pos=start_pos,
                    to_pos=dest,
                    ap_spent=ap_spent,
                    distance=distance,
                    reactions_triggered=reactions
                )

                self.detailed_log.log_move(f"{current.name} moved to ({dest.q}, {dest.r})", move_data)

        return summary

    def execute_attack(
        self, target_pos: Position, attacker: Unit, defender: Optional[Unit]
    ) -> Optional[dict]:
        """Execute attack on target position.

        Args:
            target_pos: Target hex position
            attacker: Attacking unit (not used - battle service uses current_unit)
            defender: Defending unit (if any)

        Returns:
            Attack summary or None if failed
        """
        if not defender:
            self.show_message("No target at that hex")
            return None

        # Execute attack (uses current_unit from battle service)
        summary = self.battle.attack_current_unit(defender=defender)

        if "error" in summary:
            self.show_message(f"Attack failed: {summary['error']}")
            logger.warning(f"Attack failed: {summary['error']}")
            return None

        attack_res = self._extract_attack_result_from_summary(summary)
        if not attack_res:
            logger.warning("No attack_result in attack summary")
            return None

        # Format and show message
        msg = self._format_attack_result_message(attack_res)
        self.show_message(msg)

        # Log detailed attack
        if self.detailed_log:
            is_flank, is_rear, facing_ignored_ve = self._get_attack_angle_info(attacker, defender)

            # Check stamina for penalties
            attacker_penalties = {}
            attacker_buffs = {}
            defender_penalties = {}
            defender_buffs = {}

            if attacker.stamina.current_stamina < attacker.stamina.max_stamina * 0.3:
                attacker_penalties["Low Stamina"] = "High fatigue penalties"
            if defender.stamina.current_stamina < defender.stamina.max_stamina * 0.3:
                defender_penalties["Low Stamina"] = "Reduced defense"

            attack_data = self._build_attack_data_from_result(
                attack_res, attacker, defender, is_flank, is_rear, facing_ignored_ve,
                attacker_penalties, attacker_buffs, defender_penalties, defender_buffs
            )

            self.detailed_log.log_attack(msg, attack_data)

        ap_spent = summary.get("action_result").ap_spent if "action_result" in summary else 0
        logger.info(f"{attacker.name} attacked {defender.name} (AP spent: {ap_spent})")

        return summary

        ap_spent = getattr(action_result, "ap_spent", 0) if action_result else 0
        logger.info(f"{attacker.name} attacked {defender.name} (AP spent: {ap_spent})")

        return summary

    def execute_attack_combination(
        self, target_pos: Position, attacker: Unit, defender: Optional[Unit]
    ) -> Optional[dict]:
        """Execute dagger attack combination on target position."""
        if not defender:
            self.show_message("No target at that hex")
            return None

        summary = self.battle.attack_combination_current_unit(defender=defender)

        if "error" in summary:
            self.show_message(f"Attack combination failed: {summary['error']}")
            logger.warning(f"Attack combination failed: {summary['error']}")
            return summary

        action_result = summary.get("action_result")
        if not action_result:
            logger.warning("No action_result in attack combination summary")
            return summary

        combo_results = None
        combo_config = None
        stopped_early = False
        if hasattr(action_result, "data") and action_result.data:
            combo_results = action_result.data.get("attack_results")
            combo_config = action_result.data.get("combo_config")
            stopped_early = action_result.data.get("combo_stopped_early", False)

        if combo_results:
            total_attacks = getattr(combo_config, "attack_count", len(combo_results)) if combo_config else len(combo_results)
            msg = self._format_attack_combination_message(attacker, defender, combo_results, total_attacks, stopped_early)
            self.show_message(msg)

            # Log detailed action entry
            if self.detailed_log:
                for idx, res in enumerate(combo_results, start=1):
                    attack_msg = (
                        f"Combo {idx}/{total_attacks}: {attacker.name} -> {defender.name}\n"
                        f"{self._format_attack_result_message(res)}"
                    )
                    attack_data = DetailedAttackData(
                        attacker_name=attacker.name,
                        defender_name=defender.name,
                        round_number=self.battle.round,
                        attack_roll=res.attack_roll,
                        all_te=res.all_te,
                        all_ve=res.all_ve,
                        outcome=res.outcome.value,
                        is_flank_attack=False,
                        is_rear_attack=False,
                        facing_ignored_ve=False,
                        damage_to_fp=res.damage_to_fp,
                        damage_to_ep=res.damage_to_ep,
                        mandatory_ep_loss=res.mandatory_ep_loss,
                        armor_absorbed=res.armor_absorbed,
                        stamina_spent_defender=res.stamina_spent_defender,
                        hit_zone=res.hit_zone,
                        zone_sfe=res.zone_sfe,
                        is_critical=res.is_critical,
                        is_overpower=res.is_overpower,
                        attacker_penalties={},
                        attacker_buffs={},
                        defender_penalties={},
                        defender_buffs={},
                    )
                    self.detailed_log.log_attack(attack_msg, attack_data)

                # Calculate total damage with ÉP source breakdown
                total_fp = sum(r.damage_to_fp for r in combo_results)
                total_overflow_ep = 0  # FP damage that overflowed to ÉP
                total_mandatory_ep = 0  # Weapon size rule (purple)
                total_overpower_ep = 0  # Excess TE causing direct ÉP (red)

                for res in combo_results:
                    total_mandatory_ep += res.mandatory_ep_loss
                    if res.is_overpower:
                        total_overpower_ep += res.damage_to_ep
                    else:
                        total_overflow_ep += res.damage_to_ep

                total_ep = total_overflow_ep + total_mandatory_ep + total_overpower_ep

                # Build attack lines for battle log
                attack_lines = []
                for i, res in enumerate(combo_results, start=1):
                    outcome_str = res.outcome.value.replace("_", " ").title()
                    damage_roll = getattr(res, "rolled_damage", 0)
                    base = f"{i}. TÉ {res.all_te} ({res.attack_roll}) vs VÉ {res.all_ve} | {outcome_str}"

                    from domain.mechanics.attack_resolution import AttackOutcome

                    if res.outcome in (
                        AttackOutcome.HIT,
                        AttackOutcome.OVERPOWER,
                        AttackOutcome.CRITICAL,
                        AttackOutcome.CRITICAL_OVERPOWER,
                    ):
                        ep_total = res.damage_to_ep + res.mandatory_ep_loss
                        line = (
                            f"{base} | DMG {damage_roll} SFÉ {res.zone_sfe} | "
                            f"FP {res.damage_to_fp} ÉP {ep_total}"
                        )
                    elif res.outcome in (AttackOutcome.BLOCKED, AttackOutcome.PARRIED):
                        line = (
                            f"{base} | DMG {damage_roll} | "
                            f"Stamina {res.stamina_spent_defender}"
                        )
                    else:
                        line = f"{base}"

                    attack_lines.append(line)

                action_data = DetailedActionData(
                    unit_name=attacker.name,
                    round_number=self.battle.round,
                    action_type="dagger_combo",
                    ap_spent=getattr(action_result, "ap_spent", 0),
                    description=f"Dagger Combo ({len(combo_results)}/{total_attacks})",
                    extra_data={
                        "defender": defender.name,
                        "attacks": attack_lines,
                        "total_fp": total_fp,
                        "total_ep": total_ep,
                        "total_overflow_ep": total_overflow_ep,
                        "total_mandatory_ep": total_mandatory_ep,
                        "total_overpower_ep": total_overpower_ep,
                        "stopped_early": stopped_early,
                    },
                )
                self.detailed_log.log_action(msg, action_data)
        else:
            self.show_message("Attack combination produced no results")

        return summary

    def execute_shield_bash(
        self, target_pos: Position, attacker: Unit, defender: Optional[Unit]
    ) -> Optional[dict]:
        """Execute shield bash on target position."""
        if not defender:
            self.show_message("No target at that hex")
            return None

        summary = self.battle.shield_bash_current_unit(defender=defender)

        if "error" in summary:
            self.show_message(f"Shield bash failed: {summary['error']}")
            logger.warning(f"Shield bash failed: {summary['error']}")
            return summary

        attack_res = self._extract_attack_result_from_summary(summary)

        if attack_res:
            # User-facing message
            msg = "Shield Bash\n" + self._format_attack_result_message(attack_res)
            self.show_message(msg)

            # Detailed logging (separate from display)
            if self.detailed_log:
                is_flank, is_rear, facing_ignored_ve = self._get_attack_angle_info(attacker, defender)

                attack_data = self._build_attack_data_from_result(
                    attack_res, attacker, defender, is_flank, is_rear, facing_ignored_ve
                )

                self.detailed_log.log_attack("Shield Bash", attack_data)
        else:
            self.show_message("Shield bash produced no results")

        return summary

    def execute_charge(
        self, target_pos: Position, attacker: Unit, defender: Optional[Unit]
    ) -> dict:
        """Execute charge special attack on target position.

        Returns a summary dict with:
        - action_result: The charge action result
        - path: Path the charger traveled
        - reaction_results: Any opportunity attacks triggered
        """
        if not defender:
            self.show_message("No target at that hex")
            return {"error": "No target at that hex"}

        enemies = self.battle.get_enemies(attacker)
        summary = self.battle.charge_current_unit(defender=defender, potential_reactors=enemies)

        if "error" in summary:
            self.show_message(f"Charge failed: {summary['error']}")
            logger.warning(f"Charge failed: {summary['error']}")
            return summary

        action_result = summary.get("action_result")
        attack_res = self._extract_attack_result_from_summary(summary)

        if attack_res:
            # User-facing message
            msg = self._format_attack_result_message(attack_res)
            self.show_message(msg)

            # Detailed logging (separate from display message)
            if self.detailed_log:
                is_flank, is_rear, facing_ignored_ve = self._get_attack_angle_info(attacker, defender)

                attacker_buffs = {"Charge Bonus": "+10 TÉ from charge"}
                attacker_penalties = {}
                defender_penalties = {}
                defender_buffs = {}

                if attacker.stamina.current_stamina < attacker.stamina.max_stamina * 0.3:
                    attacker_penalties["Low Stamina"] = "High fatigue penalties"
                if defender.stamina.current_stamina < defender.stamina.max_stamina * 0.3:
                    defender_penalties["Low Stamina"] = "Reduced defense"

                attack_data = self._build_attack_data_from_result(
                    attack_res, attacker, defender, is_flank, is_rear, facing_ignored_ve,
                    attacker_penalties, attacker_buffs, defender_penalties, defender_buffs
                )

                self.detailed_log.log_attack(f"CHARGE: {msg}", attack_data)
        else:
            self.show_message(action_result.message if action_result else "Charge produced no result")

        ap_spent = getattr(action_result, "ap_spent", 0) if action_result else 0
        logger.info(f"{attacker.name} charged {defender.name} (AP spent: {ap_spent})")

        return summary

    def execute_rotation(self, direction: int, unit: Unit) -> dict:
        """Execute unit rotation.

        Args:
            direction: Rotation direction (-1 for CCW, 1 for CW)
            unit: Unit to rotate

        Returns:
            Rotation result summary
        """
        from domain.value_objects import Facing

        direction_name = "left" if direction < 0 else "right"

        # Calculate new facing
        current_facing = unit.facing.direction
        new_facing_dir = (current_facing + direction) % 6
        new_facing = Facing(new_facing_dir)

        # Execute rotation
        result = self.battle.rotate_current_unit(new_facing)

        if "error" in result:
            self.show_message(result["error"])
        else:
            ap_spent = result.get("ap_spent", 0)
            self.show_message(f"Rotated {direction_name} (AP: -{ap_spent})")

        return result

    def execute_facing_change(self, target_q: int, target_r: int, unit: Unit) -> Optional[dict]:
        """Change unit's facing to point toward target hex.

        Args:
            target_q: Target hex q coordinate
            target_r: Target hex r coordinate
            unit: Unit to rotate

        Returns:
            Rotation result or None if invalid
        """
        # Calculate facing direction
        facing_dir = calculate_facing_to_hex(unit.position.q, unit.position.r, target_q, target_r)
        if facing_dir is None:
            self.show_message("Not an adjacent hex")
            return None

        # Execute facing change
        new_facing = Facing(facing_dir)
        result = self.battle.rotate_current_unit(new_facing)

        if "error" in result:
            self.show_message(result["error"])
        else:
            ap_spent = result.get("ap_spent", 0)
            self.show_message(f"Rotated to face hex (AP: -{ap_spent})")

        return result

    def execute_weapon_switch(
        self, unit: Unit, new_main_hand: Optional[str], new_off_hand: Optional[str]
    ) -> dict:
        """Execute weapon switch action.

        Args:
            unit: Unit switching weapons
            new_main_hand: New main hand weapon ID
            new_off_hand: New off hand weapon ID

        Returns:
            Summary dict with results
        """
        logger.info(f"{unit.name} switching weapons: main={new_main_hand}, off={new_off_hand}")

        # Call battle service to perform the switch
        result = self.battle.switch_weapon(
            unit=unit, new_main_hand=new_main_hand, new_off_hand=new_off_hand
        )

        if "error" in result:
            self.show_message(f"Weapon switch failed: {result['error']}")
            logger.warning(f"Weapon switch failed: {result['error']}")
            return result

        # Format success message
        ap_spent = result.get("ap_spent", 5)
        self.show_message(f"Weapons switched (AP: -{ap_spent})")
        logger.info(f"{unit.name} switched weapons successfully")

        # Log weapon switch
        if self.detailed_log:
            action_data = DetailedActionData(
                unit_name=unit.name,
                round_number=self.battle.round,
                action_type="weapon_switch",
                ap_spent=ap_spent,
                description=f"Switched to {new_main_hand or 'empty'} / {new_off_hand or 'empty'}",
                extra_data={"main_hand": new_main_hand, "off_hand": new_off_hand}
            )
            self.detailed_log.log_action(f"{unit.name} switched weapons", action_data)

        return result

    def end_turn(self) -> None:
        """End current unit's turn."""
        current_unit = self.battle.current_unit
        old_round = self.battle.round

        # Log turn end before ending
        if self.detailed_log and current_unit:
            entry = BattleLogEntry(
                entry_type="turn_end",
                round_number=self.battle.round,
                timestamp=time.time(),
                message=f"{current_unit.name} ended their turn",
                unit_name=current_unit.name
            )
            self.detailed_log.entries.append(entry)

        self.battle.end_turn()

        # Check if round changed
        new_round = self.battle.round
        if self.detailed_log:
            if new_round > old_round:
                # Round advanced
                self.detailed_log.set_round(new_round)

                # Log new initiative if it was re-rolled
                if self.battle.initiative_order is not None:
                    table = self.battle.get_initiative_table()
                    unit_map = {unit.id: unit for unit in self.battle.units}

                    for position, (unit_id, total, base_ke, roll) in enumerate(table, start=1):
                        unit = unit_map.get(unit_id)
                        if unit:
                            self.detailed_log.log_initiative(unit.name, total, base_ke, roll, position)

        # Show new active unit's name
        next_unit = self.battle.current_unit
        if next_unit:
            self.show_message(f"{next_unit.name}'s turn")

    def _format_attack_result_message(self, attack_result) -> str:
        """Format attack result into a multi-line user-friendly message.

        Args:
            attack_result: AttackResult from domain layer

        Returns:
            Formatted message string with multiple lines
        """
        from domain.mechanics.attack_resolution import AttackOutcome

        # Line 1: TÉ vs VÉ | Result (show roll value in TÉ)
        outcome_str = attack_result.outcome.value.replace("_", " ").title()
        line1 = f"TÉ {attack_result.all_te} ({attack_result.attack_roll}) vs VÉ {attack_result.all_ve} | {outcome_str}"

        line2 = ""
        line3 = ""

        # Add details based on outcome type
        if attack_result.outcome in (AttackOutcome.BLOCKED, AttackOutcome.PARRIED):
            # For blocks/parries: only show stamina cost on line 3
            if attack_result.stamina_spent_defender > 0:
                line3 = f"Stamina: {attack_result.stamina_spent_defender}"
        elif attack_result.outcome in (
            AttackOutcome.HIT,
            AttackOutcome.CRITICAL,
            AttackOutcome.OVERPOWER,
            AttackOutcome.CRITICAL_OVERPOWER,
        ):
            # Line 2: Zone and pre-armor damage value
            # Pre-armor damage = final damage + what armor blocked (includes all modifiers/bonuses)
            pre_armor_damage = attack_result.damage_to_fp + attack_result.armor_absorbed

            if attack_result.hit_zone:
                line2 = f"{attack_result.hit_zone} (SFÉ:{attack_result.zone_sfe}) | DMG: {pre_armor_damage}"
            else:
                line2 = f"DMG: {pre_armor_damage}"

            # Line 3: Damage breakdown with transparency
            damage_parts = []

            # Show armor absorption if any
            if attack_result.armor_absorbed > 0:
                damage_parts.append(f"Armor: -{attack_result.armor_absorbed}")

            # Final FP damage
            if attack_result.damage_to_fp > 0:
                damage_parts.append(f"FP: {attack_result.damage_to_fp}")

            # ÉP damage breakdown with clear labels
            # damage_to_ep = overflow FP damage OR overpower ÉP
            # mandatory_ep_loss = weapon size rule (large weapons always cause ÉP)
            direct_ep = attack_result.damage_to_ep
            mandatory_ep = attack_result.mandatory_ep_loss
            total_ep = direct_ep + mandatory_ep

            if total_ep > 0:
                ep_parts = []

                # Mandatory ÉP from weapon size (always show if present)
                if mandatory_ep > 0:
                    ep_parts.append(f"Weapon:{mandatory_ep}")

                # Direct ÉP damage (overflow or overpower)
                if direct_ep > 0:
                    if attack_result.is_overpower:
                        # Overpower: excess TE causes direct ÉP
                        ep_parts.append(f"Overpower:{direct_ep}")
                    else:
                        # Overflow: FP damage exceeded max FP
                        ep_parts.append(f"Overflow:{direct_ep}")

                if ep_parts:
                    ep_breakdown = "+".join(ep_parts)
                    damage_parts.append(f"ÉP: {total_ep} ({ep_breakdown})")

            if damage_parts:
                line3 = " | ".join(damage_parts)

        # Combine lines, filtering out empty ones
        msg_lines = [line1]
        if line2:
            msg_lines.append(line2)
        if line3:
            msg_lines.append(line3)

        return "\n".join(msg_lines)

    def _format_attack_combination_message(
        self,
        attacker: Unit,
        defender: Unit,
        attack_results: list,
        total_attacks: int,
        stopped_early: bool = False,
    ) -> str:
        """Format dagger attack combination results with detailed per-attack breakdown."""
        if not attack_results:
            return "Attack combination failed"

        # Line 1: Title and participants
        title = (
            f"Dagger Combo ({len(attack_results)}/{total_attacks}) "
            f"{attacker.name} -> {defender.name}"
        )

        # Lines 2+: Each attack result on its own line with TÉ/VÉ details
        attack_lines = []
        for i, res in enumerate(attack_results, start=1):
            outcome_str = res.outcome.value.replace("_", " ").title()
            # Format like normal attack: TÉ (roll) vs VÉ | Outcome
            attack_line = f"  {i}. TÉ {res.all_te} ({res.attack_roll}) vs VÉ {res.all_ve} | {outcome_str}"

            # Add damage breakdown if hit
            from domain.mechanics.attack_resolution import AttackOutcome
            if res.outcome in (AttackOutcome.HIT, AttackOutcome.CRITICAL,
                              AttackOutcome.OVERPOWER, AttackOutcome.CRITICAL_OVERPOWER):
                damage_parts = []
                if res.damage_to_fp > 0:
                    damage_parts.append(f"FP:{res.damage_to_fp}")

                ep_total = res.damage_to_ep + res.mandatory_ep_loss
                if ep_total > 0:
                    ep_breakdown = []
                    if res.mandatory_ep_loss > 0:
                        ep_breakdown.append(f"W:{res.mandatory_ep_loss}")
                    if res.damage_to_ep > 0:
                        if res.is_overpower:
                            ep_breakdown.append(f"O:{res.damage_to_ep}")
                        else:
                            ep_breakdown.append(f"Ov:{res.damage_to_ep}")
                    damage_parts.append(f"ÉP:{ep_total}({'+'.join(ep_breakdown)})")

                if damage_parts:
                    attack_line += " | " + " ".join(damage_parts)

            attack_lines.append(attack_line)

        # Final line: Total damage summary
        # Separate ÉP sources: overflow (yellow), mandatory (purple), overpower (red)
        total_overflow_ep = 0  # FP damage that overflowed to ÉP
        total_mandatory_ep = 0  # Weapon size rule (purple)
        total_overpower_ep = 0  # Excess TE causing direct ÉP (red)

        for res in attack_results:
            total_mandatory_ep += res.mandatory_ep_loss
            if res.is_overpower:
                total_overpower_ep += res.damage_to_ep
            else:
                total_overflow_ep += res.damage_to_ep

        total_ep = total_overflow_ep + total_mandatory_ep + total_overpower_ep

        # Only count FP that didn't overflow as final FP damage
        total_fp = sum(r.damage_to_fp for r in attack_results)

        summary_parts = []
        if total_fp > 0:
            summary_parts.append(f"Total FP: {total_fp}")
        if total_ep > 0:
            ep_sources = []
            if total_overflow_ep > 0:
                ep_sources.append(f"yellow {total_overflow_ep}")
            if total_mandatory_ep > 0:
                ep_sources.append(f"purple {total_mandatory_ep}")
            if total_overpower_ep > 0:
                ep_sources.append(f"red {total_overpower_ep}")
            ep_breakdown = " | ".join(ep_sources)
            summary_parts.append(f"Total ÉP: {total_ep} ({ep_breakdown})")

        summary_line = " | ".join(summary_parts)
        if stopped_early:
            summary_line = (summary_line + " | " if summary_line else "") + "Target defeated"

        # Combine all lines
        msg_lines = [title] + attack_lines
        if summary_line:
            msg_lines.append(f"  TOTAL: {summary_line}")

        return "\n".join(msg_lines)

    def show_message(self, message: str) -> None:
        """Show combat message to player.

        Args:
            message: Message text
        """
        self.combat_message = message
        self.combat_message_timer = 180  # 3 seconds at 60fps
        logger.debug(f"Combat message: {message}")

    def update_message_timer(self) -> None:
        """Update message timer and clear if expired."""
        if self.combat_message_timer > 0:
            self.combat_message_timer -= 1
            if self.combat_message_timer == 0:
                self.combat_message = None

    def inspect_hex(
        self, q: int, r: int, units: list[Unit], screen_width: int, screen_height: int
    ) -> Unit | None:
        """Inspect a hex and return unit if present.

        Args:
            q: Hex q coordinate
            r: Hex r coordinate
            units: List of all units
            screen_width: Screen width for popup positioning
            screen_height: Screen height for popup positioning

        Returns:
            Unit if found at hex, None otherwise
        """
        # Find unit at hex
        for unit in units:
            if unit.position.q == q and unit.position.r == r:
                logger.info(f"Inspecting unit: {unit.name} at ({q}, {r})")
                return unit

        logger.debug(f"No unit at ({q}, {r})")
        return None

    # ========================================================================
    # SPECIAL ATTACK EXECUTION HELPERS
    # ========================================================================

    def _get_attack_angle_info(self, attacker: Unit, defender: Unit) -> tuple[bool, bool, bool]:
        """Calculate attack angle positioning info.

        Args:
            attacker: Attacking unit
            defender: Defending unit

        Returns:
            (is_flank, is_rear, facing_ignored_ve) tuple
        """
        from domain.mechanics.attack_angle import AttackAngle, get_attack_angle

        attack_angle = get_attack_angle(attacker, defender)
        is_flank = attack_angle in (
            AttackAngle.FRONT_RIGHT,
            AttackAngle.FRONT_LEFT,
            AttackAngle.BACK_RIGHT,
            AttackAngle.BACK_LEFT,
        )
        is_rear = attack_angle == AttackAngle.BACK
        facing_ignored_ve = attack_angle not in (
            AttackAngle.FRONT,
            AttackAngle.FRONT_RIGHT,
            AttackAngle.FRONT_LEFT,
        )
        return is_flank, is_rear, facing_ignored_ve

    def _build_attack_data_from_result(
        self,
        attack_result,
        attacker: Unit,
        defender: Unit,
        is_flank: bool,
        is_rear: bool,
        facing_ignored_ve: bool,
        attacker_penalties: dict | None = None,
        attacker_buffs: dict | None = None,
        defender_penalties: dict | None = None,
        defender_buffs: dict | None = None,
    ) -> "DetailedAttackData":
        """Build DetailedAttackData from attack result.

        Args:
            attack_result: Attack result from domain
            attacker: Attacking unit
            defender: Defending unit
            is_flank: Whether this is a flank attack
            is_rear: Whether this is a rear attack
            facing_ignored_ve: Whether facing ignored VÉ
            attacker_penalties: Optional attacker penalties dict
            attacker_buffs: Optional attacker buffs dict
            defender_penalties: Optional defender penalties dict
            defender_buffs: Optional defender buffs dict

        Returns:
            DetailedAttackData object
        """
        return DetailedAttackData(
            attacker_name=attacker.name,
            defender_name=defender.name,
            round_number=self.battle.round,
            attack_roll=attack_result.attack_roll,
            all_te=attack_result.all_te,
            all_ve=attack_result.all_ve,
            outcome=attack_result.outcome.value,
            is_flank_attack=is_flank,
            is_rear_attack=is_rear,
            facing_ignored_ve=facing_ignored_ve,
            damage_to_fp=attack_result.damage_to_fp,
            damage_to_ep=attack_result.damage_to_ep,
            mandatory_ep_loss=attack_result.mandatory_ep_loss,
            armor_absorbed=attack_result.armor_absorbed,
            stamina_spent_defender=attack_result.stamina_spent_defender,
            hit_zone=attack_result.hit_zone,
            zone_sfe=attack_result.zone_sfe,
            is_critical=attack_result.is_critical,
            is_overpower=attack_result.is_overpower,
            attacker_penalties=attacker_penalties or {},
            attacker_buffs=attacker_buffs or {},
            defender_penalties=defender_penalties or {},
            defender_buffs=defender_buffs or {},
        )

    def _extract_attack_result_from_summary(self, summary: dict):
        """Extract attack result from execution summary.

        Args:
            summary: Execution summary dict

        Returns:
            Attack result or None if not found
        """
        action_result = summary.get("action_result")
        if not action_result or not hasattr(action_result, "data"):
            return None
        return action_result.data.get("attack_result")

    # ========================================================================
    # EXECUTE METHODS (refactored)
    # ========================================================================
