import pytest
from application.equipment_validation_service import EquipmentValidationService, ValidationResult
from types import SimpleNamespace

class DummyRepo:
    def __init__(self, weapons=None, armor=None):
        self._weapons = weapons or []
        self._armor = armor or []
    def load_weapons(self):
        return self._weapons
    def load_armor(self):
        return self._armor
    def find_weapon_by_id(self, item_id):
        for w in self._weapons:
            if w.get("id") == item_id:
                return w
        return None
    def find_armor_by_id(self, item_id):
        for a in self._armor:
            if a.get("id") == item_id:
                return a
        return None

def make_unit(strength=10, dexterity=10):
    return SimpleNamespace(Tulajdonságok={"Erő": strength, "Ügyesség": dexterity})

def test_variable_wielding_strength_requirement():
    repo = DummyRepo(weapons=[{"id": "var_sword", "wield_mode": "variable", "variable_strength_req": 12, "variable_dex_req": 8}])
    service = EquipmentValidationService(repo)
    unit = make_unit(strength=10, dexterity=10)
    result = service.can_wield_variable_one_handed(unit, "var_sword")
    assert not result.success
    assert "strength" in result.message.lower()

def test_variable_wielding_dexterity_requirement():
    repo = DummyRepo(weapons=[{"id": "var_sword", "wield_mode": "variable", "variable_strength_req": 8, "variable_dex_req": 12}])
    service = EquipmentValidationService(repo)
    unit = make_unit(strength=10, dexterity=10)
    result = service.can_wield_variable_one_handed(unit, "var_sword")
    assert not result.success
    assert "dexterity" in result.message.lower()

def test_variable_wielding_success():
    repo = DummyRepo(weapons=[{"id": "var_sword", "wield_mode": "variable", "variable_strength_req": 8, "variable_dex_req": 8}])
    service = EquipmentValidationService(repo)
    unit = make_unit(strength=10, dexterity=10)
    result = service.can_wield_variable_one_handed(unit, "var_sword")
    assert result.success

def test_offhand_two_handed_block():
    repo = DummyRepo(weapons=[{"id": "big_axe", "wield_mode": "two-handed"}, {"id": "dagger", "wield_mode": "one-handed"}])
    service = EquipmentValidationService(repo)
    # Main hand is two-handed, offhand should be blocked
    result = service.can_equip_offhand("big_axe", "dagger")
    assert not result.success
    assert "two-handed" in result.message.lower()

def test_offhand_one_handed_success():
    repo = DummyRepo(weapons=[{"id": "sword", "wield_mode": "one-handed"}, {"id": "dagger", "wield_mode": "one-handed"}])
    service = EquipmentValidationService(repo)
    # Main hand is one-handed, offhand is one-handed
    result = service.can_equip_offhand("sword", "dagger")
    assert result.success

def test_armor_conflict():
    # Two armor pieces, same layer, same zone
    armor1 = {"id": "a1", "name": "A1", "parts": {"torso": 2}, "layer": 1}
    armor2 = {"id": "a2", "name": "A2", "parts": {"torso": 1}, "layer": 1}
    repo = DummyRepo(armor=[armor1, armor2])
    service = EquipmentValidationService(repo)
    is_valid, warnings, conflicts = service.validate_armor_compatibility(["a1", "a2"])
    assert not is_valid
    assert warnings
    assert "torso" in str(conflicts)
