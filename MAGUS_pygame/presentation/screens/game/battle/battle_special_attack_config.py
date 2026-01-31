"""Special attack configuration registry.

Centralized configuration for all special attacks to enable data-driven mode entry
and eliminate duplicated validation/entry logic.
"""

from enum import Enum

from logger.logger import get_logger

logger = get_logger(__name__)


class SpecialAttackType(Enum):
    """Enumeration of available special attacks."""

    CHARGE = "charge"
    DAGGER_COMBO = "dagger_combo"
    SHIELD_BASH = "shield_bash"


# Configuration for each special attack
# Used to drive dynamic mode entry with common validation
SPECIAL_ATTACK_CONFIG = {
    "charge": {
        "name": "Charge",
        "min_skill": 0,
        "weapon_skill": None,  # Any weapon allowed
        "message": "Select target for charge (min 5 hexes away)",
        "validate_weapon": lambda weapon: weapon is not None,
        "weapon_error": None,
    },
    "dagger_combo": {
        "name": "Attack Combination",
        "min_skill": 3,
        "weapon_skill": "weaponskill_daggers",
        "message": "Select adjacent target for attack combination",
        "validate_weapon": lambda weapon: (
            weapon is not None and getattr(weapon, "skill_id", "") == "weaponskill_daggers"
        ),
        "weapon_error": "Attack combination requires a dagger",
    },
    "shield_bash": {
        "name": "Shield Bash",
        "min_skill": 0,
        "weapon_skill": None,  # Any weapon allowed
        "message": "Select adjacent target for shield bash",
        "validate_weapon": lambda weapon: weapon is not None,
        "weapon_error": None,
    },
}


def get_special_attack_config(attack_id: str) -> dict | None:
    """Get configuration for a special attack.

    Args:
        attack_id: Special attack identifier

    Returns:
        Configuration dict or None if not found
    """
    return SPECIAL_ATTACK_CONFIG.get(attack_id)


def validate_special_attack_entry(
    battle_screen, attack_id: str
) -> tuple[bool, str | None]:
    """Validate entry conditions for a special attack.

    Common validation for all special attacks:
    - Victory check
    - Unit existence
    - Attack capability
    - Weapon requirements
    - Skill requirements

    Args:
        battle_screen: Reference to BattleScreen
        attack_id: Special attack identifier

    Returns:
        (is_valid, error_message) tuple
    """
    # Victory check
    if battle_screen.battle.is_victory():
        return False, "Battle is over"

    # Get current unit
    current = battle_screen.battle.current_unit
    if not current:
        return False, "No active unit"

    # Can attack check
    can_attack, error_msg = battle_screen.battle.can_attack(current)
    if not can_attack:
        return False, error_msg

    # Get attack config
    config = get_special_attack_config(attack_id)
    if not config:
        return False, f"Unknown attack: {attack_id}"

    # Weapon validation
    if not config["validate_weapon"](current.weapon):
        error = config.get("weapon_error")
        if error:
            return False, error
        return False, "Invalid weapon for this attack"

    # Skill validation
    if config["min_skill"] > 0:
        if config["weapon_skill"]:  # Has specific weapon skill requirement
            skill_level = 0
            if getattr(current, "skills", None):
                skill_level = current.skills.get_rank(config["weapon_skill"], 0)

            if skill_level < config["min_skill"]:
                skill_name = config["weapon_skill"].replace("weaponskill_", "").title()
                return (
                    False,
                    f"{config['name']} requires {skill_name} skill level {config['min_skill']}+",
                )

    return True, None
