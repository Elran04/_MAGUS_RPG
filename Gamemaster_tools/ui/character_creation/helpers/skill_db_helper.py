"""
Skill Database Helper
Handles all database access for skills during character creation.
"""

import os
import sqlite3
from typing import Any


class SkillDatabaseHelper:
    """Helper class for skill database operations."""

    def __init__(self, base_dir: str):
        self.base_dir = base_dir

    def get_db_path(self, db_type: str) -> str:
        """Get database path for given type ('class' or 'skill')."""
        if db_type == "class":
            return os.path.join(self.base_dir, "data", "Class", "class_data.db")
        return os.path.join(self.base_dir, "data", "skills", "skills_data.db")

    def fetch_class_skills(
        self, class_id: str, spec_id: str | None
    ) -> list[tuple[str, Any, Any, Any, Any]]:
        """Fetch class skills from database, optionally including specialization skills."""
        query = """
            SELECT skill_id, class_level, skill_level, skill_percent, specialisation_id
            FROM class_skills 
            WHERE class_id=? AND {}
            ORDER BY class_level, skill_id
        """
        with sqlite3.connect(self.get_db_path("class")) as conn:
            if spec_id:
                return conn.execute(
                    query.format("(specialisation_id IS NULL OR specialisation_id=?)"),
                    (class_id, spec_id),
                ).fetchall()
            return conn.execute(query.format("specialisation_id IS NULL"), (class_id,)).fetchall()

    def process_skill_entries(self, skills: list[tuple]) -> tuple[list[tuple], set[str]]:
        """Process raw skills data into entries with display names and fixed skill tracking."""
        entries = []
        fixed = set()

        with sqlite3.connect(self.get_db_path("skill")) as skill_conn:
            for skill_id, class_level, skill_level, skill_percent, from_spec in skills:
                try:
                    row = skill_conn.execute(
                        "SELECT name, parameter, type, placeholder FROM skills WHERE id=?",
                        (skill_id,),
                    ).fetchone()
                    if not row:
                        continue
                    name, parameter, stype, is_placeholder = row
                    display = f"{name} ({parameter})" if parameter else name
                    entries.append(
                        (
                            skill_id,
                            class_level,
                            skill_level,
                            skill_percent,
                            from_spec,
                            is_placeholder,
                            display,
                        )
                    )
                    if is_placeholder != 1:
                        fixed.add(skill_id)
                except Exception as e:
                    print(f"Error probing skill {skill_id}: {e}")

        return entries, fixed

    def calc_kp_cost(
        self, concrete_skill_id: str, req_level: int | None, req_percent: int | None
    ) -> str:
        """Calculate KP cost for a concrete skill at given level/percent."""
        with sqlite3.connect(self.get_db_path("skill")) as skill_conn:
            srow = skill_conn.execute(
                "SELECT type FROM skills WHERE id=?", (concrete_skill_id,)
            ).fetchone()
            if not srow:
                return "?"
            ctype = srow[0]
            if ctype == 1 and req_level:
                crow = skill_conn.execute(
                    "SELECT kp_cost FROM skill_level_costs WHERE skill_id=? AND level=?",
                    (concrete_skill_id, req_level),
                ).fetchone()
                return str(crow[0]) if crow else "?"
            elif ctype == 2 and req_percent:
                crow = skill_conn.execute(
                    "SELECT kp_per_3percent FROM skill_percent_costs WHERE skill_id=?",
                    (concrete_skill_id,),
                ).fetchone()
                return str((req_percent // 3) * crow[0]) if crow else "?"
        return "?"

    def get_skill_by_display(self, display: str) -> str | None:
        """Get skill ID from display text (name and parameter)."""
        name, param = self.parse_skill_display(display)
        try:
            with sqlite3.connect(self.get_db_path("skill")) as sconn:
                res = sconn.execute(
                    "SELECT id FROM skills WHERE name=? AND IFNULL(parameter,'')=?",
                    (name, param),
                ).fetchone()
                return res[0] if res else None
        except Exception:
            return None

    @staticmethod
    def parse_skill_display(display: str) -> tuple[str, str]:
        """Parse skill display text into (name, parameter) tuple."""
        if "(" in display and display.endswith(")"):
            try:
                base, p = display.rsplit("(", 1)
                return base.strip(), p[:-1].strip()
            except Exception:
                pass
        return display, ""

    def get_skill_name_and_param(self, skill_id: str) -> tuple[str, str] | None:
        """Get skill name and parameter from skill ID."""
        try:
            with sqlite3.connect(self.get_db_path("skill")) as sconn:
                row = sconn.execute(
                    "SELECT name, parameter FROM skills WHERE id=?", (skill_id,)
                ).fetchone()
                if row:
                    return row[0], row[1] or ""
        except Exception:
            pass
        return None
