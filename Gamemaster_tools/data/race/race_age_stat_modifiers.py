DEFAULT_STAT_LIMITS = (3, 18)
DEFAULT_HARD_LIMITS = (1, 20)
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
            "Erő": (4, 19),
            "Állóképesség": (4, 19),
            "Karizma": (5, 20),
            "Asztrál": (2, 17)
        },
        "hard_limits": {
            "Erő": (1, 20),
            "Állóképesség": (1, 20),
            "Karizma": (1, 22),
            "Asztrál": (1, 17)
        }
    },
    "Dzsenn": {
        "modifiers": {
            "Intelligencia": +2
        },
        "limits": {
            "Intelligencia": (3, 20)
        },
        "hard_limits": {
            "Intelligencia": (1, 22)
        }
    },
    "Ember": {
        "modifiers": {},
        "limits": {},
        "hard_limits": {}
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
            "Erő": (3, 18),
            "Állóképesség": (3, 18),
            "Gyorsaság": (4, 19),
            "Ügyesség": (4, 19),
            "Karizma": (5, 21)
        },
        "hard_limits": {
            "Erő": (1, 18),
            "Állóképesség": (1, 18),
            "Gyorsaság": (1, 21),
            "Ügyesség": (1, 21),
            "Karizma": (1, 21)
        }
    },
    "Félelf": {
        "modifiers": {
            "Erő": -1,
            "Gyorsaság": +1
        },
        "limits": {
            "Gyorsaság": (4, 19)
        },
        "hard_limits": {
            "Gyorsaság": (1, 21)
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
            "Erő": (6, 21),
            "Állóképesség": (5, 20),
            "Gyorsaság": (5, 20),
            "Ügyesség": (4, 19),
            "Egészség": (6, 21),
            "Intelligencia": (2, 17),
            "Asztrál": (1, 13)
        },
        "hard_limits": {
            "Erő": (1, 22),
            "Állóképesség": (1, 22),
            "Gyorsaság": (1, 22),
            "Ügyesség": (1, 21),
            "Egészség": (1, 23),
            "Intelligencia": (1, 17),
            "Asztrál": (1, 13)
        }
    },
    "Törpe": {
        "modifiers": {
            "Erő": +1,
            "Állóképesség": +1,
            "Egészség": +1,
            "Karizma": -2,
            "Intelligencia": -1,
            "Asztrál": -1
        },
        "limits": {
            "Erő": (4, 19),
            "Állóképesség": (4, 19),
            "Egészség": (4, 21),
            "Karizma": (1, 15),
            "Intelligencia": (2, 18),
            "Asztrál": (1, 16)
        },
        "hard_limits": {
            "Erő": (1, 21),
            "Állóképesség": (1, 21),
            "Egészség": (1, 21),
            "Karizma": (1, 15),
            "Intelligencia": (1, 18),
            "Asztrál": (1, 16)
        }
    },
    "Udvari ork": {
        "modifiers": {
            "Erő": +2,
            "Állóképesség": +1,
            "Egészség": +2,
            "Karizma": -3,
            "Intelligencia": -1,
            "Asztrál": -3
        },
        "limits": {
            "Erő": (5, 20),
            "Állóképesség": (4, 19),
            "Egészség": (6, 22),
            "Karizma": (1, 13),
            "Intelligencia": (1, 16),
            "Asztrál": (1, 15)
        },
        "hard_limits": {
            "Erő": (1, 22),
            "Állóképesség": (1, 21),
            "Egészség": (1, 22),
            "Karizma": (1, 13),
            "Intelligencia": (1, 16),
            "Asztrál": (1, 15)
        },
    },
    "Goblin": {
        "modifiers": {
            "Erő": -2,
            "Gyorsaság": +2,
            "Karizma": -3,
            "Érzékelés": +2
        },
        "limits": {
            "Erő": (1, 16),
            "Gyorsaság": (5, 20),
            "Ügyesség": (3, 19),
            "Egészség": (3, 17),
            "Karizma": (1, 13),
            "Intelligencia": (3, 17),
            "Akaraterő": (3, 17),
            "Asztrál": (3, 16),
            "Érzékelés": (5, 19)
        },
        "hard_limits": {
            "Gyorsaság": (1, 22),
            "Ügyesség": (1, 21),
            "Érzékelés": (1, 19)
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
    4: {"Erő": -1, "Állóképesség":-1, "Gyorsaság": -1, "Ügyesség": -1, "Egészség":-1, "Intelligencia":+1, "Akaraterő":+1, "Karizma": +1},
    5: {"Erő": -2, "Állóképesség":-2, "Gyorsaság": -2, "Ügyesség": -2, "Egészség":-2, "Intelligencia":+1, "Akaraterő":+1},
    6: {"Erő": -4, "Állóképesség":-4, "Gyorsaság": -4, "Ügyesség": -4, "Egészség":-4},
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
    "Wier":        [15, 40, 70, 90, 110],
    "Goblin":      [10, 20, 28, 35, 40],
    # fajok bővíthetők
}
AGE_LIMITS = {
    "Ember": (13, 100),
    "Elf": (30, 3000),
    "Félelf": (16, 200),
    "Törpe": (25, 800),
    "Udvari ork": (9, 80),
    "Amund": (30, 120),
    "Dzsenn": (15, 250),
    "Khál": (1, 50),
    "Wier": (10, 130),
    "Goblin": (8, 45),
}

def get_age_category(race: str, age) -> int:
    try:
        age = int(age)
    except ValueError:
        raise ValueError("Az életkor csak szám lehet.")
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

    # Statok limitálása a fajhoz tartozó határokhoz
    return enforce_stat_limits(modified_stats, race)


# Statok limitálása a fajhoz tartozó határokhoz
def enforce_stat_limits(stats: dict, race: str) -> dict:
    limits = get_full_stat_limits(race)
    limited_stats = stats.copy()
    for stat, (min_val, max_val) in limits.items():
        if stat in limited_stats:
            limited_stats[stat] = max(min(limited_stats[stat], max_val), min_val)
    return limited_stats