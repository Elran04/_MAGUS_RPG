"""
Injury subsystem for MAGUS combat engine.

Models injury conditions based on FP and ÉP damage.
- Light injury (Könnyű sérülés): 75% of max FP reached
- Serious injury (Súlyos sérülés): Any ÉP damage taken
- Critical injury (Kritikus sérülés): 75% of max ÉP reached

These conditions are mutually exclusive; only the strongest applies.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class InjuryCondition(str, Enum):
    """Injury severity levels (from weakest to strongest)."""

    NONE = "Egészséges"  # No injury
    LIGHT = "Könnyű sérülés"  # Light injury
    SERIOUS = "Súlyos sérülés"  # Serious injury
    CRITICAL = "Kritikus sérülés"  # Critical injury


@dataclass(frozen=True)
class InjuryModifiers:
    """Combat stat modifiers from injury condition.

    Negative values reduce stats.
    """

    ke_mod: int = 0
    te_mod: int = 0
    ve_mod: int = 0
    ce_mod: int = 0


# Injury condition modifiers
INJURY_MODIFIERS: dict[InjuryCondition, InjuryModifiers] = {
    InjuryCondition.NONE: InjuryModifiers(0, 0, 0, 0),
    InjuryCondition.LIGHT: InjuryModifiers(-5, -10, -10, -5),
    InjuryCondition.SERIOUS: InjuryModifiers(-10, -20, -20, -10),
    InjuryCondition.CRITICAL: InjuryModifiers(-15, -25, -25, -15),
}


def calculate_injury_condition(
    current_fp: int, max_fp: int, current_ep: int, max_ep: int
) -> InjuryCondition:
    """
    Determine injury condition based on FP and ÉP.

    Priority (mutually exclusive - strongest applies):
    1. CRITICAL: if current_ep <= 75% of max_ep (rounded down)
    2. SERIOUS: if current_ep < max_ep (any ÉP damage)
    3. LIGHT: if current_fp <= 75% of max_fp (rounded down)
    4. NONE: otherwise

    Args:
        current_fp: Current fatigue points
        max_fp: Maximum fatigue points
        current_ep: Current health points (ÉP)
        max_ep: Maximum health points (ÉP)

    Returns:
        InjuryCondition enum
    """
    # Critical injury: 75% of max EP reached (rounded down)
    critical_threshold = int(max_ep * 0.75)
    if current_ep <= critical_threshold:
        return InjuryCondition.CRITICAL

    # Serious injury: any ÉP damage taken
    if current_ep < max_ep:
        return InjuryCondition.SERIOUS

    # Light injury: 75% of max FP reached (rounded down)
    light_threshold = int(max_fp * 0.75)
    if current_fp <= light_threshold:
        return InjuryCondition.LIGHT

    # No injury
    return InjuryCondition.NONE


def get_injury_modifiers(condition: InjuryCondition) -> InjuryModifiers:
    """Get combat modifiers for injury condition."""
    return INJURY_MODIFIERS.get(condition, InjuryModifiers())
