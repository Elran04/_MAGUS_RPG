# engine/character.py
import random
from typing import Any

from utils.data.class_db_manager import ClassDBManager

# Initialize managers
class_db = ClassDBManager()


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
    fp_bonus = random.randint(fp_min, fp_max) if fp_min <= fp_max else 0

    def bonus(val):
        return max(0, val - 10)

    fp = (
        (data[2] if len(data) > 2 else 0)
        + fp_bonus
        + bonus(stats["Akaraterő"])
        + bonus(stats["Állóképesség"])
    )
    ep = (data[5] if len(data) > 5 else 0) + bonus(stats["Egészség"])
    ke = (data[8] if len(data) > 8 else 0) + bonus(stats["Gyorsaság"]) + bonus(stats["Ügyesség"])
    te = (
        (data[9] if len(data) > 9 else 0)
        + bonus(stats["Erő"])
        + bonus(stats["Gyorsaság"])
        + bonus(stats["Ügyesség"])
    )
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
            "mandatory": {
                "TÉ": data[13] if len(data) > 13 else 0,
                "VÉ": data[14] if len(data) > 14 else 0,
            },
        },
    }

    character["Képzettségpontok"] = {
        "Alap": data[6] if len(data) > 6 else 0,
        "Szintenként": data[7] if len(data) > 7 else 0,
    }

    return character


def calculate_skill_points(klass: str) -> dict:
    """Calculate skill points (KP) for a given class without needing attributes.

    Args:
        klass: The class name (e.g., "Harcos", "Varázsló")

    Returns:
        Dict with "Alap" and "Szintenként" keys containing the KP values
    """
    # Get class_id from name
    classes = class_db.list_classes()
    class_id = next((cid for cid, name in classes if name == klass), None)
    if class_id is None:
        raise ValueError(f"Class '{klass}' not found in DB")

    details = class_db.get_class_details(class_id)
    data = details["combat_stats"]
    if not data:
        return {"Alap": 0, "Szintenként": 0}

    return {"Alap": data[6] if len(data) > 6 else 0, "Szintenként": data[7] if len(data) > 7 else 0}


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
