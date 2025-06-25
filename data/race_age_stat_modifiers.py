DEFAULT_STAT_LIMITS = (1, 18)
ALL_STATS = [
    "Erő", "Állóképesség", "Gyorsaság", "Ügyesség", "Karizma",
    "Egészség", "Intelligencia", "Akaraterő", "Asztrál", "Érzékelés"
]

RACE_MODIFIERS = {
    "Amund": {
        "modifiers": {
            "Erő": +1,
            "Állóképesség": +1,
            "Karizma": +2,
            "Asztrál": -1
        },  
        "limits": {
            "Erő": (2,19),
            "Állóképesség": (2,19),
            "Karizma": (3,20),
            "Asztrál": (1,17)
        }    
    },
    "Dzsenn": {
        "modifiers": {
            "Intelligencia": +2
        }, 
        "limits": {
            "Intelligencia": (3,20)
        }      
    },
    "Ember": {
        "modifiers": {},  
        "limits": {}      
    },
    "Elf": {
        "modifiers": {
            "Erő": -2,
            "Állóképesség": -1,
            "Gyorsaság": +1,
            "Ügyesség": +1,
            "Karizma": +1

        },  
        "limits": {
            "Gyorsaság": (2,19),
            "Ügyesség": (2,19),
            "Karizma": (3,21),
            "Asztrál": (1,17)
        }    
    },
    "Félelf": {
        "modifiers": {
            "Erő": -1,
            "Gyorsaság": +1
        },  
        "limits": {
            "Gyorsaság": (2,19)
        }    
    },
    "Khál": {
        "modifiers": {
            "Erő": +3,
            "Állóképesség": +2,
            "Gyorsaság": +2,
            "Ügyesség": +1,
            "Egészség": +3,
            "Intelligencia": -1,
            "Asztrál": -5

        },  
        "limits": {
            "Erő": (4,21),
            "Álloképesség": (3,20),
            "Gyorsaság": (3,20),
            "Ügyesség": (2,19),
            "Intelligencia": (1,17),
            "Asztrál": (1,13)
        }    
    },
    "Törpe": {
        "modifiers": {
            "Állóképesség": +2,
            "Asztrál": -1
        },
        "limits": {
            "Asztrál": (3, 16),
            "Karizma": (3, 17)
        }
    },
    # többi faj...
}

def get_full_stat_limits(race: str) -> dict:
    race_data = RACE_MODIFIERS.get(race, {})
    custom_limits = race_data.get("limits", {})
    full_limits = {}
    
    for stat in ALL_STATS:
        if stat in custom_limits:
            full_limits[stat] = custom_limits[stat]
        else:
            full_limits[stat] = DEFAULT_STAT_LIMITS
    return full_limits

AGE_CATEGORY_EFFECTS = {
    1: {"Erő": -3, "Állóképesség": -3, "Ügyesség": -1, "Intelligencia":-1, "Akaraterő":-1, "Karizma": -1},
    2: {},
    3: {"Gyorsaság": -1, "Ügyesség": -1, "Intelligencia":+1, "Akaraterő":+1, "Karizma": +1},
    4: {"Erő": -1, "Állóképesség":-1, "Gyorsaság": -3, "Ügyesség": -1, "Egészség":-1, "Intelligencia":+1, "Akaraterő":+1, "Karizma": +1},
    5: {"Erő": -2, "Állóképesség":-2, "Gyorsaság": -5, "Ügyesség": -2, "Egészség":-2, "Intelligencia":+1, "Akaraterő":+1},
    6: {"Erő": -4, "Állóképesség":-4, "Gyorsaság": -7, "Ügyesség": -4, "Egészség":-4},
}

AGE_LIMITS_BY_RACE = {
    "Ember":       [17, 30, 43, 55, 75],
    "Elf":         [50, 1400, 1600, 1800, 1900],
    "Félelf":      [23,110,130,150,170],
    "Törpe":       [40, 350, 600, 680, 750],
    "Udvari ork":  [12, 27, 35, 45, 60],
    "Amund":       [18, 35, 55, 70, 90],
    "Dzsenn":      [19, 120, 150, 170, 200],
    "Khál":        [6, 12, 29, 39, 44],
    # fajok bővíthetők
}

def get_age_category(race: str, age: int) -> int:
    limits = AGE_LIMITS_BY_RACE.get(race)
    if not limits:
        return 2  # ha nincs faj megadva, alapértelmezett "felnőtt" kategória
    for i, limit in enumerate(limits, start=1):
        if age < limit:
            return i
    return 6

def get_age_modifiers(race: str, age: int) -> dict:
    category = get_age_category(race, age)
    return AGE_CATEGORY_EFFECTS.get(category, {})


def apply_race_modifiers(stats: dict, race: str) -> dict:
    mods = RACE_MODIFIERS.get(race, {})
    modified_stats = stats.copy()
    
    for stat, bonus in mods.get("modifiers", {}).items():
        modified_stats[stat] = modified_stats.get(stat, 0) + bonus

    for stat, (min_val, max_val) in mods.get("limits", {}).items():
        modified_stats[stat] = max(min(modified_stats[stat], max_val), min_val)

    return modified_stats

def apply_age_modifiers(stats: dict, race: str, age: int) -> dict:
    age_mods = get_age_modifiers(race, age)
    modified_stats = stats.copy()
    for stat, mod in age_mods.items():
        modified_stats[stat] = modified_stats.get(stat, 0) + mod
    return modified_stats