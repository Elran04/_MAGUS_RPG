"""
Placeholder Skill Manager
Manages placeholder skill resolution and tracking during character creation.
"""

from typing import Any


class PlaceholderSkillManager:
    """Manages placeholder skill choices and validation."""

    def __init__(self, placeholder_mgr, prereq_checker):
        """
        Args:
            placeholder_mgr: PlaceholderManager instance
            prereq_checker: SkillPrerequisiteChecker instance
        """
        self.placeholder_mgr = placeholder_mgr
        self.prereq_checker = prereq_checker
        self.placeholder_choices: dict[Any, str] = {}
        self._fixed_skill_ids: set[str] = set()

    def set_fixed_skills(self, skill_ids: set[str]):
        """Set the collection of fixed (non-placeholder) skill IDs."""
        self._fixed_skill_ids = skill_ids

    def compute_taken_skills(self, exclude_instance=None) -> set[str]:
        """Compute set of all skill IDs currently assigned (fixed + placeholder choices).

        Args:
            exclude_instance: Optional instance key to exclude from computation

        Returns:
            Set of skill IDs that are currently taken
        """
        taken = set(self._fixed_skill_ids)
        for ikey, chosen in self.placeholder_choices.items():
            if exclude_instance is not None and ikey == exclude_instance:
                continue
            if chosen:
                taken.add(chosen)
        return taken

    def get_valid_resolutions(
        self,
        placeholder_id: str,
        instance_key: tuple,
        req_level: int,
        req_percent: int,
        current_skills_map: dict[str, dict[str, Any]],
        attributes: dict[str, int],
    ) -> list[dict[str, Any]]:
        """Get list of valid resolution options for a placeholder skill.

        Args:
            placeholder_id: The placeholder skill ID
            instance_key: Unique instance identifier for this placeholder
            req_level: Required level for the skill
            req_percent: Required percentage for the skill
            current_skills_map: Current skill assignments
            attributes: Current character attributes

        Returns:
            List of resolution dicts with keys: skill_name, parameter, target_skill_id
        """
        resolutions = self.placeholder_mgr.get_resolutions(placeholder_id)
        taken = self.compute_taken_skills(exclude_instance=instance_key)
        valid = []

        for res in resolutions:
            tid = res["target_skill_id"]
            if tid in taken:
                continue

            # Check prerequisites for hypothetical selection
            temp_map = dict(current_skills_map)
            temp_map[tid] = {"level": int(req_level or 0), "%": int(req_percent or 0)}
            ok, _ = self.prereq_checker.check_prerequisites(
                tid, int(req_level or 0), int(req_percent or 0), temp_map, attributes
            )
            if ok:
                valid.append(res)

        return valid

    def set_choice(self, instance_key: tuple, chosen_skill_id: str | None):
        """Set or clear a placeholder choice.

        Args:
            instance_key: Unique instance identifier
            chosen_skill_id: Selected skill ID or None to clear
        """
        if chosen_skill_id:
            self.placeholder_choices[instance_key] = chosen_skill_id
        elif instance_key in self.placeholder_choices:
            del self.placeholder_choices[instance_key]

    def get_choice(self, instance_key: tuple) -> str | None:
        """Get the chosen skill ID for a placeholder instance."""
        return self.placeholder_choices.get(instance_key)

    def build_skills_map_from_choices(
        self, fixed_skills: dict[str, dict[str, Any]], all_instances: list[tuple]
    ) -> dict[str, dict[str, Any]]:
        """Build a complete skills map including fixed skills and placeholder choices.

        Args:
            fixed_skills: Dict of fixed skill_id -> {"level": int, "%": int}
            all_instances: List of (skill_id, class_level, req_level, req_percent, from_spec, occurrence) tuples

        Returns:
            Complete skills map
        """
        skills_map = dict(fixed_skills)

        # Add placeholder choices
        for instance_key in all_instances:
            chosen = self.placeholder_choices.get(instance_key)
            if chosen:
                # Extract requirements from instance key
                _, _, req_level, req_percent, _, _ = instance_key
                skills_map[chosen] = {"level": int(req_level or 0), "%": int(req_percent or 0)}

        return skills_map
