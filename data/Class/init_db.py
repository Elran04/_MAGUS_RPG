import sqlite3

# Adatbázis létrehozása
conn = sqlite3.connect("magus_rpg.db")
cursor = conn.cursor()

# Kasztok tábla
cursor.execute("""
CREATE TABLE IF NOT EXISTS classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
)
""")

# Statok tábla
cursor.execute("""
CREATE TABLE IF NOT EXISTS stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id INTEGER NOT NULL,
    stat_name TEXT NOT NULL,
    min_value INTEGER,
    max_value INTEGER,
    FOREIGN KEY(class_id) REFERENCES classes(id)
)
""")

# Harci értékek tábla

cursor.execute("""
CREATE TABLE IF NOT EXISTS combat_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id INTEGER NOT NULL,
    fp INTEGER,
    fp_min_per_level INTEGER,
    fp_max_per_level INTEGER,
    ep INTEGER,
    kp INTEGER,
    kp_per_level INTEGER,
    ke INTEGER,
    te INTEGER,
    ve INTEGER,
    ce INTEGER,
    hm_total INTEGER,
    hm_te INTEGER,
    hm_ve INTEGER,
    FOREIGN KEY(class_id) REFERENCES classes(id)
)
""")

# Szintkövetelmények tábla
cursor.execute("""
CREATE TABLE IF NOT EXISTS level_requirements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id INTEGER NOT NULL,
    level INTEGER NOT NULL,
    xp INTEGER NOT NULL,
    FOREIGN KEY(class_id) REFERENCES classes(id)
)
""")

# Kezdő tőke tábla
cursor.execute("""
CREATE TABLE IF NOT EXISTS starting_currency (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id INTEGER NOT NULL,
    min_gold INTEGER,
    max_gold INTEGER,
    FOREIGN KEY(class_id) REFERENCES classes(id)
)
""")

conn.commit()
conn.close()
