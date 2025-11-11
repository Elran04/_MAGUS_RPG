"""Skills Repository - Loads and caches skill metadata from SQLite DB.

Provides id -> name lookup for skills shown in UI components.
Falls back gracefully if DB or table unavailable.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from logger.logger import get_logger

logger = get_logger(__name__)


class SkillsRepository:
    """Repository for skill data access.

    Usage:
        repo = SkillsRepository()
        name = repo.get_skill_name("two_handed_sword")
    """

    def __init__(self, db_path: Path | None = None):
        self._db_path = db_path or Path("Gamemaster_tools/data/skills/skills_data.db")
        self._cache: dict[str, str] | None = None
        self._initialized = False

    def _ensure_loaded(self) -> None:
        """Load skill names from DB once. Safe to call multiple times."""
        if self._initialized:
            return
        self._initialized = True
        self._cache = {}

        if not self._db_path.exists():
            logger.warning(f"Skills DB not found at {self._db_path}, using fallback formatting.")
            return
        try:
            conn = sqlite3.connect(self._db_path)
            cur = conn.cursor()

            # Try common table name candidates
            candidates = [
                "skills",
                "skill",
                "skill_defs",
                "skills_defs",
                "skill_names",
                "skill_catalog",
            ]
            table_found = None
            for cand in candidates:
                try:
                    cur.execute(f"PRAGMA table_info({cand})")
                    cols = cur.fetchall()
                    if cols:
                        # Look for probable id/name columns
                        col_names = [c[1].lower() for c in cols]
                        if any(cn == "id" or cn.endswith("_id") for cn in col_names) and any(
                            cn == "name" or cn.endswith("_name") for cn in col_names
                        ):
                            table_found = cand
                            break
                except Exception:
                    continue

            if not table_found:
                logger.warning("No suitable skills table discovered; falling back to formatting.")
                conn.close()
                return

            # Fetch rows
            try:
                cur.execute(f"SELECT * FROM {table_found}")
                rows = cur.fetchall()
                # Map columns
                cur.execute(f"PRAGMA table_info({table_found})")
                cols = cur.fetchall()
                name_idx = None
                id_idx = None
                for col in cols:
                    cname = col[1].lower()
                    if cname == "id" or cname.endswith("_id"):
                        id_idx = col[0]
                    if cname == "name" or cname.endswith("_name"):
                        name_idx = col[0]
                if id_idx is None or name_idx is None:
                    logger.warning(
                        "Could not detect id/name columns; fallback formatting will be used."
                    )
                else:
                    for r in rows:
                        try:
                            sid = str(r[id_idx])
                            sname = str(r[name_idx])
                            self._cache[sid] = sname
                        except Exception:
                            continue
                    logger.info(
                        f"Loaded {len(self._cache)} skill names from '{table_found}' table."
                    )
            finally:
                conn.close()
        except Exception as e:
            logger.exception(f"Failed loading skills DB: {e}")

    def get_skill_name(self, skill_id: str) -> str:
        """Return human-readable skill name given an id."""
        self._ensure_loaded()
        if self._cache and skill_id in self._cache:
            return self._cache[skill_id]
        # Fallback formatting
        return skill_id.replace("_", " ").title()

    def clear_cache(self) -> None:
        """Clear the loaded cache for testing or reload scenarios."""
        self._cache = None
        self._initialized = False
        logger.debug("Skills cache cleared")
