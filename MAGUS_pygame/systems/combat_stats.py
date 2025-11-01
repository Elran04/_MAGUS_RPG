"""
Centralized combat stat computation service.

Provides compute_effective_combat_stats(unit) to standardize how combat
stats are calculated across the codebase. This encapsulates:
- Base stats (from unit.combat: KÉ/TÉ/VÉ/CÉ)
- Weapon modifiers (from unit.weapon: KE/TE/VE/CE)
- Wielding bonuses for variable weapons (KÉ/TÉ/VÉ)
- Condition modifiers (placeholder for future)

Returned breakdown can be used by both UI and game logic to ensure
consistency and to make future additions (like conditions) easy.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from core.unit_manager import Unit

# Local import to avoid circular dependencies during module import time
from systems.weapon_wielding import get_wielding_info

STAT_KEYS = ("KE", "TE", "VE", "CE")


def _int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def compute_effective_combat_stats(unit: Unit) -> dict[str, dict[str, int]]:
    """
    Compute effective combat stats with full breakdown.

    Args:
        unit: The unit whose stats to compute.

    Returns:
        A dict with keys: base, weapon, wielding, conditions, total.
        Each maps to a dict of stat values for KE/TE/VE/CE.
    """
    # Base stats from character combat profile (Hungarian keys)
    base = {
        "KE": _int(unit.combat.get("KÉ", 0)),
        "TE": _int(unit.combat.get("TÉ", 0)),
        "VE": _int(unit.combat.get("VÉ", 0)),
        "CE": _int(unit.combat.get("CÉ", 0)),
    }

    # Weapon modifiers (English short keys)
    weapon = dict.fromkeys(STAT_KEYS, 0)
    if getattr(unit, "weapon", None):
        weapon["KE"] = _int(unit.weapon.get("KE", 0))
        weapon["TE"] = _int(unit.weapon.get("TE", 0))
        weapon["VE"] = _int(unit.weapon.get("VE", 0))
        weapon["CE"] = _int(unit.weapon.get("CE", 0))

    # Wielding bonuses (apply only for variable weapons and only KE/TE/VE)
    wielding = {"KE": 0, "TE": 0, "VE": 0, "CE": 0}
    if getattr(unit, "weapon", None) and unit.weapon.get("wield_mode") == "Változó":
        info = get_wielding_info(unit, unit.weapon)
        bonuses = info.get("bonuses", {})
        wielding["KE"] = _int(bonuses.get("KE", 0))
        wielding["TE"] = _int(bonuses.get("TE", 0))
        wielding["VE"] = _int(bonuses.get("VE", 0))
        # CE has no wielding effect currently

    # Conditions placeholder (to be integrated later)
    conditions = dict.fromkeys(STAT_KEYS, 0)

    # Totals
    total = {}
    for k in STAT_KEYS:
        total[k] = base.get(k, 0) + weapon.get(k, 0) + wielding.get(k, 0) + conditions.get(k, 0)

    return {
        "base": base,
        "weapon": weapon,
        "wielding": wielding,
        "conditions": conditions,
        "total": total,
    }
