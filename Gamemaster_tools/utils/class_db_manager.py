import os
import sqlite3

# Resolve DB path relative to this file (.. / data / Class / class_data.db)
DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data", "Class", "class_data.db"
)

class ClassDBManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    # --- Classes table extensions ---
    def ensure_classes_description_column(self):
        """Ensure classes table has a description_file column for base class descriptions."""
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute("PRAGMA table_info(classes)")
            cols = {row[1] for row in c.fetchall()}
            if "description_file" not in cols:
                c.execute("ALTER TABLE classes ADD COLUMN description_file TEXT")
                conn.commit()

    # --- Starting equipment support ---
    def ensure_starting_equipment_table(self):
        """Create starting_equipment table if it does not exist.

        Schema:
          - entry_id INTEGER PRIMARY KEY
          - class_id TEXT NOT NULL
          - specialisation_id TEXT NULL (NULL = alap kaszt)
          - item_type TEXT NOT NULL (armor | weapon | shield | general | currency)
          - item_id TEXT NULL (csak akkor kötelező, ha nem currency)
          - min_currency INTEGER NULL (csak currency esetén töltött)
          - max_currency INTEGER NULL (csak currency esetén töltött)
        Constraints:
          - CHECK az item_type-ra
          - CHECK a currency vs item kötelező mezőkre
          - max_currency >= min_currency currency esetén
          - FK classes(id) és opcionálisan specialisations(class_id, specialisation_id) ha létezik
        """
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS starting_equipment (
                    entry_id INTEGER PRIMARY KEY,
                    class_id TEXT NOT NULL,
                    specialisation_id TEXT,
                    item_type TEXT NOT NULL,
                    item_id TEXT,
                    min_currency INTEGER,
                    max_currency INTEGER,
                    -- Allowed values based on current project schema
                    CHECK (item_type IN ('armor','weaponandshield','general','currency')),
                    CHECK (
                        (item_type = 'currency' AND item_id IS NULL AND min_currency IS NOT NULL AND max_currency IS NOT NULL AND max_currency >= min_currency)
                        OR
                        (item_type <> 'currency' AND item_id IS NOT NULL AND min_currency IS NULL AND max_currency IS NULL)
                    ),
                    -- Keep class FK, and prefer composite FK to specialisations if table exists
                    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE
                    -- FOREIGN KEY (class_id, specialisation_id) REFERENCES specialisations(class_id, specialisation_id) ON DELETE CASCADE
                )
                """
            )
            c.execute("CREATE INDEX IF NOT EXISTS idx_starting_equipment_class_spec ON starting_equipment (class_id, COALESCE(specialisation_id, ''))")
            c.execute("CREATE INDEX IF NOT EXISTS idx_starting_equipment_type ON starting_equipment (item_type)")
            conn.commit()

    def add_starting_equipment_currency(self, class_id: str, specialisation_id: str | None, min_currency: int, max_currency: int):
        """Insert a currency row for a class/spec."""
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute(
                """
                INSERT INTO starting_equipment (class_id, specialisation_id, item_type, item_id, min_currency, max_currency)
                VALUES (?, ?, 'currency', NULL, ?, ?)
                """,
                (class_id, specialisation_id, int(min_currency), int(max_currency))
            )
            conn.commit()

    def add_starting_equipment_item(self, class_id: str, specialisation_id: str | None, item_type: str, item_id: str):
        """Insert a non-currency starting item for a class/spec."""
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute(
                """
                INSERT INTO starting_equipment (class_id, specialisation_id, item_type, item_id, min_currency, max_currency)
                VALUES (?, ?, ?, ?, NULL, NULL)
                """,
                (class_id, specialisation_id, item_type, item_id)
            )
            conn.commit()

    def update_starting_equipment_currency(self, entry_id: int, min_currency: int, max_currency: int):
        """Update a currency row identified by entry_id."""
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute(
                """
                UPDATE starting_equipment
                SET min_currency = ?, max_currency = ?
                WHERE entry_id = ? AND item_type = 'currency'
                """,
                (int(min_currency), int(max_currency), int(entry_id))
            )
            conn.commit()

    def update_starting_equipment_item(self, entry_id: int, item_type: str, item_id: str):
        """Update a non-currency item row identified by entry_id."""
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute(
                """
                UPDATE starting_equipment
                SET item_type = ?, item_id = ?
                WHERE entry_id = ? AND item_type <> 'currency'
                """,
                (item_type, item_id, int(entry_id))
            )
            conn.commit()

    def delete_starting_equipment(self, entry_id: int):
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM starting_equipment WHERE entry_id = ?", (int(entry_id),))
            conn.commit()

    def list_starting_equipment(self, class_id: str, specialisation_id: str | None = None):
        """Return list of starting equipment rows for a class/spec.

        Returns list of dicts with keys: entry_id, item_type, item_id, min_currency, max_currency.
        """
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            if specialisation_id is None:
                c.execute(
                    """
                    SELECT entry_id, item_type, item_id, min_currency, max_currency
                    FROM starting_equipment
                    WHERE class_id = ? AND specialisation_id IS NULL
                    ORDER BY entry_id
                    """,
                    (class_id,)
                )
            else:
                c.execute(
                    """
                    SELECT entry_id, item_type, item_id, min_currency, max_currency
                    FROM starting_equipment
                    WHERE class_id = ? AND specialisation_id = ?
                    ORDER BY entry_id
                    """,
                    (class_id, specialisation_id)
                )
            rows = [dict(row) for row in c.fetchall()]
            return rows

    # --- Specialisations support ---
    def ensure_specialisations_table(self):
        """Ensure the specialisations table exists (compatible with current project schema)."""
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS specialisations (
                    class_id TEXT,
                    specialisation_id TEXT,
                    specialisation_name TEXT,
                    specialisation_description TEXT,
                    PRIMARY KEY (class_id, specialisation_id)
                )
                """
            )
            conn.commit()

    def list_specialisations(self, class_id: str):
        """List specialisations for a class."""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute(
                """
                SELECT class_id, specialisation_id, specialisation_name, specialisation_description
                FROM specialisations
                WHERE class_id = ?
                ORDER BY specialisation_name
                """,
                (class_id,)
            )
            return [dict(row) for row in c.fetchall()]

    def upsert_specialisation(self, class_id: str, specialisation_id: str, name: str, description_file: str | None):
        """Insert or update a specialisation row."""
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute(
                """
                INSERT INTO specialisations (class_id, specialisation_id, specialisation_name, specialisation_description)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(class_id, specialisation_id) DO UPDATE SET
                    specialisation_name=excluded.specialisation_name,
                    specialisation_description=excluded.specialisation_description
                """,
                (class_id, specialisation_id, name, description_file)
            )
            conn.commit()

    def delete_specialisation(self, class_id: str, specialisation_id: str):
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute(
                "DELETE FROM specialisations WHERE class_id = ? AND specialisation_id = ?",
                (class_id, specialisation_id)
            )
            conn.commit()

    # --- Currency resolver ---
    def get_effective_starting_currency(self, class_id: str, specialisation_id: str | None = None):
        """Resolve starting currency for a class/spec by priority:
        1) starting_equipment currency row for given specialisation
        2) starting_equipment currency row for base class (NULL spec)
        3) starting_currency fallback table (min_gold, max_gold)
        Returns tuple (min_value, max_value) or (None, None) if not found.
        """
        with self.get_connection() as conn:
            c = conn.cursor()
            # 1) Spec currency
            if specialisation_id is not None:
                c.execute(
                    """
                    SELECT min_currency, max_currency
                    FROM starting_equipment
                    WHERE class_id = ? AND specialisation_id = ? AND item_type = 'currency'
                    LIMIT 1
                    """,
                    (class_id, specialisation_id)
                )
                row = c.fetchone()
                if row:
                    return row[0], row[1]
            # 2) Base class currency
            c.execute(
                """
                SELECT min_currency, max_currency
                FROM starting_equipment
                WHERE class_id = ? AND specialisation_id IS NULL AND item_type = 'currency'
                LIMIT 1
                """,
                (class_id,)
            )
            row = c.fetchone()
            if row:
                return row[0], row[1]
            # 3) Fallback to starting_currency
            c.execute("SELECT min_gold, max_gold FROM starting_currency WHERE class_id = ?", (class_id,))
            row = c.fetchone()
            if row:
                return row[0], row[1]
            return None, None

    def list_classes(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM classes ORDER BY name")
            return cursor.fetchall()

    def get_class_details(self, class_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Get class name
            cursor.execute("SELECT name, COALESCE(description_file, '') FROM classes WHERE id = ?", (class_id,))
            row = cursor.fetchone()
            name = row[0]
            class_description_file = row[1] if row and len(row) > 1 else ""
            # Get stat ranges, including double_chance
            cursor.execute("SELECT stat_name, min_value, max_value, double_chance FROM stats WHERE class_id = ?", (class_id,))
            stats = cursor.fetchall()
            # Get combat stats
            cursor.execute("SELECT * FROM combat_stats WHERE class_id = ?", (class_id,))
            combat_stats = cursor.fetchone()
            # Get level requirements
            cursor.execute("SELECT level, xp FROM level_requirements WHERE class_id = ? ORDER BY level", (class_id,))
            level_requirements = cursor.fetchall()
            # Get starting currency
            cursor.execute("SELECT min_gold, max_gold FROM starting_currency WHERE class_id = ?", (class_id,))
            starting_currency = cursor.fetchone()
            # Get starting equipment (base class level, no specialisation)
            try:
                cursor.execute(
                    "SELECT item_type, item_id, min_currency, max_currency FROM starting_equipment WHERE class_id = ? AND specialisation_id IS NULL ORDER BY entry_id",
                    (class_id,)
                )
                starting_equipment = cursor.fetchall()
            except sqlite3.OperationalError:
                # Table may not exist yet
                starting_equipment = []
            # Get further level requirements
            cursor.execute("SELECT extra_xp FROM further_level_requirements WHERE class_id = ?", (class_id,))
            extra_xp = cursor.fetchone()
            return {
                "name": name,
                "stats": stats,
                "combat_stats": combat_stats,
                "level_requirements": level_requirements,
                "starting_currency": starting_currency,
                "starting_equipment": starting_equipment,
                "extra_xp": extra_xp[0] if extra_xp else None,
                "class_description_file": class_description_file,
            }

    def update_class_name(self, class_id, new_name):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE classes SET name = ? WHERE id = ?", (new_name, class_id))
            conn.commit()

    # Add more update/insert/delete methods as needed for stats, combat stats, etc.

    def update_class_description_file(self, class_id: str, description_file: str | None):
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute("UPDATE classes SET description_file = ? WHERE id = ?", (description_file, class_id))
            conn.commit()
