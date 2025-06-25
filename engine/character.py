# engine/character.py
import random
from data.class_stat_weights import CLASS_STAT_WEIGHTS , UPGRADABLE_STATS
from data.race_age_stat_modifiers import apply_age_modifiers , apply_race_modifiers

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

def generate_character(name, gender, age, race, klass):
    stats = generate_stats(klass)
    stats = apply_race_modifiers(stats, race)
    stats = apply_age_modifiers(stats, race, age)
    upgradable = UPGRADABLE_STATS.get(klass, [])
    
    return {
        "Név": name,
        "Nem": gender,
        "Kor": age,
        "Faj": race,
        "Kaszt": klass,
        "Tulajdonságok": stats,
        "Fejleszthető": upgradable
    }

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