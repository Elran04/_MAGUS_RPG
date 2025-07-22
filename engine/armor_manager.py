import json
import os

class ArmorManager:
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
        if json_path is None:
            json_path = os.path.join(os.path.dirname(__file__), "..", "data", "equipment", "armor.json")
        with open(json_path, encoding="utf-8") as f:
            self.armors = json.load(f)
        self.modifiers = []  # ideiglenes módosítók listája

    def get_zone_protection(self, armor, zone):
        # override ellenőrzés
        if "protection_overrides" in armor and zone in armor["protection_overrides"]:
            base = armor["protection_overrides"][zone]
        else:
            # főzóna keresés
            base = 0
            for main, subs in self.MAIN_ZONES.items():
                if zone in subs:
                    # új szerkezet: protection dict
                    if isinstance(armor.get("protection"), dict):
                        base = armor["protection"].get(main, 0)
                    else:
                        base = armor.get("protection", 0)
                    break
        # ideiglenes módosítók alkalmazása
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
        for armor in self.armors:
            if armor["name"].lower() == name.lower():
                return armor
        return None
