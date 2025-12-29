import sqlite3

import pytest

from utils.placeholder_manager import PlaceholderManager


def create_skills_table(db_path):
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE skills (
                id TEXT PRIMARY KEY,
                name TEXT,
                parameter TEXT,
                placeholder INTEGER
            )
            """
        )
        conn.commit()


def test_add_get_and_remove_resolution(tmp_path):
    db = tmp_path / "skills.db"
    create_skills_table(db)
    with sqlite3.connect(db) as conn:
        conn.executemany(
            "INSERT INTO skills(id, name, parameter, placeholder) VALUES (?, ?, ?, ?)",
            [
                ("p_placeholder", "Placeholder", None, 1),
                ("skill_light", "Light Blade", "", 0),
                ("skill_heavy", "Heavy Axe", "", 0),
            ],
        )
        conn.commit()

    mgr = PlaceholderManager(str(db))

    mgr.add_resolution("p_placeholder", "skill_light", category="light", notes="n1")
    mgr.add_resolution("p_placeholder", "skill_heavy", category="heavy", notes="n2")

    all_res = mgr.get_resolutions("p_placeholder")
    assert {r["target_skill_id"] for r in all_res} == {"skill_light", "skill_heavy"}

    light_only = mgr.get_resolutions("p_placeholder", category="light")
    assert [r["target_skill_id"] for r in light_only] == ["skill_light"]
    assert light_only[0]["resolution_category"] == "light"
    assert light_only[0]["notes"] == "n1"

    mgr.remove_resolution("p_placeholder", "skill_light")
    remaining = mgr.get_resolutions("p_placeholder")
    assert {r["target_skill_id"] for r in remaining} == {"skill_heavy"}


def test_placeholder_queries(tmp_path):
    db = tmp_path / "skills.db"
    create_skills_table(db)
    with sqlite3.connect(db) as conn:
        conn.executemany(
            "INSERT INTO skills(id, name, parameter, placeholder) VALUES (?, ?, ?, ?)",
            [
                ("p1", "Placeholder 1", None, 1),
                ("p2", "Placeholder 2", None, 1),
                ("real", "Real Skill", None, 0),
            ],
        )
        conn.commit()

    mgr = PlaceholderManager(str(db))

    assert mgr.is_placeholder("p1") is True
    assert mgr.is_placeholder("real") is False
    placeholders = mgr.get_all_placeholders()
    assert {p["id"] for p in placeholders} == {"p1", "p2"}