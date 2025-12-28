# Archived: Weapon Wielding System

This document described variable wielding rules. Current combat focus is evolving; consult `docs/COMBAT_MECHANICS*.md` and code for the latest behavior.

---

# Weapon Wielding System

## Overview

The weapon wielding system handles "Változó" (Variable) wield mode weapons that can be wielded in either 1-handed or 2-handed mode depending on the wielder's attributes.

## Core Concepts

### Wield Modes

1. **ONE_HANDED**: Fixed 1-handed weapon (e.g., dagger, shortsword)
2. **TWO_HANDED**: Fixed 2-handed weapon (e.g., greatsword, halberd)
3. **VARIABLE (Változó)**: Can be wielded either way (e.g., longsword, bastard sword)

### Variable Weapon Rules

**If unit meets BOTH requirements:**
- Erő (Strength) >= variable_strength_req
- Ügyesség (Dexterity) >= variable_dex_req

Then:
- Player can **choose** 1-handed or 2-handed
- If choosing 2-handed: gains bonus KÉ, TÉ, VÉ from weapon
- If choosing 1-handed: no bonuses (normal stats)

**If unit doesn't meet requirements:**
- **Must** wield 2-handed (forced)
- **No bonus stats** (penalty for being too weak/clumsy)

## Architecture

### Value Objects

#### WieldMode
```python
class WieldMode(str, Enum):
    ONE_HANDED = "1-handed"
    TWO_HANDED = "2-handed"
    VARIABLE = "Változó"
```

#### WieldingBonuses
```python
@dataclass(frozen=True)
class WieldingBonuses:
    ke_bonus: int = 0  # Initiative bonus
    te_bonus: int = 0  # Attack bonus
    ve_bonus: int = 0  # Defense bonus
    
    def is_active(self) -> bool:
        """Check if any bonuses are active."""
```

#### WieldingInfo
```python
@dataclass(frozen=True)
class WieldingInfo:
    mode: WieldMode                # Current wielding mode
    can_choose: bool               # Can player choose?
    bonuses: WieldingBonuses       # Active bonuses
    forced_two_handed: bool        # Must use 2-handed?
    meets_requirements: bool       # Meets attribute requirements?
```

## API Functions

### can_wield_one_handed
```python
def can_wield_one_handed(
    unit: Unit,
    weapon: Weapon,
    strength_req: int,
    dex_req: int
) -> bool
```
Check if unit meets attribute requirements to wield variable weapon 1-handed.

**Example:**
```python
if can_wield_one_handed(warrior, longsword, strength_req=16, dex_req=13):
    print("Can wield 1-handed!")
else:
    print("Must wield 2-handed")
```

### get_wielding_info
```python
def get_wielding_info(
    unit: Unit,
    weapon: Weapon,
    wield_mode: str,
    strength_req: int = 0,
    dex_req: int = 0,
    ke_bonus: int = 0,
    te_bonus: int = 0,
    ve_bonus: int = 0,
    preference: Optional[WieldMode] = None
) -> WieldingInfo
```
Get complete wielding information for a unit's weapon.

**Example:**
```python
info = get_wielding_info(
    unit=warrior,
    weapon=longsword,
    wield_mode="Változó",
    strength_req=16,
    dex_req=13,
    te_bonus=5,
    ve_bonus=3,
    preference=WieldMode.TWO_HANDED
)

if info.bonuses.is_active():
    print(f"2-Handed Bonuses: TÉ +{info.bonuses.te_bonus}, VÉ +{info.bonuses.ve_bonus}")
```

### validate_wielding_mode_change
```python
def validate_wielding_mode_change(
    unit: Unit,
    weapon: Weapon,
    wield_mode: str,
    new_mode: WieldMode,
    strength_req: int,
    dex_req: int
) -> bool
```
Validate if a wielding mode change is allowed.

**Example:**
```python
if validate_wielding_mode_change(warrior, longsword, "Változó", WieldMode.ONE_HANDED, 16, 13):
    # Allow player to switch to 1-handed
    apply_mode_change(warrior, WieldMode.ONE_HANDED)
else:
    show_message("Cannot wield 1-handed: insufficient attributes")
```

## Usage Examples

### Example 1: Strong Fighter with Variable Weapon
```python
# Unit attributes
warrior = Unit(
    id="warrior",
    name="Strong Warrior",
    attributes=Attributes(strength=18, dexterity=16),
    ...
)

# Variable weapon
longsword = Weapon(
    id="longsword",
    name="Longsword",
    te_modifier=10,
    ve_modifier=8,
    ...
)

# Get wielding info (defaults to 1-handed)
info = get_wielding_info(
    warrior, longsword,
    wield_mode="Változó",
    strength_req=16,
    dex_req=13,
    te_bonus=5,
    ve_bonus=3
)

print(f"Mode: {info.mode.value}")              # "1-handed"
print(f"Can choose: {info.can_choose}")        # True
print(f"Forced 2H: {info.forced_two_handed}")  # False
print(f"Bonuses active: {info.bonuses.is_active()}")  # False

# Player chooses 2-handed
info_2h = get_wielding_info(
    warrior, longsword,
    wield_mode="Változó",
    strength_req=16,
    dex_req=13,
    te_bonus=5,
    ve_bonus=3,
    preference=WieldMode.TWO_HANDED
)

print(f"Mode: {info_2h.mode.value}")           # "2-handed"
print(f"TÉ bonus: +{info_2h.bonuses.te_bonus}")  # +5
print(f"VÉ bonus: +{info_2h.bonuses.ve_bonus}")  # +3
```

### Example 2: Weak Fighter Forced 2-Handed
```python
# Unit with low attributes
rookie = Unit(
    id="rookie",
    name="Rookie Fighter",
    attributes=Attributes(strength=12, dexterity=10),
    ...
)

# Same variable weapon
info = get_wielding_info(
    rookie, longsword,
    wield_mode="Változó",
    strength_req=16,
    dex_req=13,
    te_bonus=5,
    ve_bonus=3
)

print(f"Mode: {info.mode.value}")              # "2-handed"
print(f"Can choose: {info.can_choose}")        # False
print(f"Forced 2H: {info.forced_two_handed}")  # True
print(f"Meets reqs: {info.meets_requirements}") # False
print(f"Bonuses: {info.bonuses.is_active()}")  # False (penalty!)

# Rookie must use 2 hands but gets NO bonuses
# This represents struggling with a weapon too heavy/complex
```

### Example 3: UI Integration
```python
def on_weapon_equip(unit: Unit, weapon: Weapon, weapon_data: dict):
    """When player equips a weapon, show wielding options."""
    
    info = get_wielding_info(
        unit, weapon,
        wield_mode=weapon_data.get("wield_mode", "1-handed"),
        strength_req=weapon_data.get("variable_strength_req", 0),
        dex_req=weapon_data.get("variable_dex_req", 0),
        ke_bonus=weapon_data.get("variable_bonus_KE", 0),
        te_bonus=weapon_data.get("variable_bonus_TE", 0),
        ve_bonus=weapon_data.get("variable_bonus_VE", 0)
    )
    
    if info.can_choose:
        # Show UI dialog: "How do you want to wield this weapon?"
        show_wielding_choice_dialog(unit, weapon, info)
    elif info.forced_two_handed:
        show_message(f"{unit.name} must wield {weapon.name} 2-handed (insufficient attributes)")
    
    # Apply current mode's combat stats
    apply_wielding_bonuses(unit, info.bonuses)
```

### Example 4: Combat Stats Calculation
```python
def calculate_unit_combat_stats(unit: Unit, weapon: Weapon) -> CombatStats:
    """Calculate unit's combat stats including wielding bonuses."""
    
    # Get wielding info with current preference
    info = get_wielding_info(
        unit, weapon,
        wield_mode=weapon_data["wield_mode"],
        strength_req=weapon_data["variable_strength_req"],
        dex_req=weapon_data["variable_dex_req"],
        ke_bonus=weapon_data["variable_bonus_KE"],
        te_bonus=weapon_data["variable_bonus_TE"],
        ve_bonus=weapon_data["variable_bonus_VE"],
        preference=unit.wielding_preference
    )
    
    # Base stats + weapon + wielding bonuses
    total_ke = unit.base_ke + weapon.ke_modifier + info.bonuses.ke_bonus
    total_te = unit.base_te + weapon.te_modifier + info.bonuses.te_bonus
    total_ve = unit.base_ve + weapon.ve_modifier + info.bonuses.ve_bonus
    
    return CombatStats(KE=total_ke, TE=total_te, VE=total_ve)
```

## Testing

**30 comprehensive tests** covering:

### Attribute Requirements (6 tests)
- Meets both requirements
- Fails strength requirement
- Fails dexterity requirement
- Exact requirements (boundary)
- One point below requirement
- No attributes

### Wielding Bonuses (5 tests)
- Bonuses with requirements and 2-handed
- No bonuses without requirements
- No bonuses wielding 1-handed
- Zero bonuses
- Partial bonuses

### Wielding Mode Determination (6 tests)
- Variable with requirements (defaults 1-handed)
- Variable with requirements (prefers 2-handed)
- Variable without requirements (forced 2-handed)
- Variable without requirements (ignores preference)
- Fixed 1-handed weapon
- Fixed 2-handed weapon

### Complete Wielding Info (5 tests)
- Variable strong unit 1-handed
- Variable strong unit 2-handed
- Variable weak unit forced 2-handed
- Fixed 1-handed weapon info
- Fixed 2-handed weapon info

### Mode Validation (4 tests)
- Can change to 1-handed with requirements
- Cannot change to 1-handed without requirements
- Can always change to 2-handed
- Cannot change fixed weapon

### Edge Cases (4 tests)
- All zero bonuses
- High requirements
- Zero requirements
- Unknown wield mode

## Integration Points

### With Attack Resolution
```python
from domain.mechanics import get_wielding_info, resolve_attack

# Calculate attack including wielding bonuses
info = get_wielding_info(attacker, attacker.weapon, ...)
attack_te_bonus = info.bonuses.te_bonus

result = resolve_attack(
    attacker=attacker,
    defender=defender,
    te_bonus=attack_te_bonus,
    ...
)
```

### With Equipment Loading
```python
from infrastructure.repositories import equipment_repository
from domain.mechanics import get_wielding_info

# Load weapon data
weapon_data = equipment_repository.get_weapon("longsword")

# Get wielding info for UI
info = get_wielding_info(
    unit, weapon,
    wield_mode=weapon_data["wield_mode"],
    strength_req=weapon_data.get("variable_strength_req", 0),
    ...
)
```

## Design Decisions

### Why Immutable Value Objects?
- **WieldingBonuses** and **WieldingInfo** are frozen dataclasses
- Makes them safe to pass around without worrying about mutation
- Easy to test and reason about

### Why Separate from Unit Entity?
- Weapon wielding is pure domain logic
- Doesn't require mutation of Unit entity
- Can be calculated on-the-fly when needed
- Unit can store wielding preference as optional field

### Why Not Store in Weapon Entity?
- Wielding depends on BOTH weapon AND unit
- Same weapon wielded differently by different units
- Keeps Weapon entity simple and reusable

## Future Enhancements

- [ ] **Stance system**: Different wielding modes could be combat stances
- [ ] **Fatigue costs**: Switching wielding modes could cost stamina
- [ ] **Combat modifiers**: Special attacks only available in certain modes
- [ ] **Skill bonuses**: Weapon mastery skills could improve 2-handed bonuses
- [ ] **Equipment slots**: 1-handed allows shields, 2-handed doesn't
- [ ] **Animation support**: Different attack animations per mode

---

*Last updated: 2025-01-XX*
*Status: Complete with 30 passing tests*
*Total mechanics tests: 145 passing*
