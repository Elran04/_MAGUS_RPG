"""
Game Context - Dependency container for the application.

Manages lifecycle of repositories, services, and provides centralized access.
"""

from domain.mechanics.damage import DamageService
from domain.services import UnitFactory
from application.scenario_service import ScenarioService
from infrastructure.repositories import (
    CharacterRepository,
    EquipmentRepository,
    SpriteRepository,
    ScenarioRepository,
)
from logger.logger import get_logger

logger = get_logger(__name__)


class GameContext:
    """
    Application-wide dependency container.

    Provides:
    - Repository instances
    - Domain services
    - Configuration access
    """

    def __init__(self):
        logger.info("Initializing GameContext")

        # Infrastructure
        self.character_repo = CharacterRepository()
        self.equipment_repo = EquipmentRepository()
        self.sprite_repo = SpriteRepository()
        self.scenario_repo = ScenarioRepository()
        self.scenario_service = ScenarioService(
            scenario_repo=self.scenario_repo,
            character_repo=self.character_repo,
            sprite_repo=self.sprite_repo,
        )

        # Domain services
        self.unit_factory = UnitFactory(
            character_repo=self.character_repo, equipment_repo=self.equipment_repo
        )
        self.damage_service = DamageService()

        logger.info("GameContext initialized")

    def shutdown(self):
        """Clean up resources."""
        logger.info("Shutting down GameContext")
        self.character_repo.clear_cache()
        self.equipment_repo.clear_cache()
        self.sprite_repo.clear_cache()
        # Scenario repo currently stateless
