"""
Lucky and unlucky roll mechanics for MAGUS combat.

Lucky rolls: Roll twice and take the BETTER outcome
- Applies to attack rolls (d100) or damage rolls (weapon dice)
- Granted by high weapon skill levels (damage 5+, attack 6+) or special effects

Unlucky rolls: Roll twice and take the WORSE outcome
- Opposite of lucky rolls
- Applies to same roll types
- Can come from conditions, curses, or special circumstances (injuries, fatigue, etc.)

The mechanics are symmetric and apply to any roll type.
"""

from __future__ import annotations

from enum import Enum
from typing import Protocol


class LuckyRollType(Enum):
    """Type of roll that can be lucky."""

    ATTACK_ROLL = "attack_roll"  # d100 attack roll (higher is better)
    DAMAGE_ROLL = "damage_roll"  # Weapon damage roll (higher is better)
    DEFENSE_ROLL = "defense_roll"  # Future: defense/dodge checks


class UnluckyRollType(Enum):
    """Type of roll that can be unlucky."""

    ATTACK_ROLL = "attack_roll"  # d100 attack roll (lower is worse)
    DAMAGE_ROLL = "damage_roll"  # Weapon damage roll (lower is worse)
    DEFENSE_ROLL = "defense_roll"  # Future: defense/dodge checks


class LuckyRollContext(Protocol):
    """Protocol for objects that might have lucky/unlucky roll properties."""

    def has_lucky_attack_roll(self) -> bool:
        """Check if this entity grants lucky attack rolls."""
        ...

    def has_lucky_damage_roll(self) -> bool:
        """Check if this entity grants lucky damage rolls."""
        ...

    def has_unlucky_attack_roll(self) -> bool:
        """Check if this entity suffers unlucky attack rolls."""
        ...

    def has_unlucky_damage_roll(self) -> bool:
        """Check if this entity suffers unlucky damage rolls."""
        ...


# ============================================================================
# LUCKY ROLLS (Roll twice, take better)
# ============================================================================


def apply_lucky_roll(roll_1: int, roll_2: int) -> int:
    """
    Apply lucky roll mechanic: roll twice, take the better one.

    Args:
        roll_1: First roll value
        roll_2: Second roll value

    Returns:
        The better of the two rolls
    """
    return max(roll_1, roll_2)


def resolve_lucky_roll(roll_1: int, roll_2: int) -> tuple[int, int]:
    """
    Resolve a lucky roll by taking the better of two rolls.

    Args:
        roll_1: First roll value
        roll_2: Second roll value

    Returns:
        Tuple of (better_roll, worse_roll)
    """
    if roll_1 >= roll_2:
        return (roll_1, roll_2)
    else:
        return (roll_2, roll_1)


def should_use_lucky_roll(
    unit: Unit,
    roll_type: LuckyRollType,
    weapon: Weapon | None = None,
    weapon_skill_level: int = 0,
) -> bool:
    """
    Determine if a unit should use lucky rolls for this attack.

    Lucky rolls come from:
    - Weapon skill levels (level 5+ for damage, level 6+ for attack)
    - Equipment properties
    - Status effects/conditions/buffs

    Args:
        unit: Attacking unit
        roll_type: Type of roll to check
        weapon: Weapon being used (optional)
        weapon_skill_level: Skill level with weapon

    Returns:
        True if rolls should be lucky
    """
    # Lucky roll rules are general and apply to all weapon skills
    if roll_type == LuckyRollType.DAMAGE_ROLL and weapon_skill_level >= 5:
        return True
    if roll_type == LuckyRollType.ATTACK_ROLL and weapon_skill_level >= 6:
        return True

    # Could check unit conditions/buffs for lucky effects
    # (future expansion: bless, luck spells, etc.)

    return False


# ============================================================================
# UNLUCKY ROLLS (Roll twice, take worse)
# ============================================================================


def apply_unlucky_roll(roll_1: int, roll_2: int) -> int:
    """
    Apply unlucky roll mechanic: roll twice, take the worse one.

    Args:
        roll_1: First roll value
        roll_2: Second roll value

    Returns:
        The worse of the two rolls
    """
    return min(roll_1, roll_2)


def resolve_unlucky_roll(roll_1: int, roll_2: int) -> tuple[int, int]:
    """
    Resolve an unlucky roll by taking the worse of two rolls.

    Args:
        roll_1: First roll value
        roll_2: Second roll value

    Returns:
        Tuple of (worse_roll, better_roll)
    """
    if roll_1 <= roll_2:
        return (roll_1, roll_2)
    else:
        return (roll_2, roll_1)


def should_use_unlucky_roll(
    unit: Unit,
    roll_type: UnluckyRollType,
    weapon: Weapon | None = None,
    weapon_skill_level: int = 0,
) -> bool:
    """
    Determine if a unit should use unlucky rolls for this roll.

    Unlucky rolls come from:
    - Status conditions (injuries, fatigue, curses)
    - Negative effects/debuffs
    - Special circumstances (exhaustion, pain, bleeding, etc.)

    Args:
        unit: Unit performing the roll
        roll_type: Type of roll to check
        weapon: Weapon being used (optional)
        weapon_skill_level: Skill level with weapon

    Returns:
        True if rolls should be unlucky
    """
    # Check unit injury/fatigue conditions for unlucky effects
    # These would be checked from unit.conditions or unit.stamina state
    # (future expansion: serious injury, critical injury, exhaustion, curse effects, etc.)

    return False


# Import at end to avoid circular imports
if __name__ != "__main__":
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from domain.entities import Unit, Weapon
