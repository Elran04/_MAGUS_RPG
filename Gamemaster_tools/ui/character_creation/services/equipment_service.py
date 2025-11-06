"""
Equipment Service
Handles buy/sell logic and inventory management.
"""

from typing import Any

from engine.currency_manager import CurrencyManager
from utils.log.logger import get_logger

logger = get_logger(__name__)


class EquipmentService:
    """Service for managing character equipment and transactions."""

    def __init__(self) -> None:
        self.currency_manager = CurrencyManager()
        # Inventory keyed by internal item_id -> { name, category, price, data, quantity }
        self.inventory: dict[str, dict[str, Any]] = {}
        self.currency_base: int = 0  # Currency in copper/réz base units
        self._next_item_id = 1

    def set_currency(self, amount_in_gold: int) -> None:
        """Set character's currency from gold amount."""
        self.currency_base = self.currency_manager.to_base(amount_in_gold, "arany")
        logger.info(
            f"Currency set to {amount_in_gold} gold = {self.currency_manager.format(self.currency_base)}"
        )

    def add_starting_item(self, item_data: dict[str, Any], category: str) -> None:
        """
        Add a starting equipment item to inventory.

        Args:
            item_data: Item data dict with 'name', 'price', etc.
            category: Category key ('armor', 'weapons_and_shields', 'general')
        """
        if not item_data:
            return

        # If stackable and already have same item (by category+id), increase quantity
        stackable = bool(item_data.get("stackable", False))
        if stackable:
            for inv in self.inventory.values():
                if inv.get("category") == category and (
                    inv.get("data", {}).get("id") == item_data.get("id")
                ):
                    inv["quantity"] = int(inv.get("quantity", 1)) + 1
                    logger.info(
                        f"Increased stack for {item_data.get('name')} -> qty {inv['quantity']}"
                    )
                    return

        item_id = f"item_{self._next_item_id}"
        self._next_item_id += 1

        self.inventory[item_id] = {
            "name": item_data.get("name", "Unknown"),
            "category": category,
            "price": item_data.get("price", 0),
            "data": item_data,
            "quantity": 1,
        }

        logger.info(f"Added starting item: {item_data.get('name')} ({category})")

    def buy_item(self, item_data: dict[str, Any], category: str) -> bool:
        """
        Purchase an item if character has enough currency.

        Args:
            item_data: Item data dict
            category: Category key

        Returns:
            True if purchase successful, False otherwise
        """
        price = item_data.get("price", 0)

        if self.currency_base < price:
            logger.warning(f"Not enough currency to buy {item_data.get('name')}")
            return False

        # Deduct currency
        self.currency_base -= price

        # If stackable and already in inventory, increase quantity
        stackable = bool(item_data.get("stackable", False))
        if stackable:
            for inv in self.inventory.values():
                if inv.get("category") == category and (
                    inv.get("data", {}).get("id") == item_data.get("id")
                ):
                    inv["quantity"] = int(inv.get("quantity", 1)) + 1
                    logger.info(
                        f"Purchased stackable: {item_data.get('name')} (+1 -> {inv['quantity']})"
                    )
                    return True

        # Otherwise add as new entry
        item_id = f"item_{self._next_item_id}"
        self._next_item_id += 1

        self.inventory[item_id] = {
            "name": item_data.get("name", "Unknown"),
            "category": category,
            "price": price,
            "data": item_data,
            "quantity": 1,
        }

        logger.info(f"Purchased: {item_data.get('name')} for {self.currency_manager.format(price)}")
        return True

    def buy_item_bulk(self, item_data: dict[str, Any], category: str, quantity: int) -> bool:
        """Purchase multiple units at once with proper currency deduction and stacking.

        Args:
            item_data: Item dict with price and id
            category: Category key
            quantity: Number of units to purchase (>0)

        Returns:
            True if successful, False otherwise
        """
        try:
            qty = int(quantity)
        except Exception:
            qty = 0
        if qty <= 0:
            return False

        unit_price = int(item_data.get("price", 0) or 0)
        total = unit_price * qty
        if self.currency_base < total:
            logger.warning(
                f"Not enough currency to bulk buy {qty} x {item_data.get('name')} "
                f"needs {self.currency_manager.format(total)} has {self.currency_manager.format(self.currency_base)}"
            )
            return False

        # Deduct currency first
        self.currency_base -= total

        stackable = bool(item_data.get("stackable", False))
        if stackable:
            # Find existing stack to increase, else create new with given quantity
            for inv in self.inventory.values():
                if inv.get("category") == category and (
                    inv.get("data", {}).get("id") == item_data.get("id")
                ):
                    inv["quantity"] = int(inv.get("quantity", 1)) + qty
                    logger.info(
                        f"Purchased stackable bulk: {item_data.get('name')} (+{qty} -> {inv['quantity']})"
                    )
                    return True
            # No existing stack, add new entry with quantity
            item_id = f"item_{self._next_item_id}"
            self._next_item_id += 1
            self.inventory[item_id] = {
                "name": item_data.get("name", "Unknown"),
                "category": category,
                "price": unit_price,
                "data": item_data,
                "quantity": qty,
            }
            logger.info(
                f"Purchased new stack: {item_data.get('name')} x{qty} for {self.currency_manager.format(total)}"
            )
            return True
        else:
            # Non-stackable: add separate entries qty times
            for _ in range(qty):
                item_id = f"item_{self._next_item_id}"
                self._next_item_id += 1
                self.inventory[item_id] = {
                    "name": item_data.get("name", "Unknown"),
                    "category": category,
                    "price": unit_price,
                    "data": item_data,
                    "quantity": 1,
                }
            logger.info(
                f"Purchased non-stackable bulk: {item_data.get('name')} x{qty} for {self.currency_manager.format(total)}"
            )
            return True

    def sell_item(self, item_id: str) -> bool:
        """
        Sell an item from inventory.

        Args:
            item_id: ID of item in inventory

        Returns:
            True if sale successful, False otherwise
        """
        if item_id not in self.inventory:
            logger.warning(f"Item {item_id} not found in inventory")
            return False

        item = self.inventory[item_id]
        price = item["price"]

        # Add currency at full price during character creation
        sell_price = price
        self.currency_base += sell_price

        # If stackable and qty > 1, decrement, else remove
        qty = int(item.get("quantity", 1))
        if qty > 1:
            item["quantity"] = qty - 1
            logger.info(f"Decreased stack: {item['name']} -> qty {item['quantity']}")
        else:
            del self.inventory[item_id]

        logger.info(f"Sold: {item['name']} for {self.currency_manager.format(sell_price)}")
        return True

    def get_currency_display(self) -> str:
        """Get formatted currency string with colors."""
        return self.currency_manager.format(self.currency_base)

    def get_inventory_by_category(self) -> dict[str, list[tuple[str, dict[str, Any]]]]:
        """
        Get inventory organized by category.

        Returns:
            Dict mapping category to list of (item_id, item_data) tuples
        """
        categorized: dict[str, list[tuple[str, dict[str, Any]]]] = {
            "armor": [],
            "weapons_and_shields": [],
            "general": [],
        }

        for item_id, item in self.inventory.items():
            category = item.get("category", "general")
            if category in categorized:
                categorized[category].append((item_id, item))

        return categorized

    def get_export_data(self) -> dict[str, Any]:
        """
        Export inventory and currency for character save.

        Returns:
            Dict with 'currency' (base copper) and minimal 'items'
            items = [{ 'category': <str>, 'id': <str> }]
        """
        minimal_items: list[dict[str, Any]] = []
        for inv_item in self.inventory.values():
            item_data = inv_item.get("data", {}) or {}
            item_id = item_data.get("id")
            category = inv_item.get("category")
            if item_id and category:
                entry = {
                    "category": category,
                    "id": item_id,
                }
                qty = int(inv_item.get("quantity", 1))
                stackable = bool(item_data.get("stackable", False))
                # Persist qty only when stackable and qty > 1 (keep JSON minimal otherwise)
                if stackable and qty > 1:
                    entry["qty"] = qty
                minimal_items.append(entry)

        return {
            "currency": self.currency_base,
            "items": minimal_items,
        }
