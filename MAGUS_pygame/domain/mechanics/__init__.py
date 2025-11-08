"""
Domain mechanics package - Combat rules and calculations.

Modules:
- damage: Damage calculation with attribute bonuses, multipliers, armor
- reach: Weapon reach hexes, mandatory EP loss from FP damage
- armor: Armor entities, SFÉ absorption, degradation on overpower
- critical: Critical hit detection based on skill and roll
- attack_resolution: Complete attack flow from roll to damage application
- weapon_wielding: Variable weapon wielding modes and bonuses
- stamina: Stamina resource, thresholds, and combat penalties
"""

from .damage import (
    DamageContext,
    DamageResult,
    calculate_final_damage,
    DamageService,
)

from .reach import (
    get_weapon_reach,
    compute_reach_hexes,
    can_attack_target,
    calculate_mandatory_ep_loss,
)

from .armor import (
    ArmorPiece,
    calculate_total_armor_absorption,
    calculate_total_mgt,
    apply_overpower_degradation,
)

from .critical import (
    CriticalContext,
    is_critical_hit,
    get_critical_damage_multiplier,
    apply_critical_effects,
)

from .attack_resolution import (
    AttackOutcome,
    DefenseValues,
    AttackResult,
    calculate_defense_values,
    calculate_attack_value,
    resolve_attack,
    apply_attack_result,
)

from .weapon_wielding import (
    WieldMode,
    WieldingBonuses,
    WieldingInfo,
    can_wield_one_handed,
    calculate_wielding_bonuses,
    get_wielding_mode,
    get_wielding_info,
    validate_wielding_mode_change,
)

from .stamina import (
    Stamina,
    StaminaState,
    CombatModifiers,
    DEFAULT_COMBAT_MODIFIERS,
    THRESHOLDS,
)

__all__ = [
    # Damage
    "DamageContext",
    "DamageResult",
    "calculate_final_damage",
    "DamageService",
    # Reach
    "get_weapon_reach",
    "compute_reach_hexes",
    "can_attack_target",
    "calculate_mandatory_ep_loss",
    # Armor
    "ArmorPiece",
    "calculate_total_armor_absorption",
    "calculate_total_mgt",
    "apply_overpower_degradation",
    # Critical
    "CriticalContext",
    "is_critical_hit",
    "get_critical_damage_multiplier",
    "apply_critical_effects",
    # Attack Resolution
    "AttackOutcome",
    "DefenseValues",
    "AttackResult",
    "calculate_defense_values",
    "calculate_attack_value",
    "resolve_attack",
    "apply_attack_result",
    # Weapon Wielding
    "WieldMode",
    "WieldingBonuses",
    "WieldingInfo",
    "can_wield_one_handed",
    "calculate_wielding_bonuses",
    "get_wielding_mode",
    "get_wielding_info",
    "validate_wielding_mode_change",
    # Stamina
    "Stamina",
    "StaminaState",
    "CombatModifiers",
    "DEFAULT_COMBAT_MODIFIERS",
    "THRESHOLDS",
]
