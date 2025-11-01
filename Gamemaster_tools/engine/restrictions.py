"""
Centralized character selection restrictions.
- Gender-based class restrictions (static constants)
- Helper to validate class selection against gender and allowed-classes per race
"""

from __future__ import annotations

from collections.abc import Iterable

# Source gender restrictions from character.py to avoid duplication
try:
    from engine.character import GENDER_RESTRICTIONS
except Exception:
    # Fallback (should rarely be used)
    GENDER_RESTRICTIONS = {
        "Nő": {"Lovag", "Paplovag", "Barbár", "Boszorkánymester"},
        "Férfi": {"Boszorkány", "Amazon"},
    }


def is_class_allowed(gender: str, klass: str, allowed_for_race: Iterable[str] | None) -> bool:
    """Validate a class choice against gender restrictions and race-allowed list.

    Args:
        gender: "Férfi" or "Nő"
        klass: class name
        allowed_for_race: names of classes allowed for the selected race; if None, treat as all allowed
    """
    if klass in GENDER_RESTRICTIONS.get(gender, set()):
        return False
    if allowed_for_race is not None and klass not in set(allowed_for_race):
        return False
    return True
