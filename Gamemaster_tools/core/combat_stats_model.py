"""
Combat Stats Data Model
Provides type-safe access to combat stats data from the database.
"""

from dataclasses import dataclass
from typing import Any


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
