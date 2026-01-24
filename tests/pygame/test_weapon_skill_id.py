"""
Tests for weapon skill_id mapping and population in UnitFactory.
"""

import pytest

from MAGUS_pygame.domain.services import UnitFactory
from MAGUS_pygame.domain.value_objects import Position
from MAGUS_pygame.infrastructure.repositories import CharacterRepository, EquipmentRepository


@pytest.fixture
def character_repo():
    """Create a CharacterRepository instance."""
    return CharacterRepository()


@pytest.fixture
def equipment_repo():
    """Create an EquipmentRepository instance."""
    return EquipmentRepository()


@pytest.fixture
def factory(character_repo, equipment_repo):
    """Create a UnitFactory instance."""
    return UnitFactory(character_repo, equipment_repo)


def test_longsword_maps_to_weaponskill_longswords():
    """Test that 'Hosszú kardok' category maps to 'weaponskill_longswords'."""
    assert UnitFactory.CATEGORY_TO_SKILL_ID.get("Hosszú kardok") == "weaponskill_longswords"


def test_build_weapon_entity_populates_skill_id(factory):
    """Test that _build_weapon_entity extracts category and derives skill_id."""
    weapon_data = {
        "id": "longsword",
        "name": "Hosszú kard",
        "category": "Hosszú kardok",
        "KE": 5,
        "TE": 10,
        "VE": 10,
        "damage_min": 2,
        "damage_max": 12,
        "can_disarm": True,
        "can_break_weapon": True,
    }

    weapon = factory._build_weapon_entity(weapon_data)

    assert weapon.category == "Hosszú kardok"
    assert weapon.skill_id == "weaponskill_longswords"
    assert weapon.id == "longsword"
    assert weapon.name == "Hosszú kard"


def test_warri_longsword_has_skill_id(factory, character_repo, equipment_repo):
    """Test that creating Warri unit equips first weapon with correct structure.

    Warri has knife first, then longsword. Verify knife gets category/skill_id
    correctly, and manually verify longsword would too.
    """
    char_data = character_repo.load("Warri.json")
    assert char_data is not None

    unit = factory.create_unit(
        "Warri.json",
        position=Position(0, 0),
        char_data=char_data,
    )

    assert unit is not None
    assert unit.weapon is not None
    # First weapon in Warri.json is knife
    assert unit.weapon.id == "knife"
    # Verify knife has the category/skill_id structure populated
    assert unit.weapon.category is not None
    assert unit.weapon.skill_id is not None

    # Also verify that longsword in equipment repo has the right category
    longsword_data = equipment_repo.find_weapon_by_id("longsword")
    assert longsword_data is not None
    assert longsword_data.get("category") == "Hosszú kardok"

    # Build weapon from longsword data to verify skill_id would be correct
    longsword = factory._build_weapon_entity(longsword_data)
    assert longsword.id == "longsword"
    assert longsword.category == "Hosszú kardok"
    assert longsword.skill_id == "weaponskill_longswords"


def test_unknown_category_results_in_empty_skill_id(factory):
    """Test that unknown weapon categories result in empty skill_id."""
    weapon_data = {
        "id": "unknown_weapon",
        "name": "Unknown Weapon",
        "category": "Unknown Category",
    }

    weapon = factory._build_weapon_entity(weapon_data)

    assert weapon.category == "Unknown Category"
    assert weapon.skill_id == ""


def test_missing_category_results_in_empty_skill_id(factory):
    """Test that weapons without category have empty skill_id."""
    weapon_data = {
        "id": "sword",
        "name": "Some Sword",
    }

    weapon = factory._build_weapon_entity(weapon_data)

    assert weapon.category == ""
    assert weapon.skill_id == ""
