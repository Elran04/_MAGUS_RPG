import pytest
from unittest.mock import MagicMock
from MAGUS_pygame.application.scenario_service import ScenarioService, ScenarioState
from MAGUS_pygame.domain.value_objects import UnitSetup, ScenarioConfig

@pytest.fixture
def mock_repos():
    scenario_repo = MagicMock()
    character_repo = MagicMock()
    sprite_repo = MagicMock()
    scenario_repo.resolve_background.return_value = "bg.jpg"
    scenario_repo.load_scenario.return_value = {
        "spawn_zones": {"team_a": [1,2], "team_b": [3]},
        "name": "test_map",
        "background": "bg.jpg"
    }
    scenario_repo.list_scenarios.return_value = ["test_map"]
    character_repo.exists.return_value = True
    sprite_repo.character_sprite_exists.return_value = True
    return scenario_repo, character_repo, sprite_repo

def test_add_unit_team_size_limit(mock_repos):
    scenario_repo, character_repo, sprite_repo = mock_repos
    service = ScenarioService(scenario_repo, character_repo, sprite_repo)
    service.set_map("test_map")
    # Team A limit is 2
    assert service.add_unit(True, "char1", "sprite1") is True
    assert service.add_unit(True, "char2", "sprite2") is True
    assert service.add_unit(True, "char3", "sprite3") is False  # Exceeds limit
    # Team B limit is 1
    assert service.add_unit(False, "char4", "sprite4") is True
    assert service.add_unit(False, "char5", "sprite5") is False

def test_duplicate_prevention(mock_repos):
    scenario_repo, character_repo, sprite_repo = mock_repos
    service = ScenarioService(scenario_repo, character_repo, sprite_repo, allow_duplicates=False)
    service.set_map("test_map")
    assert service.add_unit(True, "char1", "sprite1") is True
    assert service.add_unit(True, "char1", "sprite1") is False  # Duplicate

def test_missing_character_or_sprite(mock_repos):
    scenario_repo, character_repo, sprite_repo = mock_repos
    character_repo.exists.return_value = False
    sprite_repo.character_sprite_exists.return_value = False
    service = ScenarioService(scenario_repo, character_repo, sprite_repo)
    service.set_map("test_map")
    # Should still add, but log warnings
    assert service.add_unit(True, "char_missing", "sprite_missing") is True

def test_update_unit_and_remove_last(mock_repos):
    scenario_repo, character_repo, sprite_repo = mock_repos
    service = ScenarioService(scenario_repo, character_repo, sprite_repo)
    service.set_map("test_map")
    service.add_unit(True, "char1", "sprite1")
    service.add_unit(True, "char2", "sprite2")
    new_setup = UnitSetup(
        character_file="char_new",
        sprite_file="sprite_new",
        equipment={},
        inventory={},
        skills={},
        facing=0
    )
    service.update_unit(True, 1, new_setup)
    assert service.get_team(True)[1].character_file == "char_new"
    service.remove_last(True)
    assert len(service.get_team(True)) == 1

def test_build_config_validation(mock_repos):
    scenario_repo, character_repo, sprite_repo = mock_repos
    service = ScenarioService(scenario_repo, character_repo, sprite_repo)
    service.set_map("test_map")
    service.add_unit(True, "char1", "sprite1")
    service.add_unit(False, "char2", "sprite2")
    config = service.build_config()
    # ScenarioConfig is a dataclass, but may be a subclass or factory result; check by attribute
    assert hasattr(config, "map_name") and hasattr(config, "team_a") and hasattr(config, "team_b")
    # Missing map
    service2 = ScenarioService(scenario_repo, character_repo, sprite_repo)
    with pytest.raises(ValueError):
        service2.build_config()
    # Missing teams
    service3 = ScenarioService(scenario_repo, character_repo, sprite_repo)
    service3.set_map("test_map")
    with pytest.raises(ValueError):
        service3.build_config()
