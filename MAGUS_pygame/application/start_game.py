"""
start_game(context) - menu -> scenario -> deployment -> battle bootstrap.

This is a thin orchestration layer; it assumes the presentation layer exposes
MenuScreen, ScenarioScreen, DeploymentScreen, and a simple Battle loop renderer.

Note: This is a stub that sketches control flow; hook it into your actual
presentation and event loop.
"""
from __future__ import annotations

from typing import List
import pygame

from application.battle_service import BattleService
from application.action_handler import ActionHandler
from domain.entities import Unit
from domain.value_objects import Position, Facing
from domain.value_objects.scenario_config import ScenarioConfig, UnitSetup
from logger.logger import get_logger

logger = get_logger(__name__)

# Placeholder imports - adjust paths to your presentation layer
# from presentation.screens.menu_screen import MenuScreen
# from presentation.screens.scenario_screen import ScenarioScreen
# from presentation.screens.deployment_screen import DeploymentScreen
# from infrastructure.rendering.battle_renderer import BattleRenderer


def _units_from_config(context, config: ScenarioConfig) -> tuple[List[Unit], List[Unit]]:
    """Create units for both teams from a finalized ScenarioConfig.

    Returns (team_a_units, team_b_units).
    Missing sprite loading is acceptable placeholder for now.
    """
    unit_factory = context.unit_factory
    team_a: List[Unit] = []
    team_b: List[Unit] = []

    for setup in config.team_a:
        if not setup.is_deployed():
            logger.warning(f"Team A unit {setup.character_file} not deployed - skipping")
            continue
        u = unit_factory.create_unit(
            character_filename=setup.character_file,
            position=Position(setup.start_q, setup.start_r),  # type: ignore[arg-type]
            facing=Facing(setup.facing),
        )
        if u:
            team_a.append(u)
    for setup in config.team_b:
        if not setup.is_deployed():
            logger.warning(f"Team B unit {setup.character_file} not deployed - skipping")
            continue
        u = unit_factory.create_unit(
            character_filename=setup.character_file,
            position=Position(setup.start_q, setup.start_r),  # type: ignore[arg-type]
            facing=Facing(setup.facing),
        )
        if u:
            team_b.append(u)
    return team_a, team_b


def start_game(context) -> None:
    """Run menu -> scenario -> deployment -> battle loop.

    NOTE: Menu / Scenario / Deployment screens are placeholders; replace with
    actual screen invocations. This now constructs real Unit instances.
    """
    # 1) Menu
    # menu = MenuScreen(...)
    # if not menu.run(): return

    # 2) Scenario selection
    # scenario_screen = ScenarioScreen(..., context)
    # scenario_config = scenario_screen.run_and_get_config_or_none()
    # if scenario_config is None: return

    # 3) Deployment
    # deployment_screen = DeploymentScreen(..., scenario_config, context)
    # final_config = deployment_screen.run_and_get_config_or_none()
    # if final_config is None: return

    # 4) Construct Units from final_config (via UnitFactory in context)
    # Placeholder: simulate received config or abort if not available
    dummy_config = ScenarioConfig()  # Replace with real final_config
    team_a_units, team_b_units = _units_from_config(context, dummy_config)
    units: List[Unit] = team_a_units + team_b_units

    if not units:
        logger.error("No units created; aborting battle start")
        return

    # 5) Setup battle service with teams
    battle = BattleService(units=units)
    battle.set_teams(team_a_units, team_b_units)
    battle.start_battle()

    # 6) Main battle loop (placeholder)
    running = True
    clock = pygame.time.Clock()

    while running and not battle.is_victory():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # TODO: Translate input into move/attack invocations via ActionHandler

        # Example: no-op per frame
        # renderer.draw(units, ...)

        clock.tick(60)

    # Exit to menu or end
