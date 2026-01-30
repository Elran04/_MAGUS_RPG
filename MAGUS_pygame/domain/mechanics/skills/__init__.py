"""
Skills mechanics package - Weapon and shield skill modifiers and registries.
"""

from .shieldskill_modifiers import (
    ShieldskillModifiers,
    UnskilledDebuff,
    calculate_block_stamina_cost,
    can_use_reaction_bash,
    can_use_shield_bash,
    get_attacker_stamina_cost_dice,
    get_shieldskill_modifiers,
    get_unskilled_shield_penalty,
    has_shield_equipped,
    shield_protects_from_angle,
)
from .weaponskill_modifiers import (
    BASE_WEAPONSKILL_MODIFIERS,
    WEAPONSKILL_UNIQUE_EFFECTS,
    WeaponskillModifiers,
    apply_weaponskill_modifiers,
    get_opportunity_attack_limit,
    get_overpower_threshold_for_skill,
    get_weaponskill_modifiers,
    should_grant_skill_opportunity_attack,
)

__all__ = [
    # Weapon skills
    "WeaponskillModifiers",
    "BASE_WEAPONSKILL_MODIFIERS",
    "WEAPONSKILL_UNIQUE_EFFECTS",
    "get_weaponskill_modifiers",
    "apply_weaponskill_modifiers",
    "get_overpower_threshold_for_skill",
    "should_grant_skill_opportunity_attack",
    "get_opportunity_attack_limit",
    # Shield skills
    "ShieldskillModifiers",
    "UnskilledDebuff",
    "get_shieldskill_modifiers",
    "shield_protects_from_angle",
    "get_unskilled_shield_penalty",
    "has_shield_equipped",
    "calculate_block_stamina_cost",
    "get_attacker_stamina_cost_dice",
    "can_use_shield_bash",
    "can_use_reaction_bash",
]
