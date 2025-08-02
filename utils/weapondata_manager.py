import os
import json
from utils.json_manager import JsonManager

class WeaponDataManager(JsonManager):
    """
    UI-független adatkezelő fegyverekhez és pajzsokhoz.
    Betöltés, mentés, validáció, konverziók, kategória lekérdezés.
    """
    def __init__(self, json_path=None):
        if json_path is None:
            json_path = os.path.join(os.path.dirname(__file__), "..", "data", "equipment", "weapons_and_shields.json")
        super().__init__(json_path)

    def validate(self, item):
        required = [
            "id", "name", "type", "category", "weight", "price", "stp", "armor_penetration",
            "can_disarm", "can_break_weapon", "damage_min", "damage_max"
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
        skills_path = os.path.join(os.path.dirname(__file__), "..", "data", "skills", "skills.json")
        try:
            with open(skills_path, encoding="utf-8") as f:
                skills = json.load(f)
            categories = set()
            if type_value in ["közelharci", "távolsági"]:
                for skill in skills:
                    if skill.get("name") == "Fegyverhasználat" and skill.get("parameter"):
                        categories.add(skill["parameter"])
            elif type_value == "hajító":
                for skill in skills:
                    if skill.get("name") == "Fegyverdobás" and skill.get("parameter"):
                        categories.add(skill["parameter"])
            # pajzs esetén üres
            return sorted(categories)
        except Exception:
            return []

    # További UI-független adatkezelő metódusok ide jöhetnek
    # Pl. keresés, szűrés, konverziók, stb.
