"""
Skill Database Service
Handles all database access for skills during character creation.
"""

import sqlite3
from typing import Any

from config.paths import CLASSES_DB, SKILLS_DB
from utils.log.logger import get_logger

logger = get_logger(__name__)


class SkillDatabaseService:
    """Service class for skill database operations."""

    def __init__(self, base_dir: str):
        # base_dir kept for backward compatibility; paths now centralized
        self.base_dir = base_dir

    def get_db_path(self, db_type: str) -> str:
        """Get database path for given type ('class' or 'skill')."""
        if db_type == "class":
            return str(CLASSES_DB)
        return str(SKILLS_DB)

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

    def process_skill_entries(
        self, skills: list[tuple[str, Any, Any, Any, Any]]
    ) -> tuple[list[tuple[str, Any, Any, Any, Any, int, str]], set[str]]:
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
                except (sqlite3.Error, TypeError, ValueError) as e:
                    logger.error(f"Error probing skill {skill_id}: {e}", exc_info=True)

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
        except sqlite3.Error:
            return None

    @staticmethod
    def parse_skill_display(display: str) -> tuple[str, str]:
        """Parse skill display text into (name, parameter) tuple."""
        if "(" in display and display.endswith(")"):
            try:
                base, p = display.rsplit("(", 1)
                return base.strip(), p[:-1].strip()
            except (ValueError, AttributeError):
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
        except sqlite3.Error:
            pass
        return None

    def get_skill_categories(self, skill_id: str) -> tuple[str, str] | None:
        """Get (category, subcategory) for a given skill id, or None if not found."""
        try:
            with sqlite3.connect(self.get_db_path("skill")) as sconn:
                row = sconn.execute(
                    "SELECT category, subcategory FROM skills WHERE id=?",
                    (skill_id,),
                ).fetchone()
                if row:
                    cat = row[0] or ""
                    sub = row[1] or ""
                    return cat, sub
        except sqlite3.Error:
            pass
        return None

    def get_skill_info(self, skill_id: str) -> tuple[str, str, int] | None:
        """
        Get skill name, parameter, and type from skill ID.
        Returns (name, parameter, type) or None if not found.
        """
        try:
            with sqlite3.connect(self.get_db_path("skill")) as sconn:
                row = sconn.execute(
                    "SELECT name, parameter, type FROM skills WHERE id=?", (skill_id,)
                ).fetchone()
                if row:
                    return row[0], row[1] or "", row[2]
        except sqlite3.Error:
            pass
        return None

    def get_all_skill_categories(self) -> list[str]:
        """Get all distinct skill categories (excluding placeholders)."""
        try:
            with sqlite3.connect(self.get_db_path("skill")) as conn:
                cursor = conn.execute(
                    "SELECT DISTINCT category FROM skills WHERE placeholder = 0 AND category IS NOT NULL ORDER BY category"
                )
                return [row[0] for row in cursor.fetchall() if row[0]]
        except sqlite3.Error as e:
            logger.error(f"Error fetching categories: {e}", exc_info=True)
            return []

    def get_learnable_skills(
        self, category_filter: str | None = None
    ) -> list[tuple[str, str, str, str, int]]:
        """
        Get all learnable skills (non-placeholder).
        Returns list of (id, name, parameter, category, type) tuples.

        Args:
            category_filter: Optional category to filter by
        """
        try:
            with sqlite3.connect(self.get_db_path("skill")) as conn:
                query = (
                    "SELECT id, name, parameter, category, type FROM skills WHERE placeholder = 0"
                )
                params: list[Any] = []
                if category_filter:
                    query += " AND category = ?"
                    params.append(category_filter)
                query += " ORDER BY category, name"

                return conn.execute(query, params).fetchall()
        except sqlite3.Error as e:
            logger.error(f"Error fetching learnable skills: {e}", exc_info=True)
            return []

    def get_skill_attribute_prerequisites(self, skill_id: str) -> list[tuple[str, int, int | None]]:
        """
        Get attribute prerequisites for a skill.
        Returns list of (attribute, min_value, level) tuples.
        """
        try:
            with sqlite3.connect(self.get_db_path("skill")) as conn:
                return conn.execute(
                    "SELECT attribute, min_value, level FROM skill_prerequisites_attributes "
                    "WHERE skill_id=? ORDER BY level",
                    (skill_id,),
                ).fetchall()
        except sqlite3.Error as e:
            logger.error(f"Error fetching attribute prerequisites: {e}", exc_info=True)
            return []

    def get_skill_skill_prerequisites(self, skill_id: str) -> list[tuple[str, int, int | None]]:
        """
        Get skill prerequisites for a skill.
        Returns list of (required_skill_id, min_level, level) tuples.
        """
        try:
            with sqlite3.connect(self.get_db_path("skill")) as conn:
                return conn.execute(
                    "SELECT required_skill_id, min_level, level FROM skill_prerequisites_skills "
                    "WHERE skill_id=? ORDER BY level",
                    (skill_id,),
                ).fetchall()
        except sqlite3.Error as e:
            logger.error(f"Error fetching skill prerequisites: {e}", exc_info=True)
            return []

    def get_skill_type(self, skill_id: str) -> int | None:
        """Get skill type (1=level, 2=percent) for a skill."""
        try:
            with sqlite3.connect(self.get_db_path("skill")) as conn:
                row = conn.execute("SELECT type FROM skills WHERE id=?", (skill_id,)).fetchone()
                return int(row[0]) if row else None
        except sqlite3.Error as e:
            logger.error(f"Error fetching skill type: {e}", exc_info=True)
            return None
