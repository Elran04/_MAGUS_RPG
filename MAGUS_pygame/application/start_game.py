"""
start_game(context) - Orchestrates complete game flow from scenario to battle.

Complete flow: Scenario Selection -> Deployment -> Battle
"""

from __future__ import annotations

import pygame
from application.battle_service import BattleService
from config import BACKGROUND_SPRITES_DIR, HEIGHT, WIDTH
from domain.entities import Unit
from domain.value_objects import Facing, Position
from domain.value_objects.scenario_config import ScenarioConfig
from logger.logger import get_logger
from presentation.screens.battle_screen import BattleScreen
from presentation.screens.deployment_screen import DeploymentScreen
from presentation.screens.scenario_screen import ScenarioScreen

logger = get_logger(__name__)


def _units_from_config(context, config: ScenarioConfig) -> tuple[list[Unit], list[Unit]]:
    """Create units for both teams from a finalized ScenarioConfig.

    Returns (team_a_units, team_b_units).
    """
    unit_factory = context.unit_factory
    sprite_repo = context.sprite_repo
    team_a: list[Unit] = []
    team_b: list[Unit] = []

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
            # Load sprite
            sprite = sprite_repo.load_character_sprite(setup.sprite_file)
            if sprite:
                u.sprite = sprite
            team_a.append(u)
            logger.debug(f"Created Team A unit: {u.name} at ({setup.start_q}, {setup.start_r})")

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
            # Load sprite
            sprite = sprite_repo.load_character_sprite(setup.sprite_file)
            if sprite:
                u.sprite = sprite
            team_b.append(u)
            logger.debug(f"Created Team B unit: {u.name} at ({setup.start_q}, {setup.start_r})")

    return team_a, team_b


def start_game(context, screen: pygame.Surface, clock: pygame.time.Clock) -> None:
    """Run complete game flow: Scenario -> Deployment -> Battle.

    Args:
        context: Game context with repositories and factories
        screen: Pygame display surface
        clock: Pygame clock for timing
    """
    logger.info("Starting game flow: Scenario Selection")

    # 1) Scenario selection
    scenario_screen = ScenarioScreen(WIDTH, HEIGHT, context)

    while not scenario_screen.is_complete():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                logger.info("Game quit during scenario selection")
                return
            scenario_screen.handle_event(event)

        scenario_screen.draw(screen)
        pygame.display.flip()
        clock.tick(60)

    # Check if cancelled
    if scenario_screen.get_action() == "scenario_cancelled":
        logger.info("Scenario selection cancelled")
        return

    scenario_config = scenario_screen.get_config()
    logger.info(
        f"Scenario configured: {scenario_config.map_name}, "
        f"Team A: {len(scenario_config.team_a)}, Team B: {len(scenario_config.team_b)}"
    )

    # 2) Deployment
    logger.info("Starting deployment phase")
    deployment_screen = DeploymentScreen(WIDTH, HEIGHT, scenario_config, context)

    while not deployment_screen.is_complete():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                logger.info("Game quit during deployment")
                return
            deployment_screen.handle_event(event)

        deployment_screen.draw(screen)
        pygame.display.flip()
        clock.tick(60)

    # Check if cancelled
    if deployment_screen.get_action() == "deployment_cancelled":
        logger.info("Deployment cancelled")
        return

    final_config = deployment_screen.get_config()
    logger.info("Deployment complete, creating units")

    # 3) Create units from configuration
    team_a_units, team_b_units = _units_from_config(context, final_config)
    units: list[Unit] = team_a_units + team_b_units

    if not units:
        logger.error("No units created; aborting battle start")
        return

    logger.info(f"Created {len(team_a_units)} Team A units and {len(team_b_units)} Team B units")

    # 4) Setup battle service with teams
    battle_service = BattleService(units=units)
    battle_service.set_teams(team_a_units, team_b_units)
    battle_service.start_battle()

    logger.info("Battle started!")

    # 5) Load background for battle
    background: pygame.Surface | None = None
    try:
        bg_path = BACKGROUND_SPRITES_DIR / final_config.background_file
        background = pygame.image.load(str(bg_path)).convert()
        background = pygame.transform.smoothscale(background, (WIDTH, HEIGHT))
        logger.debug(f"Loaded battle background: {final_config.background_file}")
    except Exception as e:
        logger.warning(f"Failed to load background {final_config.background_file}: {e}")

    # 6) Battle screen
    battle_screen = BattleScreen(WIDTH, HEIGHT, battle_service, context, background)

    while not battle_screen.is_complete():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                logger.info("Game quit during battle")
                return
            battle_screen.handle_event(event)

        battle_screen.update()
        battle_screen.draw(screen)
        pygame.display.flip()
        clock.tick(60)

    # Battle ended
    action = battle_screen.get_action()
    logger.info(f"Battle ended: {action}")

    # Show final screen for a moment before returning
    for _ in range(120):  # 2 seconds
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return

        battle_screen.draw(screen)
        pygame.display.flip()
        clock.tick(60)

    logger.info("Game flow complete, returning to menu")
