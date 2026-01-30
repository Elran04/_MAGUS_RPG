"""
Battle screen for turn-based combat gameplay.

Lightweight coordinator that wires together input handling, action execution,
and rendering for turn-based combat.
"""

import pygame
from application.battle_service import BattleService
from application.detailed_battle_log import DetailedBattleLog
from application.game_context import GameContext
from config import PLAY_AREA_WIDTH, SIDEBAR_WIDTH
from domain.entities import Unit
from domain.value_objects import Position
from infrastructure.rendering.battle_renderer import BattleRenderer
from infrastructure.rendering.hex_grid import get_grid_bounds
from logger.logger import get_logger
from presentation.components.action_panel import ActionPanel
from presentation.components.battle_log_popup import BattleLogPopup
from presentation.components.hud import HUD
from presentation.components.pause_menu import PauseMenu
from presentation.components.reaction_popup import ReactionPopup
from presentation.components.unit_info.unit_info_popup import UnitInfoPopup
from presentation.components.weapon_switch_popup import WeaponSwitchPopup
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
        self.weapon_switch_popup: WeaponSwitchPopup | None = None
        self.reaction_popup: ReactionPopup | None = None
        self._active_special_attack: str | None = (
            None  # Name of active special attack (e.g., "charge")
        )

        # Detailed battle log system
        self.detailed_log = DetailedBattleLog()
        self.detailed_log.set_round(battle_service.round)  # Initialize with starting round
        self._log_initiative(battle_service)  # Log initial turn order
        self.battle_log_popup = BattleLogPopup(self.detailed_log)

        # Create play area surface (to the right of sidebar)
        self.play_surface = pygame.Surface((PLAY_AREA_WIDTH, screen_height))

        # Rendering (renderer draws to play area surface)
        grid_bounds = get_grid_bounds()
        # Ensure background fits the play area; keep presentation-side scaling here
        if background and background.get_size() != (PLAY_AREA_WIDTH, screen_height):
            background = pygame.transform.smoothscale(background, (PLAY_AREA_WIDTH, screen_height))

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
        self.reaction_popup = ReactionPopup(screen_width, screen_height)

        # Coordinators
        self.input_handler = BattleInputHandler()
        self.action_executor = BattleActionExecutor(battle_service, self.detailed_log)
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
        # Let reaction popup handle its own events
        if self.reaction_popup and self.reaction_popup.visible:
            if self.reaction_popup.handle_event(event):
                return

        # Let battle log popup handle its own events (scrolling)
        if self.battle_log_popup and self.battle_log_popup.visible:
            if self.battle_log_popup.handle_event(event):
                return

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
            # Priority: Reaction popup > Battle log popup > Weapon switch popup > Unit popup > Action mode > Pause menu toggle
            if self.reaction_popup and self.reaction_popup.visible:
                self.reaction_popup.hide()
            elif self.battle_log_popup and self.battle_log_popup.visible:
                self.battle_log_popup.hide()
            elif self.weapon_switch_popup and self.weapon_switch_popup.visible:
                self.weapon_switch_popup.hide()
            elif self.unit_popup and self.unit_popup.visible:
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
        elif key == pygame.K_w:
            self._open_weapon_switch_popup()
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
        if self.reaction_popup:
            self.reaction_popup.handle_mouse_motion(mouse_pos)

        if not self.pause_menu.visible:
            hovered = self.input_handler.update_hovered_hex(mouse_pos)
            if hovered:
                # Auto-switch action mode based on what's hovered (disabled during special attacks)
                if self._active_special_attack is None:
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

        # Handle reaction popup clicks
        if self.reaction_popup and self.reaction_popup.visible:
            action = self.reaction_popup.handle_click(mouse_pos)
            if action:  # Accept or Decline
                return
            # Check if click outside popup
            if self.reaction_popup.is_click_outside(mouse_pos):
                self.reaction_popup.handle_click(mouse_pos)  # Will call decline via callback
                return
            return

        # Check action panel clicks
        if button == 1:
            action = self.action_panel.handle_click(mouse_pos)
            if action:
                self._handle_action_button(action)
                return

            # Check if click is on message area to open battle log
            if self.action_panel.is_message_area_click(mouse_pos[0], mouse_pos[1]):
                self.battle_log_popup.show()
                return

        # Handle unit popup clicks
        if self.unit_popup and self.unit_popup.visible:
            if self.unit_popup.handle_click(*mouse_pos):
                return
            if self.unit_popup.is_click_outside(*mouse_pos):
                self.unit_popup.hide()
                return

        # Handle weapon switch popup clicks
        if self.weapon_switch_popup and self.weapon_switch_popup.visible:
            action, new_main, new_off = self.weapon_switch_popup.handle_click(*mouse_pos)
            if action == "cancel":
                self.weapon_switch_popup.hide()
                return
            elif action == "apply":
                self._apply_weapon_switch(new_main, new_off)
                return
            # Check if click outside popup
            if self.weapon_switch_popup.is_click_outside(*mouse_pos):
                self.weapon_switch_popup.hide()
                return
            # If no action, click was inside popup but not on buttons
            return

        # Handle battle log popup
        if self.battle_log_popup and self.battle_log_popup.visible:
            if self.battle_log_popup.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": button, "pos": mouse_pos})):
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
            if self._active_special_attack == "charge":
                is_valid, error_msg = self.battle.validate_charge_target(current, target_pos)
                if is_valid:
                    self._execute_charge(target_pos)
                else:
                    self.action_executor.show_message(error_msg)
                # Exit special mode after an attempt
                self._active_special_attack = None
            else:
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
            action: Action name (e.g., "move", "attack", "end_turn", "special_attack_charge")
        """
        # Clear special mode if switching away
        if not action.startswith("special"):
            self._active_special_attack = None

        if action == "move":
            self._enter_move_mode()
        elif action == "attack":
            self._enter_attack_mode()
        elif action == "special":
            # Toggle special attacks dropdown (handled in action_panel)
            pass
        elif action == "special_attack_charge":
            self._enter_charge_mode()
        elif action == "switch_weapon":
            self._open_weapon_switch_popup()
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

        self._active_special_attack = None

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

        self._active_special_attack = None

        current = self.battle.current_unit
        can_attack, error_msg = self.battle.can_attack(current)
        if not can_attack:
            self.action_executor.show_message(error_msg)
            return

        self.action_mode = ActionMode.ATTACK
        self.selected_unit = current

    def _enter_charge_mode(self) -> None:
        """Enter charge special attack mode."""
        if self.battle.is_victory():
            return

        current = self.battle.current_unit
        if not current:
            self.action_executor.show_message("No active unit")
            return

        # Check if unit can perform charge (simplified; detail validation done during targeting)
        can_attack, error_msg = self.battle.can_attack(current)
        if not can_attack:
            self.action_executor.show_message("Cannot charge: " + error_msg)
            return

        self.action_mode = ActionMode.ATTACK  # Reuse attack mode for targeting
        self.selected_unit = current
        # Mark that this is a charge action (application layer detail)
        self._active_special_attack = "charge"
        self.action_executor.show_message("Select target for charge (min 5 hexes away)")

    def _enter_inspect_mode(self) -> None:
        """Enter inspect mode."""
        self.action_mode = ActionMode.INSPECT
        self.selected_unit = None
        self._active_special_attack = None

    def _cancel_action(self) -> None:
        """Cancel current action and return to idle."""
        self.action_mode = ActionMode.IDLE
        self.selected_unit = None
        self.movement_path = None
        self._active_special_attack = None

    def _execute_move(self, dest: Position) -> None:
        """Execute movement to destination."""
        current = self.battle.current_unit
        enemies = self.battle.get_enemies(current)

        summary = self.action_executor.execute_move(dest, enemies)

        # Enqueue opportunity attacks as reactions
        oa_results = summary.get("reaction_results") or summary.get("opportunity_attacks")
        if oa_results:
            self._enqueue_opportunity_attacks(oa_results)

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

    def _execute_charge(self, target_pos: Position) -> None:
        """Execute charge special attack on target position."""
        current = self.battle.current_unit
        target = self.battle.get_unit_at_position(target_pos)

        summary = self.action_executor.execute_charge(target_pos, current, target)

        # Enqueue opportunity attacks from charge movement BEFORE the charge happens
        oa_results = summary.get("reaction_results", [])
        if oa_results:
            self._enqueue_opportunity_attacks(oa_results)

        # Cancel action if no AP left
        if current and current.weapon:
            remaining_ap = self.battle.remaining_ap(current)
            if remaining_ap < 1:
                self._cancel_action()
        else:
            self._cancel_action()

        self._check_victory()

    def _rotate_current_unit(self, direction: int) -> None:
        """Rotate current unit."""
        self._active_special_attack = None
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
                self.unit_popup = UnitInfoPopup(context=self.context)
            self.unit_popup.show(unit)

    def _open_weapon_switch_popup(self) -> None:
        """Open weapon switch popup for current unit."""
        if self.battle.is_victory():
            return

        self._active_special_attack = None

        current = self.battle.current_unit
        if not current:
            self.action_executor.show_message("No active unit")
            return

        if not self.weapon_switch_popup:
            self.weapon_switch_popup = WeaponSwitchPopup(context=self.context)

        self.weapon_switch_popup.show(current)

    def _apply_weapon_switch(self, new_main_hand: str | None, new_off_hand: str | None) -> None:
        """Apply weapon switch selection.

        Args:
            new_main_hand: New main hand weapon ID
            new_off_hand: New off hand weapon ID
        """
        current = self.battle.current_unit
        if not current:
            self.action_executor.show_message("No active unit")
            return

        # Execute the weapon switch
        result = self.action_executor.execute_weapon_switch(current, new_main_hand, new_off_hand)

        if "error" not in result:
            self.weapon_switch_popup.hide()
            self._check_victory()
        # If error, message is already shown by action_executor

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

    def _enqueue_opportunity_attacks(self, oa_results) -> None:
        """Enqueue opportunity attacks as reactions for player decision.

        Args:
            oa_results: List of opportunity attack results from reaction handler
        """
        for idx, oa_result in enumerate(oa_results):
            # Extract unit names from the reaction result's data
            attacker_name = oa_result.data.get("attacker_name", "Unknown") if oa_result.data else "Unknown"
            defender_name = oa_result.data.get("defender_name", "Unknown") if oa_result.data else "Unknown"

            # Get attack result for additional info
            attack_result = oa_result.data.get("attack_result") if oa_result.data else None

            # Create description for the reaction popup
            description = f"{attacker_name} can make an opportunity attack against {defender_name}!"
            if attack_result and hasattr(attack_result, 'requires_dodge_check') and attack_result.requires_dodge_check:
                description += "\nDefender may dodge."

            # Enqueue as a reaction
            self.action_executor.enqueue_reaction(
                reaction_type="opportunity_attack",
                description=description,
                reaction_data={
                    "index": idx,
                    "attacker_name": attacker_name,
                    "defender_name": defender_name,
                    "result": oa_result,
                },
                on_accept=lambda data: self._accept_opportunity_attack(data),
                on_decline=lambda data: self._decline_opportunity_attack(data),
            )

    def _accept_opportunity_attack(self, reaction_data: dict) -> None:
        """Handle acceptance of an opportunity attack reaction.

        Args:
            reaction_data: Reaction data dict with attack details
        """
        # Show the attack result message
        oa_result = reaction_data.get("result")
        attacker_name = reaction_data.get("attacker_name", "Attacker")
        defender_name = reaction_data.get("defender_name", "Defender")

        # Extract and format the attack result
        if oa_result and oa_result.data:
            attack_result = oa_result.data.get("attack_result")
            if attack_result:
                # Format the attack result nicely
                msg = self.action_executor._format_attack_result_message(attack_result)
                full_msg = f"{attacker_name} -> {defender_name}:\n{msg}"
                self.action_executor.show_message(full_msg)

                # Also add to battle log with clear opportunity attack label
                if self.action_executor.detailed_log:
                    from domain.battle_log_entry import DetailedAttackData
                    attack_data = DetailedAttackData(
                        attacker_name=attacker_name,
                        defender_name=defender_name,
                        round_number=self.battle.round,
                        attack_roll=attack_result.attack_roll,
                        all_te=attack_result.all_te,
                        all_ve=attack_result.all_ve,
                        outcome=attack_result.outcome,
                        is_flank_attack=False,  # OA doesn't consider flanking
                        is_rear_attack=False,   # OA doesn't consider rear attacks
                        facing_ignored_ve=False,  # OA uses normal VÉ
                        hit_zone=attack_result.hit_zone,
                        zone_sfe=attack_result.zone_sfe,
                        damage_to_fp=attack_result.damage_to_fp,
                        damage_to_ep=attack_result.damage_to_ep,
                        armor_absorbed=attack_result.armor_absorbed,
                        stamina_spent_defender=attack_result.stamina_spent_defender,
                        is_critical=attack_result.is_critical,
                        is_overpower=attack_result.is_overpower,
                        is_opportunity_attack=True,
                    )
                    self.action_executor.detailed_log.log_attack(
                        f"{attacker_name} -> {defender_name}",
                        attack_data
                    )
            else:
                self.action_executor.show_message(f"{attacker_name} -> {defender_name}!")
        elif oa_result and hasattr(oa_result, "message"):
            self.action_executor.show_message(oa_result.message)
        else:
            self.action_executor.show_message(f"{attacker_name} -> {defender_name}!")

    def _decline_opportunity_attack(self, reaction_data: dict) -> None:
        """Handle declining of an opportunity attack reaction.

        Args:
            reaction_data: Reaction data dict with attack details
        """
        attacker_name = reaction_data.get("attacker_name", "Attacker")
        self.action_executor.show_message(f"{attacker_name}'s opportunity attack was declined")


    def _log_initiative(self, battle_service) -> None:
        """Log initiative roll data for all units.

        Args:
            battle_service: BattleService instance with initiative data
        """
        if battle_service.initiative_order is None:
            return  # Initiative not enabled

        # Get initiative table: (unit_id, total, base_ke, roll)
        table = battle_service.get_initiative_table()

        # Get units for name lookup
        unit_map = {unit.id: unit for unit in battle_service.units}

        # Log each unit's initiative in order
        for position, (unit_id, total, base_ke, roll) in enumerate(table, start=1):
            unit = unit_map.get(unit_id)
            if unit:
                self.detailed_log.log_initiative(unit.name, total, base_ke, roll, position)

    def update(self, delta_time: float = 1 / 60) -> None:
        """Update battle state (timers, etc)."""
        # Update message timer in action_executor and sync with action_panel
        if self.action_executor.combat_message_timer > 0:
            self.action_executor.combat_message_timer -= 1
            if self.action_executor.combat_message_timer <= 0:
                self.action_executor.combat_message = None

        # Update combat message in action panel
        self.action_panel.update_combat_message()

        # Update reaction popup if there's a pending reaction
        self._update_reaction_popup()

        # Check for auto-victory if not already detected
        if not self.action and self.battle.is_victory():
            self._check_victory()

    def _update_reaction_popup(self) -> None:
        """Update reaction popup visibility based on pending reactions."""
        if not self.reaction_popup:
            return

        current_reaction = self.action_executor.get_current_reaction()
        if current_reaction and not self.reaction_popup.visible:
            # Show the reaction popup
            self.reaction_popup.show(
                reaction_type=current_reaction["type"],
                description=current_reaction["description"],
                reaction_data=current_reaction["data"],
                on_result=lambda accepted: self.action_executor.resolve_reaction(accepted),
            )
        elif not current_reaction and self.reaction_popup.visible:
            # Hide popup if no more reactions
            self.reaction_popup.hide()

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the battle screen."""
        # Delegate rendering to render coordinator
        self.render_coordinator.draw_battle_scene(
            surface=surface,
            play_surface=self.play_surface,
            battle=self.battle,
            action_mode=self.action_mode,
            active_special_attack=self._active_special_attack,
            movement_path=self.movement_path,
            hovered_hex=self.input_handler.hovered_hex,
            combat_message=self.action_executor.combat_message,
            unit_popup=self.unit_popup,
            weapon_switch_popup=self.weapon_switch_popup,
            battle_log_popup=self.battle_log_popup,
            reaction_popup=self.reaction_popup,
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
