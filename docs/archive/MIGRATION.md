# Migration Guide - From Old to New Architecture

## Quick Reference: Where Things Moved

### Domain Logic

| Old Location | New Location | Status |
|-------------|--------------|--------|
| `core/unit_manager.py` → Unit | `domain/entities/__init__.py` | ✅ Migrated (with value objects) |
| `systems/combat_stats.py` | `domain/value_objects/__init__.py` | ✅ Migrated (CombatStats value object) |
| `systems/hex_grid.py` | `infrastructure/rendering/hex_grid.py` + `domain/value_objects/Position` | ✅ Migrated (split logic/data) |
| `systems/damage_calculator.py` | `domain/mechanics/damage.py` | ✅ Migrated (with tests) |
| `systems/reach.py` | `domain/mechanics/reach.py` | ✅ Migrated (with 28 tests) |
| `systems/weapon_wielding.py` | `domain/mechanics/weapon_wielding.py` | ✅ Migrated (with 30 tests) |
| `systems/skill_system.py` | TODO: `domain/mechanics/skills.py` | 📋 Pending |
| `systems/stamina_system.py` | `domain/mechanics/stamina.py` | ✅ Migrated (with 18 tests) |
| `systems/magic_system.py` | TODO: `domain/mechanics/magic.py` | 📋 Pending |
| `systems/conditions.py` | TODO: `domain/mechanics/conditions.py` | 📋 Pending |

### Data Loading

| Old Location | New Location | Pattern | Status |
|-------------|--------------|---------|--------|
| `systems/character_loader.py` | `infrastructure/repositories/character_repository.py` | Repository pattern | ✅ Complete |
| `systems/equipment_loader.py` | `infrastructure/repositories/equipment_repository.py` | Repository pattern | ✅ Complete |
| `rendering/sprite_manager.py` (loading) | `infrastructure/repositories/sprite_repository.py` | Repository pattern | ✅ Complete |
| `core/game_setup.py` | `domain/services.py` → UnitFactory | Factory pattern | ✅ Complete |
| N/A | `application/game_context.py` → GameContext (DI Container) | Service Locator | ✅ Complete |

### UI

| Old Location | New Location | Status |
|-------------|--------------|--------|
| `old_system/ui/menu.py` | `presentation/screens/menu_screen.py` | ✅ Migrated (with logging) |
| `old_system/ui/hud.py` | `presentation/components/hud.py` | ✅ Migrated (using domain entities) |
| `old_system/ui/unit_info_popup.py` | `presentation/components/unit_info_popup.py` | ✅ Migrated (using domain model) |
| `old_system/ui/scenario_selector.py` | `presentation/screens/scenario_screen.py` + 3 components | ✅ Migrated (with ScenarioConfig value object, character/map/roster components) |
| `old_system/ui/deployment_screen.py` | `presentation/screens/deployment_screen.py` | ✅ Migrated (hex grid placement, position validation, auto-advance) |

### Rendering

| Old Location | New Location | Status |
|-------------|--------------|--------|
| `old_system/rendering/sprite_manager.py` (masking) | `infrastructure/rendering/sprite_utils.py` | ✅ Migrated (using domain entities) |
| `old_system/rendering/renderer.py` | `infrastructure/rendering/battle_renderer.py` | ✅ Migrated (clean separation of concerns) |
| `old_system/rendering/camera.py` | `infrastructure/rendering/camera.py` | ✅ Migrated (with logging & extra utilities) |
| N/A | `infrastructure/rendering/__init__.py` | ✅ Complete (unified rendering API) |

### Actions

| Old Location | New Location | Status |
|-------------|--------------|--------|
| `actions/attack.py` | `domain/mechanics/actions/attack_action.py` | ✅ Migrated (AttackAction wraps resolve_attack) |
| `actions/movement.py` | `domain/mechanics/actions/movement_action.py` | ✅ Migrated (MovementAction path + ZoC metadata) |
| `actions/handler.py` | `application/action_handler.py` | ✅ Implemented (orchestrates actions + reactions) |

### Reactions (Phase 2)
### Armor (Layered Redesign)

| Old Location | New Location | Status |
|-------------|--------------|--------|
| `systems/armor_system.py` | `domain/mechanics/armor.py` | ✅ Redesigned (ArmorPiece, ArmorSystem, HitzoneResolver) |
| N/A | `domain/equipment/equipment_manager.py` | ✅ Implemented (equip + validate + MGT) |
| N/A | `domain/services.py` (UnitFactory) | ✅ Integrates ArmorSystem on unit creation |
| N/A | `domain/mechanics/attack_resolution.py` | ✅ Uses hit zone, zone SFÉ, overpower zone degrade, critical ignore |

**Integration Notes**:
- Attack flow now always selects a hit zone via HitzoneResolver (criticals included for future hooks).
- Overpower reduces outermost layer SFÉ for that zone before damage.
- Critical results ignore all armor SFÉ (after any overpower adjustment).

**Follow-ups**:
- Future: facing-dependent zone weighting, partial coverage, condition-based modifiers.
- UI loadout can surface overlap validation messages from ArmorSystem.

| Old Location | New Location | Status |
|-------------|--------------|--------|
| N/A (implicit in systems) | `domain/mechanics/reactions/opportunity_attack.py` | ✅ Implemented (OpportunityAttackReaction) |
| N/A | `domain/mechanics/reactions/base.py` | ✅ Implemented (Reaction protocol + result) |
| N/A | `application/reaction_handler.py` | ✅ Implemented (reaction budget & execution) |

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

**Goal**: Port scenario selector ✅ COMPLETE

**Completed Migration**:
1. ✅ Created `domain/value_objects/scenario_config.py` (UnitSetup, ScenarioConfig)
2. ✅ Created `presentation/screens/scenario_screen.py` (3-phase selection: map, team A, team B)
3. ✅ Created supporting components:
   - `presentation/components/map_preview.py` - background preview and scenario info
   - `presentation/components/roster_panel.py` - team roster display with validation
   - `presentation/components/character_preview.py` - character stats/skills/equipment preview
4. ✅ Uses domain value objects (UnitSetup, ScenarioConfig)
5. ✅ Emits action strings ("scenario_confirmed", "scenario_cancelled")
6. ✅ Integrated logging throughout

**Key Design Decisions**:
- ScenarioConfig is immutable value object with `with_*` methods
- Components accept pre-loaded data (no I/O in presentation layer)
- File scanning done by screen, caching for performance
- Validation indicators in roster panel (missing files highlighted)
- Three-phase flow: MAP → TEAM_A → TEAM_B

**Example Usage**:
```python
# In application layer
context = GameContext()
scenario_screen = ScenarioScreen(WIDTH, HEIGHT, context)

while not scenario_screen.is_complete():
    for event in pygame.event.get():
        scenario_screen.handle_event(event)
    
    scenario_screen.draw(screen)
    pygame.display.flip()

if scenario_screen.get_action() == "scenario_confirmed":
    config = scenario_screen.get_config()
    # Use config.team_a, config.team_b, config.map_name
```

### Deploying Units on Hex Grid

**Goal**: Port deployment screen ✅ COMPLETE

**Completed Migration**:
1. ✅ Created `presentation/screens/deployment_screen.py`
2. ✅ Hex grid unit placement with click-to-deploy
3. ✅ Position validation (prevents overlapping)
4. ✅ Auto-advance to next undeployed unit after placement
5. ✅ Reset all positions functionality
6. ✅ Visual feedback (hover highlighting, unit numbers)
7. ✅ Uses immutable ScenarioConfig with `with_deployment()` method

**Key Design Decisions**:
- Accepts ScenarioConfig from scenario selector, returns updated config with positions
- Uses UnitSetup.with_deployment() to create new instances with positions
- Converts mutable list during placement, builds immutable config on confirm
- Emits action strings: "deployment_confirmed", "deployment_cancelled"
- Integrates with hex_grid rendering infrastructure
- Sprite loading via sprite repository

**Example Usage**:
```python
# After scenario selection
config = scenario_screen.get_config()  # Has teams but no positions
deployment_screen = DeploymentScreen(WIDTH, HEIGHT, config, context)

while not deployment_screen.is_complete():
    for event in pygame.event.get():
        deployment_screen.handle_event(event)
    
    deployment_screen.draw(screen)
    pygame.display.flip()

if deployment_screen.get_action() == "deployment_confirmed":
    final_config = deployment_screen.get_config()
    # final_config now has all units with start_q, start_r, facing
    # Ready to create Unit entities and start battle
```

### Adding Game State Management

**Goal**: Create battle state orchestrator

**Steps**:
1. ✅ Create `application/battle_service.py`
2. ✅ Define BattleState with list of units, turn order, AP pool, round
3. ✅ Implement turn management logic + per-turn reaction reset
4. ✅ Use domain mechanics via `ActionHandler`
5. 📋 Emit events for UI updates (presentation wiring)

**Example**:
```python
from application.battle_service import BattleService
from application.action_handler import ActionHandler
from domain.value_objects import Position

battle = BattleService(units)
battle.start_battle()
u = battle.current_unit()

# Move example
summary = battle.move_current_unit(dest=Position(5, 3), potential_reactors=[enemy for enemy in units if enemy is not u])
if 'error' in summary:
    print('Move failed:', summary['error'])
else:
    print('AP spent:', summary['ap_spent'])

# Attack example
res = battle.attack_current_unit(defender=some_target)
print(res.get('action_result').message)
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
