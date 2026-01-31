"""
Game Context - Dependency container for the application.

Manages lifecycle of repositories, services, and provides centralized access.
"""

from enum import Enum
from functools import lru_cache

from application.equipment_validation_service import EquipmentValidationService
from application.scenario_service import ScenarioService
from application.unit_setup_service import UnitSetupService
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


class EquipmentCategory(Enum):
    """Valid equipment categories."""

    WEAPONS_AND_SHIELDS = "weapons_and_shields"
    ARMOR = "armor"
    GENERAL = "general"


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

        try:
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

            logger.info("GameContext initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize GameContext: {e}", exc_info=True)
            raise

    def shutdown(self):
        """Clean up resources."""
        logger.info("Shutting down GameContext")
        try:
            self.character_repo.clear_cache()
            self.equipment_repo.clear_cache()
            self.sprite_repo.clear_cache()
            self.skills_repo.clear_cache()
            # Scenario repo is stateless; no cleanup needed
            logger.info("GameContext shutdown complete")
        except Exception as e:
            logger.error(f"Error during GameContext shutdown: {e}", exc_info=True)

    # Facade methods for presentation layer

    def get_skill_name(self, skill_id: str) -> str:
        """Get human-readable skill name from skill ID.

        Args:
            skill_id: Skill identifier

        Returns:
            Human-readable skill name
        """
        return self.skills_repo.get_skill_name(skill_id)

    def _find_equipment_by_id(
        self, category: EquipmentCategory | str, item_id: str
    ) -> dict | None:
        """Find equipment item by category and ID.

        Args:
            category: Equipment category (Enum or string)
            item_id: Equipment item identifier

        Returns:
            Equipment dict or None if not found
        """
        # Support both Enum and string for backward compatibility
        if isinstance(category, EquipmentCategory):
            category = category.value

        try:
            if category == "weapons_and_shields":
                return self.equipment_repo.find_weapon_by_id(item_id)
            elif category == "armor":
                return self.equipment_repo.find_armor_by_id(item_id)
            else:  # general
                return self.equipment_repo.find_general_by_id(item_id)
        except Exception as e:
            logger.warning(f"Equipment lookup failed for {item_id} (category={category}): {e}")
            return None

    def get_equipment_name(self, item_id: str, category: str) -> str:
        """Get human-readable equipment name from item ID and category.

        Args:
            item_id: Equipment item identifier
            category: Equipment category ('weapons_and_shields', 'armor', 'general')

        Returns:
            Human-readable equipment name (with [???] suffix if lookup failed)
        """
        # Try to find equipment in repository
        item = self._find_equipment_by_id(category, item_id)
        if item:
            return item.get("name", item_id.replace("_", " ").title())

        # Fallback: format item_id as readable text with failure marker
        fallback_name = item_id.replace("_", " ").title()
        logger.info(f"Equipment not found: {item_id} (category={category}); using fallback: {fallback_name}")
        return fallback_name
