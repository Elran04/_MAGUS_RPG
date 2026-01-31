"""
Input handling for battle screen.

Centralizes all keyboard and mouse input processing, translating user actions
into battle commands and delegating to appropriate coordinators.
"""

import pygame
from config import SIDEBAR_WIDTH
from domain.value_objects import Position
from infrastructure.rendering.hex_grid import get_grid_bounds, pixel_to_hex
from logger.logger import get_logger

logger = get_logger(__name__)


class BattleInputHandler:
    """Centralized input handler for battle screen.

    Routes all keyboard and mouse events to appropriate handlers and coordinators.
    Maintains input state (hovered hex, etc.) and coordinates input flow.
    """

    def __init__(self, battle_screen=None):
        """Initialize input handler.

        Args:
            battle_screen: Reference to BattleScreen for access to coordinators
        """
        self.battle_screen = battle_screen
        self.hovered_hex: tuple[int, int] | None = None

    def translate_mouse_to_play_area(self, mouse_pos: tuple[int, int]) -> tuple[int, int]:
        """Translate screen mouse coordinates to play area coordinates.

        Args:
            mouse_pos: Mouse position in screen coordinates

        Returns:
            Mouse position in play area coordinates (offset by sidebar)
        """
        return (mouse_pos[0] - SIDEBAR_WIDTH, mouse_pos[1])

    def update_hovered_hex(self, mouse_pos: tuple[int, int]) -> tuple[int, int] | None:
        """Update hovered hex from mouse position.

        Args:
            mouse_pos: Mouse position (x, y) in screen coordinates

        Returns:
            Updated hovered hex (q, r) or None
        """
        # Translate to play area coordinates
        play_pos = self.translate_mouse_to_play_area(mouse_pos)
        q, r = pixel_to_hex(*play_pos)
        min_q, max_q, min_r, max_r = get_grid_bounds()

        if min_q <= q < max_q and min_r <= r < max_r:
            self.hovered_hex = (q, r)
            return self.hovered_hex
        else:
            self.hovered_hex = None
            return None

    def is_click_in_play_area(self, mouse_pos: tuple[int, int]) -> bool:
        """Check if mouse click is in play area (not on sidebar).

        Args:
            mouse_pos: Mouse position in screen coordinates

        Returns:
            True if click is in play area
        """
        return mouse_pos[0] >= SIDEBAR_WIDTH

    def handle_event(self, event: pygame.event.Event) -> None:
        """Route pygame events to appropriate handlers.

        Args:
            event: Pygame event
        """
        if event.type == pygame.KEYDOWN:
            self.handle_keypress(event.key)
        elif event.type == pygame.MOUSEMOTION:
            self.handle_mouse_motion(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.handle_mouse_click(event.button, event.pos)

    # --- Public input routing methods ---

    def handle_keypress(self, key: int) -> None:
        """Route keyboard input to keyboard handler.

        Args:
            key: Pygame key constant
        """
        if not self.battle_screen:
            return
        self.battle_screen.keyboard_handler.handle_keypress(key)

    def handle_mouse_motion(self, mouse_pos: tuple[int, int]) -> None:
        """Handle mouse movement.

        Args:
            mouse_pos: Mouse position in screen coordinates
        """
        if not self.battle_screen:
            return

        # Update UI hover states
        self.battle_screen.pause_menu.handle_mouse_motion(mouse_pos)
        self.battle_screen.action_panel.handle_mouse_motion(mouse_pos)
        if self.battle_screen.reaction_popup:
            self.battle_screen.reaction_popup.handle_mouse_motion(mouse_pos)

        # Handle play area mouse motion (hover preview)
        if not self.battle_screen.pause_menu.visible:
            hovered = self.update_hovered_hex(mouse_pos)
            if hovered:
                # Auto-switch action mode based on what's hovered (disabled during special attacks or explicit mode selection)
                if self.battle_screen._active_special_attack is None and not self.battle_screen._action_mode_explicitly_set:
                    hovered_unit = self.battle_screen.battle.get_unit_at_hex(*hovered)
                    current_unit = self.battle_screen.battle.current_unit
                    if (
                        hovered_unit
                        and current_unit
                        and self.battle_screen.battle.is_enemy(current_unit, hovered_unit)
                    ):
                        # Hovering over enemy unit -> Attack mode
                        if self.battle_screen.action_mode.value != "attack":  # Check using enum
                            from presentation.screens.game.battle.battle_action_mode_manager import (
                                ActionMode,
                            )
                            self.battle_screen.action_mode = ActionMode.ATTACK
                    else:
                        # Hovering over empty tile or friendly unit -> Move mode
                        if self.battle_screen.action_mode.value != "move":  # Check using enum
                            from presentation.screens.game.battle.battle_action_mode_manager import (
                                ActionMode,
                            )
                            self.battle_screen.action_mode = ActionMode.MOVE

                from presentation.screens.game.battle.battle_action_mode_manager import ActionMode
                if self.battle_screen.action_mode == ActionMode.MOVE:
                    self.battle_screen._update_movement_path_preview(*hovered)
                else:
                    self.battle_screen.movement_path = None
            else:
                self.battle_screen.movement_path = None

    def handle_mouse_click(self, button: int, mouse_pos: tuple[int, int]) -> None:
        """Route mouse clicks to appropriate handlers.

        Args:
            button: Mouse button (1=left, 3=right)
            mouse_pos: Mouse position in screen coordinates
        """
        if not self.battle_screen:
            return

        if button != 1 and button != 3:  # Only handle left/right click
            return

        # Check pause menu clicks first (if visible)
        if self._handle_pause_menu_click(button, mouse_pos):
            return

        # Block all game clicks if paused
        if self.battle_screen.pause_menu.visible:
            return

        # Handle reaction popup clicks
        if self._handle_reaction_popup_click(mouse_pos):
            return

        # Check action panel clicks
        if button == 1 and self._handle_action_panel_click(mouse_pos):
            return

        # Handle unit popup clicks
        if self._handle_unit_popup_click(mouse_pos):
            return

        # Handle weapon switch popup clicks
        if self._handle_weapon_switch_popup_click(mouse_pos):
            return

        # Handle battle log popup
        if self._handle_battle_log_click(button, mouse_pos):
            return

        # Handle play area clicks
        if not self.is_click_in_play_area(mouse_pos):
            return

        if button == 1:
            self._handle_play_area_left_click()
        elif button == 3:
            self._handle_play_area_right_click()

    # --- Private popup/UI click handlers ---

    def _handle_pause_menu_click(self, button: int, mouse_pos: tuple[int, int]) -> bool:
        """Handle pause menu clicks; returns True if handled."""
        if self.battle_screen.pause_menu.visible and button == 1:
            action = self.battle_screen.pause_menu.handle_click(mouse_pos)
            if action == "continue":
                self.battle_screen.pause_menu.hide()
            elif action == "exit_to_menu":
                self.battle_screen.action = "battle_cancelled"
                logger.info("Exiting to main menu from pause menu")
            return True
        return False

    def _handle_reaction_popup_click(self, mouse_pos: tuple[int, int]) -> bool:
        """Handle reaction popup clicks; returns True if handled."""
        if self.battle_screen.reaction_popup and self.battle_screen.reaction_popup.visible:
            action = self.battle_screen.reaction_popup.handle_click(mouse_pos)
            if action:  # Accept or Decline
                return True
            # Check if click outside popup
            if self.battle_screen.reaction_popup.is_click_outside(mouse_pos):
                self.battle_screen.reaction_popup.handle_click(mouse_pos)  # Will call decline via callback
                return True
            return True
        return False

    def _handle_action_panel_click(self, mouse_pos: tuple[int, int]) -> bool:
        """Handle action panel clicks; returns True if handled."""
        try:
            action = self.battle_screen.action_panel.handle_click(mouse_pos)
            if action:
                logger.debug(f"Action panel returned action: {action}")
                self._handle_action_button(action)
                return True

            if self.battle_screen.action_panel.is_message_area_click(mouse_pos[0], mouse_pos[1]):
                self.battle_screen.battle_log_popup.show()
                return True

            return False
        except Exception as e:
            logger.error(f"Error in _handle_action_panel_click: {e}", exc_info=True)
            return False

    def _handle_unit_popup_click(self, mouse_pos: tuple[int, int]) -> bool:
        """Handle unit popup clicks; returns True if handled."""
        if self.battle_screen.unit_popup and self.battle_screen.unit_popup.visible:
            if self.battle_screen.unit_popup.handle_click(*mouse_pos):
                return True
            if self.battle_screen.unit_popup.is_click_outside(*mouse_pos):
                self.battle_screen.unit_popup.hide()
                return True
        return False

    def _handle_weapon_switch_popup_click(self, mouse_pos: tuple[int, int]) -> bool:
        """Handle weapon switch popup clicks; returns True if handled."""
        if self.battle_screen.weapon_switch_popup and self.battle_screen.weapon_switch_popup.visible:
            action, new_main, new_off = self.battle_screen.weapon_switch_popup.handle_click(*mouse_pos)
            if action == "cancel":
                self.battle_screen.weapon_switch_popup.hide()
                return True
            elif action == "apply":
                self._apply_weapon_switch(new_main, new_off)
                return True
            # Check if click outside popup
            if self.battle_screen.weapon_switch_popup.is_click_outside(*mouse_pos):
                self.battle_screen.weapon_switch_popup.hide()
                return True
            # If no action, click was inside popup but not on buttons
            return True
        return False

    def _handle_battle_log_click(self, button: int, mouse_pos: tuple[int, int]) -> bool:
        """Handle battle log popup clicks; returns True if handled."""
        if self.battle_screen.battle_log_popup and self.battle_screen.battle_log_popup.visible:
            return self.battle_screen.battle_log_popup.handle_event(
                pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": button, "pos": mouse_pos})
            )
        return False

    # --- Private play area click handlers ---

    def _handle_play_area_left_click(self) -> None:
        """Handle left click in play area."""
        hovered_hex = self.hovered_hex
        if not hovered_hex:
            return

        q, r = hovered_hex
        current = self.battle_screen.battle.current_unit
        target_pos = Position(q, r)

        from presentation.screens.game.battle.battle_action_mode_manager import ActionMode

        if self.battle_screen.action_mode == ActionMode.MOVE:
            is_valid, error_msg = self.battle_screen.battle.validate_move_target(current, target_pos)
            if is_valid:
                self.battle_screen._execute_move(target_pos)
            else:
                self.battle_screen.action_executor.show_message(error_msg)

        elif self.battle_screen.action_mode == ActionMode.ATTACK:
            self._handle_attack_click(current, target_pos)

        elif self.battle_screen.action_mode == ActionMode.INSPECT or self.battle_screen.action_mode == ActionMode.IDLE:
            # Try facing change if adjacent, otherwise inspect hex
            if current and self.battle_screen.action_executor.execute_facing_change(q, r, current):
                self.battle_screen._check_victory()
            else:
                self.battle_screen._inspect_hex(q, r)

    def _handle_attack_click(self, current, target_pos: Position) -> None:
        """Handle attack mode click in the play area."""
        special_handlers = {
            "charge": (self.battle_screen.battle.validate_charge_target, self.battle_screen._execute_charge),
            "dagger_combo": (
                self.battle_screen.battle.validate_attack_combination_target,
                self.battle_screen._execute_dagger_combo,
            ),
            "shield_bash": (self.battle_screen.battle.validate_shield_bash_target, self.battle_screen._execute_shield_bash),
        }

        if self.battle_screen._active_special_attack in special_handlers:
            validate_fn, execute_fn = special_handlers[self.battle_screen._active_special_attack]
            is_valid, error_msg = validate_fn(current, target_pos)
            if is_valid:
                execute_fn(target_pos)
            else:
                self.battle_screen.action_executor.show_message(error_msg)
            # Exit special mode after an attempt
            self.battle_screen._active_special_attack = None
            return

        is_valid, error_msg = self.battle_screen.battle.validate_attack_target(current, target_pos)
        if is_valid:
            self.battle_screen._execute_attack(target_pos)
        else:
            self.battle_screen.action_executor.show_message(error_msg)

    def _handle_play_area_right_click(self) -> None:
        """Handle right click in play area (quick inspect)."""
        hovered_hex = self.hovered_hex
        if hovered_hex:
            self.battle_screen._inspect_hex(*hovered_hex)

    # --- Private action button handler ---

    def _handle_action_button(self, action: str) -> None:
        """Handle action button click from the action panel.

        Args:
            action: Action name (e.g., "move", "attack", "end_turn", "special_attack_charge")
        """
        try:
            from presentation.screens.game.battle.battle_action_mode_manager import ActionMode

            # Check if clicking same action to deselect (toggle behavior)
            if action == "move":
                if self.battle_screen.action_mode == ActionMode.MOVE:
                    self.battle_screen._cancel_action()
                else:
                    self.battle_screen._enter_move_mode()
            elif action == "attack":
                if self.battle_screen.action_mode == ActionMode.ATTACK and self.battle_screen._active_special_attack is None:
                    self.battle_screen._cancel_action()
                else:
                    self.battle_screen._enter_attack_mode()
            elif action == "special_attack_charge":
                if self.battle_screen._active_special_attack == "charge":
                    self.battle_screen._cancel_action()
                else:
                    self.battle_screen._enter_charge_mode()
            elif action == "special_attack_dagger_combo":
                if self.battle_screen._active_special_attack == "dagger_combo":
                    self.battle_screen._cancel_action()
                else:
                    self.battle_screen._enter_dagger_combo_mode()
            elif action == "special_attack_shield_bash":
                if self.battle_screen._active_special_attack == "shield_bash":
                    self.battle_screen._cancel_action()
                else:
                    self.battle_screen._enter_shield_bash_mode()
            elif action == "switch_weapon":
                self._open_weapon_switch_popup()
            elif action == "inspect":
                if self.battle_screen.action_mode == ActionMode.INSPECT:
                    self.battle_screen._cancel_action()
                else:
                    self.battle_screen._enter_inspect_mode()
            elif action == "rotate_ccw":
                self.battle_screen._rotate_current_unit(-1)
            elif action == "rotate_cw":
                self.battle_screen._rotate_current_unit(1)
            elif action == "end_turn":
                self.battle_screen._end_current_turn()
            else:
                logger.warning(f"Unknown action: {action}")
        except Exception as e:
            logger.error(f"Error handling action '{action}': {e}", exc_info=True)

    def _open_weapon_switch_popup(self) -> None:
        """Open weapon switch popup for current unit."""
        if self.battle_screen.battle.is_victory():
            return

        self.battle_screen._active_special_attack = None

        current = self.battle_screen.battle.current_unit
        if not current:
            self.battle_screen.action_executor.show_message("No active unit")
            return

        if not self.battle_screen.weapon_switch_popup:
            from presentation.components.weapon_switch_popup import WeaponSwitchPopup
            self.battle_screen.weapon_switch_popup = WeaponSwitchPopup(context=self.battle_screen.context)
            # Update popup_manager reference when popup is created
            self.battle_screen.popup_manager.weapon_switch_popup = self.battle_screen.weapon_switch_popup

        self.battle_screen.weapon_switch_popup.show(current)

    def _apply_weapon_switch(self, new_main_hand: str | None, new_off_hand: str | None) -> None:
        """Apply weapon switch selection.

        Args:
            new_main_hand: New main hand weapon ID
            new_off_hand: New off hand weapon ID
        """
        current = self.battle_screen.battle.current_unit
        if not current:
            self.battle_screen.action_executor.show_message("No active unit")
            return

        # Execute the weapon switch
        result = self.battle_screen.action_executor.execute_weapon_switch(current, new_main_hand, new_off_hand)

        if "error" not in result:
            self.battle_screen.weapon_switch_popup.hide()
            self.battle_screen._check_victory()
        # If error, message is already shown by action_executor
