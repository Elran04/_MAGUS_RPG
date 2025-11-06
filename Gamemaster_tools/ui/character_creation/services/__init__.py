"""
Service layer for character creation.
Provides stable import points for DB access, prerequisite checks, and selection logic.

Usage:
    from ui.character_creation.services import (
        SkillDatabaseService,
        SkillPrerequisiteChecker,
        PrerequisiteFormatter,
        SkillSelectionManager,
        PlaceholderSkillManager,
        EquipmentLoader,
        EquipmentService
    )
"""

from .equipment_loader import EquipmentLoader
from .equipment_service import EquipmentService
from .placeholder_skill_service import PlaceholderSkillManager
from .prerequisite_formatter import PrerequisiteFormatter
from .skill_prerequisites_service import SkillPrerequisiteChecker
from .skill_repository import SkillDatabaseService
from .skill_selection_service import SkillSelectionManager

__all__ = [
    "SkillDatabaseService",
    "SkillPrerequisiteChecker",
    "PrerequisiteFormatter",
    "SkillSelectionManager",
    "PlaceholderSkillManager",
    "EquipmentLoader",
    "EquipmentService",
]
