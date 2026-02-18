"""
Scenario selector coordinator - manages phase-based selection flow.

Flow:
1. Map selection
2. Team A composition
3. Team B composition
4. Equipment selection (optional)
5. Proceed to deployment

This coordinator delegates to phase-specific screens for cleaner separation.
"""

from enum import Enum

import pygame
from application.game_context import GameContext
from config import DEJAVU_FONT_PATH, load_font
from domain.value_objects import ScenarioConfig
from logger.logger import get_logger
from presentation.screens.scenario_setup.scenario_phases import (
    EquipmentPhase,
    MapSelectionPhase,
    SelectionPhaseBase,
    TeamCompositionPhase,
)

logger = get_logger(__name__)


class FlowPhase(Enum):
    """Current phase in selection flow."""

    MAP = "map"
    TEAM_A = "team_a"
    TEAM_B = "team_b"
    EQUIPMENT = "equipment"


class ScenarioScreen:
    """Scenario selector coordinator with modular phase architecture.

    Manages 4-phase selection flow by delegating to phase-specific screens:
    - MapSelectionPhase: Map/scenario selection
    - TeamCompositionPhase: Team roster building (used twice)
    - EquipmentPhase: Equipment selection (TODO)

    Benefits:
    - Each phase is isolated and testable
    - Easy to add new phases (e.g., tactical options, handicaps)
    - Clear separation of concerns
    - Reusable team composition logic

    Emits action strings:
    - "scenario_confirmed": User completed all phases
    - "scenario_cancelled": User cancelled selection
    """

    def __init__(self, screen_width: int, screen_height: int, context: GameContext):
        """Initialize scenario selector coordinator.

        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
            context: Game context for data access
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.context = context

        # Flow state
        self.current_phase = FlowPhase.MAP
        self.action: str | None = None

        # Phase screens (lazy-initialized)
        self.map_phase: MapSelectionPhase | None = None
        self.team_a_phase: TeamCompositionPhase | None = None
        self.team_b_phase: TeamCompositionPhase | None = None
        self.equipment_phase: EquipmentPhase | None = None

        # Fonts for navigation UI
        self.font_normal = load_font(DEJAVU_FONT_PATH, 24)

        # Colors
        self.color_bg = (20, 20, 30)
        self.color_text = (255, 255, 255)
        self.color_button = (60, 60, 80)
        self.color_button_hover = (80, 80, 100)
        self.color_disabled = (40, 40, 50)

        # Navigation buttons
        self.button_next = pygame.Rect(screen_width - 250, screen_height - 70, 200, 50)
        self.button_back = pygame.Rect(50, screen_height - 70, 200, 50)

        # Initialize first phase
        self._init_current_phase()

        logger.info("Scenario selector coordinator (v2) initialized with modular phases")

    def _init_current_phase(self) -> None:
        """Initialize the current phase screen."""
        if self.current_phase == FlowPhase.MAP:
            self.map_phase = MapSelectionPhase(self.screen_width, self.screen_height, self.context)
            logger.debug("Initialized map selection phase")

        elif self.current_phase == FlowPhase.TEAM_A:
            self.team_a_phase = TeamCompositionPhase(
                self.screen_width,
                self.screen_height,
                self.context,
                is_team_a=True,
                team_name="Team A (Blue)",
            )
            logger.debug("Initialized Team A composition phase")

        elif self.current_phase == FlowPhase.TEAM_B:
            self.team_b_phase = TeamCompositionPhase(
                self.screen_width,
                self.screen_height,
                self.context,
                is_team_a=False,
                team_name="Team B (Red)",
            )
            logger.debug("Initialized Team B composition phase")

        elif self.current_phase == FlowPhase.EQUIPMENT:
            team_a_size = len(self.context.scenario_service.get_team(True))
            team_b_size = len(self.context.scenario_service.get_team(False))
            self.equipment_phase = EquipmentPhase(
                self.screen_width, self.screen_height, self.context, team_a_size, team_b_size
            )
            logger.debug("Initialized equipment phase")

    def _get_current_phase_screen(self) -> SelectionPhaseBase | None:
        """Get the current phase screen instance.

        Returns:
            Current phase screen or None
        """
        if self.current_phase == FlowPhase.MAP:
            return self.map_phase
        elif self.current_phase == FlowPhase.TEAM_A:
            return self.team_a_phase
        elif self.current_phase == FlowPhase.TEAM_B:
            return self.team_b_phase
        elif self.current_phase == FlowPhase.EQUIPMENT:
            return self.equipment_phase
        return None

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle input events.

        Args:
            event: Pygame event
        """
        phase_screen = self._get_current_phase_screen()
        if not phase_screen:
            return

        # Pass event to current phase
        phase_screen.handle_event(event)

        # Check phase completion
        if phase_screen.is_completed():
            self._advance_phase()
        elif phase_screen.is_cancelled():
            self._go_back()

        # Navigation buttons
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.button_next.collidepoint(event.pos) and phase_screen.can_proceed():
                # For map phase, ensure selection is confirmed before advancing
                if self.current_phase == FlowPhase.MAP and hasattr(
                    phase_screen, "_confirm_selection"
                ):
                    phase_screen._confirm_selection()
                phase_screen.completed = True
                self._advance_phase()
            elif self.button_back.collidepoint(event.pos) and self.current_phase != FlowPhase.MAP:
                self._go_back()

    def _advance_phase(self) -> None:
        """Advance to next phase in flow."""
        if self.current_phase == FlowPhase.MAP:
            self.current_phase = FlowPhase.TEAM_A
            self._init_current_phase()

        elif self.current_phase == FlowPhase.TEAM_A:
            self.current_phase = FlowPhase.TEAM_B
            self._init_current_phase()

        elif self.current_phase == FlowPhase.TEAM_B:
            self.current_phase = FlowPhase.EQUIPMENT
            self._init_current_phase()

        elif self.current_phase == FlowPhase.EQUIPMENT:
            # Build final config and complete
            self.action = "scenario_confirmed"
            logger.info("Scenario selection completed - all phases done")

    def _go_back(self) -> None:
        """Go back to previous phase."""
        if self.current_phase == FlowPhase.TEAM_A:
            self.current_phase = FlowPhase.MAP
            if self.map_phase:
                self.map_phase.reset()

        elif self.current_phase == FlowPhase.TEAM_B:
            self.current_phase = FlowPhase.TEAM_A
            if self.team_a_phase:
                self.team_a_phase.reset()

        elif self.current_phase == FlowPhase.EQUIPMENT:
            self.current_phase = FlowPhase.TEAM_B
            if self.team_b_phase:
                self.team_b_phase.reset()

        elif self.current_phase == FlowPhase.MAP:
            # Cancel from first phase
            self.action = "scenario_cancelled"
            logger.info("Scenario selection cancelled from map phase")

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the current phase screen with navigation.

        Args:
            surface: Surface to draw on
        """
        # Draw current phase
        phase_screen = self._get_current_phase_screen()
        if phase_screen:
            phase_screen.draw(surface)

        # Draw navigation buttons (overlay)
        self._draw_navigation_buttons(surface)

    def _draw_navigation_buttons(self, surface: pygame.Surface) -> None:
        """Draw next/back navigation buttons."""
        phase_screen = self._get_current_phase_screen()
        if not phase_screen:
            return

        # Back button (not on first phase)
        if self.current_phase != FlowPhase.MAP:
            pygame.draw.rect(surface, self.color_button, self.button_back)
            back_text = self.font_normal.render("Back", True, self.color_text)
            back_rect = back_text.get_rect(center=self.button_back.center)
            surface.blit(back_text, back_rect)

        # Next button (with validation)
        can_proceed = phase_screen.can_proceed()
        button_color = self.color_button_hover if can_proceed else self.color_disabled
        pygame.draw.rect(surface, button_color, self.button_next)

        # Label changes on final phase
        next_label = "Start" if self.current_phase == FlowPhase.EQUIPMENT else "Next"
        next_color = self.color_text if can_proceed else (100, 100, 100)
        next_text = self.font_normal.render(next_label, True, next_color)
        next_rect = next_text.get_rect(center=self.button_next.center)
        surface.blit(next_text, next_rect)

    def get_action(self) -> str | None:
        """Get emitted action (if any).

        Returns:
            Action string or None
        """
        return self.action

    def get_config(self) -> ScenarioConfig:
        """Get configured scenario.

        Returns:
            Configured ScenarioConfig
        """
        return self.context.scenario_service.build_config()

    def is_complete(self) -> bool:
        """Check if selection is complete.

        Returns:
            True if confirmed or cancelled
        """
        return self.action is not None
