# Archived: Scenario Selection Refactoring

Historical design notes for refactoring the scenario selection flow. Current scenario flow is maintained under services and presentation phases; refer to `docs/DEVELOPER_GUIDE.md` and code for up-to-date behavior.

---

# Scenario Selection Refactoring

## Problem
The original `scenario_screen.py` was a monolithic 559-line file handling all selection phases:
- Map selection with preview
- Team A composition
- Team B composition
- Navigation and validation

This made it:
- **Hard to extend**: Adding equipment phase would make it even larger
- **Hard to test**: All logic coupled in one class
- **Hard to maintain**: Mixed concerns (UI, validation, state management)
- **Hard to reuse**: Team composition logic duplicated for both teams

## Solution: Phase-Based Architecture

Break scenario selection into **independent, reusable phases**:

```
presentation/screens/scenario_phases/
├── __init__.py              # Public exports
├── phase_base.py            # Abstract base class
├── map_phase.py             # Map selection (210 lines)
├── team_phase.py            # Team composition (282 lines, reusable)
├── equipment_phase.py       # Equipment selection (TODO: 130 lines placeholder)
└── (future phases)          # Easy to add new phases

presentation/screens/
├── scenario_screen.py       # Original (kept for compatibility)
└── scenario_screen_v2.py    # New coordinator (232 lines)
```

### Architecture Benefits

#### 1. **Single Responsibility**
Each phase handles one concern:
- `MapSelectionPhase`: Map selection + preview
- `TeamCompositionPhase`: Character selection + roster building
- `EquipmentPhase`: Equipment assignment (TODO)
- `ScenarioScreenV2`: Flow coordination only

#### 2. **Reusability**
`TeamCompositionPhase` is used twice (Team A and Team B) with different parameters:
```python
team_a_phase = TeamCompositionPhase(
    width, height, context,
    is_team_a=True,
    team_name="Team A (Blue)"
)

team_b_phase = TeamCompositionPhase(
    width, height, context,
    is_team_a=False,
    team_name="Team B (Red)"
)
```

#### 3. **Extensibility**
Adding new phases is trivial:
```python
# Create new phase file
class TacticalOptionsPhase(SelectionPhaseBase):
    def handle_event(self, event): ...
    def draw(self, surface): ...
    def can_proceed(self): ...

# Add to coordinator
self.current_phase = FlowPhase.TACTICAL_OPTIONS
self.tactical_phase = TacticalOptionsPhase(...)
```

#### 4. **Testability**
Each phase can be tested in isolation:
```python
# Test map selection
map_phase = MapSelectionPhase(width, height, context)
assert map_phase.can_proceed() == True
map_phase.handle_event(enter_key_event)
assert map_phase.is_completed() == True

# Test team composition with mock service
team_phase = TeamCompositionPhase(width, height, mock_context, True, "Test Team")
assert team_phase.can_proceed() == False  # No units added
mock_context.scenario_service.add_unit(True, "char.json", "sprite.png")
assert team_phase.can_proceed() == True
```

## Phase Interface

All phases implement `SelectionPhaseBase`:

```python
class SelectionPhaseBase(ABC):
    """Common interface for all selection phases."""
    
    @abstractmethod
    def handle_event(self, event: pygame.event.Event) -> None:
        """Process user input."""
        pass
    
    @abstractmethod
    def draw(self, surface: pygame.Surface) -> None:
        """Render phase UI."""
        pass
    
    @abstractmethod
    def can_proceed(self) -> bool:
        """Validate if can advance to next phase."""
        pass
    
    def is_completed(self) -> bool:
        """Check if user confirmed and moved forward."""
        return self.completed
    
    def is_cancelled(self) -> bool:
        """Check if user cancelled (go back)."""
        return self.cancelled
    
    def reset(self) -> None:
        """Reset state when returning to phase."""
        self.completed = False
        self.cancelled = False
```

## Flow Coordination

`ScenarioScreenV2` manages the phase sequence:

```python
FlowPhase.MAP
    ↓ (user confirms)
FlowPhase.TEAM_A
    ↓ (user confirms)
FlowPhase.TEAM_B
    ↓ (user confirms)
FlowPhase.EQUIPMENT
    ↓ (user confirms)
Complete → "scenario_confirmed"

(ESC at any point goes back or cancels)
```

### Coordinator Responsibilities
- Initialize current phase screen
- Forward events to active phase
- Detect completion/cancellation
- Navigate between phases
- Build final ScenarioConfig

### Phase Responsibilities
- Render own UI
- Handle own input
- Validate own state
- Signal completion/cancellation

## Migration Path

### Current Usage (scenario_screen.py)
```python
# In start_game.py or main.py
scenario_screen = ScenarioScreen(WIDTH, HEIGHT, context)
while not scenario_screen.is_complete():
    scenario_screen.handle_event(event)
    scenario_screen.draw(screen)
    if scenario_screen.get_action() == "scenario_confirmed":
        config = scenario_screen.get_config()
```

### New Usage (scenario_screen_v2.py)
```python
# Drop-in replacement
scenario_screen = ScenarioScreenV2(WIDTH, HEIGHT, context)
while not scenario_screen.is_complete():
    scenario_screen.handle_event(event)
    scenario_screen.draw(screen)
    if scenario_screen.get_action() == "scenario_confirmed":
        config = scenario_screen.get_config()
```

**Same interface, different implementation!**

## Equipment Phase Implementation

The equipment phase placeholder is ready for implementation:

```python
class EquipmentPhase(SelectionPhaseBase):
    """Equipment selection for all units.
    
    TODO Features:
    - Iterate through all units (Team A + Team B)
    - Select weapons from equipment repository
    - Choose armor/protection
    - Validate equipment restrictions (class/race requirements)
    - Preview stat changes
    - Store equipment choices in unit data
    """
```

### Suggested Equipment Flow
1. **Unit Selection**: Choose which unit to equip (from combined roster)
2. **Weapon Slots**: Primary weapon, secondary weapon, ranged weapon
3. **Armor Slots**: Head, torso, legs, hands, feet
4. **Inventory**: Consumables, tools, magic items
5. **Validation**: Check class/race restrictions, weight limits
6. **Preview**: Show stat changes (AC, damage, speed)

### Integration with Domain
Equipment choices should be stored in `UnitSetup`:
```python
@dataclass
class UnitSetup:
    character_file: str
    sprite_file: str
    equipment: dict[str, str] = field(default_factory=dict)  # NEW
    # equipment = {
    #     "primary_weapon": "longsword.json",
    #     "armor": "chainmail.json",
    #     "shield": "round_shield.json"
    # }
```

## File Size Comparison

### Before (Monolithic)
- `scenario_screen.py`: **559 lines** (all logic)

### After (Modular)
- `phase_base.py`: 76 lines (interface)
- `map_phase.py`: 210 lines (map selection)
- `team_phase.py`: 282 lines (team composition, reusable)
- `equipment_phase.py`: 130 lines (placeholder)
- `scenario_screen_v2.py`: 232 lines (coordinator)
- **Total: 930 lines** (but highly organized and reusable)

**930 vs 559**: More code, but:
- ✅ Each file has single responsibility
- ✅ Team phase reused for both teams
- ✅ Easy to add equipment phase
- ✅ Easy to test each phase
- ✅ Clear separation of concerns

## Future Extensions

Easy to add:
- **Handicap Phase**: Configure difficulty modifiers
- **Tactical Options Phase**: Choose battle rules (permadeath, fog of war, etc.)
- **Briefing Phase**: Show mission objectives before deployment
- **Quick Setup Phase**: Preset templates for rapid testing

Each is just a new phase class + one line in coordinator.

## Testing Strategy

### Unit Tests
```python
def test_map_phase_selection():
    phase = MapSelectionPhase(1024, 768, mock_context)
    assert phase.can_proceed() == True
    phase.handle_event(confirm_event)
    assert phase.is_completed() == True

def test_team_phase_empty_roster():
    phase = TeamCompositionPhase(1024, 768, mock_context, True, "Team A")
    assert phase.can_proceed() == False
    
def test_team_phase_with_units():
    phase = TeamCompositionPhase(1024, 768, mock_context, True, "Team A")
    mock_context.scenario_service.add_unit(True, "char.json", "sprite.png")
    assert phase.can_proceed() == True
```

### Integration Tests
```python
def test_full_scenario_flow():
    coordinator = ScenarioScreenV2(1024, 768, context)
    
    # Map phase
    assert coordinator.current_phase == FlowPhase.MAP
    coordinator.handle_event(enter_event)
    assert coordinator.current_phase == FlowPhase.TEAM_A
    
    # Team A phase
    add_units_to_team_a(coordinator)
    coordinator.handle_event(enter_event)
    assert coordinator.current_phase == FlowPhase.TEAM_B
    
    # Team B phase
    add_units_to_team_b(coordinator)
    coordinator.handle_event(enter_event)
    assert coordinator.current_phase == FlowPhase.EQUIPMENT
    
    # Equipment phase
    coordinator.handle_event(enter_event)
    assert coordinator.is_complete() == True
    assert coordinator.get_action() == "scenario_confirmed"
```

## Performance Considerations

- **Lazy Initialization**: Phases created only when entered
- **Caching**: Each phase caches its own data (no global cache)
- **Memory**: Old phases can be garbage collected when coordinator advances
- **Rendering**: Only active phase renders (no hidden overhead)

## Backward Compatibility

`scenario_screen.py` remains unchanged for gradual migration:
1. New features use `scenario_screen_v2.py`
2. Old code continues using `scenario_screen.py`
3. Eventually deprecate and remove old version

## Summary

✅ **Before**: 559-line monolith, hard to extend
✅ **After**: Modular phases, easy to extend
✅ **Equipment Phase**: Ready to implement
✅ **Testing**: Each phase testable in isolation
✅ **Reusability**: Team phase used twice
✅ **Extensibility**: Add phases without touching existing code
