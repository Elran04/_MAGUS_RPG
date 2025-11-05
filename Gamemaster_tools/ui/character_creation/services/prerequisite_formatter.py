import sqlite3
from typing import Any


class PrerequisiteInfoHelper:
    """
    Centralizes prerequisite text building and checks for skills.
    Wraps DB access through the provided db_helper and uses prereq_checker for actual validation.
    """

    def __init__(self, db_helper, prereq_checker) -> None:
        self.db_helper = db_helper
        self.prereq_checker = prereq_checker

    def get_prerequisite_info(
        self,
        skill_id: str,
        current_level: int,
        current_percent: int,
        current_map: dict[str, dict[str, int]],
        attributes: dict[str, Any],
    ) -> tuple[str, bool]:
        """
        Returns a human-readable prerequisite description and whether they are met.
        """
        try:
            with sqlite3.connect(self.db_helper.get_db_path("skill")) as conn:
                rows = conn.execute(
                    """
                        SELECT required_skill_id, min_level, level
                        FROM skill_prerequisites_skills
                        WHERE skill_id = ?
                    """,
                    (skill_id,),
                ).fetchall()

                if not rows:
                    # No prereqs
                    ok, _ = self.prereq_checker.check_prerequisites(
                        skill_id, current_level, current_percent, current_map, attributes
                    )
                    return "-", ok

                parts: list[str] = []
                for req_skill_id, min_level, for_level in rows:
                    # Only include prereqs up to this level
                    if for_level and int(for_level) > int(current_level or 0):
                        continue
                    req_row = conn.execute(
                        "SELECT name, parameter FROM skills WHERE id=?",
                        (req_skill_id,),
                    ).fetchone()
                    if req_row:
                        req_name, req_param = req_row
                        disp = f"{req_name} ({req_param})" if req_param else req_name
                        txt = disp
                        if min_level:
                            txt += f" - Szint/%: {min_level}"
                        parts.append(txt)

                ok, _ = self.prereq_checker.check_prerequisites(
                    skill_id, int(current_level or 0), int(current_percent or 0), current_map, attributes
                )
                return "; ".join(parts) if parts else "-", ok
        except Exception:
            # On any error, do not block UI
            return "-", True

    def get_missing_prereq_tooltip_for_level(
        self, 
        skill_id: str, 
        target_level: int,
        current_skills: dict[str, dict[str, int]] = None,
        attributes: dict[str, Any] = None
    ) -> str:
        """
        Returns a tooltip text listing prerequisites for a target level.
        If current_skills and attributes are provided, shows which ones are actually missing.
        """
        try:
            with sqlite3.connect(self.db_helper.get_db_path("skill")) as conn:
                rows = conn.execute(
                    """
                        SELECT required_skill_id, min_level, level
                        FROM skill_prerequisites_skills
                        WHERE skill_id = ?
                    """,
                    (skill_id,),
                ).fetchall()
                
                if not rows:
                    return "Előfeltételek nem teljesülnek"

                parts: list[str] = []
                for req_skill_id, min_level, for_level in rows:
                    # Show prerequisites that apply up to and including this level
                    if for_level and int(for_level) > int(target_level or 0):
                        continue
                    
                    req_row = conn.execute(
                        "SELECT name, parameter FROM skills WHERE id=?",
                        (req_skill_id,),
                    ).fetchone()
                    if not req_row:
                        continue
                    
                    req_name, req_param = req_row
                    disp = f"{req_name} ({req_param})" if req_param else req_name
                    
                    # If we have current skills, check if this prereq is met
                    if current_skills is not None:
                        have = current_skills.get(req_skill_id)
                        
                        # Determine the type of the required skill
                        type_row = conn.execute(
                            "SELECT type FROM skills WHERE id=?",
                            (req_skill_id,),
                        ).fetchone()
                        req_skill_type = type_row[0] if type_row else 1
                        
                        if have:
                            have_level = int(have.get("level", 0))
                            have_percent = int(have.get("%", 0))
                            required = int(min_level or 0)
                            
                            # Check based on skill type
                            if req_skill_type == 1:  # Level-based
                                if have_level >= required:
                                    continue  # This prereq is met, don't show it
                                parts.append(f"{disp} - Szükséges: {required}. szint, Van: {have_level}. szint")
                            else:  # Percent-based
                                if have_percent >= required:
                                    continue  # This prereq is met, don't show it
                                parts.append(f"{disp} - Szükséges: {required}%, Van: {have_percent}%")
                        else:
                            # Don't have this skill at all
                            if req_skill_type == 1:
                                parts.append(f"{disp} - Szükséges: {min_level}. szint, Van: Nincs")
                            else:
                                parts.append(f"{disp} - Szükséges: {min_level}%, Van: Nincs")
                    else:
                        # No current skills provided, just list the requirement
                        parts.append(f"{disp} - Szint/%: {min_level}")

                return ("Hiányzó előfeltételek:\n" + "\n".join(parts)) if parts else "Előfeltételek nem teljesülnek"
        except Exception as e:
            return f"Előfeltételek nem teljesülnek: {str(e)}"
