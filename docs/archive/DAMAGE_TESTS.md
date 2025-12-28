# Archived: Damage Mechanics Test Suite

This document is archived historical testing notes. Current automated tests live under `MAGUS_pygame/tests/`. For up-to-date mechanics, see `docs/COMBAT_MECHANICS*.md`.

---

# Damage Mechanics Test Suite

## Overview
Comprehensive unit tests for MAGUS combat damage calculation system. All tests pass (28/28).

## Test Coverage

### 1. Attribute Value Retrieval (4 tests)
- ✅ Lowercase Hungarian keys (erő, ügyesség)
- ✅ Capitalized Hungarian keys (Erő, Ügyesség)
- ✅ All 10 attributes mapped correctly
- ✅ Unknown attributes return 0

### 2. Attribute Bonus Calculation (6 tests)
- ✅ No bonus when attributes ≤ 15 (threshold)
- ✅ Correct bonus when attributes > 15 (value - 15)
- ✅ Multiple attributes accumulate bonuses
- ✅ Single attribute weapons work correctly
- ✅ No weapon = no bonus
- ✅ Empty damage_bonus_attributes = no bonus
- ✅ High attributes (25) correctly compute bonus (+10)

### 3. Final Damage Calculation (10 tests)
- ✅ Basic damage with no modifiers
- ✅ Damage with attribute bonuses
- ✅ Charge multiplier applied after bonuses
- ✅ Armor absorption reduces final damage
- ✅ Penetration flag set when damage > armor
- ✅ Armor blocks all damage when armor > damage
- ✅ Combined multipliers and armor work correctly
- ✅ Zero base damage + attribute bonus
- ✅ Negative base damage clamped to 0
- ✅ No weapon = no attribute bonuses

### 4. Edge Cases (5 tests)
- ✅ Very high charge multipliers (x10)
- ✅ Zero charge multiplier clamped to 1
- ✅ Negative charge multiplier clamped to 1
- ✅ Negative armor absorption treated as 0
- ✅ Default context (None) works correctly

### 5. DamageService Integration (3 tests)
- ✅ resolve_attack applies damage to defender
- ✅ resolve_attack with context (charge + armor)
- ✅ Damage cannot reduce EP below 0

## Key Mechanics Verified

### Damage Calculation Flow
```
base_damage → +attribute_bonus → *charge_multiplier → -armor_absorption → final_damage
```

### Attribute Bonus Rule
For each attribute in weapon's `damage_bonus_attributes`:
- If attribute > 15: bonus += (attribute - 15)
- If attribute ≤ 15: no bonus

### Armor Penetration
- `penetrated = True` when `modified_damage > armor_absorption`
- `penetrated = False` when armor blocks all damage

### Example Calculations
```python
# Example 1: Strong unit (Str 18, Dex 16) with sword
base_damage = 7
attribute_bonus = (18-15) + (16-15) = 4
modified = 7 + 4 = 11
final = 11  # no armor

# Example 2: With charge and armor
base_damage = 5
attribute_bonus = 4
charge_multiplier = 2
armor_absorption = 5
modified = (5 + 4) * 2 = 18
final = 18 - 5 = 13
```

## Test Fixtures

### Units
- `basic_unit`: All attributes at 10 (no bonuses)
- `strong_unit`: Strength 18, Dexterity 16

### Weapons
- `basic_weapon`: Str + Dex bonus (2-10 damage)
- `strength_weapon`: Str only bonus (3-12 damage)

## Running Tests

```bash
# From project root
python -m pytest MAGUS_pygame/tests/test_damage.py -v

# With coverage
python -m pytest MAGUS_pygame/tests/test_damage.py --cov=domain.mechanics.damage
```

## Integration Points

### GameContext
`DamageService` is exposed via `GameContext.damage_service` for application-layer usage.

### Unit Entity
- `Unit.take_damage(amount)` applies damage to EP
- `Unit.attributes` provides bonus source
- `Unit.weapon` provides damage_bonus_attributes

### Weapon Entity
- `damage_bonus_attributes: list[str]` defines which attributes add bonuses
- Supports lowercase Hungarian keys from equipment JSON

## Next Steps for Combat System

1. **Critical Hits**: Add `is_critical` flag logic (roll-based or attack success margin)
2. **Overkill**: Calculate `overkill = max(0, damage - defender.ep.current)`
3. **Attack Resolution**: Integrate with attack/defense roll comparison
4. **Status Effects**: Add damage type resistance/vulnerability modifiers
5. **Armor System**: Load actual armor pieces from equipment, calculate SFÉ/MGT absorption values
