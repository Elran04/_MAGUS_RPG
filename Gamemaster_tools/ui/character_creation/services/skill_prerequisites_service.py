"""
Skill Prerequisites Checker
Handles prerequisite validation for skills.
"""

import sqlite3
from typing import Any

from utils.log.logger import get_logger

logger = get_logger(__name__)


class SkillPrerequisiteChecker:
    """Service class for checking skill prerequisites."""

    def __init__(self, skill_db_service: Any, placeholder_mgr: Any | None = None) -> None:
        """
        Args:
            skill_db_service: SkillDatabaseService instance for DB access
            placeholder_mgr: Optional PlaceholderManager for resolving placeholder prerequisites
        """
        self.skill_db_service = skill_db_service
        self.placeholder_mgr = placeholder_mgr

    def check_prerequisites(
        self,
        skill_id: str,
        req_level: int,
        req_percent: int,
        current_skills: dict[str, dict[str, Any]],
        attributes: dict[str, int],
    ) -> tuple[bool, list[str]]:
        """Check attribute and skill prerequisites for a concrete skill at a given target level/percent.

        Args:
            skill_id: The skill to check prerequisites for
            req_level: Required level for the skill
            req_percent: Required percentage for the skill
            current_skills: Dict mapping skill_id to {"level": int, "%": int}
            attributes: Dict mapping attribute name to value

        Returns:
            Tuple of (ok: bool, reasons: list[str]) listing unmet requirements.
        """
        reasons = []
        try:
            with sqlite3.connect(self.skill_db_service.get_db_path("skill")) as sconn:
                max_check_level = max(1, int(req_level or 0))

                # Check attribute prerequisites
                reasons.extend(
                    self._check_attribute_prerequisites(
                        sconn, skill_id, max_check_level, attributes
                    )
                )

                # Check skill prerequisites
                reasons.extend(
                    self._check_skill_prerequisites(
                        sconn, skill_id, max_check_level, current_skills
                    )
                )

        except Exception as e:
            logger.error(f"Prereq check error: {e}", exc_info=True)

        return (len(reasons) == 0, reasons)

    def _check_attribute_prerequisites(
        self,
        conn: sqlite3.Connection,
        skill_id: str,
        max_check_level: int,
        attributes: dict[str, int],
    ) -> list[str]:
        """Check attribute prerequisites for a skill."""
        reasons = []
        rows = conn.execute(
            "SELECT attribute, min_value, level FROM skill_prerequisites_attributes "
            "WHERE skill_id=? ORDER BY level",
            (skill_id,),
        ).fetchall()

        for attr, min_val, lvl in rows:
            if lvl and int(lvl) > max_check_level:
                continue
            current_val = attributes.get(attr)
            if current_val is None or int(current_val) < int(min_val):
                reasons.append(
                    f"Képesség: {attr} {min_val}+ (most: {current_val if current_val is not None else '-'})"
                )
        return reasons

    def _check_skill_prerequisites(
        self,
        conn: sqlite3.Connection,
        skill_id: str,
        max_check_level: int,
        current_skills: dict[str, dict[str, Any]],
    ) -> list[str]:
        """Check skill prerequisites for a skill."""
        reasons = []
        srows = conn.execute(
            "SELECT required_skill_id, min_level, level FROM skill_prerequisites_skills "
            "WHERE skill_id=? ORDER BY level",
            (skill_id,),
        ).fetchall()

        for req_id, min_lvl, lvl in srows:
            if lvl and int(lvl) > max_check_level:
                continue

            # Check if this is a placeholder (OR logic)
            if self.placeholder_mgr and self.placeholder_mgr.is_placeholder(req_id):
                # Get all valid alternatives
                alternatives = self.placeholder_mgr.get_resolutions(req_id)

                # Check if user has ANY of the alternatives at required level
                has_any = False
                for alt in alternatives:
                    alt_id = alt["target_skill_id"]
                    have = current_skills.get(alt_id)

                    if have:
                        # Determine skill type
                        trow = conn.execute(
                            "SELECT type FROM skills WHERE id=?", (alt_id,)
                        ).fetchone()
                        alt_type = trow[0] if trow else 1

                        if alt_type == 1:  # Level-based
                            if int(have.get("level", 0)) >= int(min_lvl or 0):
                                has_any = True
                                break
                        else:  # Percent-based
                            if int(have.get("%", 0)) >= int(min_lvl or 0):
                                has_any = True
                                break

                # If user doesn't have ANY alternative, add to reasons
                if not has_any:
                    reasons.append(self._format_skill_req(req_id, min_lvl, conn))
            else:
                # Regular (non-placeholder) prerequisite
                # Determine required skill type
                trow = conn.execute("SELECT type FROM skills WHERE id=?", (req_id,)).fetchone()
                req_type = trow[0] if trow else 1

                have = current_skills.get(req_id)
                if not have:
                    reasons.append(self._format_skill_req(req_id, min_lvl, conn))
                else:
                    if req_type == 1:  # Level-based
                        if int(have.get("level", 0)) < int(min_lvl or 0):
                            reasons.append(
                                self._format_skill_req(req_id, min_lvl, conn, have.get("level"))
                            )
                    else:  # Percent-based
                        if int(have.get("%", 0)) < int(min_lvl or 0):
                            reasons.append(
                                self._format_skill_req(
                                    req_id, min_lvl, conn, have.get("%"), percent=True
                                )
                            )
        return reasons

    @staticmethod
    def _format_skill_req(
        skill_id: str,
        min_lvl: int,
        conn: sqlite3.Connection,
        have_val: Any = None,
        percent: bool = False,
    ) -> str:
        """Format a skill requirement message."""
        name_row = conn.execute(
            "SELECT name, parameter FROM skills WHERE id=?", (skill_id,)
        ).fetchone()

        if name_row:
            name, param = name_row
            base = f"{name}{f' ({param})' if param else ''}"
        else:
            base = str(skill_id)

        if percent:
            return f"Képzettség: {base} {int(min_lvl)}%+ (most: {have_val if have_val is not None else '-'}%)"
        else:
            return f"Képzettség: {base} {int(min_lvl)}. szint (most: {have_val if have_val is not None else '-'})"
