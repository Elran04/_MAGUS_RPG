"""
Battle outcome and victory determination.

Handles victory condition checking and end-of-battle messaging.
"""

from logger.logger import get_logger

logger = get_logger(__name__)


class BattleOutcomeResolver:
    """Determines and communicates battle outcomes."""

    # Outcome action constants
    VICTORY_TEAM_A = "battle_victory_team_a"
    VICTORY_TEAM_B = "battle_victory_team_b"
    DRAW = "battle_draw"
    CANCELLED = "battle_cancelled"

    def __init__(self, battle_service, action_executor):
        """Initialize outcome resolver.

        Args:
            battle_service: BattleService for victory checking
            action_executor: BattleActionExecutor for messaging
        """
        self.battle = battle_service
        self.action_executor = action_executor

    def check_victory(self) -> str | None:
        """Check for victory and emit appropriate action.

        Returns:
            Action string (battle_victory_team_a, battle_victory_team_b, battle_draw) or None
        """
        if not self.battle.is_victory():
            return None

        winner = self.battle.get_winner()
        if winner == "team_a":
            self.action_executor.show_message("Team A Victorious!")
            return self.VICTORY_TEAM_A
        elif winner == "team_b":
            self.action_executor.show_message("Team B Victorious!")
            return self.VICTORY_TEAM_B
        else:
            self.action_executor.show_message("Battle ended in a draw")
            return self.DRAW

    def get_victory_message(self) -> str:
        """Get victory message for display.

        Returns:
            Human-readable victory message
        """
        if not self.battle.is_victory():
            return ""

        winner = self.battle.get_winner()
        if winner == "team_a":
            return "Team A Wins!"
        elif winner == "team_b":
            return "Team B Wins!"
        else:
            return "Battle Complete"

    def is_victory(self) -> bool:
        """Check if battle has ended in victory.

        Returns:
            True if battle is over
        """
        return self.battle.is_victory()
