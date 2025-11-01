"""
Skill Prerequisites Checker
Handles prerequisite validation for skills.
"""
import sqlite3
from typing import Any


class SkillPrerequisiteChecker:
    """Helper class for checking skill prerequisites."""

    def __init__(self, skill_db_helper):
        """
        Args:
            skill_db_helper: SkillDatabaseHelper instance for DB access
        """
        self.db_helper = skill_db_helper

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
            with sqlite3.connect(self.db_helper.get_db_path("skill")) as sconn:
                max_check_level = max(1, int(req_level or 0))
                
                # Check attribute prerequisites
                reasons.extend(self._check_attribute_prerequisites(
                    sconn, skill_id, max_check_level, attributes
                ))
                
                # Check skill prerequisites
                reasons.extend(self._check_skill_prerequisites(
                    sconn, skill_id, max_check_level, current_skills
                ))
                
        except Exception as e:
            print(f"Prereq check error: {e}")
            
        return (len(reasons) == 0, reasons)

    def _check_attribute_prerequisites(
        self,
        conn,
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
        conn,
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
                            self._format_skill_req(
                                req_id, min_lvl, conn, have.get("level")
                            )
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
        skill_id: str, min_lvl: int, conn, have_val: Any = None, percent: bool = False
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
