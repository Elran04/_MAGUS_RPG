# Architectural Improvements - November 2025

## Overview
This document summarizes the architectural refactorings applied to improve code quality, maintainability, and adherence to clean architecture principles.

## 1. Config Module Star Import Elimination

**Problem**: The `config/__init__.py` module used `from config.config import *` anti-pattern, which:
- Obscures dependencies
- Makes refactoring difficult
- Hides what's actually exported
- Can cause namespace pollution

**Solution**: Replaced star import with explicit imports and organized `__all__` list.

**Files Changed**:
- `config/__init__.py`

**Benefits**:
- Clear visibility of all exported configuration values
- Organized exports by category (Display, Colors, Game Modes, etc.)
- IDE autocomplete works better
- Breaking changes are immediately visible

**Example**:
```python
# Before
from config.config import *

# After
from config.config import (
    # Display & Grid Configuration
    WIDTH,
    HEIGHT,
    HEX_SIZE,
    # ... explicit imports
)

__all__ = [
    # Display & Grid Configuration
    "WIDTH",
    "HEIGHT",
    # ... organized exports
]
```

## 2. Event Bus Dependency Injection

**Problem**: The event bus used module-level state with `Optional[Queue]` that required external initialization via `init_queues()`:
- Fragile state management
- Not testable in isolation
- Violates dependency injection principles
- Hidden dependencies between processes

**Solution**: Created `EditorEventBus` class accepting queue instances in constructor.

**Files Changed**:
- `infrastructure/events/event_bus.py` (new class-based implementation)
- `main.py` (creates and injects bus instance)
- `presentation/screens/scenario_editor_screen.py` (receives bus via DI)
- `presentation/desktop/editor_tool_window.py` (receives bus via DI)

**Benefits**:
- Explicit dependencies (queues passed at construction)
- Testable (can mock queues easily)
- No global state
- Clear ownership (main process creates and distributes)
- Type-safe (event_bus is typed as `EditorEventBus`, not module reference)

**Example**:
```python
# Before (module-level state)
from infrastructure.events import editor_event_bus as bus
bus.init_queues(ui_to_game_queue, game_to_ui_queue)
bus.publish(event)

# After (dependency injection)
from infrastructure.events.event_bus import EditorEventBus

event_bus = EditorEventBus(ui_to_game_queue, game_to_ui_queue)
scenario_editor.set_event_bus(event_bus)
event_bus.publish(event)
```

**Architecture Pattern**:
```
main.py
  ├─> Creates multiprocessing.Queue instances
  ├─> Creates EditorEventBus(queue_ui_to_game, queue_game_to_ui)
  ├─> Injects into ScenarioEditorScreen
  └─> Passes queues to run_tool_window() subprocess
       └─> Creates second EditorEventBus instance in subprocess
```

## 3. Application Service Layer with Facades

**Problem**: Presentation layer bypassed application services to access repositories directly:
- Violates clean architecture layers
- Duplicates business logic across screens
- Hard to change data access patterns
- Tight coupling between presentation and infrastructure

**Solution**: Added facade methods to `ScenarioService` for common presentation operations.

**Files Changed**:
- `application/scenario_service.py` (added facade methods)
- `presentation/screens/scenario_screen.py` (uses facades instead of direct repository access)

**New Facade Methods**:
- `get_scenario_list()` → list available scenarios
- `load_scenario_data(name)` → load raw scenario data
- `get_scenario_preview_data(name)` → load formatted preview data
- `get_background_path(name)` → resolve background file path

**Benefits**:
- Presentation layer doesn't know about repositories
- Single point of change for data access
- Can add caching/validation in service layer
- Follows dependency inversion principle
- Easier to test presentation components (mock service instead of repository)

**Example**:
```python
# Before (direct repository access)
scenarios = context.scenario_repo.list_scenarios()
data = context.scenario_repo.load_scenario(name)
bg = context.scenario_repo.resolve_background(name)

# After (service facade)
scenarios = context.scenario_service.get_scenario_list()
data = context.scenario_service.get_scenario_preview_data(name)
bg = context.scenario_service.get_background_path(name)
```

**Architecture Compliance**:
```
Presentation Layer (scenario_screen.py)
    ↓ (only calls)
Application Layer (scenario_service.py)
    ↓ (only calls)
Infrastructure Layer (scenario_repository.py)
```

## Remaining Recommendations

These architectural issues were identified but left for user implementation:

### 1. Component Reorganization (MEDIUM priority)
- Create `presentation/components/shared/` for reusable components
- Move `map_preview.py` to shared (remove duplicate)
- Move `editor_tool_window.py` to `components/scenario_editor/`
- Organize by feature, not type

### 2. Old System Cleanup (LOW priority)
- Archive or remove `old_system/` directory
- Keep only for reference if needed
- Document migration path if preserving

## Testing Recommendations

To validate these improvements:

1. **Config Module**: Import any config value in new module, verify autocomplete works
2. **Event Bus**: Run scenario editor, verify tool window communication works
3. **Service Facades**: Run scenario selection screen, verify loading works

## Migration Notes

No breaking changes for existing functionality. All changes are internal refactorings that maintain the same public interfaces.

## Future Improvements

Consider adding:
- Unit tests for `EditorEventBus` (now easily testable)
- Integration tests for service facades
- Configuration validation on startup
- Service layer for character/sprite data (following same facade pattern)
