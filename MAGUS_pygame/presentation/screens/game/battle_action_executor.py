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

        # Reaction queue system
        self.reaction_queue: list = []  # Queue of pending reactions
        self.current_reaction: Optional[dict] = None  # Currently displayed reaction
        self.reaction_callbacks: dict = {}  # Callbacks for reaction resolution

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

        # Format attack result message in presentation layer
        action_result = summary.get("action_result")
        if not action_result:
            logger.warning("No action_result in attack summary")
            return None

        # Get attack result data from action_result
        attack_res = None
        if hasattr(action_result, "data") and action_result.data:
            attack_res = action_result.data.get("attack_result")

        if attack_res:
            msg = self._format_attack_result_message(attack_res)
            self.show_message(msg)

            # Log detailed attack information
            if self.detailed_log:
                from domain.mechanics.attack_angle import AttackAngle, get_attack_angle

                # Determine attack angle and positioning
                attack_angle = get_attack_angle(attacker, defender)
                is_flank = attack_angle in (AttackAngle.FRONT_RIGHT, AttackAngle.FRONT_LEFT,
                                           AttackAngle.BACK_RIGHT, AttackAngle.BACK_LEFT)
                is_rear = attack_angle == AttackAngle.BACK

                # Check if weapon/shield VÉ was ignored due to facing
                # Weapon VÉ applies only to front arcs (FRONT, FRONT_RIGHT, FRONT_LEFT)
                # Shield VÉ applies only to FRONT
                facing_ignored_ve = attack_angle not in (AttackAngle.FRONT, AttackAngle.FRONT_RIGHT, AttackAngle.FRONT_LEFT)

                # Build penalty/buff dicts (simplified for now - can be expanded with more data)
                attacker_penalties = {}
                attacker_buffs = {}
                defender_penalties = {}
                defender_buffs = {}

                # Add stamina as penalty if significant
                if attacker.stamina.current_stamina < attacker.stamina.max_stamina * 0.3:
                    attacker_penalties["Low Stamina"] = "High fatigue penalties"
                if defender.stamina.current_stamina < defender.stamina.max_stamina * 0.3:
                    defender_penalties["Low Stamina"] = "Reduced defense"

                # Create detailed attack data
                attack_data = DetailedAttackData(
                    attacker_name=attacker.name,
                    defender_name=defender.name,
                    round_number=self.battle.round,
                    attack_roll=attack_res.attack_roll,
                    all_te=attack_res.all_te,
                    all_ve=attack_res.all_ve,
                    outcome=attack_res.outcome.value,
                    is_flank_attack=is_flank,
                    is_rear_attack=is_rear,
                    facing_ignored_ve=facing_ignored_ve,
                    damage_to_fp=attack_res.damage_to_fp,
                    damage_to_ep=attack_res.damage_to_ep,
                    armor_absorbed=attack_res.armor_absorbed,
                    stamina_spent_defender=attack_res.stamina_spent_defender,
                    hit_zone=attack_res.hit_zone,
                    zone_sfe=attack_res.zone_sfe,
                    is_critical=attack_res.is_critical,
                    is_overpower=attack_res.is_overpower,
                    attacker_penalties=attacker_penalties,
                    attacker_buffs=attacker_buffs,
                    defender_penalties=defender_penalties,
                    defender_buffs=defender_buffs
                )

                self.detailed_log.log_attack(msg, attack_data)
        else:
            logger.warning(
                f"No attack_result in action_result data. Data: {action_result.data if hasattr(action_result, 'data') else 'N/A'}"
            )

        ap_spent = getattr(action_result, "ap_spent", 0) if action_result else 0
        logger.info(f"{attacker.name} attacked {defender.name} (AP spent: {ap_spent})")

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
        reaction_results = summary.get("reaction_results", [])

        if action_result:
            # Prefer formatted attack message if available
            attack_res = (
                action_result.data.get("attack_result") if hasattr(action_result, "data") else None
            )
            if attack_res:
                msg = self._format_attack_result_message(attack_res)
                self.show_message(msg)

                # Log detailed charge attack
                if self.detailed_log:
                    from domain.mechanics.attack_angle import AttackAngle, get_attack_angle

                    # Determine attack angle and positioning
                    attack_angle = get_attack_angle(attacker, defender)
                    is_flank = attack_angle in (AttackAngle.FRONT_RIGHT, AttackAngle.FRONT_LEFT,
                                               AttackAngle.BACK_RIGHT, AttackAngle.BACK_LEFT)
                    is_rear = attack_angle == AttackAngle.BACK
                    facing_ignored_ve = attack_angle not in (AttackAngle.FRONT, AttackAngle.FRONT_RIGHT, AttackAngle.FRONT_LEFT)

                    # Build penalty/buff dicts
                    attacker_penalties = {}
                    attacker_buffs = {"Charge Bonus": "+10 TÉ from charge"}
                    defender_penalties = {}
                    defender_buffs = {}

                    if attacker.stamina.current_stamina < attacker.stamina.max_stamina * 0.3:
                        attacker_penalties["Low Stamina"] = "High fatigue penalties"
                    if defender.stamina.current_stamina < defender.stamina.max_stamina * 0.3:
                        defender_penalties["Low Stamina"] = "Reduced defense"

                    attack_data = DetailedAttackData(
                        attacker_name=attacker.name,
                        defender_name=defender.name,
                        round_number=self.battle.round,
                        attack_roll=attack_res.attack_roll,
                        all_te=attack_res.all_te,
                        all_ve=attack_res.all_ve,
                        outcome=attack_res.outcome.value,
                        is_flank_attack=is_flank,
                        is_rear_attack=is_rear,
                        facing_ignored_ve=facing_ignored_ve,
                        damage_to_fp=attack_res.damage_to_fp,
                        damage_to_ep=attack_res.damage_to_ep,
                        armor_absorbed=attack_res.armor_absorbed,
                        stamina_spent_defender=attack_res.stamina_spent_defender,
                        hit_zone=attack_res.hit_zone,
                        zone_sfe=attack_res.zone_sfe,
                        is_critical=attack_res.is_critical,
                        is_overpower=attack_res.is_overpower,
                        attacker_penalties=attacker_penalties,
                        attacker_buffs=attacker_buffs,
                        defender_penalties=defender_penalties,
                        defender_buffs=defender_buffs
                    )

                    self.detailed_log.log_attack(f"CHARGE: {msg}", attack_data)
            else:
                self.show_message(action_result.message)

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

            # Line 3: Damage deductions (final damage after armor)
            damage_parts = []
            if attack_result.damage_to_fp > 0:
                damage_parts.append(f"FP: {attack_result.damage_to_fp}")

            # Show ÉP damage with color coding based on source
            # White: overflow/direct, Purple: weapon size rule, Red: overpower
            direct_ep = attack_result.damage_to_ep  # Direct ÉP damage
            mandatory_ep = attack_result.mandatory_ep_loss  # From weapon size rule
            total_ep = direct_ep + mandatory_ep

            if total_ep > 0:
                # Check if this is from overpower (damage_to_ep is high from overpower rule)
                is_overpower_ep = attack_result.is_overpower and direct_ep > 0

                if mandatory_ep > 0 and direct_ep > 0:
                    # Both rules apply: show with color tags
                    ep_str = f"ÉP: {total_ep} (<purple>{mandatory_ep}</purple> + <white>{direct_ep}</white>)"
                    damage_parts.append(ep_str)
                elif mandatory_ep > 0:
                    # Only weapon size rule applies - purple
                    damage_parts.append(f"ÉP: <purple>{mandatory_ep}</purple>")
                elif is_overpower_ep:
                    # Overpower damage - red
                    damage_parts.append(f"ÉP: <red>{direct_ep}</red>")
                else:
                    # Overflow damage - white
                    damage_parts.append(f"ÉP: <white>{direct_ep}</white>")

            if damage_parts:
                line3 = " | ".join(damage_parts)

        # Combine lines, filtering out empty ones
        msg_lines = [line1]
        if line2:
            msg_lines.append(line2)
        if line3:
            msg_lines.append(line3)

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
    # REACTION QUEUE SYSTEM
    # ========================================================================

    def enqueue_reaction(
        self,
        reaction_type: str,
        description: str,
        reaction_data: Optional[dict] = None,
        on_accept: Optional[Callable] = None,
        on_decline: Optional[Callable] = None,
    ) -> None:
        """Enqueue a reaction for player decision.

        Args:
            reaction_type: Type of reaction (e.g., "shield_bash", "opportunity_attack")
            description: Description text to display in popup
            reaction_data: Optional dict with reaction details (attacker, defender, etc.)
            on_accept: Optional callback(reaction_data) when accepted
            on_decline: Optional callback(reaction_data) when declined
        """
        reaction = {
            "type": reaction_type,
            "description": description,
            "data": reaction_data or {},
            "on_accept": on_accept,
            "on_decline": on_decline,
        }
        self.reaction_queue.append(reaction)
        logger.info(f"Reaction enqueued: {reaction_type} - {description}")
        self._show_next_reaction()

    def _show_next_reaction(self) -> None:
        """Show the next reaction from the queue."""
        if self.reaction_queue and not self.current_reaction:
            self.current_reaction = self.reaction_queue.pop(0)
            logger.debug(f"Showing reaction: {self.current_reaction['type']}")

    def get_current_reaction(self) -> dict | None:
        """Get the current pending reaction.

        Returns:
            Current reaction dict or None if no reaction pending
        """
        return self.current_reaction

    def resolve_reaction(self, accepted: bool) -> None:
        """Resolve the current reaction.

        Args:
            accepted: Whether the reaction was accepted
        """
        if not self.current_reaction:
            return

        reaction = self.current_reaction
        self.current_reaction = None

        if accepted:
            if reaction["on_accept"]:
                reaction["on_accept"](reaction["data"])
            self.show_message(f"Accepted {reaction['type'].replace('_', ' ')}")
        else:
            if reaction["on_decline"]:
                reaction["on_decline"](reaction["data"])
            self.show_message(f"Declined {reaction['type'].replace('_', ' ')}")

        logger.info(f"Reaction resolved: {reaction['type']} - {'accepted' if accepted else 'declined'}")

        # Show next reaction if available
        self._show_next_reaction()

    def has_pending_reaction(self) -> bool:
        """Check if there are any pending reactions.

        Returns:
            True if there are reactions pending or displayed
        """
        return self.current_reaction is not None or len(self.reaction_queue) > 0

    def clear_reactions(self) -> None:
        """Clear all pending reactions."""
        self.reaction_queue.clear()
        self.current_reaction = None
        logger.debug("Reactions cleared")
