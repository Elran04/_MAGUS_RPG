"""
Game Flow Service - Orchestrates complete game flow from scenario to battle.

Complete flow: Scenario Selection -> Equipment -> Deployment -> Battle

This application service coordinates the high-level game workflow,
managing transitions between different game phases and screens.
"""

from __future__ import annotations

import pygame
from application.battle_service import BattleService
from config import BACKGROUND_SPRITES_DIR, HEIGHT, WIDTH
from domain.entities import Unit
from domain.value_objects import Facing, Position
from domain.value_objects.scenario_config import ScenarioConfig
from logger.logger import get_logger
from presentation.screens.game.battle_screen import BattleScreen
from presentation.screens.game.deployment_screen import DeploymentScreen
from presentation.screens.scenario_setup.scenario_screen import ScenarioScreen


def run_screen_loop(screen_obj, screen, clock, cancel_action=None, update_method=None):
    """Generic loop for any screen with is_complete(), handle_event(), draw(), get_action().
    Optionally calls update_method() each frame (for battle screens).
    Returns: 'quit', 'cancelled', or the action from get_action().
    """
    while not screen_obj.is_complete():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            screen_obj.handle_event(event)
        if update_method:
            update_method()
        screen_obj.draw(screen)
        pygame.display.flip()
        clock.tick(60)
    action = screen_obj.get_action()
    if cancel_action and action == cancel_action:
        return "cancelled"
    return action


logger = get_logger(__name__)


def handle_error(message: str, user_facing: bool = True):
    logger.error(message)
    if user_facing:
        font = pygame.font.SysFont(None, 36)
        screen = pygame.display.get_surface()
        if screen:
            overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            text = font.render(message, True, (255, 0, 0))
            rect = text.get_rect(center=screen.get_rect().center)
            overlay.blit(text, rect)
            screen.blit(overlay, (0, 0))
            pygame.display.flip()
            # Wait for user to acknowledge
            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type in (pygame.KEYDOWN, pygame.QUIT, pygame.MOUSEBUTTONDOWN):
                        waiting = False


def _create_units_for_team(context, team_setups, team_label: str) -> list[Unit]:
    """Create units for a team from scenario config setups."""
    unit_factory = context.unit_factory
    sprite_repo = context.sprite_repo
    team_units: list[Unit] = []

    for setup in team_setups:
        if not setup.is_deployed():
            logger.warning(f"{team_label} unit {setup.character_file} not deployed - skipping")
            continue
        try:
            char_data = context.character_repo.load(setup.character_file)
            if char_data is None:
                handle_error(
                    f"Cannot create unit: character file not found: {setup.character_file}"
                )
                continue
            char_data["equipment"] = setup.equipment.copy() if setup.equipment else {}

            u = unit_factory.create_unit(
                character_filename=setup.character_file,
                position=Position(setup.start_q, setup.start_r),  # type: ignore[arg-type]
                facing=Facing(setup.facing),
                char_data=char_data,
            )

            # Set wield state for variable weapons
            if u and u.weapon and getattr(u.weapon, "wield_mode", None) == "variable":
                eq = setup.equipment
                off_hand = eq.get("off_hand")
                off_hand_equipped = bool(off_hand)
                u.weapon.set_wield_state(main_hand=True, off_hand_equipped=off_hand_equipped)

            if u:
                try:
                    sprite = sprite_repo.load_character_sprite(setup.sprite_file)
                    if sprite:
                        u.sprite = sprite
                except Exception as e:
                    handle_error(f"Failed to load sprite for {u.name}: {e}")
                team_units.append(u)
                logger.debug(
                    f"Created {team_label} unit: {u.name} at ({setup.start_q}, {setup.start_r})"
                )
        except Exception as e:
            handle_error(
                f"Error creating {team_label} unit {getattr(setup, 'character_file', '?')}: {e}"
            )
    return team_units


def _units_from_config(context, config: ScenarioConfig) -> tuple[list[Unit], list[Unit]]:
    """Create units for both teams from a finalized ScenarioConfig."""
    team_a = _create_units_for_team(context, config.team_a, "Team A")
    team_b = _create_units_for_team(context, config.team_b, "Team B")
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
    result = run_screen_loop(scenario_screen, screen, clock, cancel_action="scenario_cancelled")
    if result in ("quit", "cancelled"):
        logger.info("Scenario selection cancelled or quit")
        return

    scenario_config = scenario_screen.get_config()
    logger.info(
        f"Scenario configured: {scenario_config.map_name}, "
        f"Team A: {len(scenario_config.team_a)}, Team B: {len(scenario_config.team_b)}"
    )

    # 2) Deployment
    logger.info("Starting deployment phase")
    deployment_screen = DeploymentScreen(WIDTH, HEIGHT, scenario_config, context)
    result = run_screen_loop(deployment_screen, screen, clock, cancel_action="deployment_cancelled")
    if result in ("quit", "cancelled"):
        logger.info("Deployment cancelled or quit")
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
    result = run_screen_loop(battle_screen, screen, clock, update_method=battle_screen.update)
    if result == "quit":
        logger.info("Game quit during battle")
        return

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
