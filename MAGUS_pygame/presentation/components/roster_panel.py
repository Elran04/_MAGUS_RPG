"""
Roster panel component for scenario selector.

Displays selected team units in a horizontal panel showing character
names, sprites, and validation status.
"""

from pathlib import Path

import pygame
from domain.value_objects import UnitSetup
from logger.logger import get_logger

logger = get_logger(__name__)


class RosterPanel:
    """Horizontal panel displaying team roster during scenario selection.

    Shows all selected units for a team with character names, sprites,
    and validation indicators (e.g., missing files).
    """

    def __init__(self, x: int, y: int, width: int, height: int):
        """Initialize roster panel.

        Args:
            x: Panel X position
            y: Panel Y position
            width: Panel width
            height: Panel height
        """
        self.rect = pygame.Rect(x, y, width, height)

        # Layout
        self.entry_width = 180
        self.max_cols = (width - 40) // self.entry_width

        # Fonts
        self.font_title = pygame.font.Font(None, 32)
        self.font_label = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 20)

        # Colors
        self.color_bg = (0, 0, 0, 160)
        self.color_title_a = (100, 150, 255)  # Team A blue
        self.color_title_b = (255, 100, 100)  # Team B red
        self.color_text = (255, 255, 255)
        self.color_missing = (230, 120, 120)
        self.color_empty = (150, 150, 150)

        # Paths for validation
        self.characters_dir: Path | None = None
        self.sprites_dir: Path | None = None

        logger.debug(f"RosterPanel initialized at ({x}, {y}) size {width}x{height}")

    def set_data_paths(self, characters_dir: Path, sprites_dir: Path) -> None:
        """Set data directory paths for file validation.

        Args:
            characters_dir: Path to characters directory
            sprites_dir: Path to character sprites directory
        """
        self.characters_dir = characters_dir
        self.sprites_dir = sprites_dir
        logger.debug(f"RosterPanel paths set: chars={characters_dir}, sprites={sprites_dir}")

    def draw(
        self,
        surface: pygame.Surface,
        team_name: str,
        roster: list[UnitSetup],
        is_team_a: bool = True,
    ) -> None:
        """Draw roster panel.

        Args:
            surface: Surface to draw on
            team_name: Display name for the team (e.g., "Team A Roster")
            roster: List of unit setups for this team
            is_team_a: True for team A (blue), False for team B (red)
        """
        # Draw panel background
        panel = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        panel.fill(self.color_bg)
        surface.blit(panel, self.rect.topleft)

        # Title
        title_color = self.color_title_a if is_team_a else self.color_title_b
        title = self.font_title.render(team_name, True, title_color)
        surface.blit(title, (self.rect.x + 15, self.rect.y + 10))

        # Empty state
        if not roster:
            empty = self.font_label.render("No units added yet", True, self.color_empty)
            surface.blit(empty, (self.rect.x + 20, self.rect.y + 50))
            return

        # Draw roster entries
        start_x = self.rect.x + 20
        start_y = self.rect.y + 50

        for idx, unit_setup in enumerate(roster):
            col = idx % self.max_cols
            row = idx // self.max_cols

            x = start_x + col * self.entry_width
            y = start_y + row * 25

            self._draw_roster_entry(surface, idx + 1, unit_setup, x, y)

    def _draw_roster_entry(
        self, surface: pygame.Surface, number: int, unit_setup: UnitSetup, x: int, y: int
    ) -> None:
        """Draw a single roster entry.

        Args:
            surface: Surface to draw on
            number: Unit number (1-indexed)
            unit_setup: Unit setup configuration
            x: Entry X position
            y: Entry Y position
        """
        # Validate files
        missing = self._check_missing_files(unit_setup)

        # Choose color based on validation
        text_color = self.color_text if not missing else self.color_missing

        # Format text
        char_name = unit_setup.character_file.replace(".json", "")
        sprite_name = unit_setup.sprite_file.rsplit(".", 1)[0]  # Remove extension

        # Add missing indicator
        suffix = ""
        if missing:
            suffix = f" [Missing {', '.join(missing)}]"

        # Draw entry
        entry_text = f"{number}. {char_name} / {sprite_name}{suffix}"
        entry_surf = self.font_small.render(entry_text, True, text_color)
        surface.blit(entry_surf, (x, y))

    def _check_missing_files(self, unit_setup: UnitSetup) -> list[str]:
        """Check if character or sprite files are missing.

        Args:
            unit_setup: Unit setup to validate

        Returns:
            List of missing file types (e.g., ["CHAR", "SPR"])
        """
        if not self.characters_dir or not self.sprites_dir:
            return []  # Can't validate without paths

        missing = []

        # Check character file
        char_path = self.characters_dir / unit_setup.character_file
        if not char_path.exists():
            missing.append("CHAR")

        # Check sprite file
        sprite_path = self.sprites_dir / unit_setup.sprite_file
        if not sprite_path.exists():
            missing.append("SPR")

        return missing
