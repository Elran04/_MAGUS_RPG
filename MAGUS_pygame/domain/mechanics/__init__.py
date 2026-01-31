"""
Domain mechanics package - Combat rules and calculations.

Modules:
- damage: Damage calculation with attribute bonuses, multipliers, armor
- reach: Weapon reach hexes, mandatory EP loss from FP damage
- armor: Armor entities, SFÉ absorption, degradation on overpower
- critical: Critical hit detection based on skill and roll
- attack_resolution: Complete attack flow from roll to damage application
- weapon_wielding: Variable weapon wielding modes and bonuses
- conditions: Combat conditions (stamina, injury, unskilled equipment)
- actions: Player-initiated action abstractions (phase 1: attack, movement)
- reactions: Event-triggered mechanics (phase 2: opportunity attack)
"""

from .actions import ActionCategory, ActionCost, ActionResult, AttackAction, MovementAction
from .armor import ArmorPiece, ArmorSystem, HitzoneResolver
from .attack_resolution import (
    AttackOutcome,
    AttackResult,
    DefenseValues,
    apply_attack_result,
    calculate_attack_value,
    calculate_defense_values,
    resolve_attack,
)
from .conditions import (
    ActiveMasteries,
    CombatModifiers,
    InjuryCondition,
    InjuryModifiers,
    MasteryModifiers,
    MasteryType,
    Stamina,
    StaminaState,
    UnskilledConditions,
    UnskilledModifiers,
    UnskilledType,
    calculate_injury_condition,
    check_all_masteries,
    check_all_unskilled_conditions,
    check_heavy_armor_mastery,
    check_shield_mastery,
    check_unskilled_heavy_armor,
    check_unskilled_shield,
    check_unskilled_weapon,
    check_weapon_mastery,
    create_fatigue_condition,
    get_combined_mastery_modifiers,
    get_combined_unskilled_modifiers,
    get_injury_modifiers,
    get_mastery_modifiers_for_unit,
    get_unskilled_modifiers_for_unit,
)
from .critical import (
    CriticalContext,
    apply_critical_effects,
    get_critical_damage_multiplier,
    get_critical_threshold_for_skill,
    is_critical_failure,
    is_critical_hit,
)
from .damage import DamageContext, DamageResult, calculate_final_damage
from .reach import (
    calculate_mandatory_ep_loss,
    can_attack_target,
    compute_reach_hexes,
    get_weapon_reach,
)
from .reactions import (
    CounterattackReaction,
    OpportunityAttackReaction,
    Reaction,
    ReactionCategory,
    ReactionResult,
    ReactionShieldBash,
)
from .weapon_wielding import (
    WieldingBonuses,
    WieldingInfo,
    WieldMode,
    calculate_wielding_bonuses,
    can_wield_one_handed,
    get_wielding_info,
    get_wielding_mode,
    validate_wielding_mode_change,
)

__all__ = [
    # Damage
    "DamageContext",
    "DamageResult",
    "calculate_final_damage",
    # Reach
    "get_weapon_reach",
    "compute_reach_hexes",
    "can_attack_target",
    "calculate_mandatory_ep_loss",
    # Armor
    "ArmorPiece",
    "ArmorSystem",
    "HitzoneResolver",
    # Critical
    "CriticalContext",
    "is_critical_hit",
    "is_critical_failure",
    "get_critical_threshold_for_skill",
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
    # Conditions
    "Stamina",
    "StaminaState",
    "CombatModifiers",
    "create_fatigue_condition",
    "InjuryCondition",
    "InjuryModifiers",
    "calculate_injury_condition",
    "get_injury_modifiers",
    "UnskilledType",
    "UnskilledModifiers",
    "UnskilledConditions",
    "check_unskilled_shield",
    "check_unskilled_weapon",
    "check_unskilled_heavy_armor",
    "check_all_unskilled_conditions",
    "get_combined_unskilled_modifiers",
    "get_unskilled_modifiers_for_unit",
    "MasteryType",
    "MasteryModifiers",
    "ActiveMasteries",
    "check_weapon_mastery",
    "check_shield_mastery",
    "check_heavy_armor_mastery",
    "check_all_masteries",
    "get_combined_mastery_modifiers",
    "get_mastery_modifiers_for_unit",
    # Actions
    "ActionCategory",
    "ActionCost",
    "ActionResult",
    "AttackAction",
    "MovementAction",
    # Reactions
    "ReactionCategory",
    "ReactionResult",
    "Reaction",
    "OpportunityAttackReaction",
    "CounterattackReaction",
    "ReactionShieldBash",
]
