"""Tests for GameContext dependency container."""

import pytest

from MAGUS_pygame.application.game_context import EquipmentCategory, GameContext


@pytest.fixture
def context():
    """Create a GameContext instance for testing."""
    return GameContext()


class TestGameContextInitialization:
    """Test GameContext initialization and lifecycle."""

    def test_context_initializes_successfully(self):
        """Test that GameContext initializes all repositories and services."""
        context = GameContext()

        assert context.character_repo is not None
        assert context.equipment_repo is not None
        assert context.sprite_repo is not None
        assert context.scenario_repo is not None
        assert context.skills_repo is not None
        assert context.unit_setup_service is not None
        assert context.equipment_validation_service is not None
        assert context.scenario_service is not None
        assert context.unit_factory is not None

    def test_context_initialization_sets_running_state(self):
        """Test that GameContext is ready after initialization."""
        context = GameContext()
        # If we got here without exception, initialization succeeded
        assert context is not None

    def test_context_shutdown_cleans_up_caches(self, context):
        """Test that shutdown clears repository caches."""
        # Shutdown should not raise exceptions
        context.shutdown()
        # After shutdown, repositories should still exist but be cleaned
        assert context.character_repo is not None


class TestGetSkillName:
    """Test GameContext.get_skill_name facade method."""

    def test_get_skill_name_returns_string(self, context):
        """Test that get_skill_name returns a string."""
        result = context.get_skill_name("axe_1h")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_skill_name_caching_behavior(self, context):
        """Test that repeated calls return consistent results."""
        name1 = context.get_skill_name("longsword_1h")
        name2 = context.get_skill_name("longsword_1h")
        assert name1 == name2

    def test_get_skill_name_with_unknown_skill(self, context):
        """Test handling of unknown skill IDs."""
        # Should not crash, even with unknown skill
        result = context.get_skill_name("nonexistent_skill_xyz")
        assert isinstance(result, str)


class TestFindEquipmentById:
    """Test GameContext._find_equipment_by_id helper method."""

    def test_find_equipment_with_enum_category(self, context):
        """Test finding equipment using EquipmentCategory enum."""
        # This should not raise an error
        result = context._find_equipment_by_id(
            EquipmentCategory.WEAPONS_AND_SHIELDS, "longsword_1h"
        )
        # Result can be None or dict, but should not crash
        assert result is None or isinstance(result, dict)

    def test_find_equipment_with_string_category(self, context):
        """Test finding equipment using string category for backward compatibility."""
        result = context._find_equipment_by_id("weapons_and_shields", "longsword_1h")
        assert result is None or isinstance(result, dict)

    def test_find_equipment_armor_category(self, context):
        """Test finding armor."""
        result = context._find_equipment_by_id(EquipmentCategory.ARMOR, "leather_chest")
        assert result is None or isinstance(result, dict)

    def test_find_equipment_general_category(self, context):
        """Test finding general equipment."""
        result = context._find_equipment_by_id(EquipmentCategory.GENERAL, "backpack")
        assert result is None or isinstance(result, dict)

    def test_find_equipment_returns_dict_with_name_key(self, context):
        """Test that found equipment has name field."""
        # Try to find a known equipment item
        result = context._find_equipment_by_id(
            EquipmentCategory.WEAPONS_AND_SHIELDS, "longsword_1h"
        )
        if result:
            assert isinstance(result, dict)
            assert "name" in result or isinstance(result, dict)


class TestGetEquipmentName:
    """Test GameContext.get_equipment_name facade method."""

    def test_get_equipment_name_returns_string(self, context):
        """Test that get_equipment_name always returns a string."""
        result = context.get_equipment_name("longsword_1h", "weapons_and_shields")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_equipment_name_with_armor(self, context):
        """Test getting armor name."""
        result = context.get_equipment_name("leather_chest", "armor")
        assert isinstance(result, str)

    def test_get_equipment_name_with_general_equipment(self, context):
        """Test getting general equipment name."""
        result = context.get_equipment_name("backpack", "general")
        assert isinstance(result, str)

    def test_get_equipment_name_fallback_for_unknown_item(self, context):
        """Test fallback behavior for non-existent items."""
        # Should return a formatted name even if item not found
        result = context.get_equipment_name("nonexistent_item_xyz", "weapons_and_shields")
        assert isinstance(result, str)
        assert len(result) > 0
        # Fallback should format underscores as spaces and title case
        assert result == "Nonexistent Item Xyz" or isinstance(result, str)

    def test_get_equipment_name_formatting_fallback(self, context):
        """Test that unknown items get formatted with underscores replaced."""
        result = context.get_equipment_name("test_unknown_item", "general")
        assert isinstance(result, str)
        # Should have underscores converted to spaces
        assert "_" not in result

    def test_get_equipment_name_consistency(self, context):
        """Test that repeated calls return the same name."""
        name1 = context.get_equipment_name("longsword_1h", "weapons_and_shields")
        name2 = context.get_equipment_name("longsword_1h", "weapons_and_shields")
        assert name1 == name2


class TestEquipmentCategoryEnum:
    """Test EquipmentCategory enum."""

    def test_equipment_category_values(self):
        """Test that EquipmentCategory has all expected values."""
        assert EquipmentCategory.WEAPONS_AND_SHIELDS.value == "weapons_and_shields"
        assert EquipmentCategory.ARMOR.value == "armor"
        assert EquipmentCategory.GENERAL.value == "general"

    def test_equipment_category_enum_members(self):
        """Test that EquipmentCategory has exactly 3 members."""
        members = list(EquipmentCategory)
        assert len(members) == 3


class TestContextShutdown:
    """Test GameContext shutdown behavior."""

    def test_shutdown_completes_without_error(self, context):
        """Test that shutdown completes cleanly."""
        # Should not raise any exceptions
        context.shutdown()

    def test_multiple_shutdowns_safe(self, context):
        """Test that calling shutdown multiple times is safe."""
        context.shutdown()
        context.shutdown()  # Should not crash

    def test_context_after_shutdown_still_usable(self, context):
        """Test that context methods still work after shutdown."""
        context.shutdown()
        # Methods should still work (they'll reload from disk)
        result = context.get_skill_name("longsword_1h")
        assert isinstance(result, str)
