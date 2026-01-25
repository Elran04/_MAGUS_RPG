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
    "map_name": "forest_clearing",
    "blocked_hexes": frozenset(),  # populated from scenario file if available
    "spawn_zones": {},  # populated from scenario file if available
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


def _scenario_metadata(scenario_repo, map_name: str) -> dict:
    """Load scenario metadata via repository; fallback to defaults on failure."""
    data = None
    if scenario_repo:
        data = scenario_repo.load_scenario(map_name)

    if not data:
        logger.warning("Scenario '%s' not found or invalid; using defaults", map_name)
        return {
            "scenario_name": QUICK_COMBAT_CONFIG["scenario_name"],
            "background_file": QUICK_COMBAT_CONFIG["background_file"],
            "blocked_hexes": QUICK_COMBAT_CONFIG.get("blocked_hexes", frozenset()),
            "spawn_zones": QUICK_COMBAT_CONFIG.get("spawn_zones", {}),
        }

    obstacles = data.get("obstacles", [])
    blocked = frozenset(
        (item.get("q"), item.get("r"))
        for item in obstacles
        if isinstance(item, dict) and item.get("type") == "blocked"
    )

    spawn_zones = data.get("spawn_zones", {})
    spawn_zones_converted: dict[str, frozenset[tuple[int, int]]] = {}
    for team, coords in spawn_zones.items():
        if isinstance(coords, list):
            spawn_zones_converted[team] = frozenset(
                (c.get("q"), c.get("r")) for c in coords if isinstance(c, dict)
            )

    return {
        "scenario_name": data.get("name", QUICK_COMBAT_CONFIG["scenario_name"]),
        "background_file": data.get("background", QUICK_COMBAT_CONFIG["background_file"]),
        "blocked_hexes": blocked,
        "spawn_zones": spawn_zones_converted,
    }


def prepare_quick_combat_battle(context) -> tuple[list[Unit], list[Unit], dict]:
    """
    Prepare quick combat battle units and configuration.

    Returns:
        Tuple of (team_a_units, team_b_units, config_dict with scenario metadata)

    Raises:
        RuntimeError on preparation failure
    """
    logger.info("=" * 60)
    logger.info("QUICK COMBAT MODE")
    logger.info("Scenario: Forest Clearing")
    logger.info("Team A: Goblin Warrior")
    logger.info("Team B: Human Warrior (Heavy Armor)")
    logger.info("=" * 60)

    # Load scenario metadata (blocked/spawn zones, background) via repo
    scenario_meta = _scenario_metadata(
        getattr(context, "scenario_repo", None), QUICK_COMBAT_CONFIG["map_name"]
    )

    blocked = scenario_meta.get("blocked_hexes", frozenset())
    spawn_zones = scenario_meta.get("spawn_zones", {})

    logger.info(
        "Quick combat scenario '%s': blocked=%d, spawn_zones=%s",
        QUICK_COMBAT_CONFIG["map_name"],
        len(blocked),
        {k: len(v) for k, v in spawn_zones.items()},
    )

    def _apply_spawn_zones(team_cfg: list[dict], team_key: str) -> list[dict]:
        """Assign spawn positions from scenario spawn zones if available and not blocked."""
        zones = list(spawn_zones.get(team_key, [])) if spawn_zones else []
        out: list[dict] = []
        idx = 0
        for cfg in team_cfg:
            if idx < len(zones):
                candidate = zones[idx]
                idx += 1
                if candidate not in blocked:
                    cfg = {**cfg, "position": candidate}
                else:
                    logger.warning(
                        "Spawn hex %s for %s is blocked; keeping default position",
                        candidate,
                        team_key,
                    )
            out.append(cfg)
        return out

    team_a_cfg = _apply_spawn_zones(QUICK_COMBAT_CONFIG["team_a"], "team_a")
    team_b_cfg = _apply_spawn_zones(QUICK_COMBAT_CONFIG["team_b"], "team_b")

    # Create Team A units
    team_a_units = _create_team_units(context, team_a_cfg, "Team A")

    # Create Team B units
    team_b_units = _create_team_units(context, team_b_cfg, "Team B")

    # Combine all units
    all_units: list[Unit] = team_a_units + team_b_units

    if not all_units:
        raise RuntimeError("Failed to create units for quick combat")

    logger.info(
        f"Quick combat units created: {len(team_a_units)} Team A, {len(team_b_units)} Team B"
    )

    # Return config with scenario metadata (loaded from file when available)
    config = {
        "scenario_name": scenario_meta["scenario_name"],
        "background_file": scenario_meta["background_file"],
        "map_name": QUICK_COMBAT_CONFIG["map_name"],
        "blocked_hexes": blocked,
        "spawn_zones": spawn_zones,
    }

    return team_a_units, team_b_units, config


def _auto_equip_from_inventory(char_data: dict, equipment_repo) -> None:
    """Auto-equip items from character inventory to slots.

    Modifies ``char_data`` in-place by setting an ``equipment`` mapping.
    If no items are present, the function exits without error.
    """
    felszereles = char_data.get("Felszerelés", {})
    items = felszereles.get("items", []) if isinstance(felszereles, dict) else []

    if not items:
        logger.debug("No items to auto-equip")
        return

    equipment_slots = {
        "main_hand": "",
        "off_hand": "",
        "weapon_quick_1": "",
        "weapon_quick_2": "",
        "armor": [],
    }

    weapons: list[str] = []
    shields: list[str] = []
    armor_items: list[str] = []

    for item in items:
        if not isinstance(item, dict):
            continue

        category = item.get("category", "")
        item_id = item.get("id", "")

        if not item_id:
            continue

        if category == "weapons_and_shields":
            weapon_data = equipment_repo.find_weapon_by_id(item_id)
            if weapon_data:
                name = weapon_data.get("name", "")
                is_shield = "shield" in item_id.lower() or "shield" in name.lower()
                if is_shield:
                    shields.append(item_id)
                else:
                    weapons.append(item_id)
        elif category == "armor":
            armor_items.append(item_id)

    if weapons:
        equipment_slots["main_hand"] = weapons[0]
        logger.debug("Auto-equipped main_hand: %s", weapons[0])

    if len(weapons) > 1:
        equipment_slots["weapon_quick_1"] = weapons[1]
        logger.debug("Auto-equipped weapon_quick_1: %s", weapons[1])

    if len(weapons) > 2:
        equipment_slots["weapon_quick_2"] = weapons[2]
        logger.debug("Auto-equipped weapon_quick_2: %s", weapons[2])

    if shields:
        equipment_slots["off_hand"] = shields[0]
        logger.debug("Auto-equipped off_hand (shield): %s", shields[0])

    equipment_slots["armor"] = armor_items
    if armor_items:
        logger.debug("Auto-equipped %d armor pieces: %s", len(armor_items), armor_items)

    char_data["equipment"] = equipment_slots

    weapon_count = sum(
        1 for slot in ["main_hand", "weapon_quick_1", "weapon_quick_2"] if equipment_slots[slot]
    )
    logger.info(
        "Auto-equipped: %d weapon(s) (main=%s, quick1=%s, quick2=%s), shield=%s, armor=%d pieces",
        weapon_count,
        equipment_slots["main_hand"],
        equipment_slots["weapon_quick_1"],
        equipment_slots["weapon_quick_2"],
        equipment_slots["off_hand"],
        len(armor_items),
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
