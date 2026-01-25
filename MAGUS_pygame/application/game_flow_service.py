"""
Game Flow Service - Orchestrates complete game flow from scenario to battle.

Complete flow: Scenario Selection -> Equipment -> Deployment -> Battle

This application service coordinates the high-level game workflow,
managing transitions between different game phases and screens.
"""

from __future__ import annotations

from domain.entities import Unit
from domain.value_objects import Facing, Position
from domain.value_objects.scenario_config import ScenarioConfig
from logger.logger import get_logger

logger = get_logger(__name__)


def _create_units_for_team(context, team_setups, team_label: str) -> list[Unit]:
    """Create units for a team from scenario config setups.

    Raises exceptions on error; caller (presentation layer) should handle display.
    """
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
                raise ValueError(f"Character file not found: {setup.character_file}")

            char_data["equipment"] = setup.equipment.copy() if setup.equipment else {}
            if setup.skills:
                char_data["skills_override"] = setup.skills.copy()

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
                    logger.warning(f"Failed to load sprite for {u.name}: {e}")

                team_units.append(u)
                logger.debug(
                    f"Created {team_label} unit: {u.name} at ({setup.start_q}, {setup.start_r})"
                )
        except Exception as e:
            raise RuntimeError(f"Error creating {team_label} unit: {e}") from e

    return team_units


def _units_from_config(context, config: ScenarioConfig) -> tuple[list[Unit], list[Unit]]:
    """Create units for both teams from a finalized ScenarioConfig."""
    team_a = _create_units_for_team(context, config.team_a, "Team A")
    team_b = _create_units_for_team(context, config.team_b, "Team B")
    return team_a, team_b


def coordinate_game_flow(
    context,
    scenario_screen,
    deployment_screen_factory,
    battle_screen,
    screen_loop_func,
) -> str:
    """Coordinate complete game flow: Scenario -> Deployment -> Battle.

    Application layer orchestration; presentation layer provides screen objects.

    Args:
        context: Game context with repositories and factories
        scenario_screen: ScenarioScreen instance (created by presentation)
        deployment_screen_factory: Callable[[ScenarioConfig], object] that returns a DeploymentScreen
        battle_screen: BattleScreen instance or None
        screen_loop_func: Function(screen_obj, cancel_action) -> result that runs screen loop

    Returns:
        Final action string ('quit', 'cancelled', or outcome)
    """
    logger.info("Starting game flow: Scenario Selection")

    # 1) Scenario selection
    result = screen_loop_func(scenario_screen, cancel_action="scenario_cancelled")
    if result in ("quit", "cancelled"):
        logger.info("Scenario selection cancelled or quit")
        return result

    scenario_config = scenario_screen.get_config()
    logger.info(
        f"Scenario configured: {scenario_config.map_name}, "
        f"Team A: {len(scenario_config.team_a)}, Team B: {len(scenario_config.team_b)}"
    )

    # 2) Deployment
    if not deployment_screen_factory:
        raise ValueError("DeploymentScreen factory required for game flow")

    deployment_screen = deployment_screen_factory(scenario_config)

    logger.info("Starting deployment phase")
    result = screen_loop_func(deployment_screen, cancel_action="deployment_cancelled")
    if result in ("quit", "cancelled"):
        logger.info("Deployment cancelled or quit")
        return result

    final_config = deployment_screen.get_config()
    logger.info("Deployment complete, creating units")

    # Get background from deployment screen (if available). Scaling is handled by presentation layer.
    background = getattr(deployment_screen, "background", None)

    # 3) Create units from configuration
    team_a_units, team_b_units = _units_from_config(context, final_config)
    units: list[Unit] = team_a_units + team_b_units

    if not units:
        logger.error("No units created; aborting battle start")
        return "error"

    logger.info(f"Created {len(team_a_units)} Team A units and {len(team_b_units)} Team B units")

    # 4) Setup battle service with teams
    from application.battle_service import BattleService

    battle_service = BattleService(
        units=units,
        equipment_repo=context.equipment_repo,
        blocked_hexes=scenario_config.blocked_hexes,
    )
    battle_service.set_teams(team_a_units, team_b_units)
    battle_service.start_battle()

    logger.info("Battle started!")

    # 5) Run battle (battle_screen already created with battle_service and context)
    if not battle_screen:
        raise ValueError("BattleScreen required for game flow")

    # Update battle_screen with the battle_service and background
    battle_screen.battle = battle_service
    if background:
        battle_screen.renderer.background = background
        logger.debug("Background updated for battle screen")

    result = screen_loop_func(battle_screen, update_method=battle_screen.update)
    if result == "quit":
        logger.info("Game quit during battle")
        return result

    # Battle ended
    action = battle_screen.get_action()
    logger.info(f"Battle ended: {action}")

    return action
