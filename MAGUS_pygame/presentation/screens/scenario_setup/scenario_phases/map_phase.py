"""Map selection phase - choose scenario/map."""

from __future__ import annotations

import pygame
from application.game_context import GameContext
from config import DEJAVU_FONT_PATH
from logger.logger import get_logger
from presentation.components.scenario_play.dropdown import Dropdown
from presentation.components.shared.map_preview import MapPreview

from .phase_base import SelectionPhaseBase

logger = get_logger(__name__)


class MapSelectionPhase(SelectionPhaseBase):
    """Map selection phase.
    
    Allows user to:
    - Browse available scenarios
    - Preview map layout with hex grid
    - See scenario name and description
    - Select background
    """
    
    def __init__(self, screen_width: int, screen_height: int, context: GameContext):
        """Initialize map selection phase.
        
        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
            context: Game context for data access
        """
        super().__init__(screen_width, screen_height, context)
        
        # Available scenarios
        self.available_scenarios = context.scenario_service.get_scenario_list()
        self.selected_index = 0
        
        # Cache for scenario data
        self._cached_scenario_name: str | None = None
        self._cached_scenario_data: dict | None = None
        self._cached_bg_surface: pygame.Surface | None = None
        self._cached_bg_file: str | None = None
        
        # UI Components
        self._setup_ui()
        
        # Fonts
        self.font_title = pygame.font.Font(DEJAVU_FONT_PATH, 40)
        self.font_small = pygame.font.Font(DEJAVU_FONT_PATH, 16)
        
        # Colors
        self.color_bg = (20, 20, 30)
        self.color_text = (255, 255, 255)
        self.color_instructions = (180, 180, 180)
        
        logger.info(f"Map selection phase initialized: {len(self.available_scenarios)} scenarios")
    
    def _setup_ui(self) -> None:
        """Setup UI components."""
        # Scenario dropdown (top of screen, centered)
        dropdown_width = 500
        dropdown_height = 40
        self.scenario_dropdown = Dropdown(
            x=(self.screen_width - dropdown_width) // 2,
            y=120,
            width=dropdown_width,
            height=dropdown_height,
            options=self.available_scenarios,
            default_index=0,
            label="Scenario"
        )
        
        # Map preview (centered, below dropdown)
        preview_width = 700
        preview_height = 500
        preview_y = 120 + dropdown_height + 20
        self.map_preview = MapPreview(
            x=(self.screen_width - preview_width) // 2,
            y=preview_y,
            width=preview_width,
            height=preview_height
        )
    
    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle input events.
        
        Args:
            event: Pygame event
        """
        # Pass events to dropdown
        map_changed = self.scenario_dropdown.handle_event(event)
        if map_changed:
            self.selected_index = self.scenario_dropdown.get_selected_index()
            # Clear cache when selection changes
            self._cached_scenario_name = None
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # Close dropdown if open, otherwise cancel
                if self.scenario_dropdown.is_open:
                    self.scenario_dropdown.is_open = False
                else:
                    self.cancelled = True
                    logger.info("Map selection cancelled")
            elif event.key == pygame.K_RETURN:
                self._confirm_selection()
            elif event.key == pygame.K_UP:
                if self.scenario_dropdown.cycle(-1):
                    self.selected_index = self.scenario_dropdown.get_selected_index()
                    self._cached_scenario_name = None
            elif event.key == pygame.K_DOWN:
                if self.scenario_dropdown.cycle(1):
                    self.selected_index = self.scenario_dropdown.get_selected_index()
                    self._cached_scenario_name = None
    
    def _confirm_selection(self) -> None:
        """Confirm map selection and register with service."""
        scenario_name = self.available_scenarios[self.selected_index]
        bg_file = self.context.scenario_service.get_background_path(scenario_name)
        self.context.scenario_service.set_map(scenario_name)
        self.completed = True
        logger.info(f"Map selected: {scenario_name} (bg: {bg_file})")
    
    def draw(self, surface: pygame.Surface) -> None:
        """Draw map selection screen.
        
        Args:
            surface: Surface to draw on
        """
        # Background
        surface.fill(self.color_bg)
        
        # Title
        title = self.font_title.render("Select Map", True, self.color_text)
        title_rect = title.get_rect(center=(self.screen_width // 2, 50))
        surface.blit(title, title_rect)
        
        # Get selected scenario
        scenario_name = self.available_scenarios[self.selected_index]
        
        # Load scenario data only if changed (cache it!)
        if self._cached_scenario_name != scenario_name:
            self._cached_scenario_name = scenario_name
            self._cached_scenario_data = self.context.scenario_service.get_scenario_preview_data(scenario_name)
            
            # Get background from scenario data
            if self._cached_scenario_data:
                bg_filename = self._cached_scenario_data.get('background')
                self._cached_bg_file = bg_filename
                if bg_filename:
                    self._cached_bg_surface = self.context.sprite_repo.load_background(bg_filename)
                else:
                    self._cached_bg_surface = None
            else:
                self._cached_bg_file = None
                self._cached_bg_surface = None
        
        # Use display name from scenario data if available
        display_name = self._cached_scenario_data.get('name') if self._cached_scenario_data else scenario_name
        self.map_preview.draw(
            surface,
            display_name,
            self._cached_bg_surface,
            self._cached_bg_file,
            self._cached_scenario_data
        )
        
        # Draw dropdown last so it appears on top
        self.scenario_dropdown.draw(surface)
        
        # Instructions
        self._draw_instructions(surface)
    
    def _draw_instructions(self, surface: pygame.Surface) -> None:
        """Draw control instructions."""
        y = self.screen_height - 40
        instructions = "Click dropdown or ↑↓: Select Map  |  Enter: Confirm  |  ESC: Cancel"
        
        inst_surf = self.font_small.render(instructions, True, self.color_instructions)
        inst_rect = inst_surf.get_rect(center=(self.screen_width // 2, y))
        surface.blit(inst_surf, inst_rect)
    
    def can_proceed(self) -> bool:
        """Check if can proceed to next phase.
        
        Returns:
            True (can always select a map from available list)
        """
        return True
    
    def get_selected_map(self) -> str:
        """Get selected map name.
        
        Returns:
            Selected scenario name
        """
        return self.available_scenarios[self.selected_index]
