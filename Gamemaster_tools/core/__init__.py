"""
Core data models and business logic for M.A.G.U.S. RPG system.
"""

from core.character_model import (
    CombatStats,
    calculate_combat_stats,
    calculate_skill_points,
    get_level_for_xp,
    get_next_level_xp,
)
from core.race_model import (
    AgeCategory,
    AgeData,
    AttributeModifiers,
    ClassRestrictions,
    Race,
    RaceAttributes,
    RacialSkill,
    SpecialAbility,
)

__all__ = [
    # Character models and functions
    "CombatStats",
    "calculate_combat_stats",
    "calculate_skill_points",
    "get_level_for_xp",
    "get_next_level_xp",
    # Race models
    "Race",
    "AgeData",
    "AgeCategory",
    "RaceAttributes",
    "AttributeModifiers",
    "RacialSkill",
    "SpecialAbility",
    "ClassRestrictions",
]
