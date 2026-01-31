"""Tests for BattleOutcomeResolver."""

from unittest.mock import MagicMock

import pytest

from MAGUS_pygame.presentation.screens.game.battle.battle_outcome import (
    BattleOutcomeResolver,
)


class TestBattleOutcomeResolver:
    """Test battle outcome resolution."""

    @pytest.fixture
    def mock_battle_service(self):
        """Create mock battle service."""
        service = MagicMock()
        service.is_victory = MagicMock(return_value=False)
        service.get_winner = MagicMock(return_value=None)
        return service

    @pytest.fixture
    def mock_action_executor(self):
        """Create mock action executor."""
        executor = MagicMock()
        executor.show_message = MagicMock()
        return executor

    @pytest.fixture
    def resolver(self, mock_battle_service, mock_action_executor):
        """Create resolver with mocks."""
        return BattleOutcomeResolver(mock_battle_service, mock_action_executor)

    def test_init(self, resolver):
        """Should initialize with services."""
        assert resolver.battle is not None
        assert resolver.action_executor is not None

    def test_constants(self):
        """Should have correct outcome constants."""
        assert BattleOutcomeResolver.VICTORY_TEAM_A == "battle_victory_team_a"
        assert BattleOutcomeResolver.VICTORY_TEAM_B == "battle_victory_team_b"
        assert BattleOutcomeResolver.DRAW == "battle_draw"
        assert BattleOutcomeResolver.CANCELLED == "battle_cancelled"

    def test_check_victory_no_victory(self, resolver, mock_battle_service):
        """Should return None when battle not over."""
        mock_battle_service.is_victory.return_value = False

        result = resolver.check_victory()

        assert result is None

    def test_check_victory_team_a_wins(
        self, resolver, mock_battle_service, mock_action_executor
    ):
        """Should return victory action for team A."""
        mock_battle_service.is_victory.return_value = True
        mock_battle_service.get_winner.return_value = "team_a"

        result = resolver.check_victory()

        assert result == BattleOutcomeResolver.VICTORY_TEAM_A
        mock_action_executor.show_message.assert_called_once_with("Team A Victorious!")

    def test_check_victory_team_b_wins(
        self, resolver, mock_battle_service, mock_action_executor
    ):
        """Should return victory action for team B."""
        mock_battle_service.is_victory.return_value = True
        mock_battle_service.get_winner.return_value = "team_b"

        result = resolver.check_victory()

        assert result == BattleOutcomeResolver.VICTORY_TEAM_B
        mock_action_executor.show_message.assert_called_once_with("Team B Victorious!")

    def test_check_victory_draw(
        self, resolver, mock_battle_service, mock_action_executor
    ):
        """Should return draw action for tie."""
        mock_battle_service.is_victory.return_value = True
        mock_battle_service.get_winner.return_value = "draw"

        result = resolver.check_victory()

        assert result == BattleOutcomeResolver.DRAW
        mock_action_executor.show_message.assert_called_once_with(
            "Battle ended in a draw"
        )

    def test_get_victory_message_no_victory(self, resolver, mock_battle_service):
        """Should return empty string when not victorious."""
        mock_battle_service.is_victory.return_value = False

        message = resolver.get_victory_message()

        assert message == ""

    def test_get_victory_message_team_a_wins(
        self, resolver, mock_battle_service
    ):
        """Should return team A victory message."""
        mock_battle_service.is_victory.return_value = True
        mock_battle_service.get_winner.return_value = "team_a"

        message = resolver.get_victory_message()

        assert message == "Team A Wins!"

    def test_get_victory_message_team_b_wins(
        self, resolver, mock_battle_service
    ):
        """Should return team B victory message."""
        mock_battle_service.is_victory.return_value = True
        mock_battle_service.get_winner.return_value = "team_b"

        message = resolver.get_victory_message()

        assert message == "Team B Wins!"

    def test_get_victory_message_draw(self, resolver, mock_battle_service):
        """Should return draw message."""
        mock_battle_service.is_victory.return_value = True
        mock_battle_service.get_winner.return_value = "draw"

        message = resolver.get_victory_message()

        assert message == "Battle Complete"

    def test_is_victory_returns_true(self, resolver, mock_battle_service):
        """Should return True when victory."""
        mock_battle_service.is_victory.return_value = True

        result = resolver.is_victory()

        assert result is True

    def test_is_victory_returns_false(self, resolver, mock_battle_service):
        """Should return False when not victory."""
        mock_battle_service.is_victory.return_value = False

        result = resolver.is_victory()

        assert result is False

    def test_check_victory_called_with_correct_service(
        self, mock_battle_service, mock_action_executor
    ):
        """Should use battle service for checking victory."""
        mock_battle_service.is_victory.return_value = True
        mock_battle_service.get_winner.return_value = "team_a"
        resolver = BattleOutcomeResolver(mock_battle_service, mock_action_executor)

        resolver.check_victory()

        mock_battle_service.is_victory.assert_called_once()
        mock_battle_service.get_winner.assert_called_once()

    def test_multiple_check_victory_calls(
        self, resolver, mock_battle_service, mock_action_executor
    ):
        """Should handle multiple victory checks."""
        mock_battle_service.is_victory.return_value = True
        mock_battle_service.get_winner.return_value = "team_a"

        result1 = resolver.check_victory()
        result2 = resolver.check_victory()

        assert result1 == result2
        assert result1 == BattleOutcomeResolver.VICTORY_TEAM_A
        assert mock_action_executor.show_message.call_count == 2
