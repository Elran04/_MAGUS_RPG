"""
Battle screen for turn-based combat gameplay.

Lightweight coordinator that wires together input handling, action execution,
and rendering for turn-based combat.
"""

import pygame
from application.battle_service import BattleService
from application.game_context import GameContext
from config import PLAY_AREA_WIDTH, SIDEBAR_WIDTH
from domain.entities import Unit
from domain.value_objects import Position
from infrastructure.rendering.battle_renderer import BattleRenderer
from infrastructure.rendering.hex_grid import get_grid_bounds
from logger.logger import get_logger
from presentation.components.action_panel import ActionPanel
from presentation.components.hud import HUD
from presentation.components.pause_menu import PauseMenu
from presentation.components.unit_info_popup import UnitInfoPopup
from presentation.screens.game.battle_action_executor import BattleActionExecutor
from presentation.screens.game.battle_input_handler import BattleInputHandler
from presentation.screens.game.battle_render_coordinator import BattleRenderCoordinator

logger = get_logger(__name__)


class ActionMode:
    """Current action mode for player input."""

    IDLE = "idle"
    MOVE = "move"
    ATTACK = "attack"
    INSPECT = "inspect"


class BattleScreen:
    """Battle screen coordinator.

    Lightweight orchestrator that delegates to:
    - BattleInputHandler: Process keyboard/mouse input
    - BattleActionExecutor: Execute combat actions
    - BattleRenderCoordinator: Render all UI components

    Emits action strings for application layer:
    - "battle_victory_team_a": Team A won
    - "battle_victory_team_b": Team B won
    - "battle_cancelled": Player quit battle
    """

    def __init__(
        self,
        screen_width: int,
        screen_height: int,
        battle_service: BattleService,
        context: GameContext,
        background: pygame.Surface | None = None,
    ):
        """Initialize battle screen.

        Args:
            screen_width: Screen width in pixels (including sidebar)
            screen_height: Screen height in pixels
            battle_service: Battle service managing combat state
            context: Game context for data access
            background: Optional background surface
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.battle = battle_service
        self.context = context

        # State
        self.action: str | None = None
        self.action_mode = ActionMode.IDLE
        self.selected_unit: Unit | None = None
        self.movement_path: list[Position] | None = None
        self.unit_popup: UnitInfoPopup | None = None

        # Create play area surface (to the right of sidebar)
        self.play_surface = pygame.Surface((PLAY_AREA_WIDTH, screen_height))

        # Rendering (renderer draws to play area surface)
        grid_bounds = get_grid_bounds()
        self.renderer = BattleRenderer(
            screen=self.play_surface,
            grid_bounds=grid_bounds,
            background=background,
            x_offset=0,
        )

        # UI Components
        self.action_panel = ActionPanel(SIDEBAR_WIDTH, screen_height)
        self.hud = HUD(PLAY_AREA_WIDTH, screen_height)
        self.pause_menu = PauseMenu(screen_width, screen_height)

        # Coordinators
        self.input_handler = BattleInputHandler()
        self.action_executor = BattleActionExecutor(battle_service)
        self.render_coordinator = BattleRenderCoordinator(
            screen_width, screen_height, self.renderer, self.action_panel, self.hud, self.pause_menu
        )

        logger.info(f"BattleScreen initialized with {len(battle_service.units)} units")
        logger.info(f"Layout: Sidebar ({SIDEBAR_WIDTH}px) + Play Area ({PLAY_AREA_WIDTH}px)")

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle input events.

        Args:
            event: Pygame event
        """
        if event.type == pygame.KEYDOWN:
            self._handle_keypress(event.key)
        elif event.type == pygame.MOUSEMOTION:
            self._handle_mouse_motion(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self._handle_mouse_click(event.button, event.pos)

    def _handle_keypress(self, key: int) -> None:
        """Handle keyboard input.

        Args:
            key: Pygame key constant
        """
        if key == pygame.K_ESCAPE:
            # Priority: Popup > Action mode > Pause menu toggle
            if self.unit_popup and self.unit_popup.visible:
                self.unit_popup.hide()
            elif self.action_mode != ActionMode.IDLE:
                self._cancel_action()
            else:
                self.pause_menu.toggle()
            return

        # Only handle game actions if pause menu is not visible
        if self.pause_menu.visible:
            return

        if key == pygame.K_SPACE or key == pygame.K_RETURN:
            self._end_current_turn()
        elif key == pygame.K_m:
            self._enter_move_mode()
        elif key == pygame.K_a:
            self._enter_attack_mode()
        elif key == pygame.K_i:
            self._enter_inspect_mode()
        elif key == pygame.K_q:
            self._rotate_current_unit(-1)
        elif key == pygame.K_e:
            self._rotate_current_unit(1)

    def _handle_mouse_motion(self, mouse_pos: tuple[int, int]) -> None:
        """Handle mouse movement."""
        self.pause_menu.handle_mouse_motion(mouse_pos)
        self.action_panel.handle_mouse_motion(mouse_pos)

        if not self.pause_menu.visible:
            hovered = self.input_handler.update_hovered_hex(mouse_pos)
            if hovered:
                # Auto-switch action mode based on what's hovered
                hovered_unit = self.battle.get_unit_at_hex(*hovered)
                current_unit = self.battle.current_unit
                if (
                    hovered_unit
                    and current_unit
                    and self.battle.is_enemy(current_unit, hovered_unit)
                ):
                    # Hovering over enemy unit -> Attack mode
                    if self.action_mode != ActionMode.ATTACK:
                        self.action_mode = ActionMode.ATTACK
                else:
                    # Hovering over empty tile or friendly unit -> Move mode
                    if self.action_mode != ActionMode.MOVE:
                        self.action_mode = ActionMode.MOVE

                if self.action_mode == ActionMode.MOVE:
                    self._update_movement_path_preview(*hovered)
                else:
                    self.movement_path = None
            else:
                self.movement_path = None

    def _handle_mouse_click(self, button: int, mouse_pos: tuple[int, int]) -> None:
        """Handle mouse button clicks.

        Args:
            button: Mouse button number
            mouse_pos: Mouse position (x, y)
        """
        if button != 1 and button != 3:  # Only handle left/right click
            return

        # Check pause menu clicks first (if visible)
        if self.pause_menu.visible and button == 1:
            action = self.pause_menu.handle_click(mouse_pos)
            if action == "continue":
                self.pause_menu.hide()
            elif action == "exit_to_menu":
                self.action = "battle_cancelled"
                logger.info("Exiting to main menu from pause menu")
            return

        # Block all game clicks if paused
        if self.pause_menu.visible:
            return

        # Check action panel clicks
        if button == 1:
            action = self.action_panel.handle_click(mouse_pos)
            if action:
                self._handle_action_button(action)
                return

        # Handle unit popup clicks
        if self.unit_popup and self.unit_popup.visible:
            if self.unit_popup.handle_click(*mouse_pos):
                return
            if self.unit_popup.is_click_outside(*mouse_pos):
                self.unit_popup.hide()
                return

        # Handle play area clicks
        if not self.input_handler.is_click_in_play_area(mouse_pos):
            return

        if button == 1:
            self._handle_play_area_left_click()
        elif button == 3:
            self._handle_play_area_right_click()

    def _handle_play_area_left_click(self) -> None:
        """Handle left click in play area."""
        hovered_hex = self.input_handler.hovered_hex
        if not hovered_hex:
            return

        q, r = hovered_hex
        current = self.battle.current_unit
        target_pos = Position(q, r)

        if self.action_mode == ActionMode.MOVE:
            is_valid, error_msg = self.battle.validate_move_target(current, target_pos)
            if is_valid:
                self._execute_move(target_pos)
            else:
                self.action_executor.show_message(error_msg)

        elif self.action_mode == ActionMode.ATTACK:
            is_valid, error_msg = self.battle.validate_attack_target(current, target_pos)
            if is_valid:
                self._execute_attack(target_pos)
            else:
                self.action_executor.show_message(error_msg)

        elif self.action_mode == ActionMode.INSPECT or self.action_mode == ActionMode.IDLE:
            # Try facing change if adjacent, otherwise inspect hex
            if current and self.action_executor.execute_facing_change(q, r, current):
                self._check_victory()
            else:
                self._inspect_hex(q, r)

    def _handle_play_area_right_click(self) -> None:
        """Handle right click in play area (quick inspect)."""
        hovered_hex = self.input_handler.hovered_hex
        if hovered_hex:
            self._inspect_hex(*hovered_hex)

    def _handle_action_button(self, action: str) -> None:
        """Handle action button click from the action panel.

        Args:
            action: Action name (e.g., "move", "attack", "end_turn")
        """
        if action == "move":
            self._enter_move_mode()
        elif action == "attack":
            self._enter_attack_mode()
        elif action == "inspect":
            self._enter_inspect_mode()
        elif action == "rotate_ccw":
            self._rotate_current_unit(-1)
        elif action == "rotate_cw":
            self._rotate_current_unit(1)
        elif action == "end_turn":
            self._end_current_turn()

    def _enter_move_mode(self) -> None:
        """Enter movement mode."""
        if self.battle.is_victory():
            return

        current = self.battle.current_unit
        can_move, error_msg = self.battle.can_move(current)
        if not can_move:
            self.action_executor.show_message(error_msg)
            return

        self.action_mode = ActionMode.MOVE
        self.selected_unit = current

    def _enter_attack_mode(self) -> None:
        """Enter attack mode."""
        if self.battle.is_victory():
            return

        current = self.battle.current_unit
        can_attack, error_msg = self.battle.can_attack(current)
        if not can_attack:
            self.action_executor.show_message(error_msg)
            return

        self.action_mode = ActionMode.ATTACK
        self.selected_unit = current

    def _enter_inspect_mode(self) -> None:
        """Enter inspect mode."""
        self.action_mode = ActionMode.INSPECT
        self.selected_unit = None

    def _cancel_action(self) -> None:
        """Cancel current action and return to idle."""
        self.action_mode = ActionMode.IDLE
        self.selected_unit = None
        self.movement_path = None

    def _execute_move(self, dest: Position) -> None:
        """Execute movement to destination."""
        current = self.battle.current_unit
        enemies = self.battle.get_enemies(current)

        summary = self.action_executor.execute_move(dest, enemies)

        # Show opportunity attack feedback if any
        oa_results = summary.get("reaction_results") or summary.get("opportunity_attacks")
        if oa_results:
            self._show_opportunity_attack_results(oa_results)

        # Only cancel move mode if movement failed or no more AP to move
        if "error" in summary:
            self._cancel_action()
        else:
            remaining_ap = self.battle.remaining_ap(current)
            if remaining_ap < 1:
                self._cancel_action()

        self._check_victory()

    def _execute_attack(self, target_pos: Position) -> None:
        """Execute attack on target position."""
        current = self.battle.current_unit
        target = self.battle.get_unit_at_position(target_pos)

        # Execute attack through action executor (which handles messaging)
        self.action_executor.execute_attack(target_pos, current, target)

        # Only cancel attack mode if no more AP
        if current and current.weapon:
            remaining_ap = self.battle.remaining_ap(current)
            if remaining_ap < 1:
                self._cancel_action()
        else:
            self._cancel_action()

        self._check_victory()

    def _rotate_current_unit(self, direction: int) -> None:
        """Rotate current unit."""
        current = self.battle.current_unit
        if current:
            self.action_executor.execute_rotation(direction, current)
            self._check_victory()

    def _end_current_turn(self) -> None:
        """End current unit's turn."""
        self.action_executor.end_turn()
        self._check_victory()

    def _inspect_hex(self, q: int, r: int) -> None:
        """Inspect a hex and show unit info if unit present."""
        unit = self.action_executor.inspect_hex(
            q, r, self.battle.units, self.screen_width, self.screen_height
        )
        if unit:
            if not self.unit_popup:
                self.unit_popup = UnitInfoPopup()
            self.unit_popup.show(unit)

    def _check_victory(self) -> None:
        """Check for victory and handle it."""
        if self.battle.is_victory():
            winner = self.battle.get_winner()
            if winner == "team_a":
                self.action = "battle_victory_team_a"
                self.action_executor.show_message("Team A Victorious!")
            elif winner == "team_b":
                self.action = "battle_victory_team_b"
                self.action_executor.show_message("Team B Victorious!")
            else:
                self.action = "battle_draw"
                self.action_executor.show_message("Battle ended in a draw")

    def _show_attack_result(self, attack_result) -> None:
        """Show attack result details."""
        # The message is already properly formatted in attack_action.py
        # This is used by opportunity attacks which have their result from domain
        # Just show the core outcome for opportunity attacks
        if attack_result.outcome:
            msg = f"{attack_result.outcome.value.replace('_', ' ').title()}"
            if attack_result.requires_dodge_check:
                msg += " | Dodge check required!"
            self.action_executor.show_message(msg)

    def _show_opportunity_attack_results(self, oa_results) -> None:
        """Show opportunity attack feedback."""
        oa_count = len(oa_results)
        self.action_executor.show_message(f"Movement triggered {oa_count} opportunity attack(s)!")
        for rr in oa_results:
            if hasattr(rr, "message"):
                self.action_executor.show_message(rr.message)
            attack_result = None
            if hasattr(rr, "data") and rr.data:
                attack_result = rr.data.get("attack_result")
            if attack_result:
                self._show_attack_result(attack_result)

    def update(self, delta_time: float = 1 / 60) -> None:
        """Update battle state (timers, etc)."""
        # Update message timer in action_executor and sync with action_panel
        if self.action_executor.combat_message_timer > 0:
            self.action_executor.combat_message_timer -= 1
            if self.action_executor.combat_message_timer <= 0:
                self.action_executor.combat_message = None

        # Update combat message in action panel
        self.action_panel.update_combat_message()

        # Check for auto-victory if not already detected
        if not self.action and self.battle.is_victory():
            self._check_victory()

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the battle screen."""
        # Delegate rendering to render coordinator
        self.render_coordinator.draw_battle_scene(
            surface=surface,
            play_surface=self.play_surface,
            battle=self.battle,
            action_mode=self.action_mode,
            movement_path=self.movement_path,
            hovered_hex=self.input_handler.hovered_hex,
            combat_message=self.action_executor.combat_message,
            unit_popup=self.unit_popup,
            victory_action=self.action,
        )

    def get_action(self) -> str | None:
        """Get emitted action (if any).

        Returns:
            Action string or None
        """
        return self.action

    def is_complete(self) -> bool:
        """Check if battle is complete.

        Returns:
            True if battle ended or cancelled
        """
        return self.action is not None

    # --- Movement path preview ---
    def _update_movement_path_preview(self, dest_q: int, dest_r: int) -> None:
        """Update movement path preview when hovering in MOVE mode.

        Args:
            dest_q, dest_r: Destination hex coordinates
        """
        current = self.battle.current_unit
        if not current:
            self.movement_path = None
            return

        # Check if destination is reachable
        reachable = self.battle.compute_reachable_hexes(current)
        if (dest_q, dest_r) not in reachable:
            self.movement_path = None
            return

        # Compute path using BFS (same as movement action)
        from domain.mechanics.actions.movement_action import bfs_path

        start = (current.position.q, current.position.r)
        dest = (dest_q, dest_r)

        # Get blocked positions (other units)
        blocked = {(u.position.q, u.position.r) for u in self.battle.units if u.id != current.id}

        path_coords = bfs_path(start, dest, blocked)

        # Convert to Position objects for rendering
        if path_coords:
            self.movement_path = [Position(q, r) for q, r in path_coords]
        else:
            self.movement_path = None
