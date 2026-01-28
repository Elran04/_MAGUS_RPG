"""
Battle Log Popup - Detailed view of combat events and history.

Shows comprehensive breakdown of all combat events including attack details,
movement, special actions, and all combat modifiers with round numbers.
"""

import pygame
from config import HEIGHT, UI_ACTIVE, UI_BORDER, UI_INACTIVE, UI_TEXT, WIDTH
from domain.battle_log_entry import BattleLogEntry
from domain.mechanics.attack_resolution import AttackOutcome
from logger.logger import get_logger

logger = get_logger(__name__)


class BattleLogPopup:
    """
    Popup window for displaying detailed battle log with full event breakdowns.

    Similar to UnitInfoPopup but focused on battle event history.
    """

    def __init__(self, battle_log):
        """Initialize battle log popup.

        Args:
            battle_log: DetailedBattleLog instance
        """
        self.battle_log = battle_log
        self.visible = False
        self.popup_rect: pygame.Rect | None = None
        self.scroll_offset = 0
        self.max_scroll = 0

        # Styling (matching unit info popup)
        self.width = 600
        self.height = 700
        self.border_radius = 10
        self.padding = 20
        self.bg_color = (40, 40, 50)
        self.overlay_alpha = 150

        # Fonts
        self.title_font = pygame.font.SysFont(None, 32, bold=True)
        self.header_font = pygame.font.SysFont(None, 24, bold=True)
        self.text_font = pygame.font.SysFont(None, 20)
        self.small_font = pygame.font.SysFont(None, 18)

        # Colors
        self.color_round = (255, 215, 0)
        self.color_turn = (100, 200, 255)
        self.color_attack = (255, 100, 100)
        self.color_move = (100, 255, 100)
        self.color_action = (255, 200, 100)
        self.color_modifier_positive = (100, 255, 100)
        self.color_modifier_negative = (255, 100, 100)

    def show(self) -> None:
        """Show the battle log popup."""
        self.visible = True
        self.scroll_offset = 0
        logger.debug("Battle log popup opened")

    def hide(self) -> None:
        """Hide the battle log popup."""
        self.visible = False
        logger.debug("Battle log popup closed")

    def handle_event(self, event: pygame.event) -> bool:
        """Handle input events for the popup.

        Args:
            event: Pygame event

        Returns:
            True if event was handled
        """
        if not self.visible:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos

            # Check if clicked outside to close
            if self.is_click_outside(mx, my):
                self.hide()
                return True

            # Handle scroll wheel
            if event.button == 4:  # Scroll up
                self.scroll_offset = max(0, self.scroll_offset - 30)
                return True
            elif event.button == 5:  # Scroll down
                self.scroll_offset = min(self.max_scroll, self.scroll_offset + 30)
                return True

        return False

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the popup on screen."""
        if not self.visible:
            return

        # Calculate popup position
        popup_x = (WIDTH - self.width) // 2
        popup_y = (HEIGHT - self.height) // 2
        self.popup_rect = pygame.Rect(popup_x, popup_y, self.width, self.height)

        # Semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, self.overlay_alpha))
        screen.blit(overlay, (0, 0))

        # Popup background
        pygame.draw.rect(screen, self.bg_color, self.popup_rect, border_radius=self.border_radius)
        pygame.draw.rect(screen, UI_BORDER, self.popup_rect, width=3, border_radius=self.border_radius)

        # Title
        title_text = self.title_font.render("Battle Log", True, self.color_round)
        screen.blit(title_text, (popup_x + self.padding, popup_y + 15))

        # Content area
        content_y = popup_y + 60
        content_height = self.height - 100
        content_rect = pygame.Rect(popup_x + self.padding, content_y,
                                   self.width - 2 * self.padding, content_height)

        # Create clipping surface for scrollable content
        clip_surface = screen.subsurface(content_rect)

        # Draw entries
        y_offset = -self.scroll_offset
        entries = self.battle_log.get_all_entries()

        for entry in reversed(entries):  # Newest first
            entry_height = self._draw_entry(clip_surface, entry, 0, y_offset)
            y_offset += entry_height + 15

        # Calculate max scroll
        total_content_height = y_offset + self.scroll_offset
        self.max_scroll = max(0, total_content_height - content_height)

        # Close instruction
        close_text = self.small_font.render("(Click outside or scroll to view history)", True, (150, 150, 150))
        close_rect = close_text.get_rect()
        close_rect.bottom = popup_y + self.height - 10
        close_rect.centerx = popup_x + self.width // 2
        screen.blit(close_text, close_rect)

    def _draw_entry(self, surface: pygame.Surface, entry: BattleLogEntry, x: int, y: int) -> int:
        """Draw a single log entry and return its height.

        Args:
            surface: Surface to draw on
            entry: Log entry to draw
            x: X position
            y: Y position

        Returns:
            Height of the drawn entry
        """
        if y + 100 < 0 or y > surface.get_height():  # Skip if off-screen
            return 50  # Estimate

        start_y = y

        # Entry type header
        if entry.entry_type == "initiative":
            color = (200, 200, 100)
            if entry.round_number == 0:
                header = "Initiative - Pre-Battle"
            else:
                header = f"Initiative - Round {entry.round_number}"
        elif entry.entry_type == "round_start":
            color = self.color_round
            header = f"Round {entry.round_number}"
        elif entry.entry_type == "turn_start":
            color = self.color_turn
            header = f"{entry.unit_name}'s Turn"
        elif entry.entry_type == "attack":
            color = self.color_attack
            header = f"Round {entry.round_number} - Attack"
        elif entry.entry_type == "move":
            color = self.color_move
            header = f"Round {entry.round_number} - Movement"
        elif entry.entry_type == "action":
            color = self.color_action
            header = f"Round {entry.round_number} - Action"
        else:
            color = UI_TEXT
            header = f"Round {entry.round_number}"

        header_text = self.header_font.render(header, True, color)
        surface.blit(header_text, (x + 5, y))
        y += 25

        # Draw details based on type
        if entry.entry_type == "initiative" and entry.initiative_data:
            y = self._draw_initiative_details(surface, entry.initiative_data, x, y)
        elif entry.entry_type == "attack" and entry.attack_data:
            y = self._draw_attack_details(surface, entry.attack_data, x, y)
        elif entry.entry_type == "move" and entry.move_data:
            y = self._draw_move_details(surface, entry.move_data, x, y)
        elif entry.entry_type == "action" and entry.action_data:
            y = self._draw_action_details(surface, entry.action_data, x, y)
        else:
            # Simple message
            msg_text = self.text_font.render(entry.message, True, UI_TEXT)
            surface.blit(msg_text, (x + 10, y))
            y += 20

        # Separator line
        pygame.draw.line(surface, (80, 80, 90), (x, y + 5), (x + surface.get_width() - 10, y + 5), 1)
        y += 10

        return y - start_y

    def _draw_attack_details(self, surface: pygame.Surface, attack: any, x: int, y: int) -> int:
        """Draw detailed attack breakdown."""
        # Attacker vs Defender
        vs_text = self.text_font.render(f"{attack.attacker_name} → {attack.defender_name}", True, (255, 255, 255))
        surface.blit(vs_text, (x + 10, y))
        y += 22

        # TÉ vs VÉ with roll
        te_ve_text = self.small_font.render(
            f"TÉ: {attack.all_te} (roll: {attack.attack_roll}) vs VÉ: {attack.all_ve}",
            True, UI_TEXT
        )
        surface.blit(te_ve_text, (x + 15, y))
        y += 20

        # Outcome
        outcome_str = attack.outcome.replace("_", " ").title()
        outcome_color = (255, 100, 100) if "CRITICAL" in attack.outcome else (200, 200, 200)
        outcome_text = self.small_font.render(f"Result: {outcome_str}", True, outcome_color)
        surface.blit(outcome_text, (x + 15, y))
        y += 20

        # Positional information
        if attack.is_flank_attack or attack.is_rear_attack:
            position_str = "Rear Attack" if attack.is_rear_attack else "Flank Attack"
            pos_text = self.small_font.render(f"• {position_str}", True, (255, 200, 100))
            surface.blit(pos_text, (x + 15, y))
            y += 18

        if attack.facing_ignored_ve:
            facing_text = self.small_font.render("• Shield/Weapon VÉ ignored (facing)", True, (255, 150, 150))
            surface.blit(facing_text, (x + 15, y))
            y += 18

        # Hit zone (always show if available)
        if attack.hit_zone:
            zone_text = self.small_font.render(f"Hit Zone: {attack.hit_zone} (SFÉ: {attack.zone_sfe})", True, UI_TEXT)
            surface.blit(zone_text, (x + 15, y))
            y += 18

        # Damage breakdown (show if any damage dealt)
        if attack.damage_to_fp > 0 or attack.damage_to_ep > 0:
            damage_parts = []
            if attack.damage_to_fp > 0:
                damage_parts.append(f"FP: -{attack.damage_to_fp}")
            if attack.damage_to_ep > 0:
                damage_parts.append(f"ÉP: -{attack.damage_to_ep}")
            if attack.mandatory_ep_loss > 0:
                damage_parts.append(f"ÉP(Weapon): -{attack.mandatory_ep_loss}")

            dmg_text = self.small_font.render(f"Damage: {', '.join(damage_parts)}", True, (255, 100, 100))
            surface.blit(dmg_text, (x + 15, y))
            y += 18

            if attack.armor_absorbed > 0:
                armor_text = self.small_font.render(f"Absorbed by armor: {attack.armor_absorbed}", True, (150, 150, 255))
                surface.blit(armor_text, (x + 20, y))
                y += 18

        # Stamina cost for defender (blocks, parries)
        if attack.stamina_spent_defender > 0:
            stamina_text = self.small_font.render(f"Defender Stamina: -{attack.stamina_spent_defender}", True, (100, 200, 255))
            surface.blit(stamina_text, (x + 15, y))
            y += 18

        # Attacker penalties/buffs
        if attack.attacker_penalties or attack.attacker_buffs:
            y += 3
            atk_mod_text = self.small_font.render("Attacker modifiers:", True, (200, 200, 150))
            surface.blit(atk_mod_text, (x + 15, y))
            y += 18

            for name, value in attack.attacker_penalties.items():
                color = self.color_modifier_negative
                mod_text = self.small_font.render(f"  {name}: {value}", True, color)
                surface.blit(mod_text, (x + 20, y))
                y += 16

            for name, value in attack.attacker_buffs.items():
                color = self.color_modifier_positive
                mod_text = self.small_font.render(f"  {name}: +{value}", True, color)
                surface.blit(mod_text, (x + 20, y))
                y += 16

        # Defender penalties/buffs
        if attack.defender_penalties or attack.defender_buffs:
            y += 3
            def_mod_text = self.small_font.render("Defender modifiers:", True, (200, 200, 150))
            surface.blit(def_mod_text, (x + 15, y))
            y += 18

            for name, value in attack.defender_penalties.items():
                color = self.color_modifier_negative
                mod_text = self.small_font.render(f"  {name}: {value}", True, color)
                surface.blit(mod_text, (x + 20, y))
                y += 16

            for name, value in attack.defender_buffs.items():
                color = self.color_modifier_positive
                mod_text = self.small_font.render(f"  {name}: +{value}", True, color)
                surface.blit(mod_text, (x + 20, y))
                y += 16

        # Round number
        round_text = self.small_font.render(
            f"Round: {attack.round_number}",
            True, (150, 150, 150)
        )
        surface.blit(round_text, (x + 15, y))
        y += 18

        return y

    def _draw_move_details(self, surface: pygame.Surface, move: any, x: int, y: int) -> int:
        """Draw detailed movement information."""
        # Unit name
        unit_text = self.text_font.render(move.unit_name, True, (255, 255, 255))
        surface.blit(unit_text, (x + 10, y))
        y += 22

        # From → To
        move_text = self.small_font.render(
            f"From ({move.from_pos.q}, {move.from_pos.r}) → ({move.to_pos.q}, {move.to_pos.r})",
            True, UI_TEXT
        )
        surface.blit(move_text, (x + 15, y))
        y += 20

        # Distance and AP
        stats_text = self.small_font.render(
            f"Distance: {move.distance} hexes | AP: -{move.ap_spent}",
            True, UI_TEXT
        )
        surface.blit(stats_text, (x + 15, y))
        y += 20

        # Reactions if any
        if move.reactions_triggered:
            react_text = self.small_font.render(
                f"Reactions: {', '.join(move.reactions_triggered)}",
                True, (255, 150, 150)
            )
            surface.blit(react_text, (x + 15, y))
            y += 20

        # Round number
        round_text = self.small_font.render(
            f"Round: {move.round_number}",
            True, (150, 150, 150)
        )
        surface.blit(round_text, (x + 15, y))
        y += 18

        return y

    def _draw_action_details(self, surface: pygame.Surface, action: any, x: int, y: int) -> int:
        """Draw detailed action information."""
        # Unit name
        unit_text = self.text_font.render(action.unit_name, True, (255, 255, 255))
        surface.blit(unit_text, (x + 10, y))
        y += 22

        # Action type
        action_text = self.small_font.render(
            f"{action.action_type.replace('_', ' ').title()} | AP: -{action.ap_spent}",
            True, UI_TEXT
        )
        surface.blit(action_text, (x + 15, y))
        y += 20

        # Description
        desc_text = self.small_font.render(action.description, True, (200, 200, 200))
        surface.blit(desc_text, (x + 15, y))
        y += 20

        # Extra data
        for key, value in action.extra_data.items():
            extra_text = self.small_font.render(f"{key}: {value}", True, (180, 180, 180))
            surface.blit(extra_text, (x + 20, y))
            y += 18

        # Round number
        round_text = self.small_font.render(
            f"Round: {action.round_number}",
            True, (150, 150, 150)
        )
        surface.blit(round_text, (x + 15, y))
        y += 18

        return y

    def _draw_initiative_details(self, surface: pygame.Surface, init_data, x: int, y: int) -> int:
        """Draw initiative roll details.

        Args:
            surface: Surface to draw on
            init_data: InitiativeData instance
            x: X position
            y: Y position

        Returns:
            New Y position
        """
        # Position in turn order
        position_text = self.text_font.render(f"#{init_data.order_position}", True, (255, 215, 0))
        surface.blit(position_text, (x + 10, y))
        y += 22

        # Unit name
        name_text = self.text_font.render(init_data.unit_name, True, (255, 255, 255))
        surface.blit(name_text, (x + 15, y))
        y += 22

        # Initiative calculation
        calc_text = self.small_font.render(
            f"KÉ {init_data.base_ke} + {init_data.roll}D = {init_data.total_initiative}",
            True, (200, 200, 200)
        )
        surface.blit(calc_text, (x + 15, y))
        y += 20

        # Round number clarification
        round_text = self.small_font.render(
            f"Rolled in: Pre-Battle Phase",
            True, (150, 150, 150)
        )
        surface.blit(round_text, (x + 15, y))
        y += 18

        return y

    def is_click_outside(self, mx: int, my: int) -> bool:
        """Check if mouse click is outside the popup area."""
        if not self.visible or not self.popup_rect:
            return False
        return not self.popup_rect.collidepoint(mx, my)
