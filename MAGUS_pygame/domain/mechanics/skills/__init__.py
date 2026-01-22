"""
Skills mechanics package - Weapon skill modifiers and registries.
"""

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
    "WeaponskillModifiers",
    "BASE_WEAPONSKILL_MODIFIERS",
    "WEAPONSKILL_UNIQUE_EFFECTS",
    "get_weaponskill_modifiers",
    "apply_weaponskill_modifiers",
    "get_overpower_threshold_for_skill",
    "should_grant_skill_opportunity_attack",
    "get_opportunity_attack_limit",
]
