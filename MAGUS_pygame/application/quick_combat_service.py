"""
Quick Combat Service - Rapid test combat with hardcoded units.

Provides a fast way to test combat mechanics with predefined characters:
- Goblin Warrior (Team A) - using goblin.png
- Human Warrior with Heavy Armor (Team B) - using warrior.png
- Forest Clearing scenario

This bypasses scenario selection and deployment screens for rapid testing.
"""

from domain.entities import Unit
from domain.value_objects import Facing, Position
from logger.logger import get_logger

logger = get_logger(__name__)

# Hardcoded quick combat configuration
QUICK_COMBAT_CONFIG = {
    "scenario_name": "Forest Clearing",
    "background_file": "grass_bg.jpg",
    "team_a": [
        {
            "character_file": "Goblin_warrior.json",
            "sprite_file": "goblin.png",
            "position": (-5, 0),  # Team A spawn zone
            "facing": 0,
        }
    ],
    "team_b": [
        {
            "character_file": "Warrior_heavy_armor.json",
            "sprite_file": "warrior.png",
            "position": (5, 0),  # Team B spawn zone
            "facing": 3,  # Facing left toward Team A
        }
    ],
}


def prepare_quick_combat_battle(context) -> tuple[list[Unit], list[Unit], dict]:
    """
    Prepare quick combat battle units and configuration.

    Returns:
        Tuple of (team_a_units, team_b_units, config_dict)

    Raises:
        RuntimeError on preparation failure
    """
    logger.info("=" * 60)
    logger.info("QUICK COMBAT MODE")
    logger.info("Scenario: Forest Clearing")
    logger.info("Team A: Goblin Warrior")
    logger.info("Team B: Human Warrior (Heavy Armor)")
    logger.info("=" * 60)

    # Create Team A units
    team_a_units = _create_team_units(context, QUICK_COMBAT_CONFIG["team_a"], "Team A")

    # Create Team B units
    team_b_units = _create_team_units(context, QUICK_COMBAT_CONFIG["team_b"], "Team B")

    # Combine all units
    all_units: list[Unit] = team_a_units + team_b_units

    if not all_units:
        raise RuntimeError("Failed to create units for quick combat")

    logger.info(
        f"Quick combat units created: {len(team_a_units)} Team A, {len(team_b_units)} Team B"
    )

    return team_a_units, team_b_units, QUICK_COMBAT_CONFIG


def _auto_equip_from_inventory(char_data: dict, equipment_repo) -> None:
    """
    Auto-equip items from character's inventory to appropriate slots.

    Modifies char_data in-place to add an 'equipment' mapping.

    Args:
        char_data: Character data dictionary
        equipment_repo: Equipment repository for item lookups
    """
    felszereles = char_data.get("Felszerelés", {})
    items = felszereles.get("items", []) if isinstance(felszereles, dict) else []

    if not items:
        logger.warning("No items to auto-equip")
        return

    # Create equipment slots mapping
    equipment_slots = {
        "main_hand": "",
        "off_hand": "",
        "weapon_quick_1": "",
        "weapon_quick_2": "",
        "armor": [],
    }

    # Categorize items
    weapons = []
    shields = []
    armor_items = []

    for item in items:
        if not isinstance(item, dict):
            continue

        category = item.get("category", "")
        item_id = item.get("id", "")

        if not item_id:
            continue

        if category == "weapons_and_shields":
            # Check if it's a shield
            weapon_data = equipment_repo.find_weapon_by_id(item_id)
            if weapon_data:
                # Simple heuristic: shields have "shield" in the ID or name
                is_shield = (
                    "shield" in item_id.lower() or "shield" in weapon_data.get("name", "").lower()
                )
                if is_shield:
                    shields.append(item_id)
                else:
                    weapons.append(item_id)
        elif category == "armor":
            armor_items.append(item_id)

    # Equip first weapon to main hand
    if weapons:
        equipment_slots["main_hand"] = weapons[0]
        logger.debug(f"Auto-equipped main_hand: {weapons[0]}")

    # Equip additional weapons to quickslots
    if len(weapons) > 1:
        equipment_slots["weapon_quick_1"] = weapons[1]
        logger.debug(f"Auto-equipped weapon_quick_1: {weapons[1]}")

    if len(weapons) > 2:
        equipment_slots["weapon_quick_2"] = weapons[2]
        logger.debug(f"Auto-equipped weapon_quick_2: {weapons[2]}")

    # Equip first shield to off hand
    if shields:
        equipment_slots["off_hand"] = shields[0]
        logger.debug(f"Auto-equipped off_hand (shield): {shields[0]}")

    # Equip all armor
    equipment_slots["armor"] = armor_items
    if armor_items:
        logger.debug(f"Auto-equipped {len(armor_items)} armor pieces: {armor_items}")

    # Add equipment mapping to character data
    char_data["equipment"] = equipment_slots

    # Count equipped weapons (including quickslots)
    weapon_count = sum(
        1 for slot in ["main_hand", "weapon_quick_1", "weapon_quick_2"] if equipment_slots[slot]
    )
    logger.info(
        f"Auto-equipped: {weapon_count} weapon(s) (main={equipment_slots['main_hand']}, "
        f"quick1={equipment_slots['weapon_quick_1']}, quick2={equipment_slots['weapon_quick_2']}), "
        f"shield={equipment_slots['off_hand']}, armor={len(armor_items)} pieces"
    )


def _create_team_units(context, team_config: list[dict], team_label: str) -> list[Unit]:
    """
    Create units for a team from configuration.

    Args:
        context: Game context
        team_config: List of unit configurations
        team_label: Team label for logging

    Returns:
        List of created units
    """
    unit_factory = context.unit_factory
    sprite_repo = context.sprite_repo
    equipment_repo = context.equipment_repo
    team_units: list[Unit] = []

    for unit_config in team_config:
        try:
            # Load character data
            char_file = unit_config["character_file"]
            char_data = context.character_repo.load(char_file)

            if not char_data:
                logger.error(f"Failed to load character: {char_file}")
                continue

            # Log equipment for debugging
            equipment = char_data.get("Felszerelés", {})
            items = equipment.get("items", []) if isinstance(equipment, dict) else []
            logger.info(f"Character {char_file} has {len(items)} equipment items")

            # Auto-equip items from inventory to slots
            _auto_equip_from_inventory(char_data, equipment_repo)

            # Create unit
            q, r = unit_config["position"]
            unit = unit_factory.create_unit(
                character_filename=char_file,
                position=Position(q, r),
                facing=Facing(unit_config["facing"]),
                char_data=char_data,
            )

            if not unit:
                logger.error(f"Failed to create unit from: {char_file}")
                continue

            # Log unit equipment status
            weapon_status = f"equipped with {unit.weapon.name}" if unit.weapon else "no weapon"
            armor_count = len(unit.armor_system.pieces) if unit.armor_system else 0
            logger.info(f"Unit {unit.name}: {weapon_status}, {armor_count} armor pieces")

            # Load sprite
            try:
                sprite_file = unit_config["sprite_file"]
                sprite = sprite_repo.load_character_sprite(sprite_file)
                if sprite:
                    unit.sprite = sprite
                    logger.debug(f"Loaded sprite: {sprite_file}")
                else:
                    logger.warning(f"No sprite loaded for: {sprite_file}")
            except Exception as e:
                logger.warning(f"Failed to load sprite {unit_config['sprite_file']}: {e}")

            team_units.append(unit)
            logger.info(f"{team_label} unit created: {unit.name} at ({q}, {r})")

        except Exception as e:
            logger.error(f"Error creating {team_label} unit: {e}", exc_info=True)

    return team_units
