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

def save_skills(skills):
    with open(SKILLS_PATH, "w", encoding="utf-8") as f:
        json.dump(skills, f, ensure_ascii=False, indent=2)

def validate_skill(skill):
    # Minimális validáció: név, kategória, leírás, típus
    required = ["name", "main_category", "sub_category", "description", "skill_type"]
    for key in required:
        if not skill.get(key):
            return False
    # További validációk ide jöhetnek
    return True