"""
Battle screen for turn-based combat gameplay.

Handles combat phase with turn management, player input, unit actions,
and victory conditions. Integrates BattleService, ActionHandler, and BattleRenderer.
"""

import pygame
from application.battle_service import BattleService
from application.game_context import GameContext
from domain.entities import Unit
from domain.value_objects import Position
from infrastructure.rendering.battle_renderer import BattleRenderer
from infrastructure.rendering.hex_grid import get_grid_bounds, pixel_to_hex
from logger.logger import get_logger
from presentation.components.hud import HUD
from presentation.components.unit_info_popup import UnitInfoPopup

logger = get_logger(__name__)


class ActionMode:
    """Current action mode for player input."""

    IDLE = "idle"
    MOVE = "move"
    ATTACK = "attack"
    INSPECT = "inspect"


class BattleScreen:
    """Battle screen managing turn-based combat gameplay.

    Handles:
    - Turn-based combat loop
    - Player input for movement and attacks
    - Unit selection and action execution
    - Victory/defeat conditions
    - Rendering through BattleRenderer

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
            screen_width: Screen width in pixels
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
        self.hovered_hex: tuple[int, int] | None = None
        self.movement_path: list[Position] | None = None
        self.combat_message: str | None = None
        self.combat_message_timer = 0

        # Rendering
        grid_bounds = get_grid_bounds()
        self.renderer = BattleRenderer(
            screen=pygame.Surface((screen_width, screen_height)),
            grid_bounds=grid_bounds,
            background=background,
        )

        # UI Components
        self.hud = HUD(screen_width, screen_height)
        self.unit_popup: UnitInfoPopup | None = None

        # Fonts
        self.font_normal = pygame.font.Font(None, 28)

        logger.info(f"BattleScreen initialized with {len(battle_service.units)} units")

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle input events.

        Args:
            event: Pygame event
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.unit_popup and self.unit_popup.visible:
                    self.unit_popup.hide()
                elif self.action_mode != ActionMode.IDLE:
                    self._cancel_action()
                else:
                    self.action = "battle_cancelled"
                    logger.info("Battle cancelled by user")

            elif event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                self._end_current_turn()

            elif event.key == pygame.K_m:
                self._enter_move_mode()

            elif event.key == pygame.K_a:
                self._enter_attack_mode()

            elif event.key == pygame.K_i:
                self._enter_inspect_mode()

            elif event.key == pygame.K_q:
                # Rotate counterclockwise (left)
                self._rotate_current_unit(-1)

            elif event.key == pygame.K_e:
                # Rotate clockwise (right)
                self._rotate_current_unit(1)

        elif event.type == pygame.MOUSEMOTION:
            self._update_hover(event.pos)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            # If popup is open, check for tab clicks or outside click
            if self.unit_popup and self.unit_popup.visible:
                mx, my = event.pos
                # First, check if click is inside popup and on a tab
                if self.unit_popup.handle_click(mx, my):
                    return  # Tab switched, do not close
                # If click is outside popup, close it
                if self.unit_popup.is_click_outside(mx, my):
                    self.unit_popup.hide()
                    return
            # If popup not open or click not handled, continue normal click handling
            if event.button == 1:  # Left click
                self._handle_click(event.pos)
            elif event.button == 3:  # Right click
                self._handle_right_click(event.pos)

    def _update_hover(self, mouse_pos: tuple[int, int]) -> None:
        """Update hovered hex from mouse position and compute movement path preview.

        Args:
            mouse_pos: Mouse position (x, y)
        """
        q, r = pixel_to_hex(*mouse_pos)
        min_q, max_q, min_r, max_r = get_grid_bounds()

        if min_q <= q < max_q and min_r <= r < max_r:
            self.hovered_hex = (q, r)

            # Update movement path preview if in MOVE mode
            if self.action_mode == ActionMode.MOVE:
                self._update_movement_path_preview(q, r)
        else:
            self.hovered_hex = None
            self.movement_path = None

    def _handle_click(self, mouse_pos: tuple[int, int]) -> None:
        """Handle left mouse click.

        Clicking behavior:
        - MOVE mode: Execute movement to hex
        - ATTACK mode: Execute attack on hex
        - IDLE/INSPECT mode: Inspect hex OR rotate if clicking adjacent hex to current unit

        Args:
            mouse_pos: Mouse position (x, y)
        """
        if not self.hovered_hex:
            return

        q, r = self.hovered_hex
        current = self.battle.current_unit()

        if self.action_mode == ActionMode.MOVE:
            # Only allow clicking on reachable hexes
            if current:
                reachable = self.battle.compute_reachable_hexes(current)
                if (q, r) not in reachable:
                    self._show_message("Hex not in movement range")
                    return
            self._execute_move(Position(q, r))

        elif self.action_mode == ActionMode.ATTACK:
            # Only allow clicking on attackable hexes with enemies
            if current:
                attackable = self.battle.compute_attackable_hexes(current)
                if (q, r) not in attackable:
                    self._show_message("Hex not in attack range")
                    return
            self._execute_attack(Position(q, r))

        elif self.action_mode == ActionMode.INSPECT or self.action_mode == ActionMode.IDLE:
            # Check if clicking adjacent hex to current unit for facing change
            if current and self._is_adjacent_to_unit(q, r, current):
                self._change_facing_to_hex(q, r)
            else:
                self._inspect_hex(q, r)

    def _handle_right_click(self, mouse_pos: tuple[int, int]) -> None:
        """Handle right mouse click (quick inspect).

        Args:
            mouse_pos: Mouse position (x, y)
        """
        if not self.hovered_hex:
            return

        q, r = self.hovered_hex
        self._inspect_hex(q, r)

    def _enter_move_mode(self) -> None:
        """Enter movement mode."""
        if self.battle.is_victory():
            return

        current = self.battle.current_unit()
        if not current.is_alive():
            self._show_message("Current unit cannot act")
            return

        if self.battle.remaining_ap(current) < 1:
            self._show_message("Insufficient AP to move")
            return

        self.action_mode = ActionMode.MOVE
        self.selected_unit = current
        logger.debug(f"Entered MOVE mode for {current.name}")

    def _enter_attack_mode(self) -> None:
        """Enter attack mode."""
        if self.battle.is_victory():
            return

        current = self.battle.current_unit()
        if not current.is_alive():
            self._show_message("Current unit cannot act")
            return

        if not current.weapon:
            self._show_message("No weapon equipped")
            return

        # Get attack AP cost from weapon's attack_time
        attack_ap = current.weapon.attack_time
        if self.battle.remaining_ap(current) < attack_ap:
            self._show_message(f"Insufficient AP to attack (need {attack_ap})")
            return

        self.action_mode = ActionMode.ATTACK
        self.selected_unit = current
        logger.debug(f"Entered ATTACK mode for {current.name}")

    def _enter_inspect_mode(self) -> None:
        """Enter inspect mode."""
        self.action_mode = ActionMode.INSPECT
        self.selected_unit = None
        logger.debug("Entered INSPECT mode")

    def _cancel_action(self) -> None:
        """Cancel current action and return to idle."""
        self.action_mode = ActionMode.IDLE
        self.selected_unit = None
        self.movement_path = None
        logger.debug("Cancelled action, returned to IDLE")

    def _execute_move(self, dest: Position) -> None:
        """Execute movement to destination.

        Args:
            dest: Destination position
        """
        current = self.battle.current_unit()

        # Get potential reactors (enemy units)
        enemies = self.battle.get_enemies(current)

        # Execute move through battle service
        summary = self.battle.move_current_unit(dest=dest, potential_reactors=enemies)

        if "error" in summary:
            self._show_message(f"Move failed: {summary['error']}")
            logger.warning(f"Move failed: {summary['error']}")
        else:
            ap_spent = summary.get("ap_spent", 0)
            self._show_message(f"Moved (AP: -{ap_spent})")
            logger.info(f"{current.name} moved to {dest} (AP spent: {ap_spent})")

            # Show full feedback for opportunity attacks
            oa_results = summary.get("reaction_results") or summary.get("opportunity_attacks")
            if oa_results:
                oa_count = len(oa_results)
                self._show_message(f"Movement triggered {oa_count} opportunity attack(s)!")
                for rr in oa_results:
                    # Show the main message for the reaction
                    if hasattr(rr, "message"):
                        self._show_message(rr.message)
                    # If there is an attack result, show details
                    attack_result = None
                    if hasattr(rr, "data") and rr.data:
                        attack_result = rr.data.get("attack_result")
                    if attack_result:
                        # Compose a detailed message
                        msg = f"Result: {attack_result.outcome.value.title()} | Hit: {attack_result.hit} | EP: -{attack_result.damage_to_ep} | FP: -{attack_result.damage_to_fp}"
                        if attack_result.is_critical:
                            msg += " | Critical!"
                        if attack_result.is_overpower:
                            msg += " | Overpower!"
                        if attack_result.requires_dodge_check:
                            msg += " | Dodge check required!"
                        self._show_message(msg)

        self._cancel_action()

    def _execute_attack(self, target_pos: Position) -> None:
        """Execute attack on target position.

        Args:
            target_pos: Target position
        """
        current = self.battle.current_unit()

        # Find unit at target position
        target = self.battle.get_unit_at_position(target_pos)

        if not target:
            self._show_message("No target at selected hex")
            return

        if not target.is_alive():
            self._show_message("Target is already defeated")
            return

        # Execute attack through battle service
        result = self.battle.attack_current_unit(defender=target)

        if "error" in result:
            self._show_message(f"Attack failed: {result['error']}")
            logger.warning(f"Attack failed: {result['error']}")
        else:
            action_result = result.get("action_result")
            if action_result:
                self._show_message(action_result.message)
                logger.info(f"{current.name} attacked {target.name}: {action_result.message}")

        self._cancel_action()

    def _inspect_hex(self, q: int, r: int) -> None:
        """Inspect unit at hex position.

        Args:
            q: Hex Q coordinate
            r: Hex R coordinate
        """
        # Find unit at position
        for unit in self.battle.units:
            if unit.position.q == q and unit.position.r == r:
                if not self.unit_popup:
                    self.unit_popup = UnitInfoPopup(context=self.context)
                self.unit_popup.show(unit)
                logger.debug(f"Opened info popup for {unit.name}")
                return

    def _end_current_turn(self) -> None:
        """End the current unit's turn."""
        if self.battle.is_victory():
            return

        current = self.battle.current_unit()
        logger.info(f"Ending turn for {current.name}")

        self.battle.end_turn()
        self._cancel_action()
        self._show_message(f"{self.battle.current_unit().name}'s turn")

        # Check for victory
        if self.battle.is_victory():
            self._handle_victory()

    def _handle_victory(self) -> None:
        """Handle battle victory."""
        winner = self.battle.get_winner()

        if winner == "team_a":
            self.action = "battle_victory_team_a"
            self._show_message("Team A Victorious!")
            logger.info("Battle ended: Team A victory")
        elif winner == "team_b":
            self.action = "battle_victory_team_b"
            self._show_message("Team B Victorious!")
            logger.info("Battle ended: Team B victory")
        else:
            self.action = "battle_draw"
            self._show_message("Battle ended in a draw")
            logger.info("Battle ended: Draw")

    def _show_message(self, message: str) -> None:
        """Show temporary combat message.

        Args:
            message: Message to display
        """
        self.combat_message = message
        self.combat_message_timer = 180  # 3 seconds at 60 FPS

    def update(self, delta_time: float = 1 / 60) -> None:
        """Update battle state (timers, etc).

        Args:
            delta_time: Time since last update in seconds
        """
        # Update message timer
        if self.combat_message_timer > 0:
            self.combat_message_timer -= 1
            if self.combat_message_timer <= 0:
                self.combat_message = None

        # Check for auto-victory if not already detected
        if not self.action and self.battle.is_victory():
            self._handle_victory()

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the battle screen.

        Args:
            surface: Surface to draw on
        """
        # Update renderer's internal surface
        self.renderer.screen = surface

        # Clear background
        self.renderer.clear()

        # Get current unit
        current_unit = self.battle.current_unit() if not self.battle.is_victory() else None

        # Compute highlights based on action mode
        reachable_hexes: set[tuple[int, int]] | None = None
        attackable_hexes: set[tuple[int, int]] | None = None
        enemy_zones: set[tuple[int, int]] = set()

        if self.action_mode == ActionMode.MOVE and current_unit:
            # Calculate reachable hexes based on remaining AP
            reachable_hexes = self.battle.compute_reachable_hexes(current_unit)
            # Show enemy zones as warning during movement
            enemy_zones = self.battle.compute_enemy_zones(current_unit)

        elif self.action_mode == ActionMode.ATTACK and current_unit:
            # Calculate attackable hexes based on weapon reach and facing
            attackable_hexes = self.battle.compute_attackable_hexes(current_unit)

        # Render complete scene
        self.renderer.render_scene(
            units=self.battle.units,
            round_num=self.battle.round,
            active_unit=current_unit,
            action_mode=self.action_mode,
            movement_path=self.movement_path,
            enemy_zone=enemy_zones,
            reachable_hexes=reachable_hexes,
            attackable_hexes=attackable_hexes,
            highlight_hex=self.hovered_hex,
            combat_message=self.combat_message,
        )

        # Draw HUD overlay
        if current_unit:
            ap_remaining = self.battle.remaining_ap(current_unit)
            self.hud.draw(
                surface=surface,
                unit=current_unit,
                round_num=self.battle.round,
                action_points=ap_remaining,
            )

        # Draw unit info popup if open
        if self.unit_popup:
            self.unit_popup.draw(surface)

        # Draw controls help
        self._draw_controls(surface)

        # Draw victory screen if battle ended
        if self.battle.is_victory() and self.action:
            self._draw_victory_overlay(surface)

    def _draw_controls(self, surface: pygame.Surface) -> None:
        """Draw control hints at bottom of screen.

        Args:
            surface: Surface to draw on
        """
        controls = [
            "M: Move",
            "A: Attack",
            "Q/E: Rotate",
            "Click Adjacent: Face",
            "I: Inspect",
            "Space: End Turn",
            "ESC: Cancel",
        ]

        y = self.screen_height - 30
        x = 10

        text = " | ".join(controls)
        text_surf = self.font_normal.render(text, True, (200, 200, 200))

        # Semi-transparent background
        bg = pygame.Surface((text_surf.get_width() + 20, 35), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 150))
        surface.blit(bg, (x - 10, y - 5))

        surface.blit(text_surf, (x, y))

    def _draw_victory_overlay(self, surface: pygame.Surface) -> None:
        """Draw victory screen overlay.

        Args:
            surface: Surface to draw on
        """
        # Semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        # Victory text
        victory_font = pygame.font.Font(None, 72)
        if "team_a" in self.action:
            title = "Team A Victorious!"
            color = (100, 150, 255)
        elif "team_b" in self.action:
            title = "Team B Victorious!"
            color = (255, 100, 100)
        else:
            title = "Battle Ended"
            color = (200, 200, 200)

        title_surf = victory_font.render(title, True, color)
        title_rect = title_surf.get_rect(
            center=(self.screen_width // 2, self.screen_height // 2 - 40)
        )
        surface.blit(title_surf, title_rect)

        # Instructions
        inst_font = pygame.font.Font(None, 36)
        inst_surf = inst_font.render("Press ESC to return to menu", True, (180, 180, 180))
        inst_rect = inst_surf.get_rect(
            center=(self.screen_width // 2, self.screen_height // 2 + 40)
        )
        surface.blit(inst_surf, inst_rect)

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
        current = self.battle.current_unit()
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

    # --- Facing control helpers ---
    def _is_adjacent_to_unit(self, q: int, r: int, unit: Unit) -> bool:
        """Check if hex (q, r) is adjacent to unit's position.

        Args:
            q, r: Hex coordinates
            unit: Unit to check adjacency to

        Returns:
            True if hex is adjacent to unit
        """
        from infrastructure.rendering.hex_grid import get_adjacent_hexes

        adjacent = get_adjacent_hexes(unit.position.q, unit.position.r)
        return (q, r) in adjacent

    def _change_facing_to_hex(self, q: int, r: int) -> None:
        """Change current unit's facing to point toward hex (q, r).

        Args:
            q, r: Target hex coordinates (should be adjacent)
        """
        from domain.value_objects import Facing
        from infrastructure.rendering.hex_grid import calculate_facing_to_hex

        current = self.battle.current_unit()
        if not current:
            return

        # Calculate facing direction
        facing_dir = calculate_facing_to_hex(current.position.q, current.position.r, q, r)
        if facing_dir is None:
            self._show_message("Not an adjacent hex")
            return

        # Execute facing change
        new_facing = Facing(facing_dir)
        result = self.battle.rotate_current_unit(new_facing)

        if "error" in result:
            self._show_message(result["error"])
            logger.warning(f"Facing change failed: {result['error']}")
        else:
            ap_spent = result.get("ap_spent", 0)
            self._show_message(f"Rotated to face hex (AP: -{ap_spent})")
            logger.info(f"{current.name} rotated to facing {facing_dir} (AP spent: {ap_spent})")

    def _rotate_current_unit(self, direction: int) -> None:
        """Rotate current unit by direction offset.

        Args:
            direction: +1 for clockwise, -1 for counterclockwise
        """
        from domain.value_objects import Facing

        current = self.battle.current_unit()
        if not current:
            return

        if self.battle.is_victory():
            return

        # Calculate new facing
        current_facing = current.facing.direction
        new_facing_dir = (current_facing + direction) % 6
        new_facing = Facing(new_facing_dir)

        # Execute rotation
        result = self.battle.rotate_current_unit(new_facing)

        if "error" in result:
            self._show_message(result["error"])
            logger.warning(f"Rotation failed: {result['error']}")
        else:
            ap_spent = result.get("ap_spent", 0)
            direction_name = "clockwise" if direction > 0 else "counterclockwise"
            self._show_message(f"Rotated {direction_name} (AP: -{ap_spent})")
            logger.info(
                f"{current.name} rotated {direction_name} to facing {new_facing_dir} (AP spent: {ap_spent})"
            )
