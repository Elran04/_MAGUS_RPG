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
- actions: Player-initiated action abstractions (phase 1: attack, movement)
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
from .critical import (
    CriticalContext,
    apply_critical_effects,
    get_critical_damage_multiplier,
    is_critical_hit,
)
from .damage import DamageContext, DamageResult, DamageService, calculate_final_damage
from .reach import (
    calculate_mandatory_ep_loss,
    can_attack_target,
    compute_reach_hexes,
    get_weapon_reach,
)
from .reactions import OpportunityAttackReaction, Reaction, ReactionCategory, ReactionResult
from .stamina import (
    DEFAULT_COMBAT_MODIFIERS,
    THRESHOLDS,
    CombatModifiers,
    FatigueCondition,
    Stamina,
    StaminaState,
    create_fatigue_condition,
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
    "DamageService",
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
    "FatigueCondition",
    "create_fatigue_condition",
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
]
