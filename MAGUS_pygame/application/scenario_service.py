"""Application layer ScenarioService.

Handles scenario assembly and roster validation independent of presentation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from domain.value_objects import ScenarioConfig, UnitSetup
from logger.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ScenarioState:
    map_name: Optional[str] = None
    background_file: Optional[str] = None
    team_a: List[UnitSetup] = field(default_factory=list)
    team_b: List[UnitSetup] = field(default_factory=list)


class ScenarioService:
    """Service coordinating map selection and team composition.

    Responsibilities:
    - Track provisional selections (map, background, rosters)
    - Enforce validation rules (non-empty teams, optional size/duplicate constraints)
    - Produce immutable ScenarioConfig when complete
    """

    def __init__(self, scenario_repo, character_repo, sprite_repo, max_team_size: int | None = None, allow_duplicates: bool = True):
        self._scenario_repo = scenario_repo
        self._character_repo = character_repo
        self._sprite_repo = sprite_repo
        self._max_team_size = max_team_size
        self._allow_duplicates = allow_duplicates
        self._state = ScenarioState()

    # Map / background -------------------------------------------------
    def set_map(self, map_name: str) -> None:
        bg = self._scenario_repo.resolve_background(map_name)
        self._state.map_name = map_name
        self._state.background_file = bg or "grass_bg.jpg"
        logger.debug(f"Scenario map set: {map_name} (bg={self._state.background_file})")

    # Roster management ------------------------------------------------
    def add_unit(self, team_a: bool, character_file: str, sprite_file: str) -> bool:
        """Add a unit to the chosen team.

        Returns True if added, False if rejected by validation.
        """
        roster = self._state.team_a if team_a else self._state.team_b

        # Size limit
        if self._max_team_size is not None and len(roster) >= self._max_team_size:
            logger.info("Roster full; rejecting add.")
            return False

        # Duplicate prevention
        if not self._allow_duplicates:
            if any(u.character_file == character_file and u.sprite_file == sprite_file for u in roster):
                logger.info("Duplicate unit rejected (duplicates disabled).")
                return False

        # Light existence check (best effort)
        if not self._character_repo.exists(character_file):
            logger.warning(f"Character file missing: {character_file}")
        if not self._sprite_repo.character_sprite_exists(sprite_file):
            logger.warning(f"Sprite file missing: {sprite_file}")

        roster.append(UnitSetup(character_file=character_file, sprite_file=sprite_file))
        logger.debug(f"Added unit to {'A' if team_a else 'B'}: {character_file}/{sprite_file}")
        return True

    def remove_last(self, team_a: bool) -> None:
        roster = self._state.team_a if team_a else self._state.team_b
        if roster:
            removed = roster.pop()
            logger.debug(f"Removed unit from {'A' if team_a else 'B'}: {removed.character_file}")

    # Validation -------------------------------------------------------
    def can_advance_from_map(self) -> bool:
        return self._state.map_name is not None

    def can_advance_from_team_a(self) -> bool:
        return len(self._state.team_a) > 0

    def can_finish(self) -> bool:
        return len(self._state.team_b) > 0

    # State exposure ---------------------------------------------------
    def get_team(self, team_a: bool) -> list[UnitSetup]:
        return self._state.team_a if team_a else self._state.team_b

    def update_unit(self, team_a: bool, index: int, new_setup: UnitSetup) -> None:
        """Replace a unit setup in the specified team at index.

        Args:
            team_a: True for Team A, False for Team B
            index: Position in the roster
            new_setup: New UnitSetup instance to place
        """
        roster = self._state.team_a if team_a else self._state.team_b
        if 0 <= index < len(roster):
            roster[index] = new_setup
        else:
            logger.warning("update_unit index out of range: %s (team_a=%s)", index, team_a)

    def build_config(self) -> ScenarioConfig:
        if not self._state.map_name:
            raise ValueError("Map not selected")
        if not self.can_advance_from_team_a() or not self.can_finish():
            raise ValueError("Teams incomplete")
        config = ScenarioConfig()
        config = config.with_map(self._state.map_name, self._state.background_file or "grass_bg.jpg")
        config = config.with_team_a(self._state.team_a)
        config = config.with_team_b(self._state.team_b)
        return config

    # Presentation layer facade methods -------------------------------
    def get_scenario_list(self) -> list[str]:
        """Get list of available scenario files.
        
        Facade method for presentation layer to avoid direct repository access.
        
        Returns:
            List of scenario file stems (without extension)
        """
        return self._scenario_repo.list_scenarios()
    
    def load_scenario_data(self, scenario_name: str) -> dict | None:
        """Load scenario data by name.
        
        Facade method for presentation layer to avoid direct repository access.
        
        Args:
            scenario_name: Scenario file stem (without extension)
            
        Returns:
            Scenario data dictionary or None if not found
        """
        return self._scenario_repo.load_scenario(scenario_name)
    
    def get_scenario_preview_data(self, scenario_name: str) -> dict | None:
        """Get scenario data formatted for preview display.
        
        Provides a convenient facade for presentation components that need
        read-only access to scenario metadata and layout.
        
        Args:
            scenario_name: Scenario file stem (without extension)
            
        Returns:
            Dictionary with preview-ready data or None if not found.
            Includes: name, description, background, spawn_zones, obstacles
        """
        data = self._scenario_repo.load_scenario(scenario_name)
        if not data:
            return None
        
        # Ensure all expected keys exist for preview
        return {
            'name': data.get('name', scenario_name),
            'description': data.get('description', ''),
            'background': data.get('background'),
            'spawn_zones': data.get('spawn_zones', {'team_a': [], 'team_b': []}),
            'obstacles': data.get('obstacles', []),
        }
    
    def get_background_path(self, scenario_name: str) -> str | None:
        """Get resolved background file path for a scenario.
        
        Args:
            scenario_name: Scenario file stem (without extension)
            
        Returns:
            Background file name or None if scenario not found
        """
        return self._scenario_repo.resolve_background(scenario_name)
