# MAGUS Combat Mechanics

## Quick Reference (Overview)

This section summarizes outcomes and routing at a glance. Detailed rules and examples follow below.

### Attack Outcomes
- MISS: `TÉ ≤ base_VÉ` → no damage.
- BLOCKED / PARRIED: `base_VÉ < TÉ ≤ block_VÉ` or `≤ parry_VÉ` → stamina cost based on raw incoming weapon damage (armor does not reduce this cost).
- DODGE ATTEMPT: `parry_VÉ < TÉ ≤ dodge_VÉ` → stamina cost (fixed base, skill-modified); resolve dodge check.
- HIT (Normal): `TÉ > base_VÉ` and not in block/parry/dodge ranges and not critical/overpower → damage to FP, armor applies, mandatory EP loss by reach.
- CRITICAL (pure): critical threshold met → auto-hit, ignore armor; damage to FP (amplified) + mandatory EP loss by reach.
- OVERPOWER (pure): `TÉ > VÉ + 50` (modifiable) → degrade all armor by 1 SFÉ; damage routes directly to EP.
- CRITICAL_OVERPOWER: both conditions → degrade armor, ignore armor, amplified damage routed to EP.

### Damage Routing Decision Tree
```
Is it OVERPOWER (TÉ > VÉ + 50)?
├─ YES → Degrade armor first
│        Is it also CRITICAL?
│        ├─ YES → CRITICAL_OVERPOWER → Damage to EP (multiplied, ignores armor)
│        └─ NO  → OVERPOWER → Damage to EP
│
└─ NO → Is it CRITICAL?
   ├─ YES → CRITICAL → Damage to FP (multiplied, ignores armor, + mandatory EP by reach)
   └─ NO  → Is it HIT/BLOCK/PARRY/DODGE?
       ├─ HIT → Damage to FP (armor applies, + mandatory EP by reach)
       ├─ BLOCK/PARRY → Stamina cost (from raw incoming damage)
       ├─ DODGE → Stamina cost + resolve dodge
       └─ MISS → No damage
```

### Mandatory EP Loss by Reach
- Reach 1: every 6 FP → 1 EP
- Reach 2–3: every 8 FP → 1 EP
- Reach 4+: every 10 FP → 1 EP

---

## Special Attacks

### Charge Attack ✅
**Status:** Complete

A powerful special attack that combines movement and a melee strike in a single action.

**Rules:**
- **Cost:** 10 AP, 20 Stamina (fixed)
- **Range:** Minimum 5 hexes from target (cannot charge closer); maximum range = 5 hexes movement + weapon forward reach
- **Movement:** Up to 5 hexes of unobstructed movement toward target
- **Landing:** Must land within weapon reach of target after movement
- **Facing:** Automatically adjusted to face target from landing position

**Combat Modifiers:**
- **Attacker TÉ:** +20 (applies only to this attack)
- **Attacker VÉ:** -25 (penalty persists through the round)
- **Damage Dealt:** 2x multiplier on final damage
- **Damage Received:** 2x multiplier on opportunity attacks during charge movement

**Interruption:**
- If opportunity attack succeeds (at least HIT) during movement, charge attack is cancelled
- Movement stops at interruption point; charge stamina cost still applies

**Examples:**
```
Scenario: Warrior with longsword (size 3, reach ~2 hexes forward)
Target: Goblin 7 hexes away

1. Charge validation: 7 hexes ≥ 5 (minimum) ✓, 7 ≤ 5+2 (max) ✗
   → Need to be within 7 hexes for this weapon

Scenario: Same warrior, goblin 6 hexes away
1. Charge validation: 6 ≥ 5 ✓, 6 ≤ 7 ✓
2. Path computed: 4 hexes movement + 2 hexes reach
3. Attack rolls: TÉ 75 + 20 (charge) = 95 vs VÉ 45
4. Hit! Damage: 8 × 2 (charge) = 16 damage
5. Warrior VÉ reduced by 25 for rest of round
```

---

## Detailed Mechanics
Complete implementation of MAGUS RPG combat system with all core mechanics and examples.

## Implemented Systems

### 1. Damage Calculation (`damage.py`) ✅
**Status:** Complete with 28 passing unit tests

- Attribute-based damage bonuses (threshold at 15)
- Charge/multiplier support
- Armor absorption
- Penetration flags
- DamageService for application layer

**Key Rules:**
- For each attribute in `weapon.damage_bonus_attributes`:
  - If value > 15: bonus += (value - 15)
- Damage flow: `base → +bonus → *multiplier → -armor → final`

---

### 2. Weapon Reach (`reach.py`) ✅
**Status:** Complete

- Directional hex attack patterns based on facing
- Mandatory EP loss from FP damage
- Attack range validation

**Key Rules:**
- **Hex Attack Pattern (directional):**
  - Forward distance F = (size_category + 1) // 2
  - Side distance S = size_category // 2
  - Can attack all hexes along forward/left/right rays

**Examples:**
```
size 1 => F=1, S=0 → forward(1) → 1 hex
size 2 => F=1, S=1 → forward(1) + left(1) + right(1) → 3 hexes
size 3 => F=2, S=1 → forward(1,2) + left(1) + right(1) → 4 hexes
size 4 => F=2, S=2 → forward(1,2) + left(1,2) + right(1,2) → 6 hexes
size 5 => F=3, S=2 → forward(1,2,3) + left(1,2) + right(1,2) → 7 hexes
```

- **Mandatory EP Loss (from FP damage):**
  - Reach > 3: Every 10 FP → 1 EP
  - Reach > 1: Every 8 FP → 1 EP  
  - Reach = 1: Every 6 FP → 1 EP

---

### 3. Armor System (`armor.py`) ✅
**Status:** Complete

- ArmorPiece entity with SFÉ (damage absorption)
- Persistent degradation on overpower strikes
- MGT (movement penalty) calculation
- Repair mechanics

**Key Features:**
```python
@dataclass
class ArmorPiece:
    sfe: int              # Base absorption
    current_sfe: int      # Degradable value
    mgt: int             # Movement penalty
    location: str        # Body part
```

**Degradation:**
- Overpower strikes reduce `current_sfe` by 1 (persistent)
- Broken armor (current_sfe = 0) provides no protection
- Can be repaired to restore SFÉ

---

### 4. Critical Hits (`critical.py`) ✅
**Status:** Complete (placeholder skill thresholds)

- Roll-based detection (d100 vs skill threshold)
- Automatic hit (ignores VÉ)
- Ignores armor absorption
- Skill-based damage multipliers

**Key Rules:**
- Check: `attack_roll >= critical_threshold`
- Threshold decreases with skill level (more frequent crits)
- Effects:
  - Auto-hit (bypasses VÉ check)
  - Ignore armor SFÉ
  - Damage multiplier (1.5x - 2.5x based on skill)

**Placeholder Thresholds:**
```
Skill 0: 99+ (1% chance)  - 1.5x damage
Skill 1: 97+ (4% chance)  - 1.5x damage
Skill 2: 95+ (6% chance)  - 1.75x damage
Skill 3: 93+ (8% chance)  - 1.75x damage
Skill 4: 91+ (10% chance) - 2.0x damage
Skill 5: 90+ (11% chance) - 2.5x damage
```

---

### 5. Stamina System (`stamina.py`) ✅
**Status:** Complete

- Physical/mental endurance tied to Állóképesség (Endurance attribute)
- Base stamina = Állóképesség × 10
- Fatigue states with progressive combat penalties
- Action point costs and stamina recovery

**Fatigue States (by stamina %):**
```
Friss (Fresh)      80-100%: no penalties
Felpezsdült        60-79%:  -2 TÉ, -1 VÉ
Kifulladt (Tired)  40-59%:  -4 TÉ, -3 VÉ
Kifáradt           20-39%:  -7 TÉ, -5 VÉ
Kimerült (Exhausted) 0-19%: -10 TÉ, -8 VÉ
Unconscious        0%:      All combat values = 0, turn skipped
```

**Stamina Costs:**
- Attack: weapon attack_time (AP cost)
- Block/Parry: raw incoming damage (before armor)
- Dodge: 6 AP base cost

**AP Cost Modifiers (Weaponskill Level):**
- Level 0 (Unskilled): 2x weapon attack_time (doubled)
- Level 1 (Basic): weapon attack_time + 2
- Level 2+: weapon attack_time (no modifier)

**Example:** Longsword with attack_time 5:
- Unskilled (level 0): 10 AP
- Basic (level 1): 7 AP
- Skilled (level 2+): 5 AP

---

### 6. Injury System (`injury.py`) ✅
**Status:** Complete

- Condition tiers based on FP/EP damage thresholds
- Progressive penalties affecting all combat stats
- Mutually exclusive (strongest condition applies)

**Injury Conditions (Priority Order):**
```
1. Kritikus sérülés (Critical)  EP ≤ 75% of max:  -15 KÉ, -25 TÉ, -25 VÉ, -15 CÉ
2. Súlyos sérülés (Serious)     EP < max (any):   -10 KÉ, -20 TÉ, -20 VÉ, -10 CÉ
3. Könnyű sérülés (Light)       FP ≤ 75% of max:   -5 KÉ, -10 TÉ, -10 VÉ,  -5 CÉ
4. Egészséges (Healthy)         Otherwise:         no penalties
```

---

### 7. Attack Resolution (`attack_resolution.py`) ✅
**Status:** Complete

Complete attack flow integrating all systems including stamina, injury, and unconscious handling.

**Atomic Transaction Model:**
- Attack resolution computes all effects (damage, stamina costs) without mutating state
- AP sufficiency is verified before any effects are applied
- Effects (FP/EP damage, stamina deductions) are applied atomically only after AP is successfully spent
- If AP is insufficient, no effects occur and stamina is not deducted
- This ensures consistent game state and prevents partial execution

**Defense Value Calculation:**
```python
base_VÉ = character VÉ ± conditions ± stamina ± injury
block_VÉ = base_VÉ + shield VÉ
parry_VÉ = base_VÉ + weapon VÉ + shield VÉ
dodge_VÉ = parry_VÉ + dodge skill modifier
all_VÉ = dodge_VÉ (or parry_VÉ if no dodge skill)
```

**Attack Value:**
```python
all_TÉ = base TÉ + weapon TÉ + d100 roll + conditions + stamina_mod + injury_mod
```

**Attack Outcomes:**
1. **MISS**: `all_TÉ <= base_VÉ`
   - No damage

2. **BLOCKED**: `base_VÉ < all_TÉ <= block_VÉ`
   - Stamina cost = raw incoming damage (before armor)
   - Reduced by shield skill (TODO)

3. **PARRIED**: `block_VÉ < all_TÉ <= parry_VÉ`
   - Stamina cost = raw incoming damage (before armor)
   - Reduced by parry skill (TODO)

4. **DODGE_ATTEMPT**: `parry_VÉ < all_TÉ <= dodge_VÉ`
   - Stamina cost: 6 AP (fixed base)
   - Requires speed check (Gyorsaság próba)
   - Success = no damage
   - Failure = reduced damage (based on dodge skill)

5. **HIT**: `all_TÉ > all_VÉ`
   - Normal damage to FP
   - Armor absorption applies
   - Mandatory EP loss from reach rules

6. **OVERPOWER**: `all_TÉ > all_VÉ + 50`
   - Damage directly to EP (bypasses FP)
   - Armor absorption applies AFTER degradation
   - Armor SFÉ reduced by 1 (persistent)
   - Threshold 50 can be reduced by skills (Mastery, Pusztító)

7. **CRITICAL**: `attack_roll >= critical_threshold`
   - Automatic hit (ignores VÉ)
   - Ignores armor SFÉ completely
   - Damage multiplied by skill level
   - Can combine with overpower for devastating effect

**Combined Critical + Overpower:**
When both occur:
- Damage ignores full SFÉ
- Armor still degrades by 1 (if SFÉ > 0)
- Damage amplified by critical multiplier
- Damage goes directly to EP
- Usually a one-shot kill

---

## Data Flow Example

### Normal Hit
```
1. Roll d100: 45
2. Calculate all_TÉ: 50 (base) + 10 (weapon) + 45 (roll) = 105
3. Calculate all_VÉ: 60 (base) + 15 (weapon) = 75
4. Compare: 105 > 75 → HIT
5. Roll damage: 7
6. Add attribute bonus: +4 (Str 18, Dex 16)
7. Apply armor: 11 - 5 (SFÉ) = 6 damage to FP
8. Mandatory EP loss: weapon reach 3 → 6 FP / 8 = 0 EP
9. Result: 6 FP damage, 0 EP damage
```

### Overpower Strike
```
1. Roll d100: 88
2. all_TÉ: 50 + 10 + 88 = 148
3. all_VÉ: 75
4. Compare: 148 > 75 + 50 → OVERPOWER
5. Roll damage: 9
6. Add attribute bonus: +4
7. Degrade armor: SFÉ 5 → 4 (persistent)
8. Apply degraded armor: 13 - 4 = 9 damage
9. Direct to EP: 9 EP damage (bypasses FP)
10. Result: 0 FP, 9 EP damage, armor permanently reduced
```

### Critical Hit
```
1. Roll d100: 96 (skill level 2 → threshold 95)
2. Critical detected!
3. Auto-hit (skip VÉ comparison)
4. Roll damage: 6
5. Add attribute bonus: +4
6. Critical multiplier: 1.75x → 10 * 1.75 = 17
7. Ignore armor (critical bypasses SFÉ)
8. Route to FP: 17 FP damage
9. Apply mandatory EP loss from reach (e.g., reach 2-3 → 17 // 8 = 2 EP)
10. Result: 17 FP damage, 2 EP (mandatory), armor unaffected
```

### Overpowered Critical (One-Shot)
```
1. Roll d100: 97 (critical!) + TÉ advantage
2. all_TÉ: 160, all_VÉ: 75 (also overpower!)
3. Both effects apply
4. Roll damage: 8
5. Add attribute bonus: +4
6. Critical multiplier: 1.75x → 12 * 1.75 = 21
7. Ignore armor (critical)
8. Degrade armor (overpower) anyway: SFÉ 5 → 4
9. Route to EP (overpower): 21 EP damage
10. Typical character EP: 10-15 → instant kill
```

---

## TODO / Not Yet Implemented

### High Priority
1. **Unit Tests** for new mechanics:
   - Reach hex calculations
   - Armor degradation
   - Critical detection
   - Attack resolution outcomes

2. **Skill System:**
   - Weapon skill levels and progression
   - Critical thresholds from actual skill data
   - Dodge skill and speed checks
   - Block/parry skill damage reduction
   - Mastery and Pusztító for overpower threshold

3. **Shield Entity:**
   - Separate from weapon
   - Shield VÉ in defense calculation
   - Block stamina cost reduction

### Medium Priority
4. **Dodge Resolution:**
   - Gyorsaság (speed) attribute check
   - Partial damage on failed dodge
   - Dodge skill level effects

5. **Stamina Recovery:**
   - End-of-combat regeneration
   - Rest/action-based recovery rates

6. **Equipment Repository Extensions:**
   - Load shields from equipment data
   - Load armor pieces from equipment data
   - Equipment validation

### Low Priority
7. **Advanced Combat:**
   - Dual wielding modifiers
   - Two-handed weapon bonuses
   - Charge mechanics
   - Opportunity attacks
   - Combat maneuvers

8. **Status Effects:**
   - Condition modifiers for TÉ/VÉ
   - Stunned, prone, bleeding, etc.
   - Effect duration tracking

---

## Integration with Game Context

To use the combat system:

```python
from application.game_context import GameContext
from domain.mechanics import resolve_attack, apply_attack_result
import random

ctx = GameContext()

# Create units
attacker = ctx.unit_factory.create_unit("Warrior.json", Position(0, 0))
defender = ctx.unit_factory.create_unit("Goblin.json", Position(1, 0))

# Roll dice
attack_roll = random.randint(1, 100)
damage_roll = random.randint(
    attacker.weapon.damage_min,
    attacker.weapon.damage_max
)

# Resolve attack
result = resolve_attack(
    attacker=attacker,
    defender=defender,
    attack_roll=attack_roll,
    base_damage_roll=damage_roll,
    weapon_skill_level=2,  # TODO: from character skills
    shield_ve=0,           # TODO: from equipment
    dodge_modifier=0,      # TODO: from skills
)

# Apply damage
apply_attack_result(result, defender)

# Log result
print(f"{result.outcome.value}: {result.damage_to_fp} FP, {result.damage_to_ep} EP")
if result.is_critical:
    print("CRITICAL HIT!")
if result.is_overpower:
    print("OVERPOWERING STRIKE!")
```

---

## File Structure

```
domain/mechanics/
├── __init__.py              # Package exports
├── damage.py                # ✅ Damage calculation (28 tests)
├── reach.py                 # ✅ Weapon reach & mandatory EP
├── armor.py                 # ✅ Armor entities & degradation
├── critical.py              # ✅ Critical hit detection
├── stamina.py               # ✅ Stamina/fatigue system
├── injury.py                # ✅ Injury condition system
└── attack_resolution.py     # ✅ Complete attack flow with conditions
```

---

## Next Steps

1. **Write comprehensive tests** for new mechanics
2. **Implement skill system** (weapon proficiency, dodge, etc.)
3. **Add shields** as separate equipment
4. **Integrate with UI** for battle screen
5. **Add combat log** for detailed feedback
