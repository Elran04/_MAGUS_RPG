"""
Conditions package - Combat conditions and status effects.

Includes:
- Injury conditions (light, serious, critical)
- Stamina states (fresh to exhausted)
- Unskilled equipment penalties
- Mastery-level skill buffs
"""

from .injury import (
    InjuryCondition,
    InjuryModifiers,
    calculate_injury_condition,
    get_injury_modifiers,
)
from .mastery import (
    ActiveMasteries,
    MasteryModifiers,
    MasteryType,
    check_all_masteries,
    check_heavy_armor_mastery,
    check_shield_mastery,
    check_weapon_mastery,
    get_combined_mastery_modifiers,
    get_mastery_modifiers_for_unit,
)
from .stamina import (
    DEFAULT_COMBAT_MODIFIERS,
    CombatModifiers,
    Stamina,
    StaminaState,
    create_fatigue_condition,
)
from .unskilled import (
    UnskilledConditions,
    UnskilledModifiers,
    UnskilledType,
    check_all_unskilled_conditions,
    check_unskilled_heavy_armor,
    check_unskilled_shield,
    check_unskilled_weapon,
    get_combined_unskilled_modifiers,
    get_unskilled_modifiers_for_unit,
)

__all__ = [
    # Injury
    "InjuryCondition",
    "InjuryModifiers",
    "calculate_injury_condition",
    "get_injury_modifiers",
    # Stamina
    "Stamina",
    "StaminaState",
    "CombatModifiers",
    "DEFAULT_COMBAT_MODIFIERS",
    "create_fatigue_condition",
    # Unskilled
    "UnskilledType",
    "UnskilledModifiers",
    "UnskilledConditions",
    "check_unskilled_shield",
    "check_unskilled_weapon",
    "check_unskilled_heavy_armor",
    "check_all_unskilled_conditions",
    "get_combined_unskilled_modifiers",
    "get_unskilled_modifiers_for_unit",
    # Mastery
    "MasteryType",
    "MasteryModifiers",
    "ActiveMasteries",
    "check_weapon_mastery",
    "check_shield_mastery",
    "check_heavy_armor_mastery",
    "check_all_masteries",
    "get_combined_mastery_modifiers",
    "get_mastery_modifiers_for_unit",
]
