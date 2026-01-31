"""Keyboard input handling for battle screen."""

import pygame
from logger.logger import get_logger

logger = get_logger(__name__)


class BattleKeyboardHandler:
    """Manages keyboard input for battle screen.

    Provides a centralized registry of keyboard mappings and handlers.
    """

    def __init__(self, battle_screen):
        """Initialize keyboard handler.

        Args:
            battle_screen: Reference to BattleScreen for action calls
        """
        self.battle_screen = battle_screen

        # Build key-to-action mapping
        self._key_handlers = {
            pygame.K_ESCAPE: self._handle_escape,
            pygame.K_SPACE: self._handle_space_return,
            pygame.K_RETURN: self._handle_space_return,
            pygame.K_m: self._handle_m,
            pygame.K_a: self._handle_a,
            pygame.K_w: self._handle_w,
            pygame.K_i: self._handle_i,
            pygame.K_q: self._handle_q,
            pygame.K_e: self._handle_e,
        }

    def handle_keypress(self, key: int) -> None:
        """Handle keyboard input.

        Args:
            key: Pygame key constant
        """
        handler = self._key_handlers.get(key)
        if handler:
            handler()

    def _handle_escape(self) -> None:
        """Handle ESC key: manage menus and popups."""
        # Priority: Reaction popup > Battle log > Weapon switch > Unit popup > Pause menu
        if self.battle_screen.reaction_popup and self.battle_screen.reaction_popup.visible:
            self.battle_screen.reaction_popup.hide()
        elif self.battle_screen.battle_log_popup and self.battle_screen.battle_log_popup.visible:
            self.battle_screen.battle_log_popup.hide()
        elif (
            self.battle_screen.weapon_switch_popup
            and self.battle_screen.weapon_switch_popup.visible
        ):
            self.battle_screen.weapon_switch_popup.hide()
        elif self.battle_screen.unit_popup and self.battle_screen.unit_popup.visible:
            self.battle_screen.unit_popup.hide()
        else:
            self.battle_screen.pause_menu.toggle()

    def _handle_space_return(self) -> None:
        """Handle SPACE or RETURN: end current turn."""
        if not self.battle_screen.pause_menu.visible:
            self.battle_screen._end_current_turn()

    def _handle_m(self) -> None:
        """Handle M key: toggle move mode."""
        if self.battle_screen.pause_menu.visible:
            return

        from presentation.screens.game.battle.battle_action_mode import ActionMode

        if self.battle_screen.action_mode == ActionMode.MOVE:
            self.battle_screen._cancel_action()
        else:
            self.battle_screen._enter_move_mode()

    def _handle_a(self) -> None:
        """Handle A key: toggle attack mode."""
        if self.battle_screen.pause_menu.visible:
            return

        from presentation.screens.game.battle.battle_action_mode import ActionMode

        if self.battle_screen.action_mode == ActionMode.ATTACK:
            self.battle_screen._cancel_action()
        else:
            self.battle_screen._enter_attack_mode()

    def _handle_w(self) -> None:
        """Handle W key: open weapon switch popup."""
        if not self.battle_screen.pause_menu.visible:
            self.battle_screen._open_weapon_switch_popup()

    def _handle_i(self) -> None:
        """Handle I key: toggle inspect mode."""
        if self.battle_screen.pause_menu.visible:
            return

        from presentation.screens.game.battle.battle_action_mode import ActionMode

        if self.battle_screen.action_mode == ActionMode.INSPECT:
            self.battle_screen._cancel_action()
        else:
            self.battle_screen._enter_inspect_mode()

    def _handle_q(self) -> None:
        """Handle Q key: rotate current unit counter-clockwise."""
        if not self.battle_screen.pause_menu.visible:
            self.battle_screen._rotate_current_unit(-1)

    def _handle_e(self) -> None:
        """Handle E key: rotate current unit clockwise."""
        if not self.battle_screen.pause_menu.visible:
            self.battle_screen._rotate_current_unit(1)
