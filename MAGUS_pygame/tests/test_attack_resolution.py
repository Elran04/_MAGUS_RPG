"""
Unit tests for attack resolution mechanics.

Tests cover:
- Defense value calculation (base/block/parry/dodge VÉ)
- Attack value calculation (TÉ + roll + modifiers)
- All attack outcomes (miss/block/parry/dodge/hit/overpower/critical)
- Critical hit detection and effects
- Overpower detection and armor degradation
- Combined critical + overpower strikes
- Damage application (FP vs EP)
"""
import pytest

from domain.entities import Unit, Weapon
from domain.value_objects import Position, ResourcePool, Attributes, CombatStats, Facing
from domain.mechanics.armor import ArmorPiece, ArmorSystem, HitzoneResolver
from domain.mechanics.attack_resolution import (
    AttackOutcome,
    calculate_defense_values,
    calculate_attack_value,
    resolve_attack,
    apply_attack_result,
)


# --- Fixtures ---

@pytest.fixture
def basic_weapon():
    """Standard weapon."""
    return Weapon(
        id="sword",
        name="Sword",
        te_modifier=10,
        ve_modifier=8,
        damage_min=3,
        damage_max=12,
        size_category=2,
        damage_bonus_attributes=["erő"],
    )


@pytest.fixture
def attacker():
    """Standard attacker unit."""
    return Unit(
        id="att",
        name="Attacker",
        position=Position(0, 0),
        fp=ResourcePool(20, 20),
        ep=ResourcePool(15, 15),
        attributes=Attributes(strength=18, dexterity=14),
        combat_stats=CombatStats(TE=50, VE=45),
    )


@pytest.fixture
def defender():
    """Standard defender unit."""
    return Unit(
        id="def",
        name="Defender",
        position=Position(1, 0),
        fp=ResourcePool(20, 20),
        ep=ResourcePool(15, 15),
        attributes=Attributes(strength=12, dexterity=16),
        combat_stats=CombatStats(TE=45, VE=60),
    )


@pytest.fixture
def armor_set():
    """Standard armor set using layered, zone-based pieces (chest + helm)."""
    chest = ArmorPiece(id="chest", name="Chainmail", parts={"mellvért": 8}, mgt=3, layer=1)
    helm = ArmorPiece(id="helm", name="Helmet", parts={"sisak": 5}, mgt=1, layer=1)
    system = ArmorSystem([chest, helm])
    return {"system": system, "chest": chest, "helm": helm}


# --- Test Defense Calculation ---

class TestDefenseCalculation:
    """Test defense value calculation."""
    
    def test_base_ve_only(self, defender):
        """Base VÉ with no equipment."""
        defense = calculate_defense_values(defender)
        
        assert defense.base_ve == 60
        assert defense.block_ve == 60  # No shield
        assert defense.parry_ve == 60  # No weapon
        assert defense.dodge_ve == 60  # No dodge skill
        assert defense.all_ve == 60
    
    def test_with_weapon_ve(self, defender, basic_weapon):
        """VÉ increases with weapon."""
        defender.weapon = basic_weapon
        defense = calculate_defense_values(defender)
        
        assert defense.base_ve == 60
        assert defense.block_ve == 60  # No shield
        assert defense.parry_ve == 68  # 60 + 8
        assert defense.all_ve == 68
    
    def test_with_shield_ve(self, defender, basic_weapon):
        """VÉ increases with shield."""
        defender.weapon = basic_weapon
        defense = calculate_defense_values(defender, shield_ve=15)
        
        assert defense.base_ve == 60
        assert defense.block_ve == 75  # 60 + 15
        assert defense.parry_ve == 83  # 60 + 8 + 15
        assert defense.all_ve == 83
    
    def test_with_dodge_skill(self, defender, basic_weapon):
        """VÉ increases with dodge skill."""
        defender.weapon = basic_weapon
        defense = calculate_defense_values(
            defender,
            shield_ve=15,
            dodge_modifier=20
        )
        
        assert defense.base_ve == 60
        assert defense.block_ve == 75
        assert defense.parry_ve == 83
        assert defense.dodge_ve == 103  # 83 + 20
        assert defense.all_ve == 103  # Uses dodge_ve when present
    
    def test_with_conditions(self, defender):
        """Conditions modify base VÉ."""
        defense = calculate_defense_values(
            defender,
            condition_modifier=-10  # Wounded, stunned, etc.
        )
        
        assert defense.base_ve == 50  # 60 - 10
        assert defense.all_ve == 50


# --- Test Attack Calculation ---

class TestAttackCalculation:
    """Test attack value calculation."""
    
    def test_basic_attack_value(self, attacker, basic_weapon):
        """Calculate TÉ + roll."""
        attacker.weapon = basic_weapon
        all_te = calculate_attack_value(attacker, attack_roll=45, weapon=basic_weapon)
        
        # 50 (base TÉ) + 10 (weapon) + 45 (roll) = 105
        assert all_te == 105
    
    def test_low_roll(self, attacker, basic_weapon):
        """Low roll results in low TÉ."""
        attacker.weapon = basic_weapon
        all_te = calculate_attack_value(attacker, attack_roll=5, weapon=basic_weapon)
        
        # 50 + 10 + 5 = 65
        assert all_te == 65
    
    def test_high_roll(self, attacker, basic_weapon):
        """High roll results in high TÉ."""
        attacker.weapon = basic_weapon
        all_te = calculate_attack_value(attacker, attack_roll=95, weapon=basic_weapon)
        
        # 50 + 10 + 95 = 155
        assert all_te == 155
    
    def test_with_conditions(self, attacker, basic_weapon):
        """Conditions modify TÉ."""
        attacker.weapon = basic_weapon
        all_te = calculate_attack_value(
            attacker,
            attack_roll=50,
            weapon=basic_weapon,
            condition_modifier=10  # Blessed, etc.
        )
        
        # 50 + 10 + 50 + 10 = 120
        assert all_te == 120


# --- Test Attack Outcomes ---

class TestAttackOutcomes:
    """Test different attack outcome scenarios."""
    
    def test_miss(self, attacker, defender, basic_weapon):
        """Attack misses when TÉ <= base VÉ."""
        attacker.weapon = basic_weapon
        
        # TÉ: 50 + 10 + 5 = 65, VÉ: 60 → HIT (65 > 60)
        # Need even lower roll
        result = resolve_attack(
            attacker, defender,
            attack_roll=1,  # 50 + 10 + 1 = 61 > 60, still hits
            base_damage_roll=5,
        )
        
        # Actually, with base VÉ 60, TÉ 61 still hits
        # Let's make defender stronger
        defender.combat_stats = CombatStats(VE=100)
        
        result = resolve_attack(
            attacker, defender,
            attack_roll=5,  # 50 + 10 + 5 = 65 < 100
            base_damage_roll=5,
        )
        
        assert result.outcome == AttackOutcome.MISS
        assert not result.hit
        assert result.damage_to_fp == 0
        assert result.damage_to_ep == 0
    
    def test_hit(self, attacker, defender, basic_weapon):
        """Normal hit when TÉ > VÉ but < VÉ+50."""
        attacker.weapon = basic_weapon
        defender.weapon = basic_weapon
        
        # TÉ: 50 + 10 + 45 = 105
        # VÉ: 60 + 8 = 68
        # 105 > 68 and 105 < 118 → HIT
        result = resolve_attack(
            attacker, defender,
            attack_roll=45,
            base_damage_roll=7,
        )
        
        assert result.outcome == AttackOutcome.HIT
        assert result.hit
        assert result.damage_to_fp > 0
        assert result.damage_to_ep == 0  # Normal hit goes to FP
        assert not result.is_critical
        assert not result.is_overpower
    
    def test_overpower(self, attacker, defender, basic_weapon):
        """Overpower when TÉ > VÉ + 50."""
        attacker.weapon = basic_weapon
        defender.weapon = basic_weapon
        
        # TÉ: 50 + 10 + 88 = 148
        # VÉ: 60 + 8 = 68
        # 148 > 68 + 50 → OVERPOWER
        result = resolve_attack(
            attacker, defender,
            attack_roll=88,
            base_damage_roll=9,
        )
        
        assert result.outcome == AttackOutcome.OVERPOWER
        assert result.is_overpower
        assert result.damage_to_fp == 0  # Overpower goes to EP
        assert result.damage_to_ep > 0
        assert not result.is_critical
    
    def test_critical(self, attacker, defender, basic_weapon):
        """Critical hit on high roll with skill."""
        attacker.weapon = basic_weapon
        
        # Roll 96, skill 2 → threshold 95 → CRITICAL
        # TÉ: 50 + 10 + 96 = 156, VÉ: 60
        # 156 > 60 + 50 → Also OVERPOWER!
        result = resolve_attack(
            attacker, defender,
            attack_roll=96,
            base_damage_roll=6,
            weapon_skill_level=2,
        )
        assert result.hit_zone is not None
        
        # This is BOTH critical and overpower - devastating combo!
        assert result.outcome == AttackOutcome.CRITICAL_OVERPOWER
        assert result.is_critical
        assert result.is_overpower
        assert result.hit
        assert result.damage_to_ep > 0  # CRITICAL_OVERPOWER goes to EP
        assert result.damage_to_fp == 0
    
    def test_critical_auto_hit(self, attacker, defender, basic_weapon):
        """Critical hits ignore VÉ (auto-hit) and deal amplified damage to FP."""
        attacker.weapon = basic_weapon
        defender.combat_stats = CombatStats(VE=200)  # Impossible to hit normally
        
        # Roll 97, skill 2 → CRITICAL (auto-hit despite high VÉ)
        # TÉ: 50 + 10 + 97 = 157, VÉ: 200
        # 157 NOT > 200 + 50 → Only CRITICAL, not overpower
        result = resolve_attack(
            attacker, defender,
            attack_roll=97,
            base_damage_roll=8,
            weapon_skill_level=2,
        )
        assert result.hit_zone is not None
        
        assert result.outcome == AttackOutcome.CRITICAL
        assert result.is_critical
        assert not result.is_overpower  # High VÉ prevents overpower
        assert result.hit  # Hits despite VÉ 200!
        assert result.damage_to_fp > 0  # Pure critical goes to FP
        assert result.mandatory_ep_loss > 0  # Mandatory EP loss still applies


# --- Test Critical + Overpower Combination ---

class TestCriticalOverpowerCombination:
    """Test the devastating combination of critical + overpower."""
    
    def test_critical_and_overpower_both_active(self, attacker, defender, basic_weapon, armor_set, monkeypatch):
        """When both critical and overpower occur, both effects apply."""
        attacker.weapon = basic_weapon
        defender.weapon = basic_weapon
        
        # High roll for critical, and TÉ advantage for overpower
        # Roll 97 (critical for skill 2)
        # TÉ: 50 + 10 + 97 = 157
        # VÉ: 60 + 8 = 68
        # 157 > 68 + 50 → Also OVERPOWER
        
        # Force chest hit zone for deterministic degradation assertion
        monkeypatch.setattr(HitzoneResolver, "resolve", classmethod(lambda cls, rng=None: "mellvért"))
        defender.armor_system = armor_set["system"]

        result = resolve_attack(
            attacker, defender,
            attack_roll=97,
            base_damage_roll=10,
            weapon_skill_level=2,
        )
        
        # Should be marked as CRITICAL_OVERPOWER (distinct outcome)
        assert result.outcome == AttackOutcome.CRITICAL_OVERPOWER
        assert result.is_critical
        assert result.is_overpower  # BOTH flags set!
        
        # Critical effects:
        # - Damage multiplied by skill (1.75x for skill 2)
        # - Ignores armor SFÉ
        # - Goes to EP
        
        # Overpower effects:
        # - Armor degraded (even though damage ignores it)
        # - Goes to EP (already from critical)

        assert result.damage_to_ep > 0
        assert result.damage_to_fp == 0
        assert result.armor_degraded  # Overpower still degrades armor (zone-specific)!
        # Only chest (mellvért) should degrade on chest hit
        assert armor_set["chest"].get_sfé("mellvért") == 7
    
    def test_critical_overpower_ignores_armor(self, attacker, defender, basic_weapon, armor_set, monkeypatch):
        """Critical component ignores armor even with overpower."""
        attacker.weapon = basic_weapon
        defender.weapon = basic_weapon

        defender.armor_system = armor_set["system"]
        # Record original armor values
        original_chest_sfe = armor_set["chest"].get_sfé("mellvért")
        original_helm_sfe = armor_set["helm"].get_sfé("sisak")
        
        # Force hit zone to chest for deterministic check
        monkeypatch.setattr(HitzoneResolver, "resolve", classmethod(lambda cls, rng=None: "mellvért"))
        result = resolve_attack(
            attacker, defender,
            attack_roll=97,  # Critical
            base_damage_roll=10,
            weapon_skill_level=2,
        )
        
        # Damage should ignore armor (critical effect)
        assert result.armor_absorbed == 0
        # Overpower degrades only the hit zone's outermost layer
        assert armor_set["chest"].get_sfé("mellvért") == original_chest_sfe - 1
        assert armor_set["helm"].get_sfé("sisak") == original_helm_sfe  # Helm unchanged on chest hit
    
    def test_critical_overpower_damage_multiplier(self, attacker, defender, basic_weapon):
        """Critical+overpower uses critical damage multiplier."""
        attacker.weapon = basic_weapon
        attacker.attributes = Attributes(strength=20)  # +5 bonus
        
        # Expected: (10 base + 5 bonus) * 1.75 = 26.25 → 26 or 27 EP
        result = resolve_attack(
            attacker, defender,
            attack_roll=96,
            base_damage_roll=10,
            weapon_skill_level=2,
        )
        
        assert result.is_critical
        # Damage should be multiplied
        assert result.damage_to_ep >= 20  # At least base + bonus
        assert result.damage_to_ep > 15  # Should be amplified
    
    def test_critical_overpower_typical_oneshot(self, attacker, defender, basic_weapon):
        """Critical+overpower typically one-shots due to high EP damage."""
        attacker.weapon = basic_weapon
        attacker.attributes = Attributes(strength=20)
        defender.ep = ResourcePool(12, 15)  # Typical EP pool
        
        result = resolve_attack(
            attacker, defender,
            attack_roll=98,
            base_damage_roll=12,
            weapon_skill_level=3,  # 1.75x multiplier
        )
        
        assert result.is_critical
        assert result.is_overpower
        
        # Apply damage
        initial_ep = defender.ep.current
        apply_attack_result(result, defender)
        
        # Likely killed or severely wounded
        assert defender.ep.current < initial_ep
        # High chance of one-shot (EP damage > 12)
        if result.damage_to_ep >= 12:
            assert not defender.is_alive()


# --- Test Damage Application ---

class TestDamageApplication:
    """Test damage application to units."""
    
    def test_apply_fp_damage(self, attacker, defender, basic_weapon):
        """Normal hit applies FP damage."""
        attacker.weapon = basic_weapon
        
        result = resolve_attack(
            attacker, defender,
            attack_roll=45,
            base_damage_roll=8,
        )
        
        initial_fp = defender.fp.current
        apply_attack_result(result, defender)
        
        assert defender.fp.current < initial_fp
        assert defender.fp.current == initial_fp - result.damage_to_fp
    
    def test_apply_ep_damage(self, attacker, defender, basic_weapon):
        """Overpower applies EP damage."""
        attacker.weapon = basic_weapon
        
        result = resolve_attack(
            attacker, defender,
            attack_roll=88,
            base_damage_roll=10,
        )
        
        initial_ep = defender.ep.current
        apply_attack_result(result, defender)
        
        assert defender.ep.current < initial_ep
        assert defender.ep.current == initial_ep - result.damage_to_ep
    
    def test_apply_mandatory_ep_loss(self, attacker, defender, basic_weapon):
        """Normal hit with mandatory EP loss."""
        attacker.weapon = basic_weapon
        
        result = resolve_attack(
            attacker, defender,
            attack_roll=45,
            base_damage_roll=12,  # High FP damage for mandatory EP
        )
        
        initial_ep = defender.ep.current
        apply_attack_result(result, defender)
        
        # Should have both FP damage and mandatory EP loss
        if result.mandatory_ep_loss > 0:
            assert defender.ep.current == initial_ep - result.mandatory_ep_loss
    
    def test_no_damage_on_miss(self, attacker, defender, basic_weapon):
        """Miss applies no damage."""
        attacker.weapon = basic_weapon
        defender.combat_stats = CombatStats(VE=150)
        
        result = resolve_attack(
            attacker, defender,
            attack_roll=5,
            base_damage_roll=10,
        )
        
        initial_fp = defender.fp.current
        initial_ep = defender.ep.current
        
        apply_attack_result(result, defender)
        
        assert defender.fp.current == initial_fp
        assert defender.ep.current == initial_ep


# --- Test Armor in Combat ---

class TestArmorInCombat:
    """Test armor absorption and degradation during combat."""
    
    def test_armor_reduces_damage(self, attacker, defender, basic_weapon, armor_set):
        """Armor reduces damage taken."""
        attacker.weapon = basic_weapon
        
        # Without armor
        result_no_armor = resolve_attack(
            attacker, defender,
            attack_roll=45,
            base_damage_roll=10,
        )
        
        # With armor
        defender.armor_system = armor_set["system"]
        result_with_armor = resolve_attack(
            attacker, defender,
            attack_roll=45,
            base_damage_roll=10,
        )
        
        # Armor should reduce damage
        assert result_with_armor.damage_to_fp < result_no_armor.damage_to_fp
        assert result_with_armor.armor_absorbed > 0
    
    def test_overpower_degrades_armor(self, attacker, defender, basic_weapon, armor_set, monkeypatch):
        """Overpower strike degrades armor."""
        attacker.weapon = basic_weapon
        
        defender.armor_system = armor_set["system"]
        original_chest = armor_set["chest"].get_sfé("mellvért")
        original_helm = armor_set["helm"].get_sfé("sisak")
        
        # Force chest hit to test deterministic degradation
        monkeypatch.setattr(HitzoneResolver, "resolve", classmethod(lambda cls, rng=None: "mellvért"))
        result = resolve_attack(
            attacker, defender,
            attack_roll=88,
            base_damage_roll=10,
        )
        
        assert result.is_overpower
        assert result.armor_degraded
        assert armor_set["chest"].get_sfé("mellvért") == original_chest - 1
        # Helm should be unchanged since hit zone is chest
        assert armor_set["helm"].get_sfé("sisak") == original_helm
    
    def test_normal_hit_preserves_armor(self, attacker, defender, basic_weapon, armor_set):
        """Normal hit doesn't degrade armor."""
        attacker.weapon = basic_weapon
        
        defender.armor_system = armor_set["system"]
        original_chest = armor_set["chest"].get_sfé("mellvért")
        
        result = resolve_attack(
            attacker, defender,
            attack_roll=45,
            base_damage_roll=10,
        )
        
        assert not result.is_overpower
        assert not result.armor_degraded
        assert armor_set["chest"].get_sfé("mellvért") == original_chest  # Unchanged


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
