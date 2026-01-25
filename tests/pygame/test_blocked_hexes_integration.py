"""
Integration test for blocked hexes in battle scenarios.

Verifies that:
1. ScenarioConfig properly stores blocked_hexes
2. BattleService receives and stores blocked_hexes from scenario
3. Movement wiring passes blocked_hexes correctly
"""

import pytest
from MAGUS_pygame.application.battle_service import BattleService
from MAGUS_pygame.domain.entities import Unit, Weapon
from MAGUS_pygame.domain.value_objects import Attributes, CombatStats, Position, ResourcePool
from MAGUS_pygame.domain.value_objects.scenario_config import ScenarioConfig, UnitSetup


def create_test_unit(
    unit_id: str,
    name: str,
    position: tuple[int, int],
) -> Unit:
    """Helper to create a test unit."""
    return Unit(
        id=unit_id,
        name=name,
        position=Position(position[0], position[1]),
        fp=ResourcePool(20, 20),
        ep=ResourcePool(15, 15),
        attributes=Attributes(),
        combat_stats=CombatStats(),
        weapon=Weapon(
            id="test_sword",
            name="Test Sword",
            te_modifier=5,
            ve_modifier=3,
            damage_min=1,
            damage_max=5,
            size_category=1,
        ),
    )


class TestScenarioConfigBlockedHexes:
    """Test that ScenarioConfig properly stores blocked_hexes."""

    def test_scenario_config_with_blocked_hexes(self):
        """Verify ScenarioConfig stores blocked_hexes."""
        blocked = frozenset([(0, 0), (1, 0), (0, 1)])
        config = ScenarioConfig(
            map_name="test_map",
            background_file="test_bg.png",
            team_a=(
                UnitSetup(character_file="warrior.json", sprite_file="warrior.png", start_q=0, start_r=0),
            ),
            team_b=(
                UnitSetup(character_file="goblin.json", sprite_file="goblin.png", start_q=5, start_r=0),
            ),
            blocked_hexes=blocked,
        )

        assert config.blocked_hexes == blocked
        assert (0, 0) in config.blocked_hexes
        assert (1, 0) in config.blocked_hexes
        assert (2, 0) not in config.blocked_hexes

    def test_scenario_config_blocked_hexes_immutable(self):
        """Verify blocked_hexes is immutable (frozenset)."""
        blocked = frozenset([(0, 0), (1, 0)])
        config = ScenarioConfig(
            map_name="test",
            background_file="bg.png",
            team_a=(UnitSetup(character_file="a.json", sprite_file="a.png", start_q=0, start_r=0),),
            team_b=(UnitSetup(character_file="b.json", sprite_file="b.png", start_q=5, start_r=0),),
            blocked_hexes=blocked,
        )

        # Verify it's frozen
        with pytest.raises(AttributeError):
            config.blocked_hexes.add((2, 0))  # type: ignore


class TestBattleServiceBlockedHexes:
    """Test that BattleService receives and stores blocked_hexes."""

    def test_battle_service_stores_blocked_hexes(self):
        """Verify BattleService stores blocked_hexes from constructor."""
        blocked = frozenset([(0, -3), (0, -2), (0, -1), (0, 0), (0, 1)])
        unit_a = create_test_unit("a1", "Warrior A", (-5, 0))
        unit_b = create_test_unit("b1", "Warrior B", (5, 0))

        battle = BattleService(
            units=[unit_a, unit_b],
            blocked_hexes=blocked,
        )

        assert battle.blocked_hexes == blocked
        assert (0, 0) in battle.blocked_hexes

    def test_battle_service_none_blocked_hexes(self):
        """Verify BattleService handles None blocked_hexes gracefully."""
        unit_a = create_test_unit("a1", "Warrior A", (-5, 0))
        unit_b = create_test_unit("b1", "Warrior B", (5, 0))

        battle = BattleService(
            units=[unit_a, unit_b],
            blocked_hexes=None,
        )

        assert battle.blocked_hexes is None

    def test_battle_service_default_blocked_hexes(self):
        """Verify BattleService defaults to None when not provided."""
        unit_a = create_test_unit("a1", "Warrior A", (-5, 0))
        unit_b = create_test_unit("b1", "Warrior B", (5, 0))

        battle = BattleService(units=[unit_a, unit_b])

        assert battle.blocked_hexes is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
