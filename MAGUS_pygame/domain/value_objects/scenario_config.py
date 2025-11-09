"""
Scenario configuration value objects for team setup and deployment.

These immutable value objects represent the configuration of a battle scenario,
including team composition, deployment zones, and map selection.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class UnitSetup:
    """Configuration for a single unit in a scenario.

    Attributes:
        character_file: Character JSON filename (e.g., "Teszt.json")
        sprite_file: Sprite image filename (e.g., "warrior.png")
        start_q: Deployment hex Q coordinate (optional until deployment phase)
        start_r: Deployment hex R coordinate (optional until deployment phase)
        facing: Initial facing direction (0-5 for hex directions)
    """

    character_file: str
    sprite_file: str
    start_q: int | None = None
    start_r: int | None = None
    facing: int = 0

    def __post_init__(self):
        """Validate unit setup configuration."""
        if self.facing < 0 or self.facing > 5:
            raise ValueError(f"Facing must be 0-5, got {self.facing}")
        if (self.start_q is None) != (self.start_r is None):
            raise ValueError("Both start_q and start_r must be set or both None")

    def with_deployment(self, q: int, r: int, facing: int = 0) -> "UnitSetup":
        """Create new UnitSetup with deployment position.

        Args:
            q: Hex Q coordinate
            r: Hex R coordinate
            facing: Facing direction (0-5)

        Returns:
            New UnitSetup with deployment coordinates
        """
        return UnitSetup(
            character_file=self.character_file,
            sprite_file=self.sprite_file,
            start_q=q,
            start_r=r,
            facing=facing,
        )

    def is_deployed(self) -> bool:
        """Check if unit has deployment coordinates.

        Returns:
            True if both start_q and start_r are set
        """
        return self.start_q is not None and self.start_r is not None


@dataclass(frozen=True)
class ScenarioConfig:
    """Complete scenario configuration for a battle.

    Attributes:
        map_name: Name of the scenario/map (used to load scenario JSON)
        background_file: Background image filename
        team_a: List of unit setups for team A (typically player team)
        team_b: List of unit setups for team B (typically enemy team)
        team_a_deploy_zone: Optional set of (q, r) tuples defining valid deployment hexes for team A
        team_b_deploy_zone: Optional set of (q, r) tuples defining valid deployment hexes for team B
    """

    map_name: str = "default"
    background_file: str = "grass_bg.jpg"
    team_a: tuple[UnitSetup, ...] = field(default_factory=tuple)
    team_b: tuple[UnitSetup, ...] = field(default_factory=tuple)
    team_a_deploy_zone: frozenset[tuple[int, int]] | None = None
    team_b_deploy_zone: frozenset[tuple[int, int]] | None = None

    def is_valid(self) -> bool:
        """Check if configuration is valid for starting a game.

        Returns:
            True if both teams have at least one unit
        """
        return len(self.team_a) > 0 and len(self.team_b) > 0

    def all_units_deployed(self) -> bool:
        """Check if all units have deployment positions.

        Returns:
            True if all units have start_q and start_r set
        """
        all_units = self.team_a + self.team_b
        return all(unit.is_deployed() for unit in all_units)

    def get_all_units(self) -> tuple[UnitSetup, ...]:
        """Get all units from both teams.

        Returns:
            Combined tuple of all unit setups
        """
        return self.team_a + self.team_b

    def with_team_a(self, team_a: list[UnitSetup]) -> "ScenarioConfig":
        """Create new config with updated team A.

        Args:
            team_a: New team A unit setups

        Returns:
            New ScenarioConfig with updated team A
        """
        return ScenarioConfig(
            map_name=self.map_name,
            background_file=self.background_file,
            team_a=tuple(team_a),
            team_b=self.team_b,
            team_a_deploy_zone=self.team_a_deploy_zone,
            team_b_deploy_zone=self.team_b_deploy_zone,
        )

    def with_team_b(self, team_b: list[UnitSetup]) -> "ScenarioConfig":
        """Create new config with updated team B.

        Args:
            team_b: New team B unit setups

        Returns:
            New ScenarioConfig with updated team B
        """
        return ScenarioConfig(
            map_name=self.map_name,
            background_file=self.background_file,
            team_a=self.team_a,
            team_b=tuple(team_b),
            team_a_deploy_zone=self.team_a_deploy_zone,
            team_b_deploy_zone=self.team_b_deploy_zone,
        )

    def with_map(self, map_name: str, background_file: str) -> "ScenarioConfig":
        """Create new config with updated map settings.

        Args:
            map_name: Scenario/map name
            background_file: Background image filename

        Returns:
            New ScenarioConfig with updated map settings
        """
        return ScenarioConfig(
            map_name=map_name,
            background_file=background_file,
            team_a=self.team_a,
            team_b=self.team_b,
            team_a_deploy_zone=self.team_a_deploy_zone,
            team_b_deploy_zone=self.team_b_deploy_zone,
        )
