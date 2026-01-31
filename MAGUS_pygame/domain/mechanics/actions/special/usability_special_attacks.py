"""
Centralized special action usability checks.

This module provides a unified API for determining special attack availability.
It imports and re-exports availability checks from their domain locations:
- Shield bash checks: domain.mechanics.skills.shieldskill_modifiers
- Dagger attack combination: defined here (action-level)
- Charge: defined here (action-level)

Separation of concerns:
- Skill-level prerequisites (has_shield_equipped, can_use_shield_bash) stay in skills/
- Action-level usability (can_use_attack_combination, can_use_charge) defined here
- This module serves as a unified access point for the UI layer
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.entities import Unit

# Import attack combination config from attack_combination module
from .attack_combination import get_attack_combination_config


# Import shield-related checks from their domain location
# These are already properly organized in shieldskill_modifiers
def has_shield_equipped(unit: Unit) -> bool:
    """Check if unit has a shield equipped. See shieldskill_modifiers for implementation."""
    from domain.mechanics.skills.shieldskill_modifiers import has_shield_equipped as _check
    return _check(unit)


def can_use_shield_bash(unit: Unit) -> bool:
    """Check if unit can use shield bash. See shieldskill_modifiers for implementation."""
    from domain.mechanics.skills.shieldskill_modifiers import can_use_shield_bash as _check
    return _check(unit)


def can_use_reaction_bash(unit: Unit, reactions_used: int) -> bool:
    """Check if unit can use reaction bash. See shieldskill_modifiers for implementation."""
    from domain.mechanics.skills.shieldskill_modifiers import can_use_reaction_bash as _check
    return _check(unit, reactions_used)


def can_use_attack_combination(
    attacker: Unit,
    defender: Unit,
    weapon_skill_level: int,
) -> bool:
    """Check if attack combination can be used.

    Requirements:
    - Weapon skill level 3+ with dagger
    - Attacker and defender must be in melee range (adjacent)
    - Attacker must have enough AP

    Args:
        attacker: Attacking unit
        defender: Defending unit
        weapon_skill_level: Dagger skill level

    Returns:
        True if attack combination can be used
    """
    # Must be skill level 3+
    if weapon_skill_level < 3:
        return False

    # Must be in melee range (adjacent hex)
    # This check would be done at application layer with actual distance calculation
    # For now, we assume validation happens before calling resolve_attack with combination flag

    # Must have enough AP
    config = get_attack_combination_config(weapon_skill_level)
    if not config:
        return False

    # Check if attacker has enough AP
    if attacker.ap.current < config.ap_cost:
        return False

    return True


# ============================================================================
# CHARGE (Weaponskill 1+, any weapon)
# ============================================================================


def can_use_charge(
    attacker: Unit,
    defender: Unit,
    distance: int,
    weapon_reach: int,
) -> bool:
    """Check if charge special action can be used.

    Requirements:
    - Attacker and defender not in melee range (distance > 1)
    - Minimum 5 hexes starting distance (cannot charge closer targets)
    - Landing position within weapon reach of target
    - Enough AP (10) and Stamina (20)

    Args:
        attacker: Attacking unit
        defender: Defending unit
        distance: Current hex distance between units
        weapon_reach: Weapon reach in hexes

    Returns:
        True if charge can be used
    """
    CHARGE_AP_COST = 10
    CHARGE_STAMINA_COST = 20
    MIN_CHARGE_DISTANCE = 5

    # Too close to charge
    if distance <= 1:
        return False

    # Below minimum distance threshold
    if distance < MIN_CHARGE_DISTANCE:
        return False

    # Check AP and Stamina availability
    if attacker.ap.current < CHARGE_AP_COST:
        return False

    if attacker.stamina.current < CHARGE_STAMINA_COST:
        return False

    return True
