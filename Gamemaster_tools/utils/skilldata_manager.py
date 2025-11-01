import os
import re
import sqlite3

DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "skills", "skills_data.db")
)
DESC_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "skills", "descriptions")
)


class SkillManager:
    def load_placeholders(self):
        """
        Betölti a helyfoglaló (placeholder=1) képzettségeket a skills táblából.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT * FROM skills WHERE placeholder=1")
        placeholders = []
        for row in c.fetchall():
            skill = {
                "id": row[0],
                "name": row[1],
                "parameter": row[2],
                "main_category": row[3],
                "sub_category": row[4],
                "acquisition_method": row[5],
                "acquisition_difficulty": row[6],
                "skill_type": row[7],
                "description_file": row[8],
                # Új mező: placeholder
                "placeholder": row[9] if len(row) > 9 else 0,
            }
            # Leírás betöltése .md-ből, ha van
            desc_path = (
                os.path.join(self.desc_dir, skill["description_file"])
                if skill.get("description_file")
                else None
            )
            if desc_path and os.path.exists(desc_path):
                with open(desc_path, encoding="utf-8") as f:
                    skill["description"] = f.read()
            else:
                skill["description"] = ""
            # KP költségek, szintleírások, előfeltételek üresen
            skill["kp_costs"] = {}
            skill["level_descriptions"] = {}
            skill["prerequisites"] = {}
            skill["is_parametric"] = bool(skill["parameter"])
            placeholders.append(skill)
        conn.close()
        return placeholders

    def __init__(self):
        self.db_path = DB_PATH
        self.desc_dir = DESC_DIR

    def delete_skill_by_id(self, skill_id):
        """
        Törli a megadott skill-t és minden hivatkozását az adatbázisból (skills tábla, placeholder mezőtől függetlenül).
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        # Fő skill törlése (normál és placeholder is)
        c.execute("DELETE FROM skills WHERE id=?", (skill_id,))
        # KP költségek törlése
        c.execute("DELETE FROM skill_level_costs WHERE skill_id=?", (skill_id,))
        c.execute("DELETE FROM skill_percent_costs WHERE skill_id=?", (skill_id,))
        # Előfeltételek törlése
        c.execute("DELETE FROM skill_prerequisites_skills WHERE skill_id=?", (skill_id,))
        c.execute("DELETE FROM skill_prerequisites_attributes WHERE skill_id=?", (skill_id,))
        # Más skillek előfeltételeiben hivatkozás törlése
        c.execute("DELETE FROM skill_prerequisites_skills WHERE required_skill_id=?", (skill_id,))
        conn.commit()
        conn.close()
        # Leírás törlése a descriptions mappából
        desc_file = os.path.join(self.desc_dir, f"{skill_id}.md")
        if os.path.exists(desc_file):
            try:
                os.remove(desc_file)
            except Exception as e:
                print(f"Leírás törlése sikertelen: {desc_file}, hiba: {e}")

    def load(self):
        """
        Betölti az összes képzettséget az adatbázisból, minden metaadatot, költséget, előfeltételt.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT * FROM skills")
        skills = []
        for row in c.fetchall():
            skill = {
                "id": row[0],
                "name": row[1],
                "parameter": row[2],
                "main_category": row[3],
                "sub_category": row[4],
                "acquisition_method": row[5],
                "acquisition_difficulty": row[6],
                "skill_type": row[7],
                "description_file": row[8] if row[8] is not None else "",
                "placeholder": row[9] if len(row) > 9 else 0,
            }
            # Csak akkor próbáljuk betölteni a leírást, ha nem placeholder
            if not skill.get("placeholder", 0):
                desc_path = (
                    os.path.join(self.desc_dir, skill["description_file"])
                    if skill["description_file"]
                    else None
                )
                if desc_path and os.path.exists(desc_path):
                    with open(desc_path, encoding="utf-8") as f:
                        skill["description"] = f.read()
                else:
                    skill["description"] = ""
            else:
                skill["description"] = ""
            # KP költségek
            if skill["skill_type"] == 1:
                c.execute(
                    "SELECT level, kp_cost FROM skill_level_costs WHERE skill_id=? ORDER BY level",
                    (skill["id"],),
                )
                skill["kp_costs"] = {str(lvl): kp for lvl, kp in c.fetchall()}
            elif skill["skill_type"] == 2:
                c.execute(
                    "SELECT kp_per_3percent FROM skill_percent_costs WHERE skill_id=?",
                    (skill["id"],),
                )
                res = c.fetchone()
                skill["kp_per_3_percent"] = res[0] if res else None
            # Szintenkénti leírások
            skill["level_descriptions"] = self._load_level_descriptions(skill["description"])
            # Előfeltételek
            skill["prerequisites"] = self._load_prerequisites(c, skill["id"])
            skills.append(skill)
        conn.close()
        return skills

    def _load_level_descriptions(self, desc_text):
        """
        Szintenkénti leírásokat kinyer .md szövegből (## Szint X ...)
        """
        result = {}
        for i in range(1, 7):
            m = re.search(rf"## Szint {i}\\s*(.+?)(?=(## Szint|$))", desc_text, re.DOTALL)
            if m:
                result[str(i)] = m.group(1).strip()
        return result

    def _load_prerequisites(self, c, skill_id):
        """
        Előfeltételek betöltése az adatbázisból szintenként.
        """
        result = {}
        for lvl in range(1, 7):
            # Képességek
            c.execute(
                "SELECT attribute, min_value FROM skill_prerequisites_attributes WHERE skill_id=? AND level=?",
                (skill_id, lvl),
            )
            stat_list = [f"{attr} {min_val}+" for attr, min_val in c.fetchall()]
            # Képzettségek
            c.execute(
                "SELECT required_skill_id, min_level FROM skill_prerequisites_skills WHERE skill_id=? AND level=?",
                (skill_id, lvl),
            )
            skill_list = []
            for req_id, min_lvl in c.fetchall():
                # Skill név/id visszakeresése
                c.execute("SELECT name, parameter FROM skills WHERE id=?", (req_id,))
                res = c.fetchone()
                if res:
                    name, param = res
                    if param:
                        display = f"{name} ({param}) {min_lvl}. szint"
                    else:
                        display = f"{name} {min_lvl}. szint"
                    skill_list.append(display)
            if stat_list or skill_list:
                result[str(lvl)] = {"képesség": stat_list, "képzettség": skill_list}
        return result

    def save(self, skills, valid_levels_dict=None):
        """
        Képzettségek mentése az adatbázisba (tömeges mentés, pl. szerkesztőből).
        valid_levels_dict: {skill_id: [valid_levels]} - csak szint alapú skilleknél szükséges
        """
        for skill in skills:
            if (
                skill.get("placeholder", 0) == 1
                or skill.get("main_category", "") == "Helyfoglaló képzettségek"
            ):
                self._save_placeholder_skill(skill)
            else:
                self._save_skill(skill, valid_levels_dict)

    def _save_placeholder_skill(self, skill):
        """
        Helyfoglaló (placeholder) skill mentése a skills táblába, csak a kötelező mezőkkel, minden más NULL/üres.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            """
            INSERT OR REPLACE INTO skills (id, name, parameter, category, subcategory, acquisition, difficulty, type, description_file, placeholder)
            VALUES (?, ?, ?, ?, ?, NULL, NULL, NULL, NULL, 1)
        """,
            (
                skill.get("id"),
                skill.get("name"),
                skill.get("parameter", ""),
                skill.get("main_category", ""),
                skill.get("sub_category", ""),
            ),
        )
        conn.commit()
        conn.close()

    def _save_skill(self, skill, valid_levels_dict=None):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        # Fő adatok mentése
        c.execute(
            """
            INSERT INTO skills (id, name, parameter, category, subcategory, acquisition, difficulty, type, description_file, placeholder)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                parameter=excluded.parameter,
                category=excluded.category,
                subcategory=excluded.subcategory,
                acquisition=excluded.acquisition,
                difficulty=excluded.difficulty,
                type=excluded.type,
                description_file=excluded.description_file,
                placeholder=excluded.placeholder
        """,
            (
                skill.get("id"),
                skill.get("name"),
                skill.get("parameter", ""),
                skill.get("main_category", ""),
                skill.get("sub_category", ""),
                skill.get("acquisition_method", None),
                skill.get("acquisition_difficulty", None),
                skill.get("skill_type", 1),
                skill.get("description_file", f"{skill.get('id')}.md"),
                skill.get("placeholder", 0),
            ),
        )
        # KP költségek mentése
        kp_costs = skill.get("kp_costs", {})
        if skill.get("skill_type") == 1:
            for lvl, kp in kp_costs.items():
                c.execute(
                    "INSERT INTO skill_level_costs (skill_id, level, kp_cost) VALUES (?, ?, ?) ON CONFLICT(skill_id, level) DO UPDATE SET kp_cost=excluded.kp_cost",
                    (skill.get("id"), int(lvl), int(kp)),
                )
        elif skill.get("skill_type") == 2:
            kp3 = skill.get("kp_per_3_percent")
            if kp3 is not None:
                c.execute(
                    """
                    INSERT OR REPLACE INTO skill_percent_costs (skill_id, kp_per_3percent) VALUES (?, ?)
                """,
                    (skill.get("id"), int(kp3)),
                )
        # Előfeltételek
        for lvl, prereq in skill.get("prerequisites", {}).items():
            # --- Képzettség előfeltételek: először törlés, majd beszúrás ---
            c.execute(
                "DELETE FROM skill_prerequisites_skills WHERE skill_id=? AND level=?",
                (skill.get("id"), int(lvl)),
            )
            skill_prereqs = []
            for skill_str in prereq.get("képzettség", []):
                m = re.match(r"(.+?)(?: \((.+?)\))? (\d+)\. szint", skill_str)
                if m:
                    name = m.group(1)
                    param = m.group(2) or ""
                    min_lvl = int(m.group(3))
                    # Skill id keresése név+param alapján
                    c.execute("SELECT id FROM skills WHERE name=? AND parameter=?", (name, param))
                    res = c.fetchone()
                    req_id = res[0] if res else name
                    skill_prereqs.append((req_id, min_lvl))
            for req_id, min_lvl in skill_prereqs:
                c.execute(
                    "INSERT INTO skill_prerequisites_skills (skill_id, level, required_skill_id, min_level) VALUES (?, ?, ?, ?)",
                    (skill.get("id"), int(lvl), req_id, min_lvl),
                )
            # --- Képesség előfeltételek: először törlés, majd beszúrás ---
            c.execute(
                "DELETE FROM skill_prerequisites_attributes WHERE skill_id=? AND level=?",
                (skill.get("id"), int(lvl)),
            )
            for stat_str in prereq.get("képesség", []):
                parts = stat_str.split()
                if len(parts) == 2 and parts[1].endswith("+"):
                    attr = parts[0]
                    min_val = int(parts[1][:-1])
                    c.execute(
                        "INSERT INTO skill_prerequisites_attributes (skill_id, level, attribute, min_value) VALUES (?, ?, ?, ?)",
                        (skill.get("id"), int(lvl), attr, min_val),
                    )
        # Leírás mentése .md-be
        desc_file = skill.get("description_file", f"{skill.get('id')}.md")
        desc_path = os.path.join(self.desc_dir, desc_file)
        # Ensure the descriptions directory exists
        os.makedirs(self.desc_dir, exist_ok=True)
        with open(desc_path, "w", encoding="utf-8") as f:
            f.write(skill.get("description", ""))
            for lvl, txt in skill.get("level_descriptions", {}).items():
                f.write(f"\n\n## Szint {lvl}\n{txt}")
        conn.commit()
        conn.close()

    def validate(self, skill):
        # Helyfoglaló képzettségnél csak az alap mezők legyenek kötelezőek
        if skill.get("main_category", "") == "Helyfoglaló képzettségek":
            required = ["id", "name", "main_category", "sub_category"]
        else:
            required = ["id", "name", "main_category", "sub_category", "description", "skill_type"]
        for key in required:
            if not skill.get(key):
                return False
        return True

    def serialize_skill(self, ui_data):
        # ...existing code...
        # level_six_available lehet bool vagy BooleanVar, mindig bool-t írjunk ki
        level_six_available = ui_data.get("level_six_available", True)
        if hasattr(level_six_available, "get"):
            level_six_available = bool(level_six_available.get())
        skill = {
            "id": ui_data.get("id", ""),
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
            "level_six_available": level_six_available,
            "description_file": f"{ui_data.get('id','')}.md",
        }
        # Tisztítsuk a paramétert
        if skill["is_parametric"] and skill["parameter"]:
            m = re.match(r"(.+?)(?: \((.+?)\))?$", skill["name"])
            base_name = m.group(1) if m else skill["name"]
            skill["name"] = base_name
        return skill

    def deserialize_skill(self, skill):
        # ...existing code...
        ui_data = {
            "id": skill.get("id", ""),
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
            "level_six_available": skill.get("level_six_available", True),
        }
        return ui_data

    def prereq_to_string(self, prereq_vars):
        # ...existing code...
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
                result[str(i + 1)] = {"képesség": stat_list, "képzettség": skill_list}
        return result

    def prereq_from_string(self, prerequisites):
        # ...existing code...
        prereq_vars: list[list[dict]] = [[] for _ in range(6)]
        for idx in range(6):
            prereq = prerequisites.get(str(idx + 1), {})
            # Tulajdonságok
            for stat_str in prereq.get("képesség", []):
                parts = stat_str.split()
                if len(parts) >= 2:
                    prereq_vars[idx].append(
                        {
                            "type": "stat",
                            "name_var": parts[0],
                            "value_var": parts[1].replace("+", ""),
                        }
                    )
            # Képzettségek
            for skill_str in prereq.get("képzettség", []):
                m = re.match(r"(.+?)(?: \((.+?)\))? (\d+)\. szint", skill_str)
                if m:
                    skillname = m.group(1)
                    param = m.group(2) or ""
                    level = m.group(3)
                    prereq_vars[idx].append(
                        {
                            "type": "skill",
                            "name_var": skillname,
                            "level_var": level,
                            "param_var": param,
                        }
                    )
        return prereq_vars
