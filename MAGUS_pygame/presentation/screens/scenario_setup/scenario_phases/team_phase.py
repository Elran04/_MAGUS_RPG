"""Team composition phase - select characters and sprites for a team."""

from __future__ import annotations

import pygame
from application.game_context import GameContext
from config import CHARACTER_SPRITES_DIR, CHARACTERS_DIR, DEJAVU_FONT_PATH
from domain.value_objects import UnitSetup
from logger.logger import get_logger
from presentation.components.scenario_play.character_preview import CharacterPreview
from presentation.components.scenario_play.dropdown import Dropdown
from presentation.components.scenario_play.roster_panel import RosterPanel

from .phase_base import SelectionPhaseBase

logger = get_logger(__name__)


class TeamCompositionPhase(SelectionPhaseBase):
    """Team composition phase.

    Allows user to:
    - Select characters from available list
    - Choose sprite for each character
    - Preview character stats and appearance
    - Build team roster
    - Remove units from roster
    """

    def __init__(
        self,
        screen_width: int,
        screen_height: int,
        context: GameContext,
        is_team_a: bool,
        team_name: str,
    ):
        """Initialize team composition phase.

        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
            context: Game context for data access
            is_team_a: True for team A, False for team B
            team_name: Display name for team (e.g., "Team A (Blue)")
        """
        super().__init__(screen_width, screen_height, context)

        self.is_team_a = is_team_a
        self.team_name = team_name

        # Available options
        self.available_characters = context.character_repo.list_all()
        self.available_sprites = context.sprite_repo.list_character_sprites()

        # Selection indices
        self.current_char_index = 0
        self.current_sprite_index = 0

        # UI Components
        self._setup_ui()

        # Fonts
        self.font_title = pygame.font.Font(DEJAVU_FONT_PATH, 40)
        self.font_normal = pygame.font.Font(DEJAVU_FONT_PATH, 24)
        self.font_small = pygame.font.Font(DEJAVU_FONT_PATH, 16)

        # Colors
        self.color_bg = (20, 20, 30)
        self.color_text = (255, 255, 255)
        self.color_button = (60, 60, 80)
        self.color_instructions = (180, 180, 180)

        # Buttons
        self.button_add_unit = pygame.Rect(screen_width // 2 - 220, screen_height - 70, 200, 50)
        self.button_remove_unit = pygame.Rect(screen_width // 2 + 20, screen_height - 70, 200, 50)

        logger.info(
            f"Team composition phase initialized: {team_name}, "
            f"{len(self.available_characters)} characters, {len(self.available_sprites)} sprites"
        )

    def _setup_ui(self) -> None:
        """Setup UI components."""
        # Dropdowns for character and sprite selection (top, side by side)
        dropdown_y = 120
        dropdown_width = 400
        dropdown_height = 40
        dropdown_spacing = 50

        # Center the dropdowns horizontally
        total_width = dropdown_width * 2 + dropdown_spacing
        start_x = (self.screen_width - total_width) // 2

        self.character_dropdown = Dropdown(
            x=start_x,
            y=dropdown_y,
            width=dropdown_width,
            height=dropdown_height,
            options=self.available_characters,
            default_index=0,
            label="Character",
        )

        self.sprite_dropdown = Dropdown(
            x=start_x + dropdown_width + dropdown_spacing,
            y=dropdown_y,
            width=dropdown_width,
            height=dropdown_height,
            options=self.available_sprites,
            default_index=0,
            label="Sprite",
        )

        # Character preview (centered, large, below dropdowns)
        preview_y = dropdown_y + dropdown_height + 60
        preview_width = self.screen_width - 100
        preview_height = self.screen_height - preview_y - 230  # Space for roster + buttons
        self.character_preview = CharacterPreview(
            x=50, y=preview_y, width=preview_width, height=preview_height, context=self.context
        )

        # Roster panel (bottom)
        self.roster_panel = RosterPanel(
            x=40, y=self.screen_height - 200, width=self.screen_width - 80, height=110
        )
        self.roster_panel.set_data_paths(CHARACTERS_DIR, CHARACTER_SPRITES_DIR)

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle input events.

        Args:
            event: Pygame event
        """
        # Pass events to dropdowns
        char_changed = self.character_dropdown.handle_event(event)
        sprite_changed = self.sprite_dropdown.handle_event(event)

        # Update indices if dropdown selections changed
        if char_changed:
            self.current_char_index = self.character_dropdown.get_selected_index()
            self.context.character_repo.load(self.available_characters[self.current_char_index])
        if sprite_changed:
            self.current_sprite_index = self.sprite_dropdown.get_selected_index()
            self.context.sprite_repo.load_character_sprite(
                self.available_sprites[self.current_sprite_index], max_size=160
            )

        # Handle scrolling for preview panel
        if event.type == pygame.MOUSEWHEEL:
            self.character_preview.handle_scroll(event)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # Close dropdowns if open, otherwise go back
                if self.character_dropdown.is_open or self.sprite_dropdown.is_open:
                    self.character_dropdown.is_open = False
                    self.sprite_dropdown.is_open = False
                else:
                    self.cancelled = True
                    logger.info(f"{self.team_name} selection cancelled (going back)")
            elif event.key == pygame.K_RETURN:
                self._confirm_team()
            elif event.key == pygame.K_UP:
                if self.character_dropdown.cycle(-1):
                    self.current_char_index = self.character_dropdown.get_selected_index()
                    self.context.character_repo.load(
                        self.available_characters[self.current_char_index]
                    )
            elif event.key == pygame.K_DOWN:
                if self.character_dropdown.cycle(1):
                    self.current_char_index = self.character_dropdown.get_selected_index()
                    self.context.character_repo.load(
                        self.available_characters[self.current_char_index]
                    )
            elif event.key == pygame.K_LEFT:
                if self.sprite_dropdown.cycle(-1):
                    self.current_sprite_index = self.sprite_dropdown.get_selected_index()
                    self.context.sprite_repo.load_character_sprite(
                        self.available_sprites[self.current_sprite_index], max_size=160
                    )
            elif event.key == pygame.K_RIGHT:
                if self.sprite_dropdown.cycle(1):
                    self.current_sprite_index = self.sprite_dropdown.get_selected_index()
                    self.context.sprite_repo.load_character_sprite(
                        self.available_sprites[self.current_sprite_index], max_size=160
                    )
            elif event.key == pygame.K_SPACE:
                self._add_current_unit()
            elif event.key == pygame.K_BACKSPACE:
                self._remove_last_unit()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                if self.button_add_unit.collidepoint(event.pos):
                    self._add_current_unit()
                elif self.button_remove_unit.collidepoint(event.pos):
                    self._remove_last_unit()

    def _add_current_unit(self) -> None:
        """Add currently selected character+sprite to team roster."""
        if not self.available_characters or not self.available_sprites:
            logger.warning("Cannot add unit: no characters or sprites available")
            return

        char_file = self.available_characters[self.current_char_index]
        sprite_file = self.available_sprites[self.current_sprite_index]

        # Load character data with proper equipment, skills, and inventory using service
        unit_data = self.context.unit_setup_service.prepare_unit_data(char_file)
        if not unit_data:
            logger.error(f"Failed to load unit data for {char_file}")
            return

        # Extract equipment, inventory, and skills from character data
        equipment = unit_data["equipment"]
        inventory = unit_data["inventory"]
        skills = unit_data["skills"]

        added = self.context.scenario_service.add_unit(
            self.is_team_a,
            char_file,
            sprite_file,
            equipment=equipment,
            inventory=inventory,
            skills=skills,
        )
        if added:
            logger.debug(
                f"Added unit to {self.team_name}: {char_file} / {sprite_file} "
                f"(equipment: {len(equipment)}, inventory: {len(inventory)}, skills: {len(skills)})"
            )
        else:
            logger.info("Unit not added (validation prevented).")

        # Warm sprite cache
        self.context.sprite_repo.load_character_sprite(sprite_file, max_size=160)

    def _remove_last_unit(self) -> None:
        """Remove last unit from team roster."""
        before = len(self.context.scenario_service.get_team(self.is_team_a))
        self.context.scenario_service.remove_last(self.is_team_a)
        after = len(self.context.scenario_service.get_team(self.is_team_a))
        if after < before:
            logger.debug(f"Removed last unit from {self.team_name}")

    def _confirm_team(self) -> None:
        """Confirm team composition and proceed."""
        if self.can_proceed():
            self.completed = True
            logger.info(
                f"{self.team_name} confirmed: {len(self.context.scenario_service.get_team(self.is_team_a))} units"
            )

    def draw(self, surface: pygame.Surface) -> None:
        """Draw team composition screen.

        Args:
            surface: Surface to draw on
        """
        # Background
        surface.fill(self.color_bg)

        # Title
        title = self.font_title.render(f"Setup {self.team_name}", True, self.color_text)
        title_rect = title.get_rect(center=(self.screen_width // 2, 50))
        surface.blit(title, title_rect)

        # Character preview
        if self.available_characters and self.available_sprites:
            char_file = self.available_characters[self.current_char_index]
            sprite_file = self.available_sprites[self.current_sprite_index]

            # Load via repositories
            char_data = self.context.character_repo.load(char_file)
            sprite_surf = self.context.sprite_repo.load_character_sprite(sprite_file, max_size=220)

            self.character_preview.draw(surface, char_data, sprite_surf, char_file, sprite_file)

        # Roster panel with size info
        roster = self.context.scenario_service.get_team(self.is_team_a)
        max_size = self.context.scenario_service.get_max_team_size(self.is_team_a)
        if max_size is not None:
            roster_title = f"{self.team_name} Roster ({len(roster)}/{max_size})"
        else:
            roster_title = f"{self.team_name} Roster ({len(roster)})"
        self.roster_panel.draw(surface, roster_title, roster, self.is_team_a)

        # Add Unit button (dim if roster is full)
        max_size = self.context.scenario_service.get_max_team_size(self.is_team_a)
        is_roster_full = max_size is not None and len(roster) >= max_size
        button_color = (40, 40, 50) if is_roster_full else self.color_button
        text_color = (100, 100, 100) if is_roster_full else self.color_text

        pygame.draw.rect(surface, button_color, self.button_add_unit)
        add_text = self.font_normal.render("Add Unit", True, text_color)
        add_rect = add_text.get_rect(center=self.button_add_unit.center)
        surface.blit(add_text, add_rect)

        # Show "FULL" message if roster is full
        if is_roster_full:
            full_text = self.font_small.render("(Roster Full)", True, (255, 100, 100))
            full_rect = full_text.get_rect(
                center=(self.button_add_unit.centerx, self.button_add_unit.bottom + 15)
            )
            surface.blit(full_text, full_rect)

        # Remove Last Unit button
        pygame.draw.rect(surface, self.color_button, self.button_remove_unit)
        remove_text = self.font_normal.render("Remove Unit", True, self.color_text)
        remove_rect = remove_text.get_rect(center=self.button_remove_unit.center)
        surface.blit(remove_text, remove_rect)

        # Instructions
        self._draw_instructions(surface)

        # Draw dropdowns
        self.character_dropdown.draw(surface)
        self.sprite_dropdown.draw(surface)

    def _draw_instructions(self, surface: pygame.Surface) -> None:
        """Draw control instructions."""
        y = self.screen_height - 590

        instructions = [
            "Click dropdown or ←→: Change selection  |  Mouse wheel: Scroll preview",
            "Space/Add Unit: Add to roster  |  Backspace: Remove last  |  Enter: Proceed  |  ESC: Back",
        ]

        for i, instruction in enumerate(instructions):
            inst_surf = self.font_small.render(instruction, True, self.color_instructions)
            inst_rect = inst_surf.get_rect(center=(self.screen_width // 2, y + i * 22))
            surface.blit(inst_surf, inst_rect)

    def can_proceed(self) -> bool:
        """Check if can proceed to next phase.

        Returns:
            True if at least one unit has been added to roster
        """
        if self.is_team_a:
            return self.context.scenario_service.can_advance_from_team_a()
        else:
            return self.context.scenario_service.can_finish()

    def get_roster(self) -> list[UnitSetup]:
        """Get current team roster.

        Returns:
            List of units in roster
        """
        return self.context.scenario_service.get_team(self.is_team_a)
