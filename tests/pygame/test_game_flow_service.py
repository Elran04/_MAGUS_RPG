from types import SimpleNamespace

from application.game_flow_service import _create_units_for_team, _units_from_config
from domain.value_objects.scenario_config import ScenarioConfig, UnitSetup


class DummyRepo:
    def __init__(self, data):
        self.data = data
        self.calls = []

    def load(self, filename):
        self.calls.append(filename)
        return self.data.get(filename)


class DummyFactory:
    def __init__(self, unit):
        self.unit = unit
        self.calls = []

    def create_unit(self, **kwargs):
        self.calls.append(kwargs)
        return self.unit


class DummySpriteRepo:
    def __init__(self, sprite=None, raise_exc: Exception | None = None):
        self.sprite = sprite
        self.raise_exc = raise_exc
        self.calls = []

    def load_character_sprite(self, sprite_file):
        self.calls.append(sprite_file)
        if self.raise_exc:
            raise self.raise_exc
        return self.sprite


class VariableWeapon:
    def __init__(self):
        self.wield_mode = "variable"
        self.calls = []

    def set_wield_state(self, main_hand: bool, off_hand_equipped: bool):
        self.calls.append((main_hand, off_hand_equipped))


class DummyUnit:
    def __init__(self, weapon=None, name="Unit"):
        self.weapon = weapon
        self.name = name
        self.sprite = None


def make_setup(deployed: bool = True, off_hand: str | None = None) -> UnitSetup:
    eq = {"off_hand": off_hand} if off_hand else {}
    return UnitSetup(
        character_file="hero.json",
        sprite_file="hero.png",
        start_q=0 if deployed else None,
        start_r=1 if deployed else None,
        facing=2,
        equipment=eq,
    )


def test_skips_undeployed_units(monkeypatch):
    repo = DummyRepo({"hero.json": {"name": "Hero"}})
    factory = DummyFactory(DummyUnit())
    sprites = DummySpriteRepo("sprite")
    context = SimpleNamespace(character_repo=repo, unit_factory=factory, sprite_repo=sprites)

    messages = []
    monkeypatch.setattr("application.game_flow_service.handle_error", lambda msg, user_facing=True: messages.append(msg))

    result = _create_units_for_team(context, (make_setup(deployed=False),), "Team A")

    assert result == []
    assert repo.calls == []
    assert factory.calls == []
    assert sprites.calls == []
    assert messages == []


def test_missing_character_triggers_error(monkeypatch):
    repo = DummyRepo({})
    factory = DummyFactory(DummyUnit())
    sprites = DummySpriteRepo("sprite")
    context = SimpleNamespace(character_repo=repo, unit_factory=factory, sprite_repo=sprites)

    messages = []
    monkeypatch.setattr("application.game_flow_service.handle_error", lambda msg, user_facing=True: messages.append(msg))

    result = _create_units_for_team(context, (make_setup(deployed=True),), "Team A")

    assert result == []
    assert repo.calls == ["hero.json"]
    assert "not found" in messages[0].lower()


def test_variable_wield_sets_state_and_loads_sprite(monkeypatch):
    weapon = VariableWeapon()
    unit = DummyUnit(weapon=weapon, name="Hero")

    repo = DummyRepo({"hero.json": {"name": "Hero"}})
    factory = DummyFactory(unit)
    sprites = DummySpriteRepo("sprite")
    context = SimpleNamespace(character_repo=repo, unit_factory=factory, sprite_repo=sprites)

    messages = []
    monkeypatch.setattr("application.game_flow_service.handle_error", lambda msg, user_facing=True: messages.append(msg))

    setup = make_setup(deployed=True, off_hand="dagger")
    result = _create_units_for_team(context, (setup,), "Team A")

    assert result == [unit]
    assert weapon.calls == [(True, True)]
    assert unit.sprite == "sprite"
    assert messages == []


def test_units_from_config_uses_helper(monkeypatch):
    context = SimpleNamespace()
    config = ScenarioConfig(team_a=(make_setup(),), team_b=(make_setup(),))

    calls = []

    def fake_create(ctx, team_setups, label):
        calls.append((label, len(team_setups)))
        return [label]

    monkeypatch.setattr("application.game_flow_service._create_units_for_team", fake_create)

    team_a_units, team_b_units = _units_from_config(context, config)

    assert team_a_units == ["Team A"]
    assert team_b_units == ["Team B"]
    assert calls == [("Team A", 1), ("Team B", 1)]