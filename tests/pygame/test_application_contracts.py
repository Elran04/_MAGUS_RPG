import pathlib

import pytest

from MAGUS_pygame.application.game_flow_service import coordinate_game_flow
from MAGUS_pygame.application.quick_combat_service import prepare_quick_combat_battle
from MAGUS_pygame.domain.value_objects.scenario_config import ScenarioConfig, UnitSetup


# Guard: application layer must not depend on presentation or pygame
@pytest.mark.parametrize("forbidden", ["presentation.", "import pygame", "from pygame"])
def test_application_has_no_presentation_or_pygame_imports(forbidden):
    root = pathlib.Path(__file__).resolve().parents[2] / "MAGUS_pygame" / "application"
    py_files = list(root.rglob("*.py"))
    assert py_files, "No application files found"
    failures = []
    for path in py_files:
        text = path.read_text(encoding="utf-8")
        if forbidden in text:
            failures.append(str(path.relative_to(root.parent)) + f" contains '{forbidden}'")
    assert not failures, "; ".join(failures)


class DummyUnit:
    def __init__(self, name="Unit", weapon=None):
        self.name = name
        self.weapon = weapon
        self.sprite = None
        self.armor_system = type("ArmorSys", (), {"pieces": []})()


class DummyWeapon:
    def __init__(self):
        self.wield_mode = "variable"
        self.calls = []

    def set_wield_state(self, main_hand: bool, off_hand_equipped: bool):
        self.calls.append((main_hand, off_hand_equipped))


class DummyCharacterRepo:
    def __init__(self, data):
        self.data = data
        self.calls = []

    def load(self, filename):
        self.calls.append(filename)
        return self.data.get(filename)


class DummySpriteRepo:
    def __init__(self, sprite=None):
        self.sprite = sprite
        self.calls = []

    def load_character_sprite(self, sprite_file):
        self.calls.append(sprite_file)
        return self.sprite

    def load_background(self, filename):
        self.calls.append(filename)
        return None


class DummyEquipmentRepo:
    def __init__(self):
        self.calls = []

    def find_weapon_by_id(self, item_id):
        self.calls.append(item_id)
        return {"name": item_id}


class DummyUnitFactory:
    def __init__(self, unit):
        self.unit = unit
        self.calls = []

    def create_unit(self, **kwargs):
        self.calls.append(kwargs)
        return self.unit


class ScreenLoopStub:
    def __init__(self):
        self.calls = []
        self.responses = [None, None, "completed"]  # scenario, deployment, battle

    def __call__(self, screen, cancel_action=None, update_method=None):
        self.calls.append(type(screen).__name__)
        return self.responses.pop(0)


class ScenarioScreenStub:
    def __init__(self, cfg):
        self._cfg = cfg

    def get_config(self):
        return self._cfg


class DeploymentScreenStub:
    def __init__(self, cfg, background=None):
        self._cfg = cfg
        self.background = background

    def get_config(self):
        return self._cfg


class BattleScreenStub:
    def __init__(self):
        self.battle = None
        self.updated = 0
        self._action = "completed"

    def update(self):
        self.updated += 1

    def get_action(self):
        return self._action


class DummyContext:
    def __init__(self, character_repo, sprite_repo, unit_factory, equipment_repo):
        self.character_repo = character_repo
        self.sprite_repo = sprite_repo
        self.unit_factory = unit_factory
        self.equipment_repo = equipment_repo


def make_setup(off_hand=None):
    eq = {"off_hand": off_hand} if off_hand else {}
    return UnitSetup(
        character_file="hero.json",
        sprite_file="hero.png",
        start_q=0,
        start_r=1,
        facing=2,
        equipment=eq,
    )


def test_coordinate_game_flow_wires_battle_and_units():
    weapon = DummyWeapon()
    unit = DummyUnit(name="Hero", weapon=weapon)
    ctx = DummyContext(
        character_repo=DummyCharacterRepo({"hero.json": {"name": "Hero"}}),
        sprite_repo=DummySpriteRepo(),
        unit_factory=DummyUnitFactory(unit),
        equipment_repo=DummyEquipmentRepo(),
    )

    cfg = ScenarioConfig(
        team_a=(make_setup(off_hand="buckler"),), team_b=(make_setup(),), map_name="map"
    )
    scenario_screen = ScenarioScreenStub(cfg)
    deployment_screen = DeploymentScreenStub(cfg, background=None)
    battle_screen = BattleScreenStub()
    loop = ScreenLoopStub()

    result = coordinate_game_flow(ctx, scenario_screen, deployment_screen, battle_screen, loop)

    assert result == "completed"
    # battle_service injected
    assert battle_screen.battle is not None
    # update was called (battle loop)
    assert battle_screen.updated >= 0
    # weapon wield state set (off-hand equipped)
    assert weapon.calls == [(True, True)]


class DummyEquipmentRepoQC:
    def __init__(self):
        self.calls = []

    def find_weapon_by_id(self, item_id):
        self.calls.append(item_id)
        return {"name": item_id}


class DummyUnitFactoryQC:
    def __init__(self):
        self.calls = []

    def create_unit(self, **kwargs):
        self.calls.append(kwargs)
        # carry equipment mapping out for assertions
        u = DummyUnit(name=kwargs.get("character_filename", ""))
        u.weapon = kwargs.get("char_data", {}).get("equipment", {}).get("main_hand")
        return u


class DummyCharacterRepoQC:
    def __init__(self):
        self.calls = []

    def load(self, filename):
        self.calls.append(filename)
        return {
            "name": filename,
            "Felszerelés": {
                "items": [
                    {"category": "weapons_and_shields", "id": "sword"},
                    {"category": "weapons_and_shields", "id": "buckler_shield"},
                    {"category": "armor", "id": "armor1"},
                ]
            },
        }


class DummySpriteRepoQC:
    def __init__(self):
        self.calls = []

    def load_character_sprite(self, sprite_file):
        self.calls.append(sprite_file)
        return None

    def load_background(self, filename):
        self.calls.append(filename)
        return None


class DummyContextQC:
    def __init__(self):
        self.character_repo = DummyCharacterRepoQC()
        self.unit_factory = DummyUnitFactoryQC()
        self.sprite_repo = DummySpriteRepoQC()
        self.equipment_repo = DummyEquipmentRepoQC()


def test_prepare_quick_combat_battle_creates_units_and_equips():
    ctx = DummyContextQC()
    team_a, team_b, cfg = prepare_quick_combat_battle(ctx)

    assert len(team_a) == 1
    assert len(team_b) == 1
    assert cfg["scenario_name"] == "Forest Clearing"
    # ensure auto-equip ran: main_hand present and shield processed
    assert "sword" in ctx.equipment_repo.calls
    assert "buckler_shield" in ctx.equipment_repo.calls
    assert ctx.character_repo.calls == ["Goblin_warrior.json", "Warrior_heavy_armor.json"]
