"""
Popup management for battle screen.

Coordinates display and interaction of popups (unit info, weapon switch, battle log, reactions).
"""

import pygame
from logger.logger import get_logger

logger = get_logger(__name__)


class BattlePopupManager:
    """Manages popup visibility and click handling."""

    def __init__(self):
        """Initialize popup manager."""
        self.unit_popup = None
        self.weapon_switch_popup = None
        self.battle_log_popup = None
        self.reaction_popup = None

    def set_popups(
        self, unit_popup, weapon_switch_popup, battle_log_popup, reaction_popup
    ) -> None:
        """Set popup references.

        Args:
            unit_popup: UnitInfoPopup instance
            weapon_switch_popup: WeaponSwitchPopup instance
            battle_log_popup: BattleLogPopup instance
            reaction_popup: ReactionPopup instance
        """
        self.unit_popup = unit_popup
        self.weapon_switch_popup = weapon_switch_popup
        self.battle_log_popup = battle_log_popup
        self.reaction_popup = reaction_popup

    def handle_unit_popup_click(self, mouse_pos: tuple[int, int]) -> bool:
        """Handle unit popup clicks; returns True if handled."""
        if self.unit_popup and self.unit_popup.visible:
            if self.unit_popup.handle_click(*mouse_pos):
                return True
            if self.unit_popup.is_click_outside(*mouse_pos):
                self.unit_popup.hide()
                return True
        return False

    def handle_weapon_switch_popup_click(
        self, mouse_pos: tuple[int, int]
    ) -> tuple[bool, str | None, str | None, str | None]:
        """Handle weapon switch popup clicks.

        Returns:
            (handled, action, new_main, new_off) tuple
        """
        if self.weapon_switch_popup and self.weapon_switch_popup.visible:
            action, new_main, new_off = self.weapon_switch_popup.handle_click(*mouse_pos)
            if action == "cancel":
                self.weapon_switch_popup.hide()
                return (True, "cancel", None, None)
            elif action == "apply":
                return (True, "apply", new_main, new_off)
            # Check if click outside popup
            if self.weapon_switch_popup.is_click_outside(*mouse_pos):
                self.weapon_switch_popup.hide()
                return (True, "outside", None, None)
            # If no action, click was inside popup but not on buttons
            return (True, "inside", None, None)
        return (False, None, None, None)

    def handle_battle_log_click(self, button: int, mouse_pos: tuple[int, int]) -> bool:
        """Handle battle log popup clicks; returns True if handled."""
        if self.battle_log_popup and self.battle_log_popup.visible:
            return self.battle_log_popup.handle_event(
                pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": button, "pos": mouse_pos})
            )
        return False

    def handle_reaction_popup_click(self, mouse_pos: tuple[int, int]) -> bool:
        """Handle reaction popup clicks; returns True if handled."""
        if self.reaction_popup and self.reaction_popup.visible:
            action = self.reaction_popup.handle_click(mouse_pos)
            if action:  # Accept or Decline
                return True
            # Check if click outside popup
            if self.reaction_popup.is_click_outside(mouse_pos):
                self.reaction_popup.handle_click(mouse_pos)  # Will call decline via callback
                return True
            return True
        return False

    def show_unit_info(self, unit, context) -> None:
        """Show unit info popup.

        Args:
            unit: Unit to display
            context: GameContext for data access
        """
        if not self.unit_popup:
            from presentation.components.unit_info.unit_info_popup import UnitInfoPopup

            self.unit_popup = UnitInfoPopup(context=context)
        self.unit_popup.show(unit)

    def show_weapon_switch(self, unit, context) -> None:
        """Show weapon switch popup.

        Args:
            unit: Unit to switch weapons
            context: GameContext for data access
        """
        if not self.weapon_switch_popup:
            from presentation.components.weapon_switch_popup import WeaponSwitchPopup

            self.weapon_switch_popup = WeaponSwitchPopup(context=context)
        self.weapon_switch_popup.show(unit)

    def show_battle_log(self) -> None:
        """Show battle log popup."""
        if self.battle_log_popup:
            self.battle_log_popup.show()

    def close_all(self) -> None:
        """Close all open popups."""
        if self.unit_popup and self.unit_popup.visible:
            self.unit_popup.hide()
        if self.weapon_switch_popup and self.weapon_switch_popup.visible:
            self.weapon_switch_popup.hide()
        if self.battle_log_popup and self.battle_log_popup.visible:
            self.battle_log_popup.hide()
        if self.reaction_popup and self.reaction_popup.visible:
            self.reaction_popup.hide()

    def any_visible(self) -> bool:
        """Check if any popup is currently visible.

        Returns:
            True if any popup is visible
        """
        return (
            (self.unit_popup and self.unit_popup.visible)
            or (self.weapon_switch_popup and self.weapon_switch_popup.visible)
            or (self.battle_log_popup and self.battle_log_popup.visible)
            or (self.reaction_popup and self.reaction_popup.visible)
        )
