"""
WeaponMaterialQualityManager
Fegyverek anyag- és minőségkezelése, minden kategória összeadódó módosítókkal.

Kategóriák:
    1. Készítés minősége
    2. Kézrekovácsolás (karakterhez kötött, True/False)
    3. Módosítások (típus + munka minősége)
    4. Alapanyag
"""

class WeaponMaterialQualityManager:
    # MODIFIABLE_STATS -> JSON kulcsok
    STAT_JSON_MAP = {
        "KÉ": "KE",
        "VÉ": "VE",
        "TÉ": "TE",
        "Sebzés": ("damage_min", "damage_max"),
        "Átütőerő": "armor_penetration",
        "Súly": "weight",
        "STP": "stp",
        "Ár": "price"
    }

    @staticmethod
    def format_stat(stat, value):
        """
        Stat érték formázása:
            - Súly: 1 tizedes, min. 0.1
            - STP: egész, min. 1
            - Ár: egész, min. 0
            - Egyéb: ahogy van
        """
        if stat == "Súly":
            try:
                v = round(float(value), 1)
                return max(0.1, v)
            except Exception:
                return value
        elif stat == "STP":
            try:
                v = int(round(float(value)))
                return max(1, v)
            except Exception:
                return value
        elif stat == "Ár":
            try:
                v = int(round(float(value)))
                return max(0, v)
            except Exception:
                return value
        else:
            return value
    # Név-jelzők (bővíthető)
    CRAFT_QUALITY_LABELS = {
        'default': '',
        'Gyenge': 'Gyenge',
        'Átlagos': '',
        'Kivételes': 'Mesteri',
        'Törpe kovács': 'Törp',
        'Gilron-pap': 'Áldott'
    }
    MODIFICATION_LABELS = {
        'default': '',
        ('Kikönnyítés', 'Átlagos munka'): 'Könnyített',
        ('Kikönnyítés', 'Kivételes munka'): 'Pehelykönnyű',
        ('Támadásra', 'Átlagos munka'): 'Offenzív',
        ('Támadásra', 'Kivételes munka'): 'Brutális',
        ('Védelemre', 'Átlagos munka'): 'Defenzív',
        ('Védelemre', 'Kivételes munka'): 'Óvó',
        ('Sebzésre', 'Átlagos munka'): 'Rongáló',
        ('Sebzésre', 'Kivételes munka'): 'Halálos',
        ('Páncélbontásra', 'Átlagos munka'): 'Átütő',
        ('Páncélbontásra', 'Kivételes munka'): 'Páncéltörő'
    }   
    MATERIAL_LABELS = {
        'default': '',
        'Bronz': 'Bronz',
        'Gyatra acél': 'Rozsdás',
        'Átlagos acél': '',
        'Kiváló acél': 'Finomacél',
        'Abbit (Tiszta)': 'Abbit',
        'Abbit-acél': 'Abbit-acél',
        'Mithrill': 'Mithrill',
        'Vöröslunír': 'Vöröslunír',
        'Kéklunír': 'Kéklunír',
        'Feketelunír': 'Feketelunír',
        'Holdlunír': 'Holdlunír'
    }
    HAND_FORGED_LABELS = {
        False: '',
        True: 'Kézrekovácsolt'
    }

    def generate_weapon_name(self, base_name, params):
        """
        Generál egy immerzív fegyvernevet a paraméterek alapján.
        Sorrend: minőségi jelző, módosító jelző(k), alapanyag, kézrekovácsolás, (testreszabás alanya)
        """
        # Minőségi jelző
        quality = params.get('craft_quality', 'default')
        quality_str = self.CRAFT_QUALITY_LABELS.get(quality, '')
        # Módosító jelző(k)
        mod_list = params.get('modifications', [])
        mod_strs = []
        for mod in mod_list:
            mod_str = self.MODIFICATION_LABELS.get(mod, '')
            if mod_str:
                mod_strs.append(mod_str)
        mod_str = ' '.join(mod_strs)
        # Alapanyag
        material = params.get('material', 'default')
        material_str = self.MATERIAL_LABELS.get(material, '')
        # Kézrekovácsolás
        handforged = params.get('handforged', False)
        handforged_str = self.HAND_FORGED_LABELS.get(handforged, '')
        # Testreszabás alanya
        handforged_by = params.get('handforged_by', None)
        # Összeállítás
        name_parts = [quality_str, mod_str, material_str, handforged_str, base_name]
        name = ' '.join([part for part in name_parts if part])
        if handforged_by:
            name += f' ({handforged_by})'
        return name.strip()
    # Módosítható statok kulcsai
    MODIFIABLE_STATS = [
        "KÉ",  # Kezdeményezés
        "VÉ",  # Védekezés
        "TÉ",  # Támadás
        "Sebzés",
        "Átütőerő",
        "Súly",
        "STP",  # Ellenálló képesség
        "Ár"
    ]
    def add_modifier(self, category, key, stat, value):
        """
        Általános metódus egy stat módosító felvételére egy kategóriához.
        category: 'craft_quality', 'handforged', 'modification', 'material'
        key: str vagy tuple
        stat: str
        value: int vagy float
        """
        if stat not in self.MODIFIABLE_STATS:
            raise ValueError(f"Ismeretlen stat: {stat}")
        if category == 'craft_quality':
            self.craft_quality_mods.setdefault(key, {})[stat] = value
        elif category == 'handforged':
            self.handforged_mods.setdefault(key, {})[stat] = value
        elif category == 'modification':
            self.modification_mods.setdefault(key, {})[stat] = value
        elif category == 'material':
            self.material_mods.setdefault(key, {})[stat] = value
        else:
            raise ValueError(f"Ismeretlen kategória: {category}")
    # Készítés minősége
    CRAFT_QUALITY = [
        "Gyenge",
        "Átlagos",
        "Kivételes",
        "Törpe kovács",
        "Gilron-pap"
    ]

    # Kézrekovácsolás (True/False, karakter azonosítóval)

    # Módosítások (típus + munka minősége)
    MOD_TYPES = [
        "Kikönnyítés",
        "Támadásra",
        "Védelemre",
        "Sebzésre",
        "Páncélbontásra"
    ]
    MOD_QUALITY = [
        "Átlagos munka",
        "Kivételes munka"
    ]

    # Alapanyagok
    MATERIALS = [
        "Bronz",
        "Gyatra acél",
        "Átlagos acél",
        "Kiváló acél",
        "Abbit (Tiszta)",
        "Abbit-acél",
        "Mithrill",
        "Vöröslunír",
        "Kéklunír",
        "Feketelunír",
        "Holdlunír"
    ]

    def __init__(self):
        # Default: nincs változás minden statra
        self.DEFAULT_MODIFIER = {stat: (1 if stat in ["Súly", "STP", "Ár"] else 0) for stat in self.MODIFIABLE_STATS}
        self.craft_quality_mods = {
            'default': self.DEFAULT_MODIFIER.copy(),
            'Gyenge': {
                "KÉ": -2,
                "TÉ": -2,
                "VÉ": -2,
                "Sebzés": -1,
                "Átütőerő": -1,
                "STP": 0.9,  # 90% (alap * 0.9)
                "Ár": 0.8
            },
            'Átlagos': self.DEFAULT_MODIFIER.copy(),
            'Kivételes': {
                "KÉ": 1,
                "TÉ": 1,
                "VÉ": 1,
                "Átütőerő": 1,
                "Súly": 0.95,  # 95% (alap * 0.95)
                "STP": 1.25,   # 125% (alap * 1.25)
                "Ár": 50.0     # 5000% (alap * 50)
            },
            'Törpe kovács': {
                "KÉ": 2,
                "TÉ": 4,
                "VÉ": 4,
                "Sebzés": 2,
                "Átütőerő": 4,
                "STP": 2.5,
                "Ár": 10000  # gyakorlatilag megfizethetetlen
            },
            'Gilron-pap': {
                "KÉ": 5,
                "TÉ": 10,
                "VÉ": 10,
                "Sebzés": 2,
                "Átütőerő": 2,
                "STP": 250,  # mágikus, extrém magas
                "Ár": 300
            }
        }
        self.customize_mods = {
            False: self.DEFAULT_MODIFIER.copy(),
            True: {
                "TÉ": 2,
                "VÉ": 2,
                "Sebzés": 1,
                "Ár": 3.0
            }
        }
        self.modification_mods = {
            'default': self.DEFAULT_MODIFIER.copy(),
            # Átlagos munka ár: 1.5, Kivételes munka ár: 5.0
            ('Kikönnyítés', 'Átlagos munka'): {
                "KÉ": 1,
                "VÉ": -2,
                "Sebzés": -1,
                "Átütőerő": -1,
                "Súly": 0.95,  # 95%
                "Ár": 1.5
            },
            ('Kikönnyítés', 'Kivételes munka'): {
                "KÉ": 2,
                "TÉ": 1,
                "VÉ": -2,
                "Sebzés": -1,
                "Átütőerő": -1,
                "Súly": 0.9,  # 90%
                "Ár": 5.0
            },
            ('Támadásra', 'Átlagos munka'): {
                "TÉ": 2,
                "VÉ": -4,
                "Sebzés": 1,
                "Ár": 1.5
            },
            ('Támadásra', 'Kivételes munka'): {
                "KÉ": 1,
                "TÉ": 2,
                "VÉ": -3,
                "Sebzés": 1,
                "Átütőerő": 1,
                "Ár": 5.0
            },
            ('Védelemre', 'Átlagos munka'): {
                "KÉ": -2,
                "TÉ": -2,
                "VÉ": 2,
                "Sebzés": -1,
                "Átütőerő": -1,
                "Ár": 1.5
            },
            ('Védelemre', 'Kivételes munka'): {
                "KÉ": -1,
                "TÉ": -1,
                "VÉ": 2,
                "Ár": 5.0
            },
            ('Sebzésre', 'Átlagos munka'): {
                "KÉ": -1,
                "TÉ": -1,
                "VÉ": -1,
                "Sebzés": 1,
                "Átütőerő": 1,
                "Ár": 1.5
            },
            ('Sebzésre', 'Kivételes munka'): {
                "KÉ": -1,
                "TÉ": -1,
                "Sebzés": 2,
                "Átütőerő": 1,
                "Ár": 5.0
            },
            ('Páncélbontásra', 'Átlagos munka'): {
                "TÉ": -2,
                "VÉ": -2,
                "Sebzés": -1,
                "Átütőerő": 2,
                "Ár": 1.5
            },
            ('Páncélbontásra', 'Kivételes munka'): {
                "TÉ": -1,
                "VÉ": -1,
                "Sebzés": -1,
                "Átütőerő": 3,
                "Ár": 5.0
            }
        }
        self.material_mods = {
            'default': self.DEFAULT_MODIFIER.copy(),
            'Bronz': {
                "KÉ": -1,
                "TÉ": -3,
                "VÉ": -3,
                "Sebzés": -1,
                "Átütőerő": -2,
                "Súly": 1.15,
                "STP": 0.65,
                "Ár": 0.6
            },
            'Gyatra acél': {
                "KÉ": -1,
                "TÉ": -1,
                "VÉ": -1,
                "Sebzés": -1,
                "Átütőerő": -2,
                "STP": 0.8
            },
            'Átlagos acél': self.DEFAULT_MODIFIER.copy(),
            'Kiváló acél': {
                "TÉ": 1,
                "VÉ": 1,
                "Átütőerő": 1,
                "STP": 1.2,
                "Ár": 2.0
            },
            'Abbit (Tiszta)': {
                "TÉ": -1,
                "VÉ": -1,
                "Átütőerő": -1,
                "STP": 1.2,
                "Ár": 2.5
            },
            'Abbit-acél': {
                "KÉ": 1,
                "TÉ": 2,
                "VÉ": 2,
                "Sebzés": 1,
                "Átütőerő": 1,
                "Súly": 0.55,
                "STP": 1.5,
                "Ár": 15.0
            },
            'Mithrill': {
                "KÉ": 2,
                "TÉ": 5,
                "VÉ": 5,
                "Sebzés": 2,
                "Átütőerő": 2,
                "Súly": 0.25,
                "STP": 2.5,
                "Ár": 100.0
            },
            'Vöröslunír': {
                "KÉ": 1,
                "TÉ": 4,
                "VÉ": 4,
                "Sebzés": 2,
                "Átütőerő": 1,
                "Súly": 0.8,
                "STP": 2.2,
                "Ár": 100.0
            },
            'Kéklunír': {
                "KÉ": 2,
                "TÉ": 4,
                "VÉ": 4,
                "Sebzés": 1,
                "Átütőerő": 1,
                "Súly": 0.7,
                "STP": 2.25,
                "Ár": 100.0
            },
            'Feketelunír': {
                "KÉ": 2,
                "TÉ": 5,
                "VÉ": 4,
                "Sebzés": 1,
                "Átütőerő": 1,
                "Súly": 0.6,
                "STP": 2.3,
                "Ár": 120.0
            },
            'Holdlunír': {
                "KÉ": 6,
                "TÉ": 8,
                "VÉ": 8,
                "Sebzés": 2,
                "Átütőerő": 2,
                "Súly": 0.5,
                "STP": 2.35,
                "Ár": 200.0
            }
        }

    def get_total_modifiers(self, params):
        """
        Összesített módosítók lekérése egy fegyverre.
        params példa:
            {
                'craft_quality': str,
                'handforged': bool,
                'handforged_by': str,
                'modifications': list of (type, quality),
                'material': str
            }
        Visszaadja az összeadódó módosítókat (pl. sebzés, támadás, védelem, stb.)
        """
        # Alap: additív statok 0, multiplikatív statok 1
        result = {stat: (1 if stat in ["Súly", "STP", "Ár"] else 0) for stat in self.MODIFIABLE_STATS}

        cq = params.get('craft_quality', 'default')
        cq_mods = self.craft_quality_mods.get(cq, self.craft_quality_mods['default'])
        handforged = params.get('handforged', False)
        customize_mods = self.customize_mods.get(handforged, self.customize_mods[False])
        mod_list = params.get('modifications', [])
        mod_mods = []
        if not mod_list:
            mod_mods.append(self.modification_mods['default'])
        else:
            for mod in mod_list:
                mod_mods.append(self.modification_mods.get(mod, self.modification_mods['default']))
        mat = params.get('material', 'default')
        mat_mods = self.material_mods.get(mat, self.material_mods['default'])

        # Statok összesítése
        for stat in self.MODIFIABLE_STATS:
            # Készítés minősége
            val = cq_mods.get(stat, 0 if stat not in ["Súly", "STP", "Ár"] else 1)
            if stat in ["Súly", "STP", "Ár"]:
                result[stat] *= val if val != 0 else 1
            else:
                result[stat] += val
            # Kézrekovácsolás
            val = customize_mods.get(stat, 0 if stat not in ["Súly", "STP", "Ár"] else 1)
            if stat in ["Súly", "STP", "Ár"]:
                result[stat] *= val if val != 0 else 1
            else:
                result[stat] += val
            # Módosítások
            for mod in mod_mods:
                val = mod.get(stat, 0 if stat not in ["Súly", "STP", "Ár"] else 1)
                if stat in ["Súly", "STP", "Ár"]:
                    result[stat] *= val if val != 0 else 1
                else:
                    result[stat] += val
            # Alapanyag
            val = mat_mods.get(stat, 0 if stat not in ["Súly", "STP", "Ár"] else 1)
            if stat in ["Súly", "STP", "Ár"]:
                result[stat] *= val if val != 0 else 1
            else:
                result[stat] += val

        # Kerekítés és formázás
        formatted = {stat: self.format_stat(stat, value) for stat, value in result.items()}
        return formatted
