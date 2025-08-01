from utils.json_manager import JsonManager
import os

SKILLS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "skills", "skills.json"))

import re

class SkillManager(JsonManager):
    def __init__(self):
        super().__init__(SKILLS_PATH)

    def validate(self, skill):
        required = ["name", "main_category", "sub_category", "description", "skill_type"]
        for key in required:
            if not skill.get(key):
                return False
        return True

    def serialize_skill(self, ui_data):
        """
        UI adatokból (SkillEditor) készít menthető skill dict-et.
        """
        # level_six_available lehet bool vagy BooleanVar, mindig bool-t írjunk ki
        level_six_available = ui_data.get("level_six_available", True)
        if hasattr(level_six_available, 'get'):
            level_six_available = bool(level_six_available.get())
        skill = {
            "name": ui_data["name"],
            "main_category": ui_data["main_category"],
            "sub_category": ui_data["sub_category"],
            "description": ui_data["description"],
            "acquisition_method": ui_data.get("acquisition_method", ""),
            "acquisition_difficulty": ui_data.get("acquisition_difficulty", ""),
            "skill_type": ui_data["skill_type"],
            "kp_per_3_percent": ui_data.get("kp_per_3_percent", None),
            "kp_costs": ui_data.get("kp_costs", {}),
            "level_descriptions": ui_data.get("level_descriptions", {}),
            "prerequisites": ui_data.get("prerequisites", {}),
            "is_parametric": ui_data.get("is_parametric", False),
            "parameter": ui_data.get("parameter", ""),
            # ÚJ: 6. szint elérhetőség
            "level_six_available": level_six_available
        }
        # Tisztítsuk a paramétert
        if skill["is_parametric"] and skill["parameter"]:
            m = re.match(r"(.+?)(?: \((.+?)\))?$", skill["name"])
            base_name = m.group(1) if m else skill["name"]
            skill["name"] = base_name
        return skill

    def deserialize_skill(self, skill):
        """
        Skill dict-ből UI adatok (SkillEditor) generálása.
        """
        ui_data = {
            "name": skill.get("name", ""),
            "main_category": skill.get("main_category", ""),
            "sub_category": skill.get("sub_category", ""),
            "description": skill.get("description", ""),
            "acquisition_method": skill.get("acquisition_method", ""),
            "acquisition_difficulty": skill.get("acquisition_difficulty", ""),
            "skill_type": skill.get("skill_type", "%"),
            "kp_per_3_percent": skill.get("kp_per_3_percent", ""),
            "kp_costs": skill.get("kp_costs", {}),
            "level_descriptions": skill.get("level_descriptions", {}),
            "prerequisites": skill.get("prerequisites", {}),
            "is_parametric": skill.get("is_parametric", False),
            "parameter": skill.get("parameter", ""),
            # ÚJ: 6. szint elérhetőség
            "level_six_available": skill.get("level_six_available", True)
        }
        return ui_data

    def prereq_to_string(self, prereq_vars):
        """
        Előfeltételek (prereq_vars) -> menthető dict (stringekkel)
        """
        result = {}
        for i in range(6):
            stat_list = []
            skill_list = []
            for prereq in prereq_vars[i]:
                if prereq["type"] == "stat":
                    stat = prereq["name_var"].get()
                    value = prereq["value_var"].get()
                    if stat and value:
                        stat_list.append(f"{stat} {value}+")
                elif prereq["type"] == "skill":
                    skillname = prereq["name_var"].get()
                    level = prereq["level_var"].get()
                    param = prereq.get("param_var", None)
                    param_val = param.get() if param is not None else ""
                    m = re.match(r"(.+?)(?: \((.+?)\))?$", skillname)
                    base_name = m.group(1) if m else skillname
                    param_in_name = m.group(2) if m and m.group(2) else ""
                    if param_val:
                        display_text = f"{base_name} ({param_val})"
                    elif param_in_name:
                        display_text = f"{base_name} ({param_in_name})"
                    else:
                        display_text = base_name
                    if skillname and level:
                        skill_list.append(f"{display_text} {level}. szint")
            if stat_list or skill_list:
                result[str(i+1)] = {"képesség": stat_list, "képzettség": skill_list}
        return result

    def prereq_from_string(self, prerequisites):
        """
        Mentett dictből (stringek) -> UI prereq_vars (list of dicts)
        """
        prereq_vars = [[] for _ in range(6)]
        for idx in range(6):
            prereq = prerequisites.get(str(idx+1), {})
            # Tulajdonságok
            for stat_str in prereq.get("képesség", []):
                parts = stat_str.split()
                if len(parts) >= 2:
                    prereq_vars[idx].append({
                        "type": "stat",
                        "name_var": parts[0],
                        "value_var": parts[1].replace("+", "")
                    })
            # Képzettségek
            for skill_str in prereq.get("képzettség", []):
                m = re.match(r"(.+?)(?: \((.+?)\))? (\d+)\. szint", skill_str)
                if m:
                    skillname = m.group(1)
                    param = m.group(2) or ""
                    level = m.group(3)
                    prereq_vars[idx].append({
                        "type": "skill",
                        "name_var": skillname,
                        "level_var": level,
                        "param_var": param
                    })
        return prereq_vars
