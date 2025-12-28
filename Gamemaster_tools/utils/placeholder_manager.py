"""
Placeholder Skill Resolution Manager

Handles the mapping between placeholder skills (e.g., "Fegyverhasználat (Választható)")
and the actual skills they can resolve to (e.g., specific weapon skills).
"""

import sqlite3
from typing import Any

from config.paths import SKILLS_DB
from utils.log.logger import get_logger

logger = get_logger(__name__)

DB_SKILLS_PATH = str(SKILLS_DB)


class PlaceholderManager:
    """Manages placeholder skill resolution mappings."""

    def __init__(self, db_path: str = DB_SKILLS_PATH) -> None:
        self.db_path = db_path
        self._ensure_table()

    def _ensure_table(self) -> None:
        """Create placeholder_resolutions table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS placeholder_resolutions (
                    placeholder_id TEXT NOT NULL,
                    target_skill_id TEXT NOT NULL,
                    -- Optional: category for grouping (e.g., 'light_weapons', 'heavy_weapons', 'ranged')
                    resolution_category TEXT,
                    -- Optional: notes or conditions
                    notes TEXT,
                    PRIMARY KEY (placeholder_id, target_skill_id),
                    FOREIGN KEY (placeholder_id) REFERENCES skills(id) ON DELETE CASCADE,
                    FOREIGN KEY (target_skill_id) REFERENCES skills(id) ON DELETE CASCADE
                )
            """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_placeholder_lookup
                ON placeholder_resolutions(placeholder_id)
            """
            )
            conn.commit()

    def add_resolution(
        self,
        placeholder_id: str,
        target_skill_id: str,
        category: str | None = None,
        notes: str | None = None,
    ) -> None:
        """Add a resolution mapping from placeholder to target skill."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO placeholder_resolutions
                (placeholder_id, target_skill_id, resolution_category, notes)
                VALUES (?, ?, ?, ?)
                """,
                (placeholder_id, target_skill_id, category, notes),
            )
            conn.commit()

    def remove_resolution(self, placeholder_id: str, target_skill_id: str) -> None:
        """Remove a specific resolution mapping."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM placeholder_resolutions WHERE placeholder_id=? AND target_skill_id=?",
                (placeholder_id, target_skill_id),
            )
            conn.commit()

    def get_resolutions(
        self, placeholder_id: str, category: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Get all skills that can replace a placeholder.

        Args:
            placeholder_id: The placeholder skill ID
            category: Optional filter by resolution_category

        Returns:
            List of dicts with keys: target_skill_id, skill_name, parameter, resolution_category, notes
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if category:
                query = """
                    SELECT
                        pr.target_skill_id,
                        s.name as skill_name,
                        s.parameter,
                        pr.resolution_category,
                        pr.notes
                    FROM placeholder_resolutions pr
                    JOIN skills s ON pr.target_skill_id = s.id
                    WHERE pr.placeholder_id = ? AND pr.resolution_category = ?
                    ORDER BY s.name, s.parameter
                """
                rows = conn.execute(query, (placeholder_id, category)).fetchall()
            else:
                query = """
                    SELECT
                        pr.target_skill_id,
                        s.name as skill_name,
                        s.parameter,
                        pr.resolution_category,
                        pr.notes
                    FROM placeholder_resolutions pr
                    JOIN skills s ON pr.target_skill_id = s.id
                    WHERE pr.placeholder_id = ?
                    ORDER BY s.name, s.parameter
                """
                rows = conn.execute(query, (placeholder_id,)).fetchall()

            return [dict(row) for row in rows]

    def is_placeholder(self, skill_id: str) -> bool:
        """Check if a skill is a placeholder."""
        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute(
                "SELECT placeholder FROM skills WHERE id = ?", (skill_id,)
            ).fetchone()
            return result[0] == 1 if result else False

    def get_all_placeholders(self) -> list[dict[str, Any]]:
        """Get all placeholder skills."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT id, name, parameter FROM skills WHERE placeholder = 1 ORDER BY name"
            ).fetchall()
            return [dict(row) for row in rows]

    def populate_default_resolutions(self) -> None:
        """
        Populate default placeholder resolutions based on MAGUS system.
        This should be called once to initialize the table with standard mappings.
        """
        # weaponskill_placeholder: General weapon skills (light/medium weapons)
        general_weapons = [
            "weaponskill_curvedblades",
            "weaponskill_longswords",
            "weaponskill_shortswords",
            "weaponskill_daggers",
            "weaponskill_sabers",
            "weaponskill_rapiers",
            "weaponskill_maces",
        ]

        # weaponskill_placeholder_heavy: Heavy weapons
        heavy_weapons = [
            "weaponskill_battleaxes",
            "weaponskill_greatswords",
            "weaponskill_longhandled",
            "weaponskill_warhammers",
        ]

        # weaponskill_placeholder_ranged: Ranged weapons
        ranged_weapons = [
            "weaponskill_bows",
            "throwing_daggers",
            "throwing_spears",
        ]

        # Add general weapon resolutions
        for skill_id in general_weapons:
            self.add_resolution("weaponskill_placeholder", skill_id, "light_medium")

        # Add heavy weapon resolutions
        for skill_id in heavy_weapons:
            self.add_resolution("weaponskill_placeholder_heavy", skill_id, "heavy")

        # Add ranged weapon resolutions
        for skill_id in ranged_weapons:
            self.add_resolution("weaponskill_placeholder_ranged", skill_id, "ranged")

        # close_quarters_combat_prereq: Belharc prerequisites (specific weapon types)
        # This might need manual configuration based on game rules
        belharc_prereq_weapons = [
            "weaponskill_shortswords",
            "weaponskill_daggers",
        ]
        for skill_id in belharc_prereq_weapons:
            self.add_resolution("close_quarters_combat_prereq", skill_id, "close_quarters")

        logger.info("Default placeholder resolutions populated successfully")

    def get_resolution_summary(self) -> list[dict[str, Any]]:
        """Get a summary of all placeholder resolutions for debugging/display."""
        placeholders = self.get_all_placeholders()
        summary = []

        for ph in placeholders:
            resolutions = self.get_resolutions(ph["id"])
            summary.append(
                {
                    "placeholder": ph,
                    "resolution_count": len(resolutions),
                    "resolutions": resolutions,
                }
            )

        return summary


if __name__ == "__main__":
    # Test/initialize the placeholder resolution system
    manager = PlaceholderManager()

    logger.info("=== Placeholder Resolution Manager ===")

    # Populate default resolutions
    manager.populate_default_resolutions()

    # Show summary
    logger.info("=== Placeholder Resolution Summary ===")
    summary = manager.get_resolution_summary()

    for item in summary:
        ph = item["placeholder"]
        logger.info(f"{ph['name']} ({ph['parameter']})")
        logger.info(f"  ID: {ph['id']}")
        logger.info(f"  Resolutions: {item['resolution_count']}")

        if item["resolutions"]:
            for res in item["resolutions"][:5]:  # Show first 5
                display = (
                    f"{res['skill_name']} ({res['parameter']})"
                    if res["parameter"]
                    else res["skill_name"]
                )
                category = f" [{res['resolution_category']}]" if res["resolution_category"] else ""
                logger.info(f"    - {display}{category}")

            if len(item["resolutions"]) > 5:
                logger.info(f"    ... and {len(item['resolutions']) - 5} more")
