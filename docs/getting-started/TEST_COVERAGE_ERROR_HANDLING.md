# Test Coverage & Error Handling

## Test Coverage Reporting

### Overview

Test coverage shows what percentage of your code is executed by tests. This helps identify untested critical paths that could hide bugs.

**Current Coverage Snapshot:**
```
Domain Mechanics:     30-60% (combat paths partially tested)
Application Layer:    25-30% (services tested at higher level)
Gamemaster Tools:      0% (no unit tests, but UI works manually)
Total:            ~5.82% (focus on domain/application, not UI)
```

### Running Coverage Reports

**Generate HTML report:**
```bash
poetry run pytest --cov=MAGUS_pygame --cov=Gamemaster_tools --cov-report=html
# Opens: htmlcov/index.html in your browser
```

**Show missing lines in terminal:**
```bash
poetry run pytest --cov=MAGUS_pygame --cov=Gamemaster_tools --cov-report=term-missing
# Lists exactly which lines aren't covered
```

**Generate JSON report (for CI):**
```bash
poetry run pytest --cov=MAGUS_pygame --cov=Gamemaster_tools --cov-report=json
# Creates: coverage.json for tracking over time
```

### Coverage Configuration

Located in `.coveragerc`:
- Tracks `MAGUS_pygame/` and `Gamemaster_tools/`
- Excludes test files, `__pycache__`, `old_system/`
- Excludes abstract methods, `TYPE_CHECKING` blocks
- Reports with 2 decimal precision

### Key Metrics to Track

| Module | Coverage | Priority | Notes |
|--------|----------|----------|-------|
| `domain/mechanics/` | 30-60% | HIGH | Combat formulas—bugs here break gameplay |
| `domain/entities/` | 60-80% | HIGH | Unit/weapon/armor logic |
| `application/` | 25-35% | MEDIUM | Services orchestrate domain |
| `infrastructure/` | 0-20% | LOW | Repositories, rendering (mostly UI) |
| Gamemaster_tools/ | 0% | LOW | PySide6 UI (manual testing sufficient) |

### Improving Coverage

Start with high-priority gaps:

1. **Combat damage calculation** - Add tests for edge cases (zero damage, armor absorption, critical overpowers)
2. **Equipment validation** - Test all slot/type combinations
3. **Stamina system** - Test recovery, thresholds, conditions
4. **Scenario service** - Test team limits, duplicates, config building

Example:
```python
def test_critical_damage_penetrates_heavy_armor():
    """Ensure critical+overpower always deal damage."""
    attacker = Unit(..., strength=10)
    defender = Unit(..., armor=[full_plate, chainmail])
    
    # Should penetrate even with high armor
    result = service.resolve_attack(attacker, defender, critical=True, overpower=True)
    assert result.ep_loss > 0
```

---

## Error Handling Utilities

### Overview

Two sets of utilities for robust error handling:

1. **`MAGUS_pygame/utils/error_handling.py`** - Domain/application errors
2. **`Gamemaster_tools/utils/error_handling.py`** - PySide6 UI errors

### Core Functions

#### Domain/Application Layer

```python
from MAGUS_pygame.utils.error_handling import (
    safe_json_load,
    validate_required_fields,
    ValidationError,
    DataLoadError,
)

# Safe JSON loading
data = safe_json_load(Path("data/character.json"), description="character")
if data is None:
    print("File missing or corrupt")

# Validate data structure
try:
    validate_required_fields(data, ["name", "attributes", "skills"], "character model")
except ValidationError as e:
    print(f"Invalid data: {e}")  # Shows missing fields

# Custom validation
if data.get("level") < 1:
    raise ValidationError("Invalid level", {"level": data.get("level")})
```

#### PySide6 UI Layer

```python
from Gamemaster_tools.utils.error_handling import (
    show_error_dialog,
    safe_load_json_file,
    safe_save_json_file,
)

# Show user-friendly error
show_error_dialog(
    self,  # parent widget
    "Character Load Failed",
    "Could not load the character file.",
    "The file may be corrupted. Try restoring from a backup."
)

# Safe file I/O with dialog
data = safe_load_json_file(Path("characters/hero.json"), parent=self, description="character")
if data:
    # Use data...
    success = safe_save_json_file(Path("characters/hero.json"), updated_data, parent=self)
    if success:
        print("Saved!")
```

### Exception Types

**ValidationError**
```python
raise ValidationError("Missing required fields", {"fields": ["name", "class"]})
# Shows: Missing required fields (fields=['name', 'class'])
```

**DataLoadError**
```python
try:
    parse_equipment()
except Exception as e:
    raise DataLoadError(file_path, "Invalid equipment JSON", e)
# Shows: Failed to load equipment.json: Invalid equipment JSON
```

### Error Logging

All errors automatically logged with context:

```python
# Logs: ERROR - File not found: data/scenarios/forest.json (scenario)
safe_json_load("data/scenarios/forest.json", "scenario")

# Logs: WARNING - File not found, returning None
# Logs: CRITICAL - Invalid JSON (line 15, col 5): ...
```

### Best Practices

**1. Use safe loading for external data**
```python
# Good ✓
character_data = safe_json_load(file_path, "character")
if character_data:
    process_character(character_data)

# Bad ✗
with open(file_path) as f:
    data = json.load(f)  # Crashes on invalid JSON
```

**2. Validate early**
```python
# Good ✓
try:
    validate_required_fields(data, ["name", "level"], "character")
    equipment = data.get("equipment", {})
    validate_required_fields(equipment, ["armor", "weapon"], "equipment")
except ValidationError as e:
    logger.error(f"Invalid data: {e}")

# Bad ✗
name = data["name"]  # KeyError if missing
```

**3. Show errors to users (UI)**
```python
# Good ✓
if not safe_save_json_file(path, data, parent=self):
    return  # User already saw error dialog

# Bad ✗
safe_save_json_file(path, data)
# User has no idea it failed
```

**4. Context in error messages**
```python
# Good ✓
raise ValidationError(
    "Strength requirement too high",
    {"weapon": "longsword", "requirement": 20, "found": 15}
)

# Bad ✗
raise ValidationError("Invalid")  # No context
```

---

## Integration Points

### Character Loader
Use `safe_json_load()` when opening character files:
```python
from MAGUS_pygame.utils.error_handling import safe_json_load

char_data = safe_json_load(char_path, "character")
if char_data:
    self.display_character(char_data)
else:
    self.show_warning("Character file not found or corrupted")
```

### Equipment Manager
Validate equipment on load:
```python
from MAGUS_pygame.utils.error_handling import validate_required_fields

equipment = safe_json_load("data/equipment.json", "equipment")
validate_required_fields(equipment, ["id", "name", "type", "sfe"], "equipment item")
```

### Scenario Service
Show user-friendly errors when loading scenarios:
```python
from Gamemaster_tools.utils.error_handling import show_error_dialog

try:
    scenario = safe_load_json_file(path, parent=self, "scenario")
except Exception as e:
    show_error_dialog(self, "Scenario Load Failed", str(e))
```

---

## Quick Commands

```bash
# Run tests (with coverage by default)
poetry run pytest

# See coverage report in HTML
poetry run pytest --cov-report=html
open htmlcov/index.html  # On macOS
# Or open htmlcov/index.html on Windows

# See which lines aren't tested
poetry run pytest --cov-report=term-missing

# Run specific test
poetry run pytest MAGUS_pygame/tests/test_damage.py -v

# Run tests matching pattern
poetry run pytest -k "combat" -v
```
