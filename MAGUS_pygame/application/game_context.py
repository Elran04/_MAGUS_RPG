"""
Game Context - Dependency container for the application.

Manages lifecycle of repositories, services, and provides centralized access.
"""

from infrastructure.repositories import (
    CharacterRepository,
    EquipmentRepository,
    SpriteRepository,
)
from domain.services import UnitFactory
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
        
        # Domain services
        self.unit_factory = UnitFactory(
            character_repo=self.character_repo,
            equipment_repo=self.equipment_repo
        )
        
        logger.info("GameContext initialized")
    
    def shutdown(self):
        """Clean up resources."""
        logger.info("Shutting down GameContext")
        self.character_repo.clear_cache()
        self.equipment_repo.clear_cache()
        self.sprite_repo.clear_cache()
