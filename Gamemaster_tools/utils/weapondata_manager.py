import os
import sqlite3

from utils.json_manager import JsonManager
from utils.logger import get_logger

logger = get_logger(__name__)


class WeaponDataManager(JsonManager):
    # Központi meződefiníciók
    BASE_FIELDS = [
        "name",
        "id",
        "type",
        "category",
        "attack_time",
        "weight",
        "stp",
        "armor_penetration",
        "damage_min",
        "damage_max",
    ]
    PRICE_FIELDS = ["price_réz", "price_ezüst", "price_arany", "price_mithrill"]
    TYPE_FIELDS = ["KE", "TE", "VE", "size_category", "range", "CE", "MGT"]
    VARIABLE_FIELDS = [
        "variable_strength_req",
        "variable_dex_req",
        "variable_bonus_KE",
        "variable_bonus_TE",
        "variable_bonus_VE",
    ]
    CHECKBOX_FIELDS = ["can_disarm", "can_break_weapon"]

    # Típusfüggő mezők definíciója
    TYPE_FIELD_DEFS = {
        "közelharci": [
            ("KE:", "KE"),
            ("TE:", "TE"),
            ("VE:", "VE"),
            ("Méretkategória:", "size_category"),
        ],
        "hajító": [
            ("KE:", "KE"),
            ("TE:", "TE"),
            ("VE:", "VE"),
            ("Táv (m):", "range"),
        ],
        "távolsági": [
            ("KE:", "KE"),
            ("CE:", "CE"),
            ("Táv (m):", "range"),
        ],
        "pajzs": [
            ("KE:", "KE"),
            ("VE:", "VE"),
            ("MGT:", "MGT"),
        ],
    }

    DAMAGE_TYPES = ["szúró", "vágó", "zúzó"]
    DAMAGE_BONUS_ATTRS = ["erő", "ügyesség"]

    @staticmethod
    def get_weapon_types():
        return ["közelharci", "hajító", "távolsági", "pajzs"]

    """
    UI-független adatkezelő fegyverekhez és pajzsokhoz.
    Betöltés, mentés, validáció, konverziók, kategória lekérdezés.
    """

    def __init__(self, json_path=None):
        if json_path is None:
            json_path = os.path.join(
                os.path.dirname(__file__), "..", "data", "equipment", "weapons_and_shields.json"
            )
        super().__init__(json_path)

    def validate(self, item):
        required = [
            "id",
            "name",
            "type",
            "category",
            "weight",
            "price",
            "stp",
            "armor_penetration",
            "can_disarm",
            "can_break_weapon",
            "damage_min",
            "damage_max",
        ]
        for field in required:
            if field not in item:
                return False
        # Típusfüggő mezők
        if item["type"] == "közelharci":
            for f in ["KE", "TE", "VE", "size_category"]:
                if f not in item:
                    return False
        elif item["type"] == "hajító":
            for f in ["KE", "TE", "VE", "range"]:
                if f not in item:
                    return False
        elif item["type"] == "távolsági":
            for f in ["KE", "CE", "range"]:
                if f not in item:
                    return False
        elif item["type"] == "pajzs":
            for f in ["KE", "VE", "MGT"]:
                if f not in item:
                    return False
        return True

    def get_weapon_categories(self, type_value):
        """
        Lekérdezi a fegyverkategóriákat a skills_data.db adatbázisból, a típus alapján.
        """
        db_path = os.path.join(os.path.dirname(__file__), "..", "data", "skills", "skills_data.db")
        categories: set[str] = set()
        try:
            with sqlite3.connect(db_path) as conn:
                c = conn.cursor()
                if type_value in ["közelharci", "távolsági"]:
                    c.execute(
                        "SELECT parameter FROM skills WHERE name='Fegyverhasználat' AND parameter IS NOT NULL AND parameter != ''"
                    )
                    categories.update(row[0] for row in c.fetchall())
                elif type_value == "hajító":
                    c.execute(
                        "SELECT parameter FROM skills WHERE name='Fegyverdobás' AND parameter IS NOT NULL AND parameter != ''"
                    )
                    categories.update(row[0] for row in c.fetchall())
                # pajzs esetén üres
            return sorted(categories)
        except sqlite3.Error as e:
            logger.error(f"Failed to load weapon categories for type '{type_value}': {e}")
            return []

    # További UI-független adatkezelő metódusok ide jöhetnek
    # Pl. keresés, szűrés, konverziók, stb.
    def build_item_from_fields(self, fields):
        """
        Készít egy item dict-et a meződefiníciók, típusfüggő logika és konverziók alapján.
        fields: dict (mezőnév: érték)
        """
        # Ár összerakása
        try:
            from engine.currency_manager import CurrencyManager

            price_total = 0
            for curr in CurrencyManager.ORDER:
                val = int(fields.get(f"price_{curr}", 0) or 0)
                price_total += CurrencyManager().to_base(val, curr)
        except Exception:
            price_total = int(fields.get("price_réz", 0) or 0)

        item = {
            "name": fields.get("name", ""),
            "id": fields.get("id", ""),
            "type": fields.get("type", ""),
            "category": fields.get("category", ""),
            "attack_time": int(fields.get("attack_time", 0) or 0),
            "damage_min": int(fields.get("damage_min", 0) or 0),
            "damage_max": int(fields.get("damage_max", 0) or 0),
            "weight": float(fields.get("weight", 0) or 0),
            "price": price_total,
            "stp": int(fields.get("stp", 0) or 0),
            "armor_penetration": int(fields.get("armor_penetration", 0) or 0),
            "can_disarm": bool(int(fields.get("can_disarm", 0))),
            "can_break_weapon": bool(int(fields.get("can_break_weapon", 0))),
            "damage_types": fields.get("damage_types", []),
            "damage_bonus_attributes": fields.get("damage_bonus_attributes", []),
        }
        t = item["type"]
        if t == "közelharci":
            item["KE"] = int(fields.get("KE", 0) or 0)
            item["TE"] = int(fields.get("TE", 0) or 0)
            item["VE"] = int(fields.get("VE", 0) or 0)
            item["size_category"] = int(fields.get("size_category", 0) or 0)
            # Wield mode mentése
            item["wield_mode"] = fields.get("wield_mode", "Egykezes")
            if item["wield_mode"] == "Változó":
                item["variable_strength_req"] = int(fields.get("variable_strength_req", 0) or 0)
                item["variable_dex_req"] = int(fields.get("variable_dex_req", 0) or 0)
                item["variable_dual_wield"] = bool(int(fields.get("variable_dual_wield", 0)))
                item["variable_bonus_KE"] = int(fields.get("variable_bonus_KE", 0) or 0)
                item["variable_bonus_TE"] = int(fields.get("variable_bonus_TE", 0) or 0)
                item["variable_bonus_VE"] = int(fields.get("variable_bonus_VE", 0) or 0)
        if t == "hajító":
            item["KE"] = int(fields.get("KE", 0) or 0)
            item["TE"] = int(fields.get("TE", 0) or 0)
            item["VE"] = int(fields.get("VE", 0) or 0)
            item["range"] = int(fields.get("range", 0) or 0)
        elif t == "távolsági":
            item["KE"] = int(fields.get("KE", 0) or 0)
            item["CE"] = int(fields.get("CE", 0) or 0)
            item["range"] = int(fields.get("range", 0) or 0)
        elif t == "pajzs":
            item["KE"] = int(fields.get("KE", 0) or 0)
            item["VE"] = int(fields.get("VE", 0) or 0)
            item["MGT"] = int(fields.get("MGT", 0) or 0)
        return item
