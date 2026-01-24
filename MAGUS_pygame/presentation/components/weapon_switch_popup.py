"""
Weapon switching popup for battle screen.

Displays equipped weapons and quickslot weapons, allowing player to swap between them.
"""

import pygame
from config import HEIGHT, UI_ACTIVE, UI_BORDER, UI_INACTIVE, UI_TEXT, WIDTH
from domain.entities import Unit
from domain.value_objects.weapon_type_check import (
    is_one_handed_weapon,
    is_ranged_weapon,
    is_shield,
    is_two_handed_weapon,
)
from logger.logger import get_logger

logger = get_logger(__name__)


class WeaponSlotButton:
    """Represents a clickable weapon slot."""

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        slot_name: str,
        weapon_id: str,
        weapon_name: str,
        weapon_type: str = "",
    ):
        """Initialize weapon slot button.

        Args:
            x: X position
            y: Y position
            width: Button width
            height: Button height
            slot_name: Slot identifier (main_hand, off_hand, weapon_quick_1, weapon_quick_2)
            weapon_id: Weapon ID from equipment
            weapon_name: Display name for the weapon
            weapon_type: Type label (1h, 2h, Shield, Ranged, Variable) - empty if weapon slot is empty
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.slot_name = slot_name
        self.weapon_id = weapon_id
        self.weapon_name = weapon_name if weapon_id else "(empty)"
        self.weapon_type = weapon_type if weapon_id else ""
        self.selected = False
        self.hovered = False
        self.is_empty = not weapon_id

    def update_hover(self, mouse_pos: tuple[int, int]) -> None:
        """Update hover state based on mouse position."""
        self.hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, mouse_pos: tuple[int, int]) -> bool:
        """Check if slot was clicked."""
        return self.rect.collidepoint(mouse_pos)

    def draw(
        self, surface: pygame.Surface, font: pygame.font.Font, small_font: pygame.font.Font
    ) -> None:
        """Draw the weapon slot button.

        Args:
            surface: Pygame surface to draw on
            font: Font for weapon name
            small_font: Font for weapon type label
        """
        # Determine color based on state
        if self.selected:
            bg_color = (60, 100, 140)
            border_color = (100, 180, 255)
            border_width = 3
        elif self.hovered:
            # Give hover feedback even on empty slots
            bg_color = (35, 35, 45) if self.is_empty else (40, 40, 50)
            border_color = (110, 110, 130)
            border_width = 2
        else:
            bg_color = UI_INACTIVE
            border_color = UI_BORDER
            border_width = 1

        # Draw button background
        pygame.draw.rect(surface, bg_color, self.rect, border_radius=5)
        pygame.draw.rect(surface, border_color, self.rect, border_width, border_radius=5)

        # Draw weapon name
        text_color = UI_TEXT if not self.is_empty else (100, 100, 100)
        label_surface = font.render(self.weapon_name, True, text_color)
        label_rect = label_surface.get_rect(center=(self.rect.centerx, self.rect.centery - 8))
        surface.blit(label_surface, label_rect)

        # Draw weapon type label below weapon name
        if self.weapon_type:
            type_color = (150, 200, 100) if not self.is_empty else (80, 80, 80)
            type_surface = small_font.render(self.weapon_type, True, type_color)
            type_rect = type_surface.get_rect(center=(self.rect.centerx, self.rect.centery + 12))
            surface.blit(type_surface, type_rect)


class WeaponSwitchPopup:
    """
    Popup window for switching weapons.

    Shows equipped weapons (main_hand, off_hand) and quickslot weapons,
    allowing player to reassign them at 5 AP cost.
    """

    SLOT_CONFIGS = (
        ("main_hand", "Main Hand"),
        ("off_hand", "Off Hand"),
        ("weapon_quick_1", "Quick Slot 1"),
        ("weapon_quick_2", "Quick Slot 2"),
        ("weapon_quick_3", "Quick Slot 3"),
        ("weapon_quick_4", "Quick Slot 4"),
    )

    STASH_SLOTS = {
        "weapon_quick_1",
        "weapon_quick_2",
        "weapon_quick_3",
        "weapon_quick_4",
    }

    EQUIPPED_SLOTS = {"main_hand", "off_hand"}

    def __init__(self, context=None):
        """Initialize weapon switch popup.

        Args:
            context: Game context for equipment repository access
        """
        self.visible = False
        self.unit: Unit | None = None
        self.context = context

        # Popup dimensions (larger to accommodate 6 slots)
        self.width = 550
        self.height = 500
        self.popup_rect: pygame.Rect | None = None

        # Fonts
        self.title_font = pygame.font.Font(None, 32)
        self.header_font = pygame.font.Font(None, 26)
        self.text_font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 20)

        # Weapon slots and buttons
        self.weapon_slots: dict[str, WeaponSlotButton] = {}
        self.cancel_button_rect: pygame.Rect | None = None
        self.apply_button_rect: pygame.Rect | None = None

        # Selection state - track which slot is selected for swapping
        self.selected_slot: str | None = None

        # Pending weapon assignments (what will be in each slot after apply)
        self.pending_weapons: dict[str, str] = {}  # slot_name -> weapon_id

        # Original state (for cancel and change detection)
        self.original_weapons: dict[str, str] = {}

    def show(self, unit: Unit) -> None:
        """Show popup for weapon switching.

        Args:
            unit: Unit whose weapons will be switched
        """
        self.visible = True
        self.unit = unit
        self.selected_slot = None

        equipment = self._get_or_initialize_equipment(unit)
        self.original_weapons = {slot: equipment.get(slot, "") for slot, _ in self.SLOT_CONFIGS}
        self.pending_weapons = dict(self.original_weapons)

        logger.debug(f"Showing weapon switch popup for {unit.name}")

    def hide(self) -> None:
        """Hide the popup without applying changes."""
        self.visible = False
        self.unit = None
        self.selected_slot = None
        self.pending_weapons = {}

    def has_changes(self) -> bool:
        """Check if any weapon assignments have changed."""
        return self.pending_weapons != self.original_weapons

    def get_weapon_name(self, weapon_id: str) -> str:
        """Get display name for a weapon ID.

        Args:
            weapon_id: Weapon ID from equipment

        Returns:
            Display name or weapon ID if not found
        """
        if not weapon_id:
            return ""

        if self.context and hasattr(self.context, "equipment_repo"):
            weapon_data = self.context.equipment_repo.find_weapon_by_id(weapon_id)
            if weapon_data:
                return weapon_data.get("name", weapon_id)

        return weapon_id

    def _get_or_initialize_equipment(self, unit: Unit) -> dict[str, str]:
        """Ensure all expected slots exist on the unit equipment."""
        empty_equipment = {slot: "" for slot, _ in self.SLOT_CONFIGS}
        if not unit.character_data or "equipment" not in unit.character_data:
            return empty_equipment

        equipment = unit.character_data["equipment"]
        for slot, _ in self.SLOT_CONFIGS:
            equipment.setdefault(slot, "")
        return equipment

    def get_weapon_type_label(self, weapon_id: str, slot_name: str) -> str:
        """Get weapon type label (1h, 2h, Shield, Ranged, Variable with current mode).

        Args:
            weapon_id: Weapon ID from equipment
            slot_name: Slot this weapon is displayed in (needed to infer current mode for variable wield)

        Returns:
            Type label string (e.g., "1h", "2h", "Shield", "1h/2h (current 1h)") or empty string if not found
        """
        if not weapon_id:
            return ""

        if not self.context or not hasattr(self.context, "equipment_repo"):
            return ""

        weapon_data = self.context.equipment_repo.find_weapon_by_id(weapon_id)
        if not weapon_data:
            return ""

        mode_raw = (weapon_data.get("wield_mode") or "").strip().lower()
        is_variable = mode_raw in ["változó", "valtozo", "variable", "1h/2h"]

        # Variable wield: show both modes and highlight current based on off-hand occupancy
        if is_variable:
            label = "1h/2h"
            # Infer current mode only when shown in main hand slot; quickslots just show base
            if slot_name == "main_hand":
                offhand_item = self.pending_weapons.get("off_hand", "")
                current = "1h" if offhand_item else "2h"
                label = f"{label} (current {current})"
            return label

        # Non-variable: use existing helpers
        if is_shield(weapon_data):
            return "Shield"
        if is_two_handed_weapon(weapon_data):
            return "2h"
        if is_one_handed_weapon(weapon_data):
            return "1h"
        if is_ranged_weapon(weapon_data):
            return "Ranged"
        return ""

    def handle_click(self, mx: int, my: int) -> tuple[str | None, str | None, str | None]:
        """Handle click within popup.

        Returns:
            Tuple of (action, new_main_hand, new_off_hand):
            - action: "cancel", "apply", or None
            - new_main_hand: New main hand weapon ID (if applying)
            - new_off_hand: New off hand weapon ID (if applying)
        """
        if not self.visible:
            return (None, None, None)

        # Check cancel button
        if self.cancel_button_rect and self.cancel_button_rect.collidepoint(mx, my):
            return ("cancel", None, None)

        # Check apply button (only if changes were made)
        if self.apply_button_rect and self.apply_button_rect.collidepoint(mx, my):
            if self.has_changes():
                return (
                    "apply",
                    self.pending_weapons.get("main_hand"),
                    self.pending_weapons.get("off_hand"),
                )
            return (None, None, None)  # No changes, ignore click

        # Check weapon slot clicks - swap selected slot with clicked slot
        for slot_name, slot_button in self.weapon_slots.items():
            if slot_button.is_clicked((mx, my)):
                # Only allow selecting non-empty slots
                weapon_in_slot = self.pending_weapons.get(slot_name, "")

                if self.selected_slot is None:
                    # First click - select this slot if not empty
                    if weapon_in_slot:
                        self.selected_slot = slot_name
                        logger.debug(f"Selected slot: {slot_name}")
                    return (None, None, None)

                elif self.selected_slot == slot_name:
                    # Click same slot again - deselect
                    self.selected_slot = None
                    logger.debug(f"Deselected slot: {slot_name}")
                    return (None, None, None)

                else:
                    # Swap: validate if weapon from selected_slot can go into target slot
                    selected_weapon = self.pending_weapons.get(self.selected_slot, "")
                    clicked_weapon = self.pending_weapons.get(slot_name, "")

                    # Validate swap is allowed based on weapon type and slot compatibility
                    if not self._is_swap_valid(
                        self.selected_slot, slot_name, selected_weapon, clicked_weapon
                    ):
                        logger.debug(f"Invalid swap: {self.selected_slot} → {slot_name}")
                        return (None, None, None)

                    # Valid swap - execute it
                    self.pending_weapons[self.selected_slot] = clicked_weapon
                    self.pending_weapons[slot_name] = selected_weapon

                    logger.debug(
                        f"Swapped {self.selected_slot} ({selected_weapon or 'empty'}) ↔ {slot_name} ({clicked_weapon or 'empty'})"
                    )
                    self.selected_slot = None
                    return (None, None, None)

        return (None, None, None)

    def _is_swap_valid(
        self, from_slot: str, to_slot: str, weapon_to_move: str, weapon_in_target: str
    ) -> bool:
        """Validate if swapping weapon between slots is allowed.

        Args:
            from_slot: Source slot name
            to_slot: Target slot name
            weapon_to_move: Weapon ID being moved
            weapon_in_target: Weapon ID in target slot

        Returns:
            True if swap is valid, False otherwise
        """
        if not self.unit or not self.context:
            return True  # No validation possible, allow
        if not hasattr(self.context, "equipment_validation_service"):
            return True  # No validation service, allow

        validation_service = self.context.equipment_validation_service

        # Build a simulated equipment state after swap to determine wield mode for variable weapons
        simulated = dict(self.pending_weapons)
        simulated[from_slot] = weapon_in_target
        simulated[to_slot] = weapon_to_move

        # Helper to decide selected_wield_mode for a weapon entering a slot (only relevant for main hand variable weapons)
        def _selected_wield_mode(slot: str, weapon_id: str) -> str | None:
            if slot != "main_hand" or not weapon_id:
                return None
            if not hasattr(self.context, "equipment_repo"):
                return None
            weapon_data = self.context.equipment_repo.find_weapon_by_id(weapon_id)
            if not weapon_data:
                return None
            mode_raw = (weapon_data.get("wield_mode") or "").strip().lower()
            is_variable = mode_raw in ["változó", "valtozo", "variable", "1h/2h"]
            if not is_variable:
                return None
            # If off-hand occupied after swap, variable weapon must be in 1h mode, otherwise 2h
            offhand_item = simulated.get("off_hand", "")
            return "one_handed" if offhand_item else "two_handed"

        offhand_after_swap = simulated.get("off_hand", "")
        validate_target = to_slot in self.EQUIPPED_SLOTS
        validate_source = from_slot in self.EQUIPPED_SLOTS

        # Hard guard only when equipping to main hand (skip variable weapons; they can be 1h)
        if validate_target and to_slot == "main_hand" and weapon_to_move and offhand_after_swap:
            weapon_data = (
                self.context.equipment_repo.find_weapon_by_id(weapon_to_move)
                if hasattr(self.context, "equipment_repo")
                else None
            )
            if weapon_data:
                mode_raw = (weapon_data.get("wield_mode") or "").strip().lower()
                is_variable = mode_raw in ["változó", "valtozo", "variable", "1h/2h"]
                if not is_variable and (
                    is_two_handed_weapon(weapon_data) or is_ranged_weapon(weapon_data)
                ):
                    logger.debug(
                        f"Invalid: {weapon_to_move} cannot be main hand while off-hand occupied"
                    )
                    return False

        # Validate weapon_to_move into target slot (skip if target is stash); allow variable 1h/2h
        if validate_target and weapon_to_move:
            weapon_data = (
                self.context.equipment_repo.find_weapon_by_id(weapon_to_move)
                if hasattr(self.context, "equipment_repo")
                else None
            )
            mode_raw = (weapon_data.get("wield_mode") or "").strip().lower() if weapon_data else ""
            is_variable = mode_raw in ["változó", "valtozo", "variable", "1h/2h"]
            if not is_variable:
                selected_wield = _selected_wield_mode(to_slot, weapon_to_move)
                result = validation_service.is_item_eligible(
                    self.unit, to_slot, weapon_to_move, selected_wield_mode=selected_wield
                )
                if not result.success:
                    logger.debug(
                        f"Invalid: {weapon_to_move} cannot go in {to_slot}: {result.message}"
                    )
                    return False

        # Reverse guard only when source is an equipped slot
        if validate_source and from_slot == "main_hand" and weapon_in_target and offhand_after_swap:
            weapon_data = (
                self.context.equipment_repo.find_weapon_by_id(weapon_in_target)
                if hasattr(self.context, "equipment_repo")
                else None
            )
            if weapon_data:
                mode_raw = (weapon_data.get("wield_mode") or "").strip().lower()
                is_variable = mode_raw in ["változó", "valtozo", "variable", "1h/2h"]
                if not is_variable and (
                    is_two_handed_weapon(weapon_data) or is_ranged_weapon(weapon_data)
                ):
                    logger.debug(
                        f"Invalid: {weapon_in_target} cannot be main hand while off-hand occupied"
                    )
                    return False

        # Validate weapon_in_target into source slot (skip if source is stash)
        if validate_source and weapon_in_target:
            selected_wield = _selected_wield_mode(from_slot, weapon_in_target)
            result = validation_service.is_item_eligible(
                self.unit, from_slot, weapon_in_target, selected_wield_mode=selected_wield
            )
            if not result.success:
                logger.debug(
                    f"Invalid: {weapon_in_target} cannot go in {from_slot}: {result.message}"
                )
                return False

        return True

    def is_click_outside(self, mx: int, my: int) -> bool:
        """Check if click was outside popup bounds."""
        if not self.visible or not self.popup_rect:
            return False
        return not self.popup_rect.collidepoint(mx, my)

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the weapon switch popup on screen."""
        if not self.visible or not self.unit:
            return

        popup_x, popup_y = self._compute_popup_position()
        self._draw_overlay(screen)
        self._draw_popup_background(screen, popup_x, popup_y)

        padding = 20
        y_offset = self._draw_title(screen, popup_x, popup_y, padding)
        y_offset = self._draw_slots(screen, popup_x, padding, y_offset)
        self._draw_actions(screen, popup_x, popup_y, padding)

        instruction_text = self.small_font.render(
            "Click slots to select, then click another to swap", True, (150, 150, 150)
        )
        instruction_rect = instruction_text.get_rect(
            centerx=popup_x + self.width // 2, bottom=popup_y + self.height - padding - 55
        )
        screen.blit(instruction_text, instruction_rect)

    def _compute_popup_position(self) -> tuple[int, int]:
        popup_x = (WIDTH - self.width) // 2
        popup_y = (HEIGHT - self.height) // 2
        self.popup_rect = pygame.Rect(popup_x, popup_y, self.width, self.height)
        return popup_x, popup_y

    def _draw_overlay(self, screen: pygame.Surface) -> None:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

    def _draw_popup_background(self, screen: pygame.Surface, popup_x: int, popup_y: int) -> None:
        pygame.draw.rect(screen, (40, 40, 50), self.popup_rect, border_radius=10)
        pygame.draw.rect(screen, UI_BORDER, self.popup_rect, width=3, border_radius=10)

    def _draw_title(self, screen: pygame.Surface, popup_x: int, popup_y: int, padding: int) -> int:
        y_offset = popup_y + padding
        title_text = self.title_font.render("Switch Weapons", True, (255, 215, 0))
        title_rect = title_text.get_rect(centerx=popup_x + self.width // 2, top=y_offset)
        screen.blit(title_text, title_rect)
        return y_offset + 50

    def _draw_slots(self, screen: pygame.Surface, popup_x: int, padding: int, y_offset: int) -> int:
        self.weapon_slots = {}
        slot_width = self.width - 2 * padding - 40
        slot_height = 45
        slot_x = popup_x + padding + 20

        for slot_name, slot_label in self.SLOT_CONFIGS:
            weapon_id = self.pending_weapons.get(slot_name, "")
            weapon_name = self.get_weapon_name(weapon_id)
            weapon_type = self.get_weapon_type_label(weapon_id, slot_name)
            display_name = f"{slot_label}: {weapon_name if weapon_name else '(empty)'}"

            slot_button = WeaponSlotButton(
                slot_x,
                y_offset,
                slot_width,
                slot_height,
                slot_name,
                weapon_id,
                display_name,
                weapon_type,
            )
            slot_button.selected = self.selected_slot == slot_name
            slot_button.update_hover(pygame.mouse.get_pos())
            slot_button.draw(screen, self.text_font, self.small_font)
            self.weapon_slots[slot_name] = slot_button
            y_offset += slot_height + 8

        return y_offset + 10

    def _draw_actions(
        self, screen: pygame.Surface, popup_x: int, popup_y: int, padding: int
    ) -> None:
        button_width = 150
        button_height = 45
        button_y = popup_y + self.height - padding - button_height

        # Cancel button
        cancel_x = popup_x + padding
        self.cancel_button_rect = pygame.Rect(cancel_x, button_y, button_width, button_height)
        pygame.draw.rect(screen, UI_INACTIVE, self.cancel_button_rect, border_radius=5)
        pygame.draw.rect(screen, UI_BORDER, self.cancel_button_rect, width=2, border_radius=5)
        cancel_text = self.text_font.render("Cancel", True, UI_TEXT)
        cancel_rect = cancel_text.get_rect(center=self.cancel_button_rect.center)
        screen.blit(cancel_text, cancel_rect)

        # Apply button
        apply_x = popup_x + self.width - padding - button_width
        self.apply_button_rect = pygame.Rect(apply_x, button_y, button_width, button_height)

        has_changes = self.has_changes()
        apply_bg = UI_ACTIVE if has_changes else (30, 30, 40)
        apply_border = (100, 180, 255) if has_changes else (60, 60, 70)
        apply_text_color = UI_TEXT if has_changes else (80, 80, 90)

        pygame.draw.rect(screen, apply_bg, self.apply_button_rect, border_radius=5)
        pygame.draw.rect(screen, apply_border, self.apply_button_rect, width=2, border_radius=5)
        apply_text = self.text_font.render("Apply (5 AP)", True, apply_text_color)
        apply_rect = apply_text.get_rect(center=self.apply_button_rect.center)
        screen.blit(apply_text, apply_rect)
