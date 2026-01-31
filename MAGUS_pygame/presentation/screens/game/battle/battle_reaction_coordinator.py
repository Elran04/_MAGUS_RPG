"""
Battle Reaction Coordinator - manages opportunity attacks and reactions.

Handles:
- Reaction queue management (add, display, resolve)
- Enqueueing opportunity attacks as player reactions
- Accepting/declining opportunity attacks
- Logging OA results to battle log
- Managing reaction workflow (popup display, result formatting)
"""

from typing import Callable, Optional

from domain.battle_log_entry import DetailedAttackData
from logger.logger import get_logger

logger = get_logger(__name__)


class BattleReactionCoordinator:
    """Coordinates opportunity attack reactions and reaction queue during battle.

    Manages:
    - Reaction queue (pending player decisions)
    - Current reaction display
    - Enqueueing and resolving reactions
    - OA and counterattack workflows
    """

    def __init__(self, action_executor, battle_service, detailed_log):
        """Initialize reaction coordinator.

        Args:
            action_executor: BattleActionExecutor for messaging/logging
            battle_service: BattleService for round number and game state
            detailed_log: DetailedBattleLog for battle logging
        """
        self.action_executor = action_executor
        self.battle_service = battle_service
        self.detailed_log = detailed_log

        # Reaction queue system
        self.reaction_queue: list = []  # Queue of pending reactions
        self.current_reaction: Optional[dict] = None  # Currently displayed reaction
        self.reaction_callbacks: dict = {}  # Callbacks for reaction resolution

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
            self.action_executor.show_message(f"Accepted {reaction['type'].replace('_', ' ')}")
        else:
            if reaction["on_decline"]:
                reaction["on_decline"](reaction["data"])
            self.action_executor.show_message(f"Declined {reaction['type'].replace('_', ' ')}")

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

    def enqueue_opportunity_attacks(self, oa_results: list) -> None:
        """Enqueue opportunity attacks as reactions for player decision.

        Args:
            oa_results: List of opportunity attack results from reaction handler
        """
        for idx, oa_result in enumerate(oa_results):
            # Extract unit names from the reaction result's data
            attacker_name = (
                oa_result.data.get("attacker_name", "Unknown")
                if oa_result.data
                else "Unknown"
            )
            defender_name = (
                oa_result.data.get("defender_name", "Unknown")
                if oa_result.data
                else "Unknown"
            )

            # Get attack result for additional info
            attack_result = oa_result.data.get("attack_result") if oa_result.data else None

            # Create description for the reaction popup
            description = (
                f"{attacker_name} can make an opportunity attack against {defender_name}!"
            )
            if (
                attack_result
                and hasattr(attack_result, "requires_dodge_check")
                and attack_result.requires_dodge_check
            ):
                description += "\nDefender may dodge."

            # Enqueue as a reaction
            self.enqueue_reaction(
                reaction_type="opportunity_attack",
                description=description,
                reaction_data={
                    "index": idx,
                    "attacker_name": attacker_name,
                    "defender_name": defender_name,
                    "result": oa_result,
                },
                on_accept=lambda data: self.accept_opportunity_attack(data),
                on_decline=lambda data: self.decline_opportunity_attack(data),
            )

    def accept_opportunity_attack(self, reaction_data: dict) -> None:
        """Handle acceptance of an opportunity attack reaction.

        Args:
            reaction_data: Reaction data dict with attack details
        """
        # Show the attack result message
        oa_result = reaction_data.get("result")
        attacker_name = reaction_data.get("attacker_name", "Attacker")
        defender_name = reaction_data.get("defender_name", "Defender")

        # Extract and format the attack result
        if oa_result and oa_result.data:
            attack_result = oa_result.data.get("attack_result")
            if attack_result:
                # Format the attack result nicely
                msg = self.action_executor._format_attack_result_message(attack_result)
                full_msg = f"{attacker_name} -> {defender_name}:\n{msg}"
                self.action_executor.show_message(full_msg)

                # Also add to battle log with clear opportunity attack label
                if self.detailed_log:
                    attack_data = DetailedAttackData(
                        attacker_name=attacker_name,
                        defender_name=defender_name,
                        round_number=self.battle_service.round,
                        attack_roll=attack_result.attack_roll,
                        all_te=attack_result.all_te,
                        all_ve=attack_result.all_ve,
                        outcome=attack_result.outcome,
                        is_flank_attack=False,  # OA doesn't consider flanking
                        is_rear_attack=False,  # OA doesn't consider rear attacks
                        facing_ignored_ve=False,  # OA uses normal VÉ
                        hit_zone=attack_result.hit_zone,
                        zone_sfe=attack_result.zone_sfe,
                        damage_to_fp=attack_result.damage_to_fp,
                        damage_to_ep=attack_result.damage_to_ep,
                        mandatory_ep_loss=attack_result.mandatory_ep_loss,
                        armor_absorbed=attack_result.armor_absorbed,
                        stamina_spent_defender=attack_result.stamina_spent_defender,
                        is_critical=attack_result.is_critical,
                        is_overpower=attack_result.is_overpower,
                        is_opportunity_attack=True,
                    )
                    self.detailed_log.log_attack(
                        f"{attacker_name} -> {defender_name}", attack_data
                    )
            else:
                self.action_executor.show_message(f"{attacker_name} -> {defender_name}!")
        elif oa_result and hasattr(oa_result, "message"):
            self.action_executor.show_message(oa_result.message)
        else:
            self.action_executor.show_message(f"{attacker_name} -> {defender_name}!")

    def decline_opportunity_attack(self, reaction_data: dict) -> None:
        """Handle declining of an opportunity attack reaction.

        Args:
            reaction_data: Reaction data dict with attack details
        """
        attacker_name = reaction_data.get("attacker_name", "Attacker")
        self.action_executor.show_message(
            f"{attacker_name}'s opportunity attack was declined"
        )

    def enqueue_post_attack_reactions(self, reaction_results: list) -> None:
        """Enqueue post-attack reactions (counterattacks, reaction shield bash) for player decision.

        Args:
            reaction_results: List of reaction results from reaction handler
        """
        for idx, reaction_result in enumerate(reaction_results):
            # Extract unit names from the reaction result's data
            attacker_name = (
                reaction_result.data.get("attacker_name", "Unknown")
                if reaction_result.data
                else "Unknown"
            )
            defender_name = (
                reaction_result.data.get("defender_name", "Unknown")
                if reaction_result.data
                else "Unknown"
            )

            # Get attack result for additional info
            attack_result = reaction_result.data.get("attack_result") if reaction_result.data else None

            # Determine reaction type for proper labeling
            reaction_type = getattr(reaction_result, "reaction_type", "counterattack")
            if hasattr(reaction_result, "data") and reaction_result.data:
                special_attack = reaction_result.data.get("special_attack", "")
                if special_attack:
                    reaction_type = special_attack

            # Create description for the reaction popup
            type_name = "Counterattack" if reaction_type == "counterattack" else "Reaction Shield Bash"

            # Enqueue as a player reaction decision (accept/decline like opportunity attacks)
            description = f"{attacker_name} triggered {type_name}!"

            reaction_data = {
                "attacker_name": attacker_name,
                "defender_name": defender_name,
                "attack_result": attack_result,
                "reaction_type": reaction_type,
            }

            self.enqueue_reaction(
                reaction_type=reaction_type,
                description=description,
                reaction_data=reaction_data,
                on_accept=lambda data: self.accept_counterattack(data),
                on_decline=lambda data: self.decline_counterattack(data),
            )

    def accept_counterattack(self, reaction_data: dict) -> None:
        """Handle acceptance of a counterattack reaction.

        Args:
            reaction_data: Dict containing attacker, defender, and attack result
        """
        attack_result = reaction_data.get("attack_result")
        attacker_name = reaction_data.get("attacker_name", "Unknown")
        defender_name = reaction_data.get("defender_name", "Unknown")
        reaction_type = reaction_data.get("reaction_type", "counterattack")

        type_name = "Counterattack" if reaction_type == "counterattack" else "Reaction Shield Bash"

        if attack_result:
            msg = self.action_executor._format_attack_result_message(attack_result)
            full_msg = f"{attacker_name} {type_name}!:\n{msg}"
            self.action_executor.show_message(full_msg)

            # Log detailed reaction attack information
            if self.detailed_log:
                attack_data = DetailedAttackData(
                    attacker_name=attacker_name,
                    defender_name=defender_name,
                    round_number=self.battle_service.round,
                    attack_roll=attack_result.attack_roll,
                    all_te=attack_result.all_te,
                    all_ve=attack_result.all_ve,
                    outcome=attack_result.outcome.value,
                    is_flank_attack=False,
                    is_rear_attack=False,
                    facing_ignored_ve=False,
                    hit_zone=attack_result.hit_zone,
                    zone_sfe=attack_result.zone_sfe,
                    damage_to_fp=attack_result.damage_to_fp,
                    damage_to_ep=attack_result.damage_to_ep,
                    mandatory_ep_loss=attack_result.mandatory_ep_loss,
                    armor_absorbed=attack_result.armor_absorbed,
                    stamina_spent_defender=attack_result.stamina_spent_defender,
                    is_critical=attack_result.is_critical,
                    is_overpower=attack_result.is_overpower,
                    is_counterattack=(reaction_type == "counterattack"),
                )
                self.detailed_log.log_attack(
                    f"{attacker_name} {type_name}", attack_data
                )
        else:
            self.action_executor.show_message(f"{attacker_name} {type_name}!")

    def decline_counterattack(self, reaction_data: dict) -> None:
        """Handle declining of a counterattack reaction.

        Args:
            reaction_data: Dict containing attacker and defender names
        """
        attacker_name = reaction_data.get("attacker_name", "Unknown")
        reaction_type = reaction_data.get("reaction_type", "counterattack")
        type_name = "Counterattack" if reaction_type == "counterattack" else "Reaction Shield Bash"

        self.action_executor.show_message(
            f"{attacker_name}'s {type_name} was declined"
        )
