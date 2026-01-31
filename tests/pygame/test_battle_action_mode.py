"""Tests for BattleActionMode Enum."""

import pytest

from MAGUS_pygame.presentation.screens.game.battle.battle_action_mode import ActionMode


class TestActionMode:
    """Test ActionMode Enum."""

    def test_enum_values(self):
        """Should have correct enum values."""
        assert ActionMode.IDLE.value == "idle"
        assert ActionMode.MOVE.value == "move"
        assert ActionMode.ATTACK.value == "attack"
        assert ActionMode.INSPECT.value == "inspect"

    def test_enum_members(self):
        """Should have all expected members."""
        modes = [ActionMode.IDLE, ActionMode.MOVE, ActionMode.ATTACK, ActionMode.INSPECT]
        assert len(modes) == 4

    def test_enum_equality(self):
        """Should compare correctly."""
        assert ActionMode.IDLE == ActionMode.IDLE
        assert ActionMode.MOVE != ActionMode.ATTACK

    def test_enum_comparison_with_value(self):
        """Should support comparison with values."""
        # Enums don't compare equal to their values, must use .value
        assert ActionMode.IDLE.value == "idle"
        assert ActionMode.MOVE.value == "move"

    def test_enum_from_value(self):
        """Should create enum from value."""
        mode = ActionMode("idle")
        assert mode == ActionMode.IDLE

        mode = ActionMode("attack")
        assert mode == ActionMode.ATTACK

    def test_enum_iteration(self):
        """Should be iterable."""
        modes = list(ActionMode)
        assert len(modes) == 4
        assert ActionMode.IDLE in modes
        assert ActionMode.MOVE in modes

    def test_enum_name_attribute(self):
        """Should have name attribute."""
        assert ActionMode.IDLE.name == "IDLE"
        assert ActionMode.MOVE.name == "MOVE"
        assert ActionMode.ATTACK.name == "ATTACK"
        assert ActionMode.INSPECT.name == "INSPECT"
