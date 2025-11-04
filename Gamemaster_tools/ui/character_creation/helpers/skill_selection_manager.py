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
        # Store both current and baseline values so we can allow decreasing
        # back to the original mandatory minimum, but not below.
        normalized: dict[str, dict[str, Any]] = {}
        for skill_id, data in skills.items():
            base_level = int(data.get("level", 0) or 0)
            base_percent = int(data.get("%", 0) or 0)
            normalized[skill_id] = {
                "level": base_level,
                "%": base_percent,
                "source": data.get("source", data.get("Forrás", "Kaszt")),
                # Baseline minima recorded separately
                "base_level": base_level,
                "base_percent": base_percent,
                # KP spent in this step on increasing this mandatory skill
                "kp_cost": int(data.get("kp_cost", 0) or 0),
            }
        self.mandatory_skills = normalized

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
        self,
        skill_id: str,
        level: int,
        percent: int,
        current_skills: dict[str, dict],
        attributes: dict | None = None,
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
            attrs = attributes or {}
            ok, reasons = self.prereq_checker.check_prerequisites(
                skill_id, level if level else 0, percent if percent else 0, current_skills, attrs
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

    def increase_skill(self, skill_id: str) -> tuple[bool, str]:
        """
        Increase a skill by one tier (level or 3%).
        Handles KP deduction and state update.

        Args:
            skill_id: Skill ID to increase

        Returns:
            (success, error_message)
        """
        # Determine current and next values
        if skill_id in self.mandatory_skills:
            data = self.mandatory_skills[skill_id]
            is_mandatory = True
        elif skill_id in self.learned_skills:
            data = self.learned_skills[skill_id]
            is_mandatory = False
        else:
            return False, "Képzettség nem található"

        current_level = int(data.get("level", 0) or 0)
        current_percent = int(data.get("%", 0) or 0)

        # Get skill type
        info = self.db_helper.get_skill_info(skill_id)
        if not info:
            return False, "Képzettség típus nem található"
        _, _, skill_type = info

        if skill_type == 1:  # Level-based
            next_level = current_level + 1
            next_percent = 0
        else:  # Percent-based
            next_level = 0
            next_percent = current_percent + 3

        # Calculate KP cost delta
        try:
            if skill_type == 1:
                # Level-based: DB returns the per-level cost for that level.
                step_cost_str = self.db_helper.calc_kp_cost(skill_id, next_level, None)
                step_cost = int(step_cost_str) if step_cost_str and step_cost_str != "?" else 0
                delta = step_cost
            else:
                # Percent-based: DB returns cumulative cost up to that percent.
                old_cum_str = self.db_helper.calc_kp_cost(skill_id, None, current_percent) if current_percent > 0 else "0"
                new_cum_str = self.db_helper.calc_kp_cost(skill_id, None, next_percent)
                old_cum = int(old_cum_str) if old_cum_str and old_cum_str != "?" else 0
                new_cum = int(new_cum_str) if new_cum_str and new_cum_str != "?" else 0
                delta = new_cum - old_cum
        except (ValueError, TypeError):
            return False, "Nem lehet kiszámítani a KP költséget"

        if delta <= 0:
            return False, "Maximális szint elérve"
        if delta > self.get_kp_remaining():
            return False, f"Nincs elég KP (szükséges: {delta})"

        # Update state
        if is_mandatory:
            self.mandatory_skills[skill_id]["level"] = next_level
            self.mandatory_skills[skill_id]["%"] = next_percent
            current_kp = self.mandatory_skills[skill_id].get("kp_cost", 0)
            self.mandatory_skills[skill_id]["kp_cost"] = current_kp + delta
        else:
            self.learned_skills[skill_id]["level"] = next_level
            self.learned_skills[skill_id]["%"] = next_percent
            current_kp = self.learned_skills[skill_id].get("kp_cost", 0)
            self.learned_skills[skill_id]["kp_cost"] = current_kp + delta

        self.kp_spent += delta
        logger.info(f"Increased skill {skill_id} to L{next_level}/{next_percent}% for {delta} KP")
        return True, ""

    def decrease_skill(self, skill_id: str) -> tuple[bool, str]:
        """
        Decrease a skill by one tier (level or 3%).
        Handles KP refund and state update. Removes learned skills at minimum.

        Args:
            skill_id: Skill ID to decrease

        Returns:
            (success, error_message)
        """
        # Determine current values
        if skill_id in self.mandatory_skills:
            data = self.mandatory_skills[skill_id]
            is_mandatory = True
            mandatory_level = int(data.get("level", 0) or 0)
            mandatory_percent = int(data.get("%", 0) or 0)
        elif skill_id in self.learned_skills:
            data = self.learned_skills[skill_id]
            is_mandatory = False
            mandatory_level = 0
            mandatory_percent = 0
        else:
            return False, "Képzettség nem található"

        current_level = int(data.get("level", 0) or 0)
        current_percent = int(data.get("%", 0) or 0)

        # Get skill type
        info = self.db_helper.get_skill_info(skill_id)
        if not info:
            return False, "Képzettség típus nem található"
        _, _, skill_type = info

        if skill_type == 1:  # Level-based
            new_level = current_level - 1
            new_percent = 0
        else:  # Percent-based
            new_level = 0
            new_percent = current_percent - 3

        # For learned skills, remove if at minimum
        if not is_mandatory:
            if (skill_type == 1 and new_level < 1) or (skill_type == 2 and new_percent < 3):
                old_kp = int(data.get("kp_cost", 0) or 0)
                self.kp_spent -= old_kp
                del self.learned_skills[skill_id]
                logger.info(f"Removed learned skill {skill_id}, refunded {old_kp} KP")
                return True, ""

        # For mandatory skills, cannot go below mandatory level
        if is_mandatory:
            base_level = int(data.get("base_level", mandatory_level) or 0)
            base_percent = int(data.get("base_percent", mandatory_percent) or 0)
            if (skill_type == 1 and new_level < base_level) or (skill_type == 2 and new_percent < base_percent):
                return False, "Nem lehet a kötelező szint alá csökkenteni"

        # Calculate KP refund for the step being undone
        try:
            if skill_type == 1:
                # Level-based: refund the cost of the current level
                step_cost_str = self.db_helper.calc_kp_cost(skill_id, current_level, None)
                refund = int(step_cost_str) if step_cost_str and step_cost_str != "?" else 0
            else:
                # Percent-based: refund the difference in cumulative cost
                old_cum_str = self.db_helper.calc_kp_cost(skill_id, None, current_percent) if current_percent > 0 else "0"
                new_cum_str = self.db_helper.calc_kp_cost(skill_id, None, new_percent) if new_percent > 0 else "0"
                old_cum = int(old_cum_str) if old_cum_str and old_cum_str != "?" else 0
                new_cum = int(new_cum_str) if new_cum_str and new_cum_str != "?" else 0
                refund = old_cum - new_cum
        except (ValueError, TypeError):
            return False, "Nem lehet kiszámítani a KP visszatérítést"

        # Update state
        if is_mandatory:
            self.mandatory_skills[skill_id]["level"] = new_level
            self.mandatory_skills[skill_id]["%"] = new_percent
            current_kp = self.mandatory_skills[skill_id].get("kp_cost", 0)
            self.mandatory_skills[skill_id]["kp_cost"] = max(0, current_kp - refund)
        else:
            self.learned_skills[skill_id]["level"] = new_level
            self.learned_skills[skill_id]["%"] = new_percent
            current_kp = self.learned_skills[skill_id].get("kp_cost", 0)
            self.learned_skills[skill_id]["kp_cost"] = max(0, current_kp - refund)

        self.kp_spent -= refund
        logger.info(f"Decreased skill {skill_id} to L{new_level}/{new_percent}%, refunded {refund} KP")
        return True, ""

    def reset(self):
        """Reset all learned skills and refund KP."""
        self.learned_skills.clear()
        self.upgrades.clear()
        self.kp_spent = 0
        logger.info("Reset all skill selections")
