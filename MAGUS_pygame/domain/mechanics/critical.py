"""
Critical hit detection for MAGUS combat.

Critical hits:
- Based on attack roll value and weapon skill level
- Automatic hit (ignores defender VÉ)
- Ignores armor absorption (SFÉ)
- Deals extra damage based on weapon skill level
- Can combine with overpower strikes
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CriticalContext:
    """
    Context for critical hit detection.

    Attributes:
        attack_roll: Raw d100 roll value for attack
        weapon_skill_level: Attacker's skill level with weapon
        critical_threshold: Roll threshold for critical (from skill)
        damage_multiplier: Extra damage on critical (from skill)
    """

    attack_roll: int
    weapon_skill_level: int = 0
    critical_threshold: int | None = None  # If None, derive from skill
    damage_multiplier: float = 1.5  # Default 1.5x damage

    def __post_init__(self):
        # Validate roll
        if not 1 <= self.attack_roll <= 100:
            object.__setattr__(self, "attack_roll", max(1, min(100, self.attack_roll)))


def get_critical_threshold_for_skill(skill_level: int) -> int:
    """
    Get critical hit threshold based on weapon skill level.

    Higher skill = lower threshold = more frequent criticals.

    Per weaponskill spec:
    - Level 0: 0-10 critical failure, NO crits (threshold 101 = impossible)
    - Level 1: 1-5 critical failure, 6+ proceed; NO crits (threshold 101)
    - Level 2: Crits only on 100 (nat 100), critical failure on 1
    - Level 3: No critical failures; crits only on 100
    - Level 4: Crits at 96+ (5%)
    - Level 5: Crits at 91+ (10%)
    - Level 6+: Crits at 91+ (10%), special unique effect

    Args:
        skill_level: Weapon skill level (0-6+)

    Returns:
        Roll threshold (if roll >= threshold, it's critical)
    """
    if skill_level <= 1:
        return 101  # No crits possible (level 0-1)
    elif skill_level == 2 or skill_level == 3:
        return 100  # Only nat 100 (1%)
    elif skill_level == 4:
        return 96  # 96-100 is critical (5%)
    else:  # 5+
        return 91  # 91-100 is critical (10%)


def get_critical_damage_multiplier(skill_level: int) -> float:
    """
    Get damage multiplier for critical hit based on skill level.

    Args:
        skill_level: Weapon skill level

    Returns:
        Damage multiplier (e.g., 1.5 = 150% damage)
    """
    # TODO: This needs actual skill progression data
    # Placeholder logic:
    # Skill 0-1: 1.5x
    # Skill 2-3: 1.75x
    # Skill 4-5: 2.0x
    # Skill 6+: 2.5x

    if skill_level <= 1:
        return 1.5
    elif skill_level <= 3:
        return 1.75
    elif skill_level <= 5:
        return 2.0
    else:
        return 2.5


def is_critical_hit(
    attack_roll: int, weapon_skill_level: int, threshold_override: int | None = None
) -> bool:
    """
    Check if attack roll results in a critical hit.

    Args:
        attack_roll: Raw d100 attack roll
        weapon_skill_level: Attacker's weapon skill level
        threshold_override: Optional explicit threshold

    Returns:
        True if critical hit
    """
    if threshold_override is not None:
        threshold = threshold_override
    else:
        threshold = get_critical_threshold_for_skill(weapon_skill_level)

    return attack_roll >= threshold


def is_critical_failure(attack_roll: int, weapon_skill_level: int) -> bool:
    """
    Check if attack roll results in a critical failure (fumble).

    Per weaponskill spec:
    - Level 0: Rolls 1-10 are critical failures
    - Level 1: Rolls 1-5 are critical failures
    - Level 2: Roll 1 is critical failure
    - Level 3+: No critical failures

    Args:
        attack_roll: Raw d100 attack roll
        weapon_skill_level: Attacker's weapon skill level

    Returns:
        True if critical failure (attack is blocked/nullified)
    """
    if weapon_skill_level == 0:
        return 1 <= attack_roll <= 10
    elif weapon_skill_level == 1:
        return 1 <= attack_roll <= 5
    elif weapon_skill_level == 2:
        return attack_roll == 1
    return False  # Level 3+ no critical failures


def apply_critical_effects(ctx: CriticalContext) -> dict:
    """
    Calculate critical hit effects.

    Returns dict with:
    - is_critical: bool
    - auto_hit: bool (critical is automatic hit)
    - ignore_armor: bool (critical ignores SFÉ)
    - damage_multiplier: float

    Args:
        ctx: Critical context with roll and skill info

    Returns:
        Dict of critical effects
    """
    threshold = ctx.critical_threshold
    if threshold is None:
        threshold = get_critical_threshold_for_skill(ctx.weapon_skill_level)

    is_crit = ctx.attack_roll >= threshold

    if is_crit:
        multiplier = ctx.damage_multiplier
        if multiplier == 1.5:  # Use skill-based if default
            multiplier = get_critical_damage_multiplier(ctx.weapon_skill_level)

        return {
            "is_critical": True,
            "auto_hit": True,  # Critical always hits
            "ignore_armor": True,  # Critical ignores SFÉ
            "damage_multiplier": multiplier,
        }
    else:
        return {
            "is_critical": False,
            "auto_hit": False,
            "ignore_armor": False,
            "damage_multiplier": 1.0,
        }
