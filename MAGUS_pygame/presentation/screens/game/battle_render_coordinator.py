"""
Rendering coordination for battle screen.

Manages drawing of all battle screen components.
"""

import pygame
from application.battle_service import BattleService
from config import PLAY_AREA_WIDTH, SIDEBAR_WIDTH
from domain.value_objects import Position
from infrastructure.rendering.battle_renderer import BattleRenderer
from logger.logger import get_logger
from presentation.components.action_panel import ActionPanel
from presentation.components.hud import HUD
from presentation.components.pause_menu import PauseMenu
from presentation.components.unit_info_popup import UnitInfoPopup
from presentation.components.weapon_switch_popup import WeaponSwitchPopup

logger = get_logger(__name__)


class BattleRenderCoordinator:
    """Coordinates rendering of all battle screen elements."""

    def __init__(
        self,
        screen_width: int,
        screen_height: int,
        renderer: BattleRenderer,
        action_panel: ActionPanel,
        hud: HUD,
        pause_menu: PauseMenu,
    ):
        """Initialize render coordinator.

        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
            renderer: Battle renderer for game area
            action_panel: Action panel sidebar
            hud: HUD component (deprecated, kept for compatibility)
            pause_menu: Pause menu overlay
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.renderer = renderer
        self.action_panel = action_panel
        self.pause_menu = pause_menu
        self.font_victory = pygame.font.Font(None, 72)

    def draw_battle_scene(
        self,
        surface: pygame.Surface,
        play_surface: pygame.Surface,
        battle: BattleService,
        action_mode: str,
        movement_path: list[Position] | None,
        hovered_hex: tuple[int, int] | None,
        combat_message: str | None,
        unit_popup: UnitInfoPopup | None,
        victory_action: str | None = None,
        weapon_switch_popup: WeaponSwitchPopup | None = None,
    ) -> None:
        """Draw complete battle scene.

        Args:
            surface: Main screen surface
            play_surface: Play area surface
            battle: Battle service
            action_mode: Current action mode
            movement_path: Movement path preview
            hovered_hex: Hovered hex coordinates
            combat_message: Combat message to display
            unit_popup: Unit info popup (if open)
            victory_action: Victory action string (if battle ended)
        """
        # Clear play area
        self.renderer.clear()

        # Get current unit
        current_unit = battle.current_unit if not battle.is_victory() else None

        # Compute highlights based on action mode
        reachable_hexes: set[tuple[int, int]] | None = None
        attackable_hexes: set[tuple[int, int]] | None = None
        enemy_zones: set[tuple[int, int]] = set()

        if action_mode == "move" and current_unit:
            reachable_hexes = battle.compute_reachable_hexes(current_unit)
            enemy_zones = battle.compute_enemy_zones(current_unit)
        elif action_mode == "attack" and current_unit:
            attackable_hexes = battle.compute_attackable_hexes(current_unit)

        # Render scene to play area surface
        self.renderer.render_scene(
            units=battle.units,
            round_num=battle.round,
            active_unit=current_unit,
            action_mode=action_mode,
            movement_path=movement_path,
            enemy_zone=enemy_zones,
            reachable_hexes=reachable_hexes,
            attackable_hexes=attackable_hexes,
            highlight_hex=hovered_hex,
            combat_message=combat_message,
        )

        # Draw action panel (left sidebar)
        self.action_panel.set_active_mode(action_mode)
        # Update unit stats in panel
        if current_unit:
            ap_remaining = battle.remaining_ap(current_unit)
            stamina_current = current_unit.stamina.current_stamina if current_unit.stamina else 0
            stamina_max = current_unit.stamina.max_stamina if current_unit.stamina else 100
            self.action_panel.set_unit_stats(
                current_unit.name,
                ap_remaining,
                current_unit.ep.current,
                current_unit.fp.current,
                stamina_current,
                current_unit.ep.maximum,
                current_unit.fp.maximum,
                stamina_max,
                battle.round,
            )

        # Update combat message
        self.action_panel.set_combat_message(combat_message)
        self.action_panel.draw(surface)

        # Blit play area surface to main screen (offset by sidebar width)
        surface.blit(play_surface, (SIDEBAR_WIDTH, 0))

        # Draw unit info popup if open
        if unit_popup:
            unit_popup.draw(surface)

        # Draw weapon switch popup if open
        if weapon_switch_popup:
            weapon_switch_popup.draw(surface)

        # Draw controls help (minimalist)
        self._draw_controls(surface)

        # Draw victory screen if battle ended
        if battle.is_victory() and victory_action:
            self._draw_victory_overlay(surface, battle)

        # Draw pause menu last (top layer)
        self.pause_menu.draw(surface)

    def _draw_controls(self, surface: pygame.Surface) -> None:
        """Draw minimal control hints.

        Args:
            surface: Main screen surface to draw on
        """
        hints = ["Right-Click: Inspect", "Space: End Turn"]

        y = self.screen_height - 25
        x = SIDEBAR_WIDTH + 10

        text = " | ".join(hints)
        hint_font = pygame.font.Font(None, 20)
        text_surf = hint_font.render(text, True, (150, 150, 160))

        surface.blit(text_surf, (x, y))

    def _draw_victory_overlay(self, surface: pygame.Surface, battle: BattleService) -> None:
        """Draw victory screen overlay.

        Args:
            surface: Surface to draw on
            battle: Battle service for victory info
        """
        # Semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        # Victory text
        winner_team = battle.get_winner()
        if winner_team:
            text = f"Team {winner_team} Wins!"
            color = (50, 255, 50) if winner_team == "A" else (255, 50, 50)
        else:
            text = "Battle Complete"
            color = (200, 200, 200)

        victory_surf = self.font_victory.render(text, True, color)
        victory_rect = victory_surf.get_rect(
            center=(self.screen_width // 2, self.screen_height // 2 - 50)
        )
        surface.blit(victory_surf, victory_rect)

        # Subtitle
        subtitle_font = pygame.font.Font(None, 32)
        subtitle = subtitle_font.render("Press ESC to return to menu", True, (180, 180, 180))
        subtitle_rect = subtitle.get_rect(
            center=(self.screen_width // 2, self.screen_height // 2 + 50)
        )
        surface.blit(subtitle, subtitle_rect)
