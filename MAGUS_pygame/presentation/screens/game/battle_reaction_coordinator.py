"""
Battle Reaction Coordinator - manages opportunity attacks and reactions.

Handles:
- Enqueueing opportunity attacks as player reactions
- Accepting/declining opportunity attacks
- Logging OA results to battle log
- Managing reaction workflow (popup display, result formatting)
"""

from domain.battle_log_entry import DetailedAttackData
from logger.logger import get_logger

logger = get_logger(__name__)


class BattleReactionCoordinator:
    """Coordinates opportunity attack reactions during battle.

    Delegates from BattleScreen to:
    - Enqueue OA opportunities for player decision
    - Format and log OA results
    - Display OA messages and outcomes
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
            self.action_executor.enqueue_reaction(
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
