"""Action mode management and entry logic for battle screen."""

from logger.logger import get_logger
from presentation.screens.game.battle.battle_action_mode import ActionMode
from presentation.screens.game.battle.battle_special_attack_config import (
    get_special_attack_config,
    validate_special_attack_entry,
)

logger = get_logger(__name__)


class BattleActionModeManager:
    """Manages entry into different action modes (move, attack, inspect) with validation."""

    def __init__(self, battle_screen):
        """Initialize action mode manager.

        Args:
            battle_screen: Reference to BattleScreen for state and action execution
        """
        self.battle_screen = battle_screen

    def enter_move_mode(self) -> None:
        """Enter movement mode."""
        if self.battle_screen.battle.is_victory():
            return

        self.battle_screen._active_special_attack = None

        current = self.battle_screen.battle.current_unit
        can_move, error_msg = self.battle_screen.battle.can_move(current)
        if not can_move:
            self.battle_screen.action_executor.show_message(error_msg)
            return

        self.battle_screen.action_mode = ActionMode.MOVE
        self.battle_screen.selected_unit = current
        self.battle_screen._action_mode_explicitly_set = True

    def enter_attack_mode(self) -> None:
        """Enter attack mode."""
        if self.battle_screen.battle.is_victory():
            return

        self.battle_screen._active_special_attack = None

        current = self.battle_screen.battle.current_unit
        can_attack, error_msg = self.battle_screen.battle.can_attack(current)
        if not can_attack:
            self.battle_screen.action_executor.show_message(error_msg)
            return

        self.battle_screen.action_mode = ActionMode.ATTACK
        self.battle_screen.selected_unit = current
        self.battle_screen._action_mode_explicitly_set = True

    def enter_charge_mode(self) -> None:
        """Enter charge special attack mode."""
        self._enter_special_attack_mode("charge")

    def enter_dagger_combo_mode(self) -> None:
        """Enter dagger attack combination special attack mode."""
        self._enter_special_attack_mode("dagger_combo")

    def enter_shield_bash_mode(self) -> None:
        """Enter shield bash special attack mode."""
        self._enter_special_attack_mode("shield_bash")

    def _enter_special_attack_mode(self, attack_id: str) -> None:
        """Enter a special attack mode with common validation.

        Args:
            attack_id: Identifier for the special attack
        """
        # Validate entry conditions
        is_valid, error_msg = validate_special_attack_entry(self.battle_screen, attack_id)
        if not is_valid:
            self.battle_screen.action_executor.show_message(error_msg)
            return

        # Get attack config for messaging
        config = get_special_attack_config(attack_id)
        if not config:
            logger.error(f"Unknown attack config: {attack_id}")
            return

        # Set action mode state
        self.battle_screen.action_mode = ActionMode.ATTACK
        self.battle_screen.selected_unit = self.battle_screen.battle.current_unit
        self.battle_screen._active_special_attack = attack_id
        self.battle_screen._action_mode_explicitly_set = True
        self.battle_screen.action_executor.show_message(config["message"])

    def enter_inspect_mode(self) -> None:
        """Enter inspect mode."""
        self.battle_screen.action_mode = ActionMode.INSPECT
        self.battle_screen.selected_unit = None
        self.battle_screen._active_special_attack = None
        self.battle_screen._action_mode_explicitly_set = True

    def cancel_action(self) -> None:
        """Cancel current action and return to idle."""
        self.battle_screen.action_mode = ActionMode.IDLE
        self.battle_screen.selected_unit = None
        self.battle_screen.movement_path = None
        self.battle_screen._active_special_attack = None
        self.battle_screen._action_mode_explicitly_set = False
