"""
Scenario selector screen for map and team composition.

Three-phase selection process:
1. Map selection - Choose scenario/map
2. Team A composition - Select characters and sprites for team A
3. Team B composition - Select characters and sprites for team B
"""

import os
import json
import pygame
from pathlib import Path
from typing import Optional, Any
from enum import Enum

from config import CHARACTERS_DIR, BACKGROUND_SPRITES_DIR, CHARACTER_SPRITES_DIR, SCENARIOS_DIR
from domain.value_objects import ScenarioConfig, UnitSetup
from application.game_context import GameContext
from presentation.components.character_preview import CharacterPreview
from presentation.components.map_preview import MapPreview
from presentation.components.roster_panel import RosterPanel
from logger.logger import get_logger

logger = get_logger(__name__)


class SelectionPhase(Enum):
    """Current phase of scenario selection."""
    MAP = "map"
    TEAM_A = "team_a"
    TEAM_B = "team_b"


class ScenarioScreen:
    """Scenario selector screen with map and team composition.
    
    Manages three-phase selection flow:
    1. Map selection with background preview
    2. Team A character/sprite selection with preview
    3. Team B character/sprite selection with preview
    
    Emits action strings for application layer:
    - "scenario_confirmed": User completed selection
    - "scenario_cancelled": User cancelled selection
    """
    
    def __init__(self, screen_width: int, screen_height: int, context: GameContext):
        """Initialize scenario selector screen.
        
        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
            context: Game context for data access
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.context = context
        
        # State
        self.phase = SelectionPhase.MAP
        self.action: Optional[str] = None
        self.config = ScenarioConfig()
        
        # Available options (scanned from filesystem)
        self.available_scenarios = self._scan_scenarios()
        self.available_characters = self._scan_characters()
        self.available_sprites = self._scan_sprites()
        
        # Selection indices
        self.selected_map_index = 0
        self.current_char_index = 0
        self.current_sprite_index = 0
        
        # Team rosters (using mutable lists during selection, converted to tuple in config)
        self.team_a_roster: list[UnitSetup] = []
        self.team_b_roster: list[UnitSetup] = []
        
        # Caches
        self._character_cache: dict[str, dict[str, Any]] = {}
        self._sprite_cache: dict[str, pygame.Surface] = {}
        self._background_cache: dict[str, pygame.Surface] = {}
        
        # UI Components
        self._setup_ui_components()
        
        # Fonts
        self.font_title = pygame.font.Font(None, 48)
        self.font_normal = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        
        # Colors
        self.color_bg = (20, 20, 30)
        self.color_text = (255, 255, 255)
        self.color_highlight = (255, 215, 0)
        self.color_button = (60, 60, 80)
        self.color_button_hover = (80, 80, 100)
        self.color_disabled = (40, 40, 50)
        self.color_instructions = (180, 180, 180)
        
        # Buttons
        self.button_next = pygame.Rect(screen_width - 250, screen_height - 80, 200, 50)
        self.button_back = pygame.Rect(50, screen_height - 80, 200, 50)
        self.button_add_unit = pygame.Rect(screen_width // 2 - 100, screen_height - 180, 200, 50)
        
        logger.info(f"ScenarioScreen initialized: {len(self.available_scenarios)} scenarios, "
                   f"{len(self.available_characters)} characters, {len(self.available_sprites)} sprites")
    
    def _setup_ui_components(self) -> None:
        """Setup UI components (preview panels, roster bar)."""
        # Map preview (right side)
        self.map_preview = MapPreview(
            x=self.screen_width - 360,
            y=120,
            width=320,
            height=400
        )
        
        # Character preview (right side)
        self.character_preview = CharacterPreview(
            x=self.screen_width - 340,
            y=120,
            width=300,
            height=460
        )
        
        # Roster panel (bottom)
        self.roster_panel = RosterPanel(
            x=40,
            y=self.screen_height - 230,
            width=self.screen_width - 80,
            height=110
        )
        self.roster_panel.set_data_paths(CHARACTERS_DIR, CHARACTER_SPRITES_DIR)
    
    def _scan_scenarios(self) -> list[str]:
        """Scan for available scenario files.
        
        Returns:
            List of scenario names (without .json extension)
        """
        try:
            files = [f.stem for f in SCENARIOS_DIR.iterdir() if f.suffix == '.json']
            return sorted(files) if files else ["default"]
        except Exception as e:
            logger.warning(f"Failed to scan scenarios: {e}")
            return ["default"]
    
    def _scan_characters(self) -> list[str]:
        """Scan for available character files.
        
        Returns:
            List of character filenames
        """
        try:
            files = [f.name for f in CHARACTERS_DIR.iterdir() if f.suffix == '.json']
            return sorted(files)
        except Exception as e:
            logger.warning(f"Failed to scan characters: {e}")
            return []
    
    def _scan_sprites(self) -> list[str]:
        """Scan for available character sprite files.
        
        Returns:
            List of sprite filenames (filtered to exclude backgrounds)
        """
        try:
            files = [
                f.name for f in CHARACTER_SPRITES_DIR.iterdir()
                if f.suffix.lower() in ['.png', '.jpg', '.jpeg']
                and 'bg' not in f.name.lower()
                and 'silhouette' not in f.name.lower()
            ]
            return sorted(files)
        except Exception as e:
            logger.warning(f"Failed to scan sprites: {e}")
            return []
    
    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle input events.
        
        Args:
            event: Pygame event
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.action = "scenario_cancelled"
                logger.info("Scenario selection cancelled")
            elif event.key == pygame.K_RETURN:
                self._handle_next()
            elif event.key == pygame.K_UP:
                self._move_selection(-1)
            elif event.key == pygame.K_DOWN:
                self._move_selection(1)
            elif event.key == pygame.K_LEFT:
                self._cycle_sprite(-1)
            elif event.key == pygame.K_RIGHT:
                self._cycle_sprite(1)
            elif event.key == pygame.K_SPACE:
                if self.phase in [SelectionPhase.TEAM_A, SelectionPhase.TEAM_B]:
                    self._add_current_unit()
            elif event.key == pygame.K_BACKSPACE:
                self._remove_last_unit()
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                self._handle_click(event.pos)
    
    def _move_selection(self, direction: int) -> None:
        """Move selection cursor up/down.
        
        Args:
            direction: -1 for up, 1 for down
        """
        if self.phase == SelectionPhase.MAP:
            self.selected_map_index = (self.selected_map_index + direction) % len(self.available_scenarios)
        elif self.phase in [SelectionPhase.TEAM_A, SelectionPhase.TEAM_B]:
            if self.available_characters:
                self.current_char_index = (self.current_char_index + direction) % len(self.available_characters)
                self._ensure_character_cached(self.available_characters[self.current_char_index])
    
    def _cycle_sprite(self, direction: int) -> None:
        """Cycle through sprite options left/right.
        
        Args:
            direction: -1 for left, 1 for right
        """
        if self.phase in [SelectionPhase.TEAM_A, SelectionPhase.TEAM_B]:
            if self.available_sprites:
                self.current_sprite_index = (self.current_sprite_index + direction) % len(self.available_sprites)
                self._ensure_sprite_cached(self.available_sprites[self.current_sprite_index])
    
    def _add_current_unit(self) -> None:
        """Add currently selected character+sprite to active team roster."""
        if not self.available_characters or not self.available_sprites:
            logger.warning("Cannot add unit: no characters or sprites available")
            return
        
        char_file = self.available_characters[self.current_char_index]
        sprite_file = self.available_sprites[self.current_sprite_index]
        
        unit_setup = UnitSetup(character_file=char_file, sprite_file=sprite_file)
        
        if self.phase == SelectionPhase.TEAM_A:
            self.team_a_roster.append(unit_setup)
            logger.debug(f"Added unit to Team A: {char_file} / {sprite_file}")
        elif self.phase == SelectionPhase.TEAM_B:
            self.team_b_roster.append(unit_setup)
            logger.debug(f"Added unit to Team B: {char_file} / {sprite_file}")
        
        # Warm caches
        self._ensure_character_cached(char_file)
        self._ensure_sprite_cached(sprite_file)
    
    def _remove_last_unit(self) -> None:
        """Remove last unit from active team roster."""
        if self.phase == SelectionPhase.TEAM_A and self.team_a_roster:
            removed = self.team_a_roster.pop()
            logger.debug(f"Removed unit from Team A: {removed.character_file}")
        elif self.phase == SelectionPhase.TEAM_B and self.team_b_roster:
            removed = self.team_b_roster.pop()
            logger.debug(f"Removed unit from Team B: {removed.character_file}")
    
    def _handle_next(self) -> None:
        """Handle next button / Enter key."""
        if self.phase == SelectionPhase.MAP:
            # Confirm map selection
            scenario_name = self.available_scenarios[self.selected_map_index]
            bg_file = self._find_background_for_scenario(scenario_name)
            self.config = self.config.with_map(scenario_name, bg_file or "grass_bg.jpg")
            self.phase = SelectionPhase.TEAM_A
            logger.info(f"Map selected: {scenario_name} (bg: {bg_file})")
        
        elif self.phase == SelectionPhase.TEAM_A:
            if len(self.team_a_roster) > 0:
                self.config = self.config.with_team_a(self.team_a_roster)
                self.phase = SelectionPhase.TEAM_B
                logger.info(f"Team A confirmed: {len(self.team_a_roster)} units")
        
        elif self.phase == SelectionPhase.TEAM_B:
            if len(self.team_b_roster) > 0:
                self.config = self.config.with_team_b(self.team_b_roster)
                self.action = "scenario_confirmed"
                logger.info(f"Team B confirmed: {len(self.team_b_roster)} units - Scenario complete")
    
    def _handle_back(self) -> None:
        """Handle back button."""
        if self.phase == SelectionPhase.TEAM_B:
            self.phase = SelectionPhase.TEAM_A
            logger.debug("Back to Team A selection")
        elif self.phase == SelectionPhase.TEAM_A:
            self.phase = SelectionPhase.MAP
            logger.debug("Back to map selection")
    
    def _handle_click(self, pos: tuple[int, int]) -> None:
        """Handle mouse click.
        
        Args:
            pos: Mouse position (x, y)
        """
        if self.button_next.collidepoint(pos):
            self._handle_next()
        elif self.button_back.collidepoint(pos):
            self._handle_back()
        elif self.button_add_unit.collidepoint(pos) and self.phase in [SelectionPhase.TEAM_A, SelectionPhase.TEAM_B]:
            self._add_current_unit()
    
    def _find_background_for_scenario(self, scenario_name: str) -> Optional[str]:
        """Find background image matching scenario name.
        
        Tries png, jpg, jpeg extensions.
        
        Args:
            scenario_name: Scenario name
            
        Returns:
            Background filename or None if not found
        """
        candidates = [f"{scenario_name}.png", f"{scenario_name}.jpg", f"{scenario_name}.jpeg"]
        for candidate in candidates:
            path = BACKGROUND_SPRITES_DIR / candidate
            if path.exists():
                return candidate
        return None
    
    def _ensure_character_cached(self, filename: str) -> None:
        """Load and cache character data.
        
        Args:
            filename: Character filename
        """
        if filename in self._character_cache:
            return
        
        path = CHARACTERS_DIR / filename
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
                self._character_cache[filename] = data
                logger.debug(f"Cached character data: {filename}")
        except Exception as e:
            logger.error(f"Failed to load character {filename}: {e}")
            self._character_cache[filename] = {}
    
    def _ensure_sprite_cached(self, filename: str) -> None:
        """Load and cache sprite surface.
        
        Args:
            filename: Sprite filename
        """
        if filename in self._sprite_cache:
            return
        
        path = CHARACTER_SPRITES_DIR / filename
        try:
            img = pygame.image.load(str(path)).convert_alpha()
            self._sprite_cache[filename] = img
            logger.debug(f"Cached sprite: {filename}")
        except Exception as e:
            logger.error(f"Failed to load sprite {filename}: {e}")
            # Fallback surface
            fallback = pygame.Surface((96, 96), pygame.SRCALPHA)
            fallback.fill((60, 60, 60, 200))
            pygame.draw.line(fallback, (180, 180, 180), (0, 0), (96, 96), 2)
            pygame.draw.line(fallback, (180, 180, 180), (0, 96), (96, 0), 2)
            self._sprite_cache[filename] = fallback
    
    def _ensure_background_cached(self, filename: str) -> None:
        """Load and cache background surface.
        
        Args:
            filename: Background filename
        """
        if filename in self._background_cache:
            return
        
        path = BACKGROUND_SPRITES_DIR / filename
        try:
            img = pygame.image.load(str(path)).convert()
            self._background_cache[filename] = img
            logger.debug(f"Cached background: {filename}")
        except Exception as e:
            logger.error(f"Failed to load background {filename}: {e}")
    
    def draw(self, surface: pygame.Surface) -> None:
        """Draw the scenario selector screen.
        
        Args:
            surface: Surface to draw on
        """
        # Background
        surface.fill(self.color_bg)
        
        # Title based on phase
        title_text = {
            SelectionPhase.MAP: "Select Map",
            SelectionPhase.TEAM_A: "Setup Team A (Blue)",
            SelectionPhase.TEAM_B: "Setup Team B (Red)"
        }[self.phase]
        
        title = self.font_title.render(title_text, True, self.color_text)
        title_rect = title.get_rect(center=(self.screen_width // 2, 50))
        surface.blit(title, title_rect)
        
        # Phase-specific content
        if self.phase == SelectionPhase.MAP:
            self._draw_map_selection(surface)
        elif self.phase == SelectionPhase.TEAM_A:
            self._draw_team_setup(surface, is_team_a=True)
        elif self.phase == SelectionPhase.TEAM_B:
            self._draw_team_setup(surface, is_team_a=False)
        
        # Buttons
        self._draw_buttons(surface)
        
        # Instructions
        self._draw_instructions(surface)
    
    def _draw_map_selection(self, surface: pygame.Surface) -> None:
        """Draw map selection list and preview."""
        # Map list (center)
        y_start = 150
        for i, scenario_name in enumerate(self.available_scenarios):
            color = self.color_highlight if i == self.selected_map_index else self.color_text
            prefix = '>' if i == self.selected_map_index else ' '
            text = self.font_normal.render(f"{prefix} {scenario_name}", True, color)
            rect = text.get_rect(center=(self.screen_width // 2, y_start + i * 50))
            surface.blit(text, rect)
        
        # Map preview (right side)
        scenario_name = self.available_scenarios[self.selected_map_index]
        bg_file = self._find_background_for_scenario(scenario_name)
        
        bg_surface = None
        if bg_file:
            self._ensure_background_cached(bg_file)
            bg_surface = self._background_cache.get(bg_file)
        
        self.map_preview.draw(surface, scenario_name, bg_surface, bg_file)
    
    def _draw_team_setup(self, surface: pygame.Surface, is_team_a: bool) -> None:
        """Draw team setup UI with character selection and preview.
        
        Args:
            surface: Surface to draw on
            is_team_a: True for team A, False for team B
        """
        # Current selection info (left side)
        y = 120
        
        if self.available_characters:
            char_text = f"Character: {self.available_characters[self.current_char_index]}"
            char_surf = self.font_normal.render(char_text, True, self.color_highlight)
            surface.blit(char_surf, (50, y))
        y += 50
        
        if self.available_sprites:
            sprite_text = f"Sprite: {self.available_sprites[self.current_sprite_index]}"
            sprite_surf = self.font_normal.render(sprite_text, True, self.color_highlight)
            surface.blit(sprite_surf, (50, y))
        y += 50
        
        hint = self.font_small.render("Character preview & roster shown →", True, self.color_instructions)
        surface.blit(hint, (50, y))
        
        # Character preview (right side)
        if self.available_characters and self.available_sprites:
            char_file = self.available_characters[self.current_char_index]
            sprite_file = self.available_sprites[self.current_sprite_index]
            
            self._ensure_character_cached(char_file)
            self._ensure_sprite_cached(sprite_file)
            
            char_data = self._character_cache.get(char_file)
            sprite_surf = self._sprite_cache.get(sprite_file)
            
            self.character_preview.draw(surface, char_data, sprite_surf, char_file, sprite_file)
        
        # Roster panel (bottom)
        roster = self.team_a_roster if is_team_a else self.team_b_roster
        team_name = "Team A Roster" if is_team_a else "Team B Roster"
        self.roster_panel.draw(surface, team_name, roster, is_team_a)
    
    def _draw_buttons(self, surface: pygame.Surface) -> None:
        """Draw navigation buttons."""
        # Back button (not on map phase)
        if self.phase != SelectionPhase.MAP:
            pygame.draw.rect(surface, self.color_button, self.button_back)
            back_text = self.font_normal.render("Back", True, self.color_text)
            back_rect = back_text.get_rect(center=self.button_back.center)
            surface.blit(back_text, back_rect)
        
        # Next button (with validation)
        can_proceed = self._can_proceed()
        button_color = self.color_button_hover if can_proceed else self.color_disabled
        pygame.draw.rect(surface, button_color, self.button_next)
        
        next_label = "Start" if self.phase == SelectionPhase.TEAM_B else "Next"
        next_color = self.color_text if can_proceed else (100, 100, 100)
        next_text = self.font_normal.render(next_label, True, next_color)
        next_rect = next_text.get_rect(center=self.button_next.center)
        surface.blit(next_text, next_rect)
        
        # Add Unit button (team phases only)
        if self.phase in [SelectionPhase.TEAM_A, SelectionPhase.TEAM_B]:
            pygame.draw.rect(surface, self.color_button, self.button_add_unit)
            add_text = self.font_normal.render("Add Unit", True, self.color_text)
            add_rect = add_text.get_rect(center=self.button_add_unit.center)
            surface.blit(add_text, add_rect)
    
    def _draw_instructions(self, surface: pygame.Surface) -> None:
        """Draw control instructions."""
        y = self.screen_height - 120
        
        if self.phase == SelectionPhase.MAP:
            instructions = [
                "↑↓: Select Map  |  Enter/Next: Confirm  |  ESC: Cancel"
            ]
        else:
            instructions = [
                "↑↓: Select Character  |  ←→: Select Sprite",
                "Space/Add Unit: Add to roster  |  Backspace: Remove last  |  Enter/Next: Proceed  |  ESC: Cancel"
            ]
        
        for i, instruction in enumerate(instructions):
            inst_surf = self.font_small.render(instruction, True, self.color_instructions)
            inst_rect = inst_surf.get_rect(center=(self.screen_width // 2, y + i * 25))
            surface.blit(inst_surf, inst_rect)
    
    def _can_proceed(self) -> bool:
        """Check if current phase allows proceeding to next.
        
        Returns:
            True if can proceed
        """
        if self.phase == SelectionPhase.MAP:
            return True
        elif self.phase == SelectionPhase.TEAM_A:
            return len(self.team_a_roster) > 0
        elif self.phase == SelectionPhase.TEAM_B:
            return len(self.team_b_roster) > 0
        return False
    
    def get_action(self) -> Optional[str]:
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
        return self.config
    
    def is_complete(self) -> bool:
        """Check if selection is complete.
        
        Returns:
            True if confirmed or cancelled
        """
        return self.action is not None
