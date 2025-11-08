# Migration Guide - From Old to New Architecture

## Quick Reference: Where Things Moved

### Domain Logic

| Old Location | New Location | Status |
|-------------|--------------|--------|
| `core/unit_manager.py` → Unit | `domain/entities/__init__.py` | ✅ Migrated (with value objects) |
| `systems/combat_stats.py` | `domain/value_objects/__init__.py` | ✅ Migrated (CombatStats value object) |
| `systems/hex_grid.py` | `infrastructure/rendering/hex_grid.py` + `domain/value_objects/Position` | ✅ Migrated (split logic/data) |
| `systems/damage_calculator.py` | `domain/mechanics/damage.py` | ✅ Migrated (with 28 tests) |
| `systems/reach.py` | `domain/mechanics/reach.py` | ✅ Migrated (with 28 tests) |
| `systems/weapon_wielding.py` | `domain/mechanics/weapon_wielding.py` | ✅ Migrated (with 30 tests) |
| `systems/skill_system.py` | TODO: `domain/mechanics/skills.py` | 📋 Pending |
| `systems/stamina_system.py` | `domain/mechanics/stamina.py` | ✅ Migrated (with 18 tests) |
| `systems/magic_system.py` | TODO: `domain/mechanics/magic.py` | 📋 Pending |
| `systems/conditions.py` | TODO: `domain/mechanics/conditions.py` | 📋 Pending |

### Data Loading

| Old Location | New Location | Pattern |
|-------------|--------------|---------|
| `systems/character_loader.py` | `infrastructure/repositories/character_repository.py` | Repository pattern |
| `systems/equipment_loader.py` | `infrastructure/repositories/equipment_repository.py` | Repository pattern |
| `rendering/sprite_manager.py` (loading) | `infrastructure/repositories/sprite_repository.py` | Repository pattern |
| `core/game_setup.py` | `domain/services.py` → UnitFactory | Factory pattern |

### UI

| Old Location | New Location | Status |
|-------------|--------------|--------|
| `ui/menu.py` | TODO: `presentation/screens/menu_screen.py` | Not ported |
| `ui/scenario_selector.py` | TODO: `presentation/screens/scenario_screen.py` | Not ported |
| `ui/deployment_screen.py` | TODO: `presentation/screens/deployment_screen.py` | Not ported |
| `ui/hud.py` | TODO: `presentation/components/hud.py` | Not ported |

### Rendering

| Old Location | New Location | Status |
|-------------|--------------|--------|
| `rendering/sprite_manager.py` (masking) | TODO: `infrastructure/rendering/sprite_utils.py` | Not ported |
| `rendering/renderer.py` | TODO: `infrastructure/rendering/battle_renderer.py` | Not ported |
| `rendering/camera.py` | TODO: `infrastructure/rendering/camera.py` | Not ported |

### Actions

| Old Location | New Location | Status |
|-------------|--------------|--------|
| `actions/attack.py` | TODO: `domain/mechanics/actions/attack.py` | Not ported |
| `actions/movement.py` | TODO: `domain/mechanics/actions/movement.py` | Not ported |
| `actions/handler.py` | TODO: `application/action_handler.py` | Not ported |

## Step-by-Step Migration for Specific Features

### Adding Combat Mechanics

**Goal**: Port damage calculation from old system

**Steps**:
1. Create `domain/mechanics/damage.py`
2. Copy damage logic from `old_system/systems/damage_calculator.py`
3. Refactor to use new value objects (Position, CombatStats, etc.)
4. Remove pygame/infrastructure dependencies
5. Write unit tests
6. Update UnitFactory or create DamageService

**Example**:
```python
# domain/mechanics/damage.py
from domain.value_objects import DamageResult, CombatStats
from domain.entities import Unit, Weapon

def calculate_damage(
    attacker: Unit,
    defender: Unit,
    weapon: Weapon
) -> DamageResult:
    # Pure domain logic - no I/O, no pygame
    base_damage = weapon.damage_max
    # ... calculation logic
    return DamageResult(
        base_damage=base_damage,
        final_damage=final_damage,
        armor_absorbed=absorbed,
        penetrated=penetrated
    )
```

### Adding a New UI Screen

**Goal**: Port scenario selector

**Steps**:
1. Create `presentation/screens/scenario_screen.py`
2. Create supporting components:
   - `presentation/components/map_preview.py`
   - `presentation/components/roster_panel.py`
   - `presentation/components/character_preview.py`
3. Use repositories from GameContext for data access
4. Keep UI logic separate from domain logic
5. Emit events/commands for state changes

**Example**:
```python
# presentation/screens/scenario_screen.py
class ScenarioScreen:
    def __init__(self, context: GameContext):
        self.context = context
        self.character_repo = context.character_repo
        self.sprite_repo = context.sprite_repo
        
        # Components
        self.map_preview = MapPreview()
        self.roster_panel = RosterPanel()
    
    def handle_event(self, event):
        # Handle input
        pass
    
    def draw(self, surface):
        # Render components
        self.map_preview.draw(surface)
        self.roster_panel.draw(surface)
```

### Adding Game State Management

**Goal**: Create battle state orchestrator

**Steps**:
1. Create `application/battle_service.py`
2. Define BattleState with list of units, turn order, etc.
3. Implement turn management logic
4. Use domain mechanics for actions
5. Emit events for UI updates

**Example**:
```python
# application/battle_service.py
from domain.entities import Unit
from domain.mechanics.damage import calculate_damage

class BattleService:
    def __init__(self, units: list[Unit]):
        self.units = units
        self.current_turn_index = 0
    
    def execute_attack(self, attacker_id: str, target_id: str):
        attacker = self._find_unit(attacker_id)
        target = self._find_unit(target_id)
        
        # Use domain mechanics
        result = calculate_damage(attacker, target, attacker.weapon)
        target.take_damage(result.final_damage)
        
        return result
```

## Common Patterns

### Pattern 1: Repository Access
```python
# ❌ Old way (direct file I/O in random places)
with open("characters/Warri.json") as f:
    data = json.load(f)

# ✅ New way (through repository)
char_repo = context.character_repo
data = char_repo.load("Warri.json")
```

### Pattern 2: Entity Creation
```python
# ❌ Old way (manual construction, scattered logic)
unit = Unit(q, r, sprite)
unit.name = data.get("Név")
unit.set_combat(data.get("Harci értékek"))
# ... 20 more lines

# ✅ New way (factory handles complexity)
unit = context.unit_factory.create_unit(
    character_filename="Warri.json",
    position=Position(q, r)
)
```

### Pattern 3: Value Objects Instead of Primitives
```python
# ❌ Old way (primitive obsession)
def move_unit(unit, q, r):
    unit.q = q
    unit.r = r

# ✅ New way (rich domain model)
def move_unit(unit: Unit, new_pos: Position):
    unit.move_to(new_pos)
```

### Pattern 4: Immutable State Where Possible
```python
# ❌ Old way (mutable state)
unit.fp -= 5  # Modifies in place

# ✅ New way (immutable value object)
unit.spend_fatigue(5)  # Creates new ResourcePool internally
```

## Testing the New Architecture

### Run Architecture Test
```bash
cd d:\_Projekt\_MAGUS_RPG\MAGUS_pygame
python main.py
```

### Run Unit Tests (TODO)
```bash
pytest tests/
```

### Check Imports
```bash
python -c "from application.game_context import GameContext; print('✓ OK')"
```

## Checklist for Porting a Feature

- [ ] Identify domain logic (pure business rules)
- [ ] Identify infrastructure (I/O, rendering, external libs)
- [ ] Create domain entities/value objects if needed
- [ ] Create or update repositories for data access
- [ ] Implement domain logic in `domain/mechanics/`
- [ ] Create application service if orchestration needed
- [ ] Create UI components in `presentation/`
- [ ] Wire dependencies through GameContext
- [ ] Add logging with existing logger
- [ ] Test with minimal example
- [ ] Update ARCHITECTURE.md if adding new patterns

## Benefits You'll Notice

1. **Easier Testing**: Domain logic can be tested without pygame
2. **Clearer Code**: Each module has one clear responsibility
3. **Better IDE Support**: Proper types and imports
4. **Easier Debugging**: Clear data flow through layers
5. **Faster Development**: Less hunting for where things are

## Getting Help

- Read `ARCHITECTURE.md` for design principles
- Check `old_system/` to see how things worked before
- Look at existing implementations (UnitFactory, TestScreen) as examples
- Follow established patterns for consistency
