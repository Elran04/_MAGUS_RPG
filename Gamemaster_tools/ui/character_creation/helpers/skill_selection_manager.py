"""
Skill Selection Manager
Centralizes skill state and KP spending logic during character creation.
"""

import sqlite3
from typing import Any

from ui.character_creation.helpers.skill_db_helper import SkillDatabaseHelper
from ui.character_creation.helpers.skill_prerequisites import SkillPrerequisiteChecker
from utils.log.logger import get_logger

logger = get_logger(__name__)


class SkillSelectionManager:
    """Manages character skill state and KP spending during creation."""

    def __init__(
        self,
        db_helper: SkillDatabaseHelper,
        prereq_checker: SkillPrerequisiteChecker,
        kp_total: int,
        kp_from_intelligence: int = 0,
        kp_from_dexterity: int = 0,
    ):
        """
        Initialize skill selection manager.

        Args:
            db_helper: Database helper for skill queries
            prereq_checker: Prerequisite checker
            kp_total: Total KP available from class (base + per level)
            kp_from_intelligence: Bonus KP from Intelligence
            kp_from_dexterity: Bonus KP from Dexterity
        """
        self.db_helper = db_helper
        self.prereq_checker = prereq_checker
        self.kp_base = kp_total
        self.kp_intelligence = kp_from_intelligence
        self.kp_dexterity = kp_from_dexterity
        self.kp_spent = 0

        # Class/spec mandatory skills (from DB) - fixed, not upgradeable in creation
        self.mandatory_skills: dict[str, dict[str, Any]] = {}  # skill_id -> {level, %, source}

        # User-learned skills (not from class)
        self.learned_skills: dict[str, dict[str, Any]] = {}  # skill_id -> {level, %, kp_cost}

        # User-upgraded skills (increase level/% of mandatory skills)
        self.upgrades: dict[str, dict[str, Any]] = {}  # skill_id -> {from_level, to_level, kp_cost}

    def set_mandatory_skills(self, skills: dict[str, dict[str, Any]]):
        """
        Set mandatory skills from class/spec.

        Args:
            skills: Dict of skill_id -> {level, %, source}
        """
        self.mandatory_skills = dict(skills)

    def get_kp_total(self) -> int:
        """Get total KP available (base + bonuses)."""
        return self.kp_base + self.kp_intelligence + self.kp_dexterity

    def get_kp_remaining(self) -> int:
        """Get remaining unspent KP."""
        return self.get_kp_total() - self.kp_spent

    def get_kp_breakdown(self) -> dict[str, int]:
        """Get detailed KP breakdown."""
        return {
            "base": self.kp_base,
            "intelligence": self.kp_intelligence,
            "dexterity": self.kp_dexterity,
            "total": self.get_kp_total(),
            "spent": self.kp_spent,
            "remaining": self.get_kp_remaining(),
        }

    def can_learn_skill(
        self, skill_id: str, level: int, percent: int, current_skills: dict[str, dict]
    ) -> tuple[bool, str, int]:
        """
        Check if a skill can be learned.

        Args:
            skill_id: Skill ID to learn
            level: Desired level (for level-based skills)
            percent: Desired percent (for percent-based skills)
            current_skills: Current skill map (mandatory + learned)

        Returns:
            (can_learn, reason, kp_cost)
        """
        # Check if already have this skill
        if skill_id in self.mandatory_skills:
            return False, "Ezt a képzettséget már megkaptad a kasztodtól", 0

        if skill_id in self.learned_skills:
            return False, "Ezt a képzettséget már megtanultad", 0

        # Calculate KP cost
        try:
            kp_cost = int(self.db_helper.calc_kp_cost(skill_id, level if level else None, percent if percent else None))
        except Exception as e:
            logger.error(f"Error calculating KP cost for {skill_id}: {e}", exc_info=True)
            return False, "Hiba a KP költség számításakor", 0

        if kp_cost == 0 or str(kp_cost) == "?":
            return False, "Nem lehet kiszámítani a KP költséget", 0

        # Check if affordable
        if kp_cost > self.get_kp_remaining():
            return False, f"Nincs elég KP (szükséges: {kp_cost}, elérhető: {self.get_kp_remaining()})", kp_cost

        # Check prerequisites (without this skill in the map yet)
        try:
            attributes = {}  # Prerequisites will be checked with full character attributes later
            ok, reasons = self.prereq_checker.check_prerequisites(
                skill_id, level if level else 0, percent if percent else 0, current_skills, attributes
            )
            if not ok:
                return False, "Előfeltételek nem teljesülnek: " + "; ".join(reasons), kp_cost
        except Exception as e:
            logger.error(f"Error checking prerequisites for {skill_id}: {e}", exc_info=True)
            return False, "Hiba az előfeltételek ellenőrzésekor", kp_cost

        return True, "OK", kp_cost

    def learn_skill(self, skill_id: str, level: int, percent: int, kp_cost: int) -> bool:
        """
        Learn a new skill and deduct KP.

        Args:
            skill_id: Skill ID
            level: Level (for level-based skills)
            percent: Percent (for percent-based skills)
            kp_cost: KP cost (pre-calculated)

        Returns:
            True if successful
        """
        if kp_cost > self.get_kp_remaining():
            logger.warning(f"Not enough KP to learn {skill_id}")
            return False

        self.learned_skills[skill_id] = {
            "level": level if level else 0,
            "%": percent if percent else 0,
            "kp_cost": kp_cost,
        }
        self.kp_spent += kp_cost
        logger.info(f"Learned skill {skill_id} for {kp_cost} KP")
        return True

    def unlearn_skill(self, skill_id: str) -> bool:
        """
        Remove a learned skill and refund KP.

        Args:
            skill_id: Skill ID to remove

        Returns:
            True if successful
        """
        if skill_id not in self.learned_skills:
            return False

        skill = self.learned_skills.pop(skill_id)
        self.kp_spent -= skill["kp_cost"]
        logger.info(f"Unlearned skill {skill_id}, refunded {skill['kp_cost']} KP")
        return True

    def get_all_skills(self) -> dict[str, dict[str, Any]]:
        """
        Get combined skill map (mandatory + learned).

        Returns:
            Dict of skill_id -> {level, %, source/kp_cost}
        """
        combined = {}
        
        # Add mandatory skills
        for skill_id, data in self.mandatory_skills.items():
            combined[skill_id] = {
                "level": data.get("level", 0),
                "%": data.get("%", 0),
                "source": data.get("source", "Kaszt"),
                "is_mandatory": True,
            }
        
        # Add learned skills
        for skill_id, data in self.learned_skills.items():
            combined[skill_id] = {
                "level": data.get("level", 0),
                "%": data.get("%", 0),
                "kp_cost": data.get("kp_cost", 0),
                "is_mandatory": False,
            }
        
        return combined

    def get_learned_skills_for_save(self) -> list[dict[str, Any]]:
        """
        Get learned skills formatted for character save.

        Returns:
            List of skill dicts with id, name, level, %
        """
        skills = []
        try:
            with sqlite3.connect(self.db_helper.get_db_path("skill")) as sconn:
                for skill_id, data in self.learned_skills.items():
                    row = sconn.execute(
                        "SELECT name, parameter FROM skills WHERE id=?", (skill_id,)
                    ).fetchone()
                    if not row:
                        continue
                    name, parameter = row
                    display = f"{name} ({parameter})" if parameter else name
                    skills.append({
                        "id": skill_id,
                        "Képzettség": display,
                        "Szint": data.get("level", 0),
                        "%": data.get("%", 0),
                        "KP": data.get("kp_cost", 0),
                        "Forrás": "Tanult",
                    })
        except Exception as e:
            logger.error(f"Error getting learned skills for save: {e}", exc_info=True)
        
        return skills

    def reset(self):
        """Reset all learned skills and refund KP."""
        self.learned_skills.clear()
        self.upgrades.clear()
        self.kp_spent = 0
        logger.info("Reset all skill selections")
