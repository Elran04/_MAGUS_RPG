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
from presentation.screens.game.battle.battle_action_executor import BattleActionExecutor
from presentation.screens.game.battle.battle_action_mode import ActionMode
from presentation.screens.game.battle.battle_action_mode_manager import BattleActionModeManager
from presentation.screens.game.battle.battle_input_handler import BattleInputHandler
from presentation.screens.game.battle.battle_keyboard_handler import BattleKeyboardHandler
from presentation.screens.game.battle.battle_outcome import BattleOutcomeResolver
from presentation.screens.game.battle.battle_popups import BattlePopupManager
from presentation.screens.game.battle.battle_reaction_coordinator import BattleReactionCoordinator
from presentation.screens.game.battle.battle_render_coordinator import BattleRenderCoordinator
from presentation.screens.game.battle.battle_special_attacks import SpecialAttackRegistry

logger = get_logger(__name__)


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
        self._action_mode_explicitly_set = False  # Track if user explicitly chose an action mode

        # Detailed battle log system
        self.detailed_log = DetailedBattleLog()
        if battle_service is not None:
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
        self.input_handler = BattleInputHandler(battle_screen=self)
        self.action_executor = BattleActionExecutor(battle_service, self.detailed_log)
        self.reaction_coordinator = BattleReactionCoordinator(
            self.action_executor, battle_service, self.detailed_log
        )
        self.render_coordinator = BattleRenderCoordinator(
            screen_width, screen_height, self.renderer, self.action_panel, self.hud, self.pause_menu
        )

        # Battle state managers
        self.special_attacks = SpecialAttackRegistry(battle_service, self.action_executor)
        self.popup_manager = BattlePopupManager()
        self.popup_manager.set_popups(
            self.unit_popup, self.weapon_switch_popup, self.battle_log_popup, self.reaction_popup
        )
        self.outcome_resolver = BattleOutcomeResolver(battle_service, self.action_executor)
        self.keyboard_handler = BattleKeyboardHandler(self)
        self.action_mode_manager = BattleActionModeManager(self)

        if battle_service is not None:
            logger.info(f"BattleScreen initialized with {len(battle_service.units)} units")
        else:
            logger.info("BattleScreen initialized (battle service will be set later)")
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

        # Delegate all input handling to input_handler
        self.input_handler.handle_event(event)



    def _enter_move_mode(self) -> None:
        """Enter movement mode."""
        self.action_mode_manager.enter_move_mode()

    def _enter_attack_mode(self) -> None:
        """Enter attack mode."""
        self.action_mode_manager.enter_attack_mode()

    def _enter_charge_mode(self) -> None:
        """Enter charge special attack mode."""
        self.action_mode_manager.enter_charge_mode()

    def _enter_dagger_combo_mode(self) -> None:
        """Enter dagger attack combination special attack mode."""
        self.action_mode_manager.enter_dagger_combo_mode()

    def _enter_shield_bash_mode(self) -> None:
        """Enter shield bash special attack mode."""
        self.action_mode_manager.enter_shield_bash_mode()

    # These wrapper methods now delegate to the consolidated methods in BattleActionModeManager.

    def _enter_inspect_mode(self) -> None:
        """Enter inspect mode."""
        self.action_mode_manager.enter_inspect_mode()

    def _cancel_action(self) -> None:
        """Cancel current action and return to idle."""
        self.action_mode_manager.cancel_action()

    def _open_weapon_switch_popup(self) -> None:
        """Open weapon switch popup (delegates to input handler)."""
        self.input_handler._open_weapon_switch_popup()

    def _execute_move(self, dest: Position) -> None:
        """Execute movement to destination."""
        current = self.battle.current_unit
        enemies = self.battle.get_enemies(current)

        summary = self.action_executor.execute_move(dest, enemies)

        # Enqueue opportunity attacks as reactions
        oa_results = summary.get("reaction_results") or summary.get("opportunity_attacks")
        if oa_results:
            self.reaction_coordinator.enqueue_opportunity_attacks(oa_results)

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
        summary = self.action_executor.execute_attack(target_pos, current, target)

        # Handle post-attack reactions (counterattacks, shield bash)
        if summary:
            reaction_results = summary.get("reaction_results")
            if reaction_results:
                self.reaction_coordinator.enqueue_post_attack_reactions(reaction_results)

        # Only cancel attack mode if no more AP
        self._cancel_if_no_ap(current)

        self._check_victory()

    def _execute_charge(self, target_pos: Position) -> None:
        """Execute charge special attack on target position."""
        current = self.battle.current_unit
        target = self.battle.get_unit_at_position(target_pos)

        summary = self.action_executor.execute_charge(target_pos, current, target)

        # Enqueue opportunity attacks from charge movement BEFORE the charge happens
        oa_results = summary.get("reaction_results", [])
        if oa_results:
            self.reaction_coordinator.enqueue_opportunity_attacks(oa_results)

        # Cancel action if no AP left
        self._cancel_if_no_ap(current)

        self._check_victory()

    def _execute_dagger_combo(self, target_pos: Position) -> None:
        """Execute dagger attack combination special attack on target position."""
        current = self.battle.current_unit
        target = self.battle.get_unit_at_position(target_pos)

        summary = self.action_executor.execute_attack_combination(target_pos, current, target)

        if "error" in summary:
            self._cancel_action()
        else:
            self._cancel_if_no_ap(current)

        self._check_victory()

    def _execute_shield_bash(self, target_pos: Position) -> None:
        """Execute shield bash special attack on target position."""
        current = self.battle.current_unit
        target = self.battle.get_unit_at_position(target_pos)

        summary = self.action_executor.execute_shield_bash(target_pos, current, target)

        if "error" in summary:
            self._cancel_action()
        else:
            self._cancel_if_no_ap(current)

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
            self.popup_manager.show_unit_info(unit, self.context)

    def _check_victory(self) -> None:
        """Check for victory and handle it."""
        self.action = self.outcome_resolver.check_victory()

    def _cancel_if_no_ap(self, current: Unit | None) -> None:
        """Cancel current action if the unit has no action points remaining."""
        if current and current.weapon:
            remaining_ap = self.battle.remaining_ap(current)
            if remaining_ap < 1:
                self._cancel_action()
        else:
            self._cancel_action()

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
            action_mode=self.action_mode.value,
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
