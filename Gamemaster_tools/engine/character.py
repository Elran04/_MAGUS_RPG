# engine/character.py
import random
from utils.class_db_manager import ClassDBManager
from data.race.race_age_stat_modifiers import apply_age_modifiers , apply_race_modifiers

class_db = ClassDBManager()


def safe_randint(low, high):
    """Robust randint that handles equal or inverted bounds gracefully.
    - Coerces bounds to int when possible.
    - If low == high, returns that value without calling randrange.
    - If low > high, swaps them.
    """
    try:
        low = int(low)
        high = int(high)
    except Exception:
        low, high = 0, 0
    if low == high:
        return low
    if low > high:
        low, high = high, low
    return random.randint(low, high)


def generate_stats(klass: str) -> dict:
    default_range = (8, 18)
    # Get class_id from name
    classes = class_db.list_classes()
    class_id = next((cid for cid, name in classes if name == klass), None)
    if class_id is None:
        raise ValueError(f"Class '{klass}' not found in DB")
    details = class_db.get_class_details(class_id)
    # details["stats"] rows may include a 4th column (double_chance)
    stat_ranges = {}
    dupla_dobas = set()
    for row in details["stats"]:
        if len(row) == 4:
            stat, minv, maxv, double_chance = row
        elif len(row) == 3:
            stat, minv, maxv = row
            double_chance = 0
        else:
            # Unexpected shape; skip this row
            continue
        stat_ranges[stat] = (minv, maxv)
        if double_chance:
            dupla_dobas.add(stat)

    stats = {}
    for stat in ["Erő", "Gyorsaság", "Ügyesség", "Állóképesség", "Karizma",
                 "Egészség", "Intelligencia", "Akaraterő", "Asztrál", "Érzékelés"]:
        low, high = stat_ranges.get(stat, default_range)
        if stat in dupla_dobas:
            val1 = safe_randint(low, high)
            val2 = safe_randint(low, high)
            stats[stat] = max(val1, val2)
        else:
            stats[stat] = safe_randint(low, high)
    return stats


def calculate_combat_stats(character):
    klass = character["Kaszt"]
    stats = character["Tulajdonságok"]
    # Get class_id from name
    classes = class_db.list_classes()
    class_id = next((cid for cid, name in classes if name == klass), None)
    if class_id is None:
        raise ValueError(f"Class '{klass}' not found in DB")
    details = class_db.get_class_details(class_id)
    data = details["combat_stats"]
    if not data:
        data = {}

    # Véletlenszerű FP bónusz első szintre
    # Note: data indices include id (0) and class_id (1), so actual stats start at index 2
    fp_min = data[3] if len(data) > 3 else 0  # fp_min_per_level
    fp_max = data[4] if len(data) > 4 else 0  # fp_max_per_level
    fp_bonus = safe_randint(fp_min, fp_max)

    def bonus(val):
        return max(0, val - 10)

    fp = (data[2] if len(data) > 2 else 0) + fp_bonus + bonus(stats["Akaraterő"]) + bonus(stats["Állóképesség"])
    ep = (data[5] if len(data) > 5 else 0) + bonus(stats["Egészség"])
    ke = (data[8] if len(data) > 8 else 0) + bonus(stats["Gyorsaság"]) + bonus(stats["Ügyesség"])
    te = (data[9] if len(data) > 9 else 0) + bonus(stats["Erő"]) + bonus(stats["Gyorsaság"]) + bonus(stats["Ügyesség"])
    ve = (data[10] if len(data) > 10 else 0) + bonus(stats["Gyorsaság"]) + bonus(stats["Ügyesség"])
    ce = (data[11] if len(data) > 11 else 0) + bonus(stats["Ügyesség"])

    character["Harci értékek"] = {
        "FP": fp,
        "ÉP": ep,
        "KÉ": ke,
        "TÉ": te,
        "VÉ": ve,
        "CÉ": ce,
        "HM/szint": {
            "total": data[12] if len(data) > 12 else 0,
            "mandatory": {"TÉ": data[13] if len(data) > 13 else 0, "VÉ": data[14] if len(data) > 14 else 0}
        },
    }

    character["Képzettségpontok"] = {
        "Alap": data[6] if len(data) > 6 else 0,
        "Szintenként": data[7] if len(data) > 7 else 0
    }

    return character


def generate_character(name, gender, age, race, klass):
    stats = generate_stats(klass)
    stats = apply_age_modifiers(stats, race, age)
    stats = apply_race_modifiers(stats, race)
    # For now, upgradable stats are not in DB, fallback to empty list
    upgradable = []

    szint = 1
    skills = []
    equipment = []
    xp = 0

    char = {
        "Név": name,
        "Nem": gender,
        "Kor": age,
        "Faj": race,
        "Kaszt": klass,
        "Szint": szint,
        "Tapasztalat": xp,
        "Tulajdonságok": stats,
        "Fejleszthető": upgradable,
        "Képzettségek": skills,
        "Felszerelés": equipment
    }

    char = calculate_combat_stats(char)
    return char


def get_level_for_xp(klass, xp):
    # Get class_id from name
    classes = class_db.list_classes()
    class_id = next((cid for cid, name in classes if name == klass), None)
    if class_id is None:
        raise ValueError(f"Class '{klass}' not found in DB")
    details = class_db.get_class_details(class_id)
    reqs = [r[1] for r in details["level_requirements"]]
    for i in range(1, len(reqs)):
        if xp < reqs[i]:
            return i - 1
    extra_xp = details["extra_xp"] if details["extra_xp"] else 50000
    if reqs:
        max_level = len(reqs) - 1
        if xp < reqs[-1]:
            return max_level
        else:
            return max_level + ((xp - reqs[-1]) // extra_xp) + 1
    return 1


def get_next_level_xp(klass, xp):
    # Get class_id from name
    classes = class_db.list_classes()
    class_id = next((cid for cid, name in classes if name == klass), None)
    if class_id is None:
        raise ValueError(f"Class '{klass}' not found in DB")
    details = class_db.get_class_details(class_id)
    reqs = [r[1] for r in details["level_requirements"]]
    level = get_level_for_xp(klass, xp)
    if level + 1 < len(reqs):
        return reqs[level + 1]
    else:
        extra_xp = details["extra_xp"] if details["extra_xp"] else 50000
        return reqs[-1] + (level - (len(reqs) - 1) + 1) * extra_xp


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
        "Harcművész", "Kardművész", "Boszorkány", "Boszorkánymester", "Tűzvarázsló", "Pszi mester"
    },
    "Félelf": {
        "Amazon", "Barbár","Pap", "Paplovag", "Szerzetes",
        "Tűzvarázsló"
    },
    "Khál": {
        "Amazon", "Barbár", "Bajvívó", "Tolvaj", "Bárd", "Pap", "Paplovag", "Szerzetes", "Sámán",
        "Harcművész", "Kardművész", "Boszorkány", "Boszorkánymester", "Tűzvarázsló", "Varázsló", "Pszi mester"
    },
    "Törpe": {
        "Fejvadász", "Lovag", "Amazon", "Barbár", "Bajvívó", "Bárd", "Paplovag", "Szerzetes", "Sámán",
        "Harcművész", "Kardművész", "Boszorkány", "Boszorkánymester", "Tűzvarázsló", "Pszi mester"
    },
    "Udvari ork": {
        "Lovag", "Amazon", "Barbár", "Bárd", "Pap", "Paplovag", "Szerzetes", "Sámán",
        "Harcművész", "Kardművész", "Boszorkány", "Tűzvarázsló", "Varázsló", "Pszi mester"
    },
    "Wier": {
        "Gladiátor", "Amazon", "Barbár", "Bárd", "Pap", "Sámán",
        "Harcművész", "Kardművész", "Tűzvarázsló"
    },
    "Goblin": {
        "Lovag", "Pap", "Paplovag", "Szerzetes", "Sámán", "Bárd", "Bajvívó", "Barbár", "Amazon",
        "Harcművész", "Kardművész", "Boszorkány", "Tűzvarázsló", "Varázsló", "Pszi mester"
    }
}

def is_valid_character(gender, race, klass):
    if klass in GENDER_RESTRICTIONS.get(gender, set()):
        return False
    if klass in RACE_RESTRICTIONS.get(race, set()):
        return False
    return True
