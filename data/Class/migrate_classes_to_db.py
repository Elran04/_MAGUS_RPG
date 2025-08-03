import sqlite3
from class_stats import (
    ALL_CLASSES,
    CLASS_STAT_WEIGHTS,
    CLASS_COMBAT_STATS_AND_SKILL_POINTS,
    CLASS_LEVEL_REQUIREMENTS,
    CLASS_STARTING_CURRENCY,
    CLASS_ADDITIONAL_STATS
)

DB_PATH = "magus_rpg.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

for class_name in ALL_CLASSES:
    # Insert class
    cursor.execute("INSERT OR IGNORE INTO classes (name) VALUES (?)", (class_name,))
    cursor.execute("SELECT id FROM classes WHERE name = ?", (class_name,))
    class_id = cursor.fetchone()[0]

    # Insert stat ranges
    stat_weights = CLASS_STAT_WEIGHTS.get(class_name, {}).get("statok", {})
    for stat_name, (min_value, max_value) in stat_weights.items():
        cursor.execute(
            "INSERT INTO stats (class_id, stat_name, min_value, max_value) VALUES (?, ?, ?, ?)",
            (class_id, stat_name, min_value, max_value)
        )

    # Insert combat stats
    combat = CLASS_COMBAT_STATS_AND_SKILL_POINTS.get(class_name, {})
    if combat:
        cursor.execute(
            """
            INSERT INTO combat_stats (
                class_id, fp, fp_min_per_level, fp_max_per_level, ep, kp, kp_per_level, ke, te, ve, ce, hm_total, hm_te, hm_ve
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                class_id,
                combat.get("FP"),
                combat.get("FP_per_level", (None, None))[0],
                combat.get("FP_per_level", (None, None))[1],
                combat.get("ÉP"),
                combat.get("KP"),
                combat.get("KP_per_level"),
                combat.get("KÉ"),
                combat.get("TÉ"),
                combat.get("VÉ"),
                combat.get("CÉ"),
                combat.get("HM_per_level", {}).get("total"),
                combat.get("HM_per_level", {}).get("mandatory", {}).get("TÉ"),
                combat.get("HM_per_level", {}).get("mandatory", {}).get("VÉ"),
            )
        )

    # Insert level requirements
    levels = CLASS_LEVEL_REQUIREMENTS.get(class_name, [])
    for level, xp in enumerate(levels):
        cursor.execute(
            "INSERT INTO level_requirements (class_id, level, xp) VALUES (?, ?, ?)",
            (class_id, level, xp)
        )

    # Insert starting currency
    currency = CLASS_STARTING_CURRENCY.get(class_name, (None, None))
    cursor.execute(
        "INSERT INTO starting_currency (class_id, min_gold, max_gold) VALUES (?, ?, ?)",
        (class_id, currency[0], currency[1])
    )

conn.commit()
conn.close()

print("Class data migration complete.")
