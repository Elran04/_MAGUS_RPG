from data.json_manager import JsonManager
import os

SKILLS_PATH = os.path.join(os.path.dirname(__file__), "skills.json")

class SkillManager(JsonManager):
    def __init__(self):
        super().__init__(SKILLS_PATH)

    def validate(self, skill):
        required = ["name", "main_category", "sub_category", "description", "skill_type"]
        for key in required:
            if not skill.get(key):
                return False
        return True
