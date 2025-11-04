# core/character_model.py
"""
Character model and combat calculations.
Uses dataclasses for type-safe access to combat stats.
"""

import random
from dataclasses import dataclass
from typing import Any

from utils.data.class_db_manager import ClassDBManager


@dataclass
class CombatStats:
    """Represents combat statistics for a character class.

    This maps directly to the combat_stats table schema.
    """

    # Database IDs
    id: int
    class_id: int

    # FP (Fájdalomtűrés Pont / Pain Tolerance)
    fp_base: int
    fp_min_per_level: int
    fp_max_per_level: int

    # ÉP (Életerő Pont / Health Points)
    ep_base: int

    # KP (Képzettség Pontok / Skill Points)
    kp_base: int
    kp_per_level: int

    # Combat values
    ke_base: int  # KÉ (Kezdeményező Érték / Initiative)
    te_base: int  # TÉ (Támadó Érték / Attack Value)
    ve_base: int  # VÉ (Védő Érték / Defense Value)
    ce_base: int  # CÉ (Célzó Érték / Aim Value)

    # HM (Harcmodor / Combat Style) points per level
    hm_total: int
    hm_te_mandatory: int
    hm_ve_mandatory: int

    @classmethod
    def from_db_row(cls, row: tuple[Any, ...] | None) -> "CombatStats | None":
        """Create CombatStats from a database row.

        Args:
            row: Tuple from SELECT * FROM combat_stats query

        Returns:
            CombatStats instance or None if row is None/empty
        """
        if not row or len(row) < 15:
            return None

        return cls(
            id=row[0],
            class_id=row[1],
            fp_base=row[2],
            fp_min_per_level=row[3],
            fp_max_per_level=row[4],
            ep_base=row[5],
            kp_base=row[6],
            kp_per_level=row[7],
            ke_base=row[8],
            te_base=row[9],
            ve_base=row[10],
            ce_base=row[11],
            hm_total=row[12],
            hm_te_mandatory=row[13],
            hm_ve_mandatory=row[14],
        )

    @classmethod
    def empty(cls) -> "CombatStats":
        """Create an empty CombatStats with all zeros.

        Returns:
            CombatStats instance with default values
        """
        return cls(
            id=0,
            class_id=0,
            fp_base=0,
            fp_min_per_level=0,
            fp_max_per_level=0,
            ep_base=0,
            kp_base=0,
            kp_per_level=0,
            ke_base=0,
            te_base=0,
            ve_base=0,
            ce_base=0,
            hm_total=0,
            hm_te_mandatory=0,
            hm_ve_mandatory=0,
        )


# Initialize managers
class_db = ClassDBManager()


def calculate_combat_stats(character: dict[str, Any]) -> dict[str, Any]:
    """Calculate combat statistics for a character.

    Args:
        character: Character dict with "Kaszt" and "Tulajdonságok" keys

    Returns:
        Updated character dict with "Harci értékek" and "Képzettségpontok"

    Raises:
        ValueError: If class not found in database
    """
    klass = character["Kaszt"]
    stats = character["Tulajdonságok"]

    # Get class_id from name
    classes = class_db.list_classes()
    class_id = next((cid for cid, name in classes if name == klass), None)
    if class_id is None:
        raise ValueError(f"Class '{klass}' not found in DB")

    details = class_db.get_class_details(class_id)

    # Parse combat stats using dataclass
    combat_stats = CombatStats.from_db_row(details["combat_stats"])
    if combat_stats is None:
        combat_stats = CombatStats.empty()

    # Véletlenszerű FP bónusz első szintre
    fp_bonus = (
        random.randint(combat_stats.fp_min_per_level, combat_stats.fp_max_per_level)
        if combat_stats.fp_min_per_level <= combat_stats.fp_max_per_level
        else 0
    )

    def bonus(val: int) -> int:
        """Calculate attribute bonus (value - 10, minimum 0)."""
        return max(0, val - 10)

    # Calculate final combat values
    fp = combat_stats.fp_base + fp_bonus + bonus(stats["Akaraterő"]) + bonus(stats["Állóképesség"])
    ep = combat_stats.ep_base + bonus(stats["Egészség"])
    ke = combat_stats.ke_base + bonus(stats["Gyorsaság"]) + bonus(stats["Ügyesség"])
    te = (
        combat_stats.te_base
        + bonus(stats["Erő"])
        + bonus(stats["Gyorsaság"])
        + bonus(stats["Ügyesség"])
    )
    ve = combat_stats.ve_base + bonus(stats["Gyorsaság"]) + bonus(stats["Ügyesség"])
    ce = combat_stats.ce_base + bonus(stats["Ügyesség"])

    character["Harci értékek"] = {
        "FP": fp,
        "ÉP": ep,
        "KÉ": ke,
        "TÉ": te,
        "VÉ": ve,
        "CÉ": ce,
        "HM/szint": {
            "total": combat_stats.hm_total,
            "mandatory": {
                "TÉ": combat_stats.hm_te_mandatory,
                "VÉ": combat_stats.hm_ve_mandatory,
            },
        },
    }

    character["Képzettségpontok"] = {
        "Alap": combat_stats.kp_base,
        "Szintenként": combat_stats.kp_per_level,
    }

    return character


def calculate_skill_points(klass: str) -> dict[str, int]:
    """Calculate skill points (KP) for a given class without needing attributes.

    Args:
        klass: The class name (e.g., "Harcos", "Varázsló")

    Returns:
        Dict with "Alap" and "Szintenként" keys containing the KP values

    Raises:
        ValueError: If class not found in database
    """
    # Get class_id from name
    classes = class_db.list_classes()
    class_id = next((cid for cid, name in classes if name == klass), None)
    if class_id is None:
        raise ValueError(f"Class '{klass}' not found in DB")

    details = class_db.get_class_details(class_id)

    # Parse combat stats using dataclass
    combat_stats = CombatStats.from_db_row(details["combat_stats"])
    if combat_stats is None:
        return {"Alap": 0, "Szintenként": 0}

    return {
        "Alap": combat_stats.kp_base,
        "Szintenként": combat_stats.kp_per_level,
    }


def get_level_for_xp(klass: str, xp: int) -> int:
    """Calculate character level based on experience points.

    Args:
        klass: The class name
        xp: Total experience points

    Returns:
        Current character level

    Raises:
        ValueError: If class not found in database
    """
    # Get class_id from name
    classes = class_db.list_classes()
    class_id = next((cid for cid, name in classes if name == klass), None)
    if class_id is None:
        raise ValueError(f"Class '{klass}' not found in DB")

    details = class_db.get_class_details(class_id)
    reqs = [r[1] for r in details["level_requirements"]]

    for i in range(1, len(reqs)):
        if xp < reqs[i]:
            return i - 1

    extra_xp = details["extra_xp"] if details["extra_xp"] else 50000
    if reqs:
        max_level = len(reqs) - 1
        if xp < reqs[-1]:
            return max_level
        else:
            return max_level + ((xp - int(reqs[-1])) // int(extra_xp)) + 1
    return 1


def get_next_level_xp(klass: str, xp: int) -> int:
    """Calculate XP required for next level.

    Args:
        klass: The class name
        xp: Current experience points

    Returns:
        Experience points required for next level

    Raises:
        ValueError: If class not found in database
    """
    # Get class_id from name
    classes = class_db.list_classes()
    class_id = next((cid for cid, name in classes if name == klass), None)
    if class_id is None:
        raise ValueError(f"Class '{klass}' not found in DB")

    details = class_db.get_class_details(class_id)
    reqs = [r[1] for r in details["level_requirements"]]
    level = get_level_for_xp(klass, xp)

    if level + 1 < len(reqs):
        return int(reqs[level + 1])
    else:
        extra_xp = details["extra_xp"] if details["extra_xp"] else 50000
        return int(reqs[-1]) + (level - (len(reqs) - 1) + 1) * int(extra_xp)
