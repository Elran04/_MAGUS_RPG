"""
Weapon skill modifiers registry for MAGUS combat.

Each weapon skill defines how its levels modify attack resolution:
- Stat bonuses/penalties (KÉ, TÉ, VÉ, CÉ)
- Stamina cost reductions
- Overpower threshold shifts
- Critical/failure range overrides
- Special effects (opportunity attacks, parries, etc.)

Weaponskills are registered per skill_id and applied during attack resolution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.entities import Unit


@dataclass(frozen=True)
class WeaponskillModifiers:
    """Stat and effect modifiers from a weapon skill at a given level.

    Note: Stat bonuses/penalties (KÉ, TÉ, VÉ, CÉ) are handled by conditions systems:
    - Unskilled penalties from domain.mechanics.conditions.unskilled
    - Mastery bonuses from domain.mechanics.conditions.mastery
    """

    level: int

    stamina_cost_modifier: float = (
        0  # >=1 multiplies cost (e.g., 2x unskilled); negative reduces flat (e.g., -1)
    )
    overpower_threshold_shift: int = 0  # Reduces overpower threshold (e.g., -10 at level 5)

    critical_threshold_override: int | None = None  # Override critical roll threshold
    critical_failure_max: int | None = None  # Highest roll that counts as critical failure

    attack_ap_multiplier: float = (
        1  # >=1 multiplies cost (e.g., 2x); <1 adds flat scaled by 100 (e.g., 0.02 = +2)
    )

    # Special effects
    has_opportunity_on_miss_parry: bool = False  # Level 3+: opportunity on miss/parry
    opportunity_attacks_per_turn: int = 0  # Level 3: 1, Level 6: 3

    @property
    def stamina_cost_reduction(self) -> int:
        """Alias for tests: positive reduction amount derived from stamina_cost_modifier."""
        if self.stamina_cost_modifier >= 0:
            return 0
        return int(abs(self.stamina_cost_modifier))


# ============================================================================
# BASE WEAPONSKILL MODIFIERS (Universal for all weapon types)
# ============================================================================

BASE_WEAPONSKILL_MODIFIERS = {
    0: WeaponskillModifiers(
        level=0,
        stamina_cost_modifier=2,  # Double stamina/AP cost for attacks
        overpower_threshold_shift=0,
        critical_threshold_override=101,  # No crits possible;
        critical_failure_max=10,  # Critical failure 1-10
        attack_ap_multiplier=2,  # Double stamina/AP cost for attacks
    ),
    1: WeaponskillModifiers(
        level=1,
        stamina_cost_modifier=0,  # No longer double stamina cost
        overpower_threshold_shift=0,
        critical_threshold_override=101,  # No crits; critical failure 1-5
        critical_failure_max=5,
        attack_ap_multiplier=0.02,  # Add +2 flat (was doubling, now less severe)
    ),
    2: WeaponskillModifiers(
        level=2,
        stamina_cost_modifier=0,
        overpower_threshold_shift=0,
        critical_threshold_override=100,  # Only nat 100 (1%); critical failure on 1
        critical_failure_max=1,
        attack_ap_multiplier=1,
    ),
    3: WeaponskillModifiers(
        level=3,
        stamina_cost_modifier=-1,  # Attack stamina cost reduced by 1
        overpower_threshold_shift=0,
        critical_threshold_override=100,  # Only nat 100; no critical failures
        # Unique effects defined per weapon type
        critical_failure_max=None,
        attack_ap_multiplier=1,
    ),
    4: WeaponskillModifiers(
        level=4,
        stamina_cost_modifier=-2,  # Attack stamina cost reduced by 2
        overpower_threshold_shift=0,
        critical_threshold_override=96,  # 96-100 critical (5%)
        critical_failure_max=None,
        attack_ap_multiplier=1,
    ),
    5: WeaponskillModifiers(
        level=5,
        stamina_cost_modifier=-3,  # Attack stamina cost reduced by 3
        overpower_threshold_shift=-10,  # Overpower threshold reduced by 10 (50 -> 40)
        critical_threshold_override=91,  # 91-100 critical (10%)
        critical_failure_max=None,
        attack_ap_multiplier=1,
    ),
    6: WeaponskillModifiers(
        level=6,
        stamina_cost_modifier=-3,
        overpower_threshold_shift=-10,
        critical_threshold_override=91,
        # Unique effects defined per weapon type
        critical_failure_max=None,
        attack_ap_multiplier=1,
    ),
}


# ============================================================================
# WEAPON-SPECIFIC UNIQUE EFFECTS (Only level 3 and 6)
# ============================================================================

WEAPONSKILL_UNIQUE_EFFECTS = {
    "weaponskill_longswords": {
        3: {
            "has_opportunity_on_miss_parry": True,
            "opportunity_attacks_per_turn": 1,
        },
        6: {
            "has_opportunity_on_miss_parry": True,
            "opportunity_attacks_per_turn": 3,
        },
    },
    # Add other weapon types here:
    # "weaponskill_shortswords": {
    #     3: {"unique_effect": ...},
    #     6: {"unique_effect": ...},
    # },
}


def get_weaponskill_modifiers(
    skill_level: int, weapon_skill_id: str = "weaponskill_longswords"
) -> WeaponskillModifiers:
    """Get modifier object for a weaponskill level.

    Merges base modifiers with weapon-specific unique effects for levels 3 and 6.

    Args:
        skill_level: Skill level (0-6+)
        weapon_skill_id: Weapon skill identifier (e.g., "weaponskill_longswords")

    Returns:
        WeaponskillModifiers for that level, or level 0 (unskilled) if out of range
    """
    import dataclasses

    # Get base modifiers
    base = BASE_WEAPONSKILL_MODIFIERS.get(skill_level, BASE_WEAPONSKILL_MODIFIERS[0])

    # Check for weapon-specific unique effects
    if weapon_skill_id in WEAPONSKILL_UNIQUE_EFFECTS:
        unique_effects = WEAPONSKILL_UNIQUE_EFFECTS[weapon_skill_id].get(skill_level)
        if unique_effects:
            # Merge unique effects into base modifiers
            return dataclasses.replace(base, **unique_effects)

    return base


def apply_weaponskill_modifiers(
    attacker: Unit,
    attack_roll: int,
    weapon_skill_level: int,
    weapon_skill_id: str = "weaponskill_longswords",
) -> tuple[float, int | None, int | None, float]:
    """Apply weaponskill modifiers to attack values.

    Args:
        attacker: Attacking unit
        attack_roll: Raw d100 roll
        weapon_skill_level: Skill level
        weapon_skill_id: Weapon skill identifier

    Returns:
        Tuple of (stamina_cost_modifier, critical_threshold_override, critical_failure_max, attack_ap_multiplier)

    Note: Stat modifiers (KÉ, TÉ, VÉ, CÉ) are applied separately via conditions systems
    """
    mods = get_weaponskill_modifiers(weapon_skill_level, weapon_skill_id)

    return (
        mods.stamina_cost_modifier,
        mods.critical_threshold_override,
        mods.critical_failure_max,
        mods.attack_ap_multiplier,
    )


def get_overpower_threshold_for_skill(
    weapon_skill_level: int,
    base_threshold: int = 50,
    weapon_skill_id: str = "weaponskill_longswords",
) -> int:
    """Calculate overpower threshold with skill modifiers.

    Args:
        weapon_skill_level: Skill level
        base_threshold: Base threshold (default 50)
        weapon_skill_id: Weapon skill identifier

    Returns:
        Adjusted overpower threshold
    """
    mods = get_weaponskill_modifiers(weapon_skill_level, weapon_skill_id)
    return base_threshold + mods.overpower_threshold_shift  # Shift is usually negative


# ============================================================================
# OPPORTUNITY ATTACK ELIGIBILITY
# ============================================================================


def should_grant_skill_opportunity_attack(
    weapon_skill_level: int, attack_outcome: str, weapon_skill_id: str = "weaponskill_longswords"
) -> bool:
    """Check if weaponskill grants opportunity attack for this outcome.

    Level 3: Opportunity on MISS or PARRIED (weapon-specific)
    Level 6: Same, but 3x per turn instead of 1x (weapon-specific)

    Args:
        weapon_skill_level: Skill level
        attack_outcome: AttackOutcome name (e.g., "miss", "parried")
        weapon_skill_id: Weapon skill identifier

    Returns:
        True if skill grants an opportunity attack
    """
    mods = get_weaponskill_modifiers(weapon_skill_level, weapon_skill_id)

    if not mods.has_opportunity_on_miss_parry:
        return False

    # Only on MISS or PARRIED
    return attack_outcome in ("miss", "parried")


def get_opportunity_attack_limit(
    weapon_skill_level: int, weapon_skill_id: str = "weaponskill_longswords"
) -> int:
    """Get number of skill-based opportunity attacks allowed.

    Args:
        weapon_skill_level: Skill level
        weapon_skill_id: Weapon skill identifier

    Returns:
        Number of opportunity attacks (0, 1, or 3)
    """
    mods = get_weaponskill_modifiers(weapon_skill_level, weapon_skill_id)
    return mods.opportunity_attacks_per_turn
