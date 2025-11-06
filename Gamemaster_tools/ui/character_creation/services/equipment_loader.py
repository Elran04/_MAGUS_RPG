"""
Equipment Loader Service
Handles loading equipment data from JSON files and database.
"""

import random
import sqlite3
from typing import Any

from config.paths import (
    ARMOR_JSON,
    CLASSES_DB,
    GENERAL_EQUIPMENT_JSON,
    WEAPONS_SHIELDS_JSON,
)
from utils.data.json_io import load_json_safe
from utils.log.logger import get_logger

logger = get_logger(__name__)


class EquipmentLoader:
    """Service for loading equipment data from various sources."""

    def __init__(self) -> None:
        self.equipment_data: dict[str, list[dict[str, Any]]] = {
            "armor": [],
            "weapons_and_shields": [],
            "general": [],
        }

    def load_all_equipment(self) -> dict[str, list[dict[str, Any]]]:
        """Load all equipment from JSON files."""
        self.equipment_data["armor"] = load_json_safe(str(ARMOR_JSON), default=[])
        self.equipment_data["weapons_and_shields"] = load_json_safe(
            str(WEAPONS_SHIELDS_JSON), default=[]
        )
        self.equipment_data["general"] = load_json_safe(str(GENERAL_EQUIPMENT_JSON), default=[])

        logger.info(f"Loaded {len(self.equipment_data['armor'])} armor items")
        logger.info(f"Loaded {len(self.equipment_data['weapons_and_shields'])} weapons/shields")
        logger.info(f"Loaded {len(self.equipment_data['general'])} general items")

        return self.equipment_data

    def load_starting_equipment(
        self, class_id: str, spec_id: str | None
    ) -> tuple[list[dict[str, Any]], int | None]:
        """
        Load starting equipment and currency from database.

        Args:
            class_id: Class ID to look up
            spec_id: Specialization ID (optional)

        Returns:
            Tuple of (starting_items, starting_currency_in_copper)
            starting_items: List of dicts with 'type' and 'id' keys
            starting_currency_in_copper: Random currency amount or None
        """
        logger.info(f"Loading starting equipment for class_id='{class_id}', spec_id='{spec_id}'")

        starting_items = []
        starting_currency = None

        try:
            with sqlite3.connect(str(CLASSES_DB)) as conn:
                query = """
                    SELECT item_type, item_id, min_currency, max_currency
                    FROM starting_equipment
                    WHERE class_id = ? AND (specialisation_id IS NULL OR specialisation_id = ?)
                """
                logger.info(
                    f"Executing query with params: class_id='{class_id}', spec_id='{spec_id}'"
                )
                rows = conn.execute(query, (class_id, spec_id)).fetchall()

                logger.info(f"Found {len(rows)} starting equipment rows")

                for item_type, item_id, min_currency, max_currency in rows:
                    logger.info(
                        f"Processing: type={item_type}, id={item_id}, min={min_currency}, max={max_currency}"
                    )

                    if item_type == "currency":
                        # Roll starting currency (values are in gold)
                        if min_currency and max_currency:
                            starting_currency = random.randint(min_currency, max_currency)
                            logger.info(f"Starting currency: {starting_currency} gold")
                    else:
                        # Add starting item
                        if item_id:
                            starting_items.append({"type": item_type, "id": item_id})

        except sqlite3.Error as e:
            logger.error(f"Database error loading starting equipment: {e}")

        return starting_items, starting_currency

    def find_item_by_id(self, item_type: str, item_id: str) -> dict[str, Any] | None:
        """
        Find an equipment item by type and ID.

        Args:
            item_type: Type of item ('armor', 'weaponandshield', 'general')
            item_id: Item ID to find

        Returns:
            Item data dict or None if not found
        """
        # Map database item_type to our category keys
        type_mapping = {
            "armor": "armor",
            "weaponandshield": "weapons_and_shields",
            "general": "general",
        }

        category = type_mapping.get(item_type)
        if not category:
            logger.warning(f"Unknown item type: {item_type}")
            return None

        items = self.equipment_data.get(category, [])
        for item in items:
            if item.get("id") == item_id:
                return item

        logger.warning(f"Item not found: type={item_type}, id={item_id}")
        return None
