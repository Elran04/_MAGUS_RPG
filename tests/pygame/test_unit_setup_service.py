import pytest

from application.unit_setup_service import UnitSetupService


class DummyRepo:
    def __init__(self, data: dict[str, dict | None]):
        self.data = data

    def load(self, filename: str):
        return self.data.get(filename)


def test_load_character_defaults_missing_sections():
    repo = DummyRepo({"hero.json": {"name": "Hero"}})
    service = UnitSetupService(repo)

    result = service.load_character_with_defaults("hero.json")

    assert result is not None
    assert result["Felszerelés"] == {"items": []}
    assert result["Képzettségek"] == []


def test_load_character_returns_none_when_missing():
    repo = DummyRepo({})
    service = UnitSetupService(repo)

    assert service.load_character_with_defaults("missing.json") is None


def test_extract_inventory_excludes_equipped_and_slotted():
    repo = DummyRepo({})
    service = UnitSetupService(repo)

    char_data = {
        "Felszerelés": {
            "items": [
                {"id": "sword", "qty": 1},
                {"id": "shield", "qty": 1, "slot": "off_hand"},
                {"id": "potion", "qty": 2},
            ]
        },
        "equipment": {"main_hand": "sword", "off_hand": "shield"},
    }

    inventory = service.extract_inventory_from_character(char_data)

    assert inventory == {"potion": 2}


def test_extract_inventory_handles_list_and_aggregates():
    repo = DummyRepo({})
    service = UnitSetupService(repo)

    char_data = {
        "Felszerelés": [
            {"id": "apple"},
            {"id": "apple"},
            {"id": "belt", "slot": "waist"},
        ]
    }

    inventory = service.extract_inventory_from_character(char_data)

    assert inventory == {"apple": 2}


def test_extract_skills_parses_levels_and_logs_invalid(caplog):
    repo = DummyRepo({})
    service = UnitSetupService(repo)

    char_data = {
        "Képzettségek": [
            {"id": "stealth", "Szint": "2"},
            {"id": "archery", "%": "5"},
            {"id": "bad", "Szint": "x"},
        ]
    }

    with caplog.at_level("WARNING"):
        skills = service.extract_skills_from_character(char_data)

    assert skills == {"stealth": 2, "archery": 5}
    assert any("Invalid skill level" in msg for msg in caplog.messages)


def test_prepare_unit_data_combines_extractions():
    char_data = {
        "Felszerelés": {"items": [{"id": "potion", "qty": 1}]},
        "Képzettségek": [{"id": "stealth", "Szint": 1}],
    }
    repo = DummyRepo({"hero.json": char_data})
    service = UnitSetupService(repo)

    result = service.prepare_unit_data("hero.json")

    assert result is not None
    assert result["char_data"]["Felszerelés"]["items"]
    assert result["inventory"] == {"potion": 1}
    assert result["skills"] == {"stealth": 1}