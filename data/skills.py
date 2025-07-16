import json
import os

SKILLS_PATH = os.path.join(os.path.dirname(__file__), "skills.json")

def load_skills():
    if not os.path.exists(SKILLS_PATH):
        return []
    try:
        with open(SKILLS_PATH, "r", encoding="utf-8") as f:
            data = f.read().strip()
            if not data:
                return []
            return json.loads(data)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def get_skill_by_name(name):
    skills = load_skills()
    for skill in skills:
        if skill["name"].lower() == name.lower():
            return skill
    return None