# engine/character.py
import random
from data.Class.class_stat_weights import CLASS_STAT_WEIGHTS , UPGRADABLE_STATS
from data.Race.race_age_stat_modifiers import apply_age_modifiers , apply_race_modifiers
from data.Class.class_additional_stats import CLASS_COMBAT_STATS_AND_SKILL_POINTS


def generate_stats(klass: str) -> dict:
    default_range = (8, 18)
    class_data = CLASS_STAT_WEIGHTS.get(klass, {})
    weights = class_data.get("statok", {})
    dupla_dobas = set(class_data.get("dupla_dobas", []))

    stats = {}
    for stat in ["Erő", "Gyorsaság", "Ügyesség", "Állóképesség", "Karizma",
                 "Egészség", "Intelligencia", "Akaraterő", "Asztrál", "Érzékelés"]:
        low, high = weights.get(stat, default_range)
        if stat in dupla_dobas:
            val1 = random.randint(low, high)
            val2 = random.randint(low, high)
            stats[stat] = max(val1, val2)
        else:
            stats[stat] = random.randint(low, high)
    return stats


def calculate_combat_stats(character):
    klass = character["Kaszt"]
    stats = character["Tulajdonságok"]
    data = CLASS_COMBAT_STATS_AND_SKILL_POINTS.get(klass, {})

    # Véletlenszerű FP bónusz első szintre
    fp_bonus = random.randint(*data.get("FP_per_level", (0, 0)))


    # További stat alapú bónuszok kiszámítása
    def bonus(val):
        return max(0, val - 10)

    fp = data.get("FP", 0) + fp_bonus + bonus(stats["Akaraterő"]) + bonus(stats["Állóképesség"])
    ep = data.get("ÉP", 0) + bonus(stats["Egészség"])
    ke = data.get("KÉ", 0) + bonus(stats["Gyorsaság"]) + bonus(stats["Ügyesség"])
    te = data.get("TÉ", 0) + bonus(stats["Erő"]) + bonus(stats["Gyorsaság"]) + bonus(stats["Ügyesség"])
    ve = data.get("VÉ", 0) + bonus(stats["Gyorsaság"]) + bonus(stats["Ügyesség"])
    ce = data.get("CÉ", 0) + bonus(stats["Ügyesség"])

    character["Harci értékek"] = {
        "FP": fp,
        "ÉP": ep,
        "KÉ": ke,
        "TÉ": te,
        "VÉ": ve,
        "CÉ": ce,
        "HM/szint": data.get("HM_per_level", {"total": 0, "mandatory": {}}),
    }

    character["Képzettségpontok"] = {
        "Alap": data.get("KP", 0),
        "Szintenként": data.get("KP_per_level", 0)
    }

    return character


def generate_character(name, gender, age, race, klass):
    stats = generate_stats(klass)
    stats = apply_age_modifiers(stats, race, age)
    stats = apply_race_modifiers(stats, race)
    upgradable = UPGRADABLE_STATS.get(klass, [])

    char = {
        "Név": name,
        "Nem": gender,
        "Kor": age,
        "Faj": race,
        "Kaszt": klass,
        "Tulajdonságok": stats,
        "Fejleszthető": upgradable
    }

    char = calculate_combat_stats(char)
    return char


# Tiltott kasztok nem szerint
GENDER_RESTRICTIONS = {
    "Nő": {"Lovag", "Paplovag", "Barbár", "Boszorkánymester"},
    "Férfi": {"Boszorkány", "Amazon"}
}

# Tiltott kasztok faj szerint
RACE_RESTRICTIONS = {
    "Amund": {
        "Fejvadász", "Amazon", "Barbár", "Bárd", "Harcművész", "Kardművész",
        "Pap", "Szerzetes", "Sámán", "Boszorkánymester", "Tűzvarázsló", "Varázsló", "Pszi mester"
    },
    "Dzsenn": {
        "Fejvadász", "Amazon", "Barbár", "Pap", "Paplovag", "Szerzetes", "Sámán",
        "Harcművész", "Kardművész", "Boszorkány", "Boszorkánymester", "Tűzvarázsló"
    },
    "Elf": {
        "Lovag", "Amazon", "Barbár", "Bajvívó", "Tolvaj", "Pap", "Paplovag", "Szerzetes", "Sámán",
        "Harcművész", "Kardművész", "Boszorkány", "Boszorkánymester", "Tűzvarázsló"
    },
    "Félelf": {
        "Amazon", "Barbár","Pap", "Paplovag", "Szerzetes",
        "Tűzvarázsló"
    },
    "Khál": {
        "Amazon", "Barbár", "Bajvívó", "Tolvaj", "Pap", "Paplovag", "Szerzetes", "Sámán",
        "Harcművész", "Kardművész", "Boszorkány", "Boszorkánymester", "Tűzvarázsló", "Varázsló"
    },
    "Törpe": {
        "Fejvadász", "Lovag", "Amazon", "Barbár", "Bajvívó", "Bárd", "Paplovag", "Szerzetes", "Sámán",
        "Harcművész", "Kardművész", "Boszorkány", "Boszorkánymester", "Tűzvarázsló"
    },
    "Udvari ork": {
        "Lovag", "Amazon", "Barbár", "Bárd", "Pap", "Paplovag", "Szerzetes", "Sámán",
        "Harcművész", "Kardművész", "Boszorkány", "Tűzvarázsló", "Varázsló"
    },
    "Wier": {
        "Gladiátor", "Amazon", "Barbár", "Bárd", "Pap", "Sámán",
        "Harcművész", "Kardművész", "Tűzvarázsló"
    },
}

def is_valid_character(gender, race, klass):
    if klass in GENDER_RESTRICTIONS.get(gender, set()):
        return False
    if klass in RACE_RESTRICTIONS.get(race, set()):
        return False
    return True
