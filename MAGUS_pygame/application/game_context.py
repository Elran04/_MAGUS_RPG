"""
Game Context - Dependency container for the application.

Manages lifecycle of repositories, services, and provides centralized access.
"""

from application.equipment_validation_service import EquipmentValidationService
from application.scenario_service import ScenarioService
from application.unit_setup_service import UnitSetupService
from domain.mechanics.damage import DamageService
from domain.services import UnitFactory
from infrastructure.repositories import (
    CharacterRepository,
    EquipmentRepository,
    ScenarioRepository,
    SpriteRepository,
)
from infrastructure.repositories.skills_repository import SkillsRepository
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

        # Cache for equipment names to avoid repeated lookups during rendering
        self._equipment_name_cache: dict[str, str] = {}

        # Infrastructure
        self.character_repo = CharacterRepository()
        self.equipment_repo = EquipmentRepository()
        self.sprite_repo = SpriteRepository()
        self.scenario_repo = ScenarioRepository()
        self.skills_repo = SkillsRepository()

        # Application services
        self.unit_setup_service = UnitSetupService(character_repo=self.character_repo)
        self.equipment_validation_service = EquipmentValidationService(
            equipment_repo=self.equipment_repo
        )
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
        self.skills_repo.clear_cache()
        # Scenario repo currently stateless

    # Facade methods for presentation layer
    def get_skill_name(self, skill_id: str) -> str:
        """Get human-readable skill name from skill ID.

        Args:
            skill_id: Skill identifier

        Returns:
            Human-readable skill name
        """
        return self.skills_repo.get_skill_name(skill_id)

    def get_equipment_name(self, item_id: str, category: str) -> str:
        """Get human-readable equipment name from item ID and category.

        Args:
            item_id: Equipment item identifier
            category: Equipment category ('weapons_and_shields', 'armor', 'general')

        Returns:
            Human-readable equipment name
        """
        # Check cache first
        cache_key = f"{category}:{item_id}"
        if cache_key in self._equipment_name_cache:
            return self._equipment_name_cache[cache_key]

        result = item_id.replace("_", " ").title()  # Default fallback

        try:
            if category == "weapons_and_shields":
                item = self.equipment_repo.find_weapon_by_id(item_id)
                if item:
                    result = item.get("name", result)
            elif category == "armor":
                item = self.equipment_repo.find_armor_by_id(item_id)
                if item:
                    result = item.get("name", result)
            else:
                item = self.equipment_repo.find_general_by_id(item_id)
                if item:
                    result = item.get("name", result)
        except Exception as e:
            logger.debug(f"Equipment lookup failed for {item_id}: {e}")

        # Cache the result
        self._equipment_name_cache[cache_key] = result
        return result
