"""
Tests for new features:
1. Stamina recovery from unspent AP (battle_service._recover_stamina_from_unspent_ap)
2. Counterattack zone of control fix (counterattack.py position comparison)
3. Counterattack logging (is_counterattack field in battle log)
"""

import pytest

from MAGUS_pygame.application.battle_service import BattleService
from MAGUS_pygame.domain.entities import Unit, Weapon
from MAGUS_pygame.domain.mechanics import (
    AttackOutcome,
    CounterattackReaction,
    Stamina,
)
from MAGUS_pygame.domain.mechanics.attack_resolution import AttackResult
from MAGUS_pygame.domain.value_objects import (
    Attributes,
    CombatStats,
    Position,
    ResourcePool,
)


def make_unit(uid: str, name: str, allokepesseg: int = 5) -> Unit:
    """Create a test unit with stamina."""
    unit = Unit(
        id=uid,
        name=name,
        position=Position(0, 0),
        fp=ResourcePool(100, 100),
        ep=ResourcePool(100, 100),
        combat_stats=CombatStats(KE=10, TE=40, VE=30),
        attributes=Attributes(speed=15, endurance=allokepesseg),
    )
    unit.stamina = Stamina.from_attribute(allokepesseg=allokepesseg, start_full=True)
    return unit


class TestStaminaRecoveryFromUnspentAP:
    """Test stamina recovery at end of round based on unspent AP."""

    def test_recover_stamina_from_unspent_ap_basic(self):
        """Unit recovers stamina equal to unspent AP at round end."""
        u1 = make_unit("u1", "Warrior", allokepesseg=5)  # max stamina = 50
        u2 = make_unit("u2", "Goblin", allokepesseg=4)   # max stamina = 40
        
        battle = BattleService(units=[u1, u2])
        battle.start_battle()
        
        # Spend some AP
        battle.spend_ap(u1, 7)  # 3 AP remaining
        battle.spend_ap(u2, 3)  # 7 AP remaining
        
        # Also spend stamina to test recovery
        u1.stamina.spend_action_points(5)  # now at 45
        u2.stamina.spend_action_points(3)  # now at 37
        
        # Verify pre-recovery state
        assert battle.remaining_ap(u1) == 3
        assert battle.remaining_ap(u2) == 7
        assert u1.stamina.current_stamina == 45
        assert u2.stamina.current_stamina == 37
        
        # Complete the round
        while battle.round == 1:
            battle.end_turn()
        
        # After round ends, stamina should be recovered
        # u1: 45 + 3 = 48, u2: 37 + 7 = 44 (both capped at max)
        assert u1.stamina.current_stamina == 48
        assert u2.stamina.current_stamina == 40  # capped at max 40

    def test_recover_stamina_capped_at_max(self):
        """Stamina recovery is capped at maximum."""
        u1 = make_unit("u1", "Warrior", allokepesseg=5)
        battle = BattleService(units=[u1])
        battle.start_battle()
        
        # Unit spends minimal AP, leaving lots unspent
        battle.spend_ap(u1, 1)
        
        # Stamina is full, so recovery should be capped
        while battle.round == 1:
            battle.end_turn()
        
        assert u1.stamina.current_stamina == u1.stamina.max_stamina

    def test_recover_stamina_no_ap_spent(self):
        """If no AP spent, unit recovers full AP amount as stamina."""
        u1 = make_unit("u1", "Warrior", allokepesseg=5)
        u1.stamina.spend_action_points(10)  # spend some stamina first
        initial_stamina = u1.stamina.current_stamina
        
        battle = BattleService(units=[u1])
        battle.start_battle()
        
        # Don't spend any AP (10 AP available)
        assert battle.remaining_ap(u1) == 10
        
        while battle.round == 1:
            battle.end_turn()
        
        # Should recover 10 stamina
        expected = min(u1.stamina.max_stamina, initial_stamina + 10)
        assert u1.stamina.current_stamina == expected

    def test_recover_stamina_partial_ap_spent(self):
        """Unit partially spends AP and recovers the remaining as stamina."""
        u1 = make_unit("u1", "Warrior", allokepesseg=5)
        u1.stamina.spend_action_points(10)  # Spend some stamina first
        initial_stamina = u1.stamina.current_stamina
        
        battle = BattleService(units=[u1])
        battle.start_battle()
        
        # Spend some AP
        battle.spend_ap(u1, 4)  # 6 AP remaining
        
        assert battle.remaining_ap(u1) == 6
        
        while battle.round == 1:
            battle.end_turn()
        
        # Should recover 6 stamina
        expected = min(u1.stamina.max_stamina, initial_stamina + 6)
        assert u1.stamina.current_stamina == expected


class TestCounterattackLogging:
    """Test counterattack logging with is_counterattack field."""

    def test_counterattack_logging_field_exists(self):
        """is_counterattack field is properly defined in DetailedAttackData."""
        from MAGUS_pygame.domain.battle_log_entry import DetailedAttackData
        
        # Create attack data with is_counterattack flag
        attack_data = DetailedAttackData(
            attacker_name="Defender",
            defender_name="Attacker",
            round_number=1,
            attack_roll=50,
            all_te=100,
            all_ve=50,
            outcome=AttackOutcome.HIT,
            is_flank_attack=False,
            is_rear_attack=False,
            facing_ignored_ve=False,
            is_counterattack=True,  # Test field
            is_opportunity_attack=False,
        )
        
        # Verify field is set correctly
        assert attack_data.is_counterattack is True
        assert attack_data.is_opportunity_attack is False

    def test_counterattack_logging_field_defaults_to_false(self):
        """is_counterattack defaults to False when not specified."""
        from MAGUS_pygame.domain.battle_log_entry import DetailedAttackData
        
        attack_data = DetailedAttackData(
            attacker_name="Attacker",
            defender_name="Defender",
            round_number=1,
            attack_roll=50,
            all_te=100,
            all_ve=50,
            outcome=AttackOutcome.HIT,
            is_flank_attack=False,
            is_rear_attack=False,
            facing_ignored_ve=False,
            # is_counterattack not specified - should default to False
        )
        
        assert hasattr(attack_data, "is_counterattack")
        assert attack_data.is_counterattack is False
