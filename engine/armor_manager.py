"""
Armor management system for MAGUS RPG.

This module manages armor equipment, protection zones, and armor modifiers.
It handles the complex zone-based protection system with armor parts and subzones.
"""

import json
import os

class ArmorManager:
    """
    Manages armor equipment, protection zones, and temporary modifiers.
    
    Handles armor parts, subzones, main zones, and protection calculations.
    Supports temporary modifiers for armor protection values.
    
    Attributes:
        PARTS (dict): Mapping of armor parts to protected subzones
        MAIN_ZONES (dict): Mapping of main body zones to their subzones
        armors (list): List of available armor items
        modifiers (list): List of temporary armor modifiers
    """
    # Páncél részegységek és az általuk védett alzónák
    PARTS = {
        "sisak": ["agykoponya", "homlok", "halánték", "arckoponya", "nyak"],
        "mellvért": [
            "jobb kulcscsont", "bal kulcscsont", "szegycsont", "bal mellkas", "jobb mellkas", "gyomorszáj", "has jobboldala", "has baloldala", "ágyék",
            "jobb lapocka", "bal lapocka", "jobb hát", "bal hát", "jobb derék", "bal derék", "ülep", "gerinc"
        ],
        "vállvédő": ["bal váll", "jobb váll"],
        "felkarvédő": ["bal felkar", "jobb felkar", "bal könyök", "jobb könyök"],
        "alkarvédő": ["bal alkar", "jobb alkar"],
        "kesztyű": ["bal csukló", "jobb csukló", "bal kézfej", "jobb kézfej"],
        "combvédő": ["bal comb", "jobb comb"],
        "lábszárvédő": ["bal lábszár", "jobb lábszár", "bal térd", "jobb térd"],
        "csizma": ["bal boka", "jobb boka", "bal lábfej", "jobb lábfej"]
        # ...bővíthető...
    }

    def get_parts_for_armor(self, armor):
        """
        Visszaadja, hogy egy páncél milyen részegységekből áll.
        """
        return armor.get("parts", [])

    def get_subzones_for_part(self, part_name):
        """
        Visszaadja, hogy egy adott részegység milyen alzónákat véd.
        """
        return self.PARTS.get(part_name, [])
    MAIN_ZONES = {
        "fej": ["agykoponya", "homlok", "halánték", "arckoponya", "nyak"],
        "torzó": [
            "jobb kulcscsont", "bal kulcscsont", "szegycsont", "bal mellkas", "jobb mellkas", "gyomorszáj", "has jobboldala", "has baloldala", "ágyék",
            "jobb lapocka", "bal lapocka", "jobb hát", "bal hát", "jobb derék", "bal derék", "ülep", "gerinc"
        ],
        "kar_jobb": ["jobb váll", "jobb felkar", "jobb könyök", "jobb alkar", "jobb csukló", "jobb kézfej"],
        "kar_bal": ["bal váll", "bal felkar", "bal könyök", "bal alkar", "bal csukló", "bal kézfej"],
        "láb_jobb": ["jobb comb", "jobb térd", "jobb lábszár", "jobb boka", "jobb lábfej"],
        "láb_bal": ["bal comb", "bal térd", "bal lábszár", "bal boka", "bal lábfej"]
    }

    def __init__(self, json_path=None):
        """
        Initialize the ArmorManager.
        
        Args:
            json_path (str, optional): Path to armor JSON file. Defaults to ../data/equipment/armor.json
        """
        if json_path is None:
            json_path = os.path.join(os.path.dirname(__file__), "..", "data", "equipment", "armor.json")
        with open(json_path, encoding="utf-8") as f:
            self.armors = json.load(f)
        self.modifiers = []  # ideiglenes módosítók listája

    def get_zone_protection(self, armor, zone):
        """
        Calculate protection value for a specific zone on an armor piece.
        
        Args:
            armor (dict): Armor item data
            zone (str): Zone name to check
            
        Returns:
            int: Protection value for the zone including any active modifiers
        """
        # 1. protection_overrides előnyben
        if "protection_overrides" in armor and zone in armor["protection_overrides"]:
            base = armor["protection_overrides"][zone]
        else:
            # 2. parts dict alapján keresés
            base = 0
            parts = armor.get("parts", {})
            for part, sfe in parts.items():
                if sfe > 0:
                    subzones = self.PARTS.get(part, [])
                    if zone in subzones:
                        base = sfe
                        break
        # 3. ideiglenes módosítók alkalmazása
        for mod in self.modifiers:
            if mod.get("armor_name") == armor["name"] and (mod.get("zone") == zone or mod.get("zone") == "*"):
                base += mod.get("value", 0)
        return base

    def add_modifier(self, armor_name, zone, value, duration=None, source=None):
        """
        Ideiglenes módosító hozzáadása egy páncélhoz/zónához.
        armor_name: páncél neve
        zone: zóna neve vagy "*" (minden zónára)
        value: módosítás értéke (+/-)
        duration: körök száma vagy None
        source: opcionális forrás (pl. varázslat, sérülés)
        """
        self.modifiers.append({
            "armor_name": armor_name,
            "zone": zone,
            "value": value,
            "duration": duration,
            "source": source
        })

    def tick_modifiers(self):
        """
        Egy kör elteltével csökkenti a duration-t, lejárt módosítókat eltávolítja.
        """
        new_mods = []
        for mod in self.modifiers:
            if mod["duration"] is not None:
                mod["duration"] -= 1
                if mod["duration"] > 0:
                    new_mods.append(mod)
            else:
                new_mods.append(mod)
        self.modifiers = new_mods

    def clear_modifiers(self, armor_name=None):
        """
        Minden vagy adott páncélhoz tartozó módosítók törlése.
        """
        if armor_name:
            self.modifiers = [m for m in self.modifiers if m["armor_name"] != armor_name]
        else:
            self.modifiers = []

    def get_armor_by_name(self, name):
        """
        Find armor by name (case-insensitive).
        
        Args:
            name (str): Armor name to search for
            
        Returns:
            dict or None: Armor data if found, None otherwise
        """
        for armor in self.armors:
            if armor["name"].lower() == name.lower():
                return armor
        return None
