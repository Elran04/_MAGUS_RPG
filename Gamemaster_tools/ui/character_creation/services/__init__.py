"""
Service layer for character creation.
Provides stable import points for DB access, prerequisite checks, and selection logic.

Usage:
    from ui.character_creation.services import (
        SkillDatabaseHelper, 
        SkillPrerequisiteChecker, 
        PrerequisiteInfoHelper, 
        SkillSelectionManager,
        PlaceholderSkillManager,
        EquipmentLoader,
        EquipmentService
    )
"""

from .skill_repository import SkillDatabaseHelper
from .skill_prerequisites_service import SkillPrerequisiteChecker
from .prerequisite_formatter import PrerequisiteInfoHelper
from .skill_selection_service import SkillSelectionManager
from .placeholder_skill_service import PlaceholderSkillManager
from .equipment_loader import EquipmentLoader
from .equipment_service import EquipmentService

__all__ = [
    'SkillDatabaseHelper',
    'SkillPrerequisiteChecker',
    'PrerequisiteInfoHelper',
    'SkillSelectionManager',
    'PlaceholderSkillManager',
    'EquipmentLoader',
    'EquipmentService',
]
