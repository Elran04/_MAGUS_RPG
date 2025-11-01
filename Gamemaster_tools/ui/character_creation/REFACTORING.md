# Character Creation Module Refactoring

## Overview
The character creation module has been refactored to improve maintainability by splitting large monolithic files into smaller, focused components.

## New Structure

### Helpers (Business Logic)
Located in `ui/character_creation/helpers/`

#### 1. `skill_db_helper.py` - SkillDatabaseHelper
**Purpose**: Centralized database access for skills
**Responsibilities**:
- Database path resolution (class DB vs skills DB)
- Fetching class skills from database
- Processing skill entries (name, parameter, placeholder status)
- Calculating KP costs for skills
- Skill display name parsing
- Skill lookup by ID or display name

**Key Methods**:
- `get_db_path(db_type)` - Get path to class or skill database
- `fetch_class_skills(class_id, spec_id)` - Fetch skills for a class/specialization
- `process_skill_entries(skills)` - Convert raw DB rows to structured entries
- `calc_kp_cost(skill_id, level, percent)` - Calculate KP cost
- `parse_skill_display(display)` - Parse "Name (Parameter)" format
- `get_skill_name_and_param(skill_id)` - Lookup skill details

#### 2. `skill_prerequisites.py` - SkillPrerequisiteChecker
**Purpose**: Validate skill prerequisites
**Responsibilities**:
- Check attribute prerequisites (minimum values)
- Check skill prerequisites (required skills and levels)
- Format prerequisite error messages
- Support both level-based and percentage-based skills

**Key Methods**:
- `check_prerequisites(skill_id, level, percent, current_skills, attributes)` - Main validation
- `_check_attribute_prerequisites(...)` - Validate attribute requirements
- `_check_skill_prerequisites(...)` - Validate skill requirements
- `_format_skill_req(...)` - Format error messages

### Widgets (UI Components)
Located in `ui/character_creation/widgets/`

#### 3. `placeholder_skill_manager.py` - PlaceholderSkillManager
**Purpose**: Manage placeholder skill resolution
**Responsibilities**:
- Track user's placeholder skill choices
- Compute which skills are "taken" (to prevent duplicates)
- Get valid resolution options (respecting prerequisites)
- Build complete skills map from fixed + chosen skills

**Key Methods**:
- `compute_taken_skills(exclude_instance)` - Get set of assigned skill IDs
- `get_valid_resolutions(placeholder_id, ...)` - Get available choices for a placeholder
- `set_choice(instance_key, skill_id)` - Record user's placeholder choice
- `get_choice(instance_key)` - Retrieve user's choice
- `build_skills_map_from_choices(...)` - Generate complete skills inventory

## Benefits of Refactoring

### 1. **Separation of Concerns**
- **Database logic** isolated in `SkillDatabaseHelper`
- **Validation logic** isolated in `SkillPrerequisiteChecker`
- **State management** isolated in `PlaceholderSkillManager`
- **UI orchestration** remains in `SkillsStepWidget`

### 2. **Improved Testability**
Each component can now be unit tested independently:
```python
# Test database helper without UI
db_helper = SkillDatabaseHelper(base_dir)
skills = db_helper.fetch_class_skills("harcos", None)

# Test prerequisite checker with mock data
prereq_checker = SkillPrerequisiteChecker(db_helper)
ok, reasons = prereq_checker.check_prerequisites(
    "skill_001", 
    level=3, 
    current_skills={}, 
    attributes={"Erő": 15}
)

# Test placeholder manager with mock dependencies
placeholder_mgr = PlaceholderSkillManager(mock_placeholder_mgr, prereq_checker)
valid_choices = placeholder_mgr.get_valid_resolutions(...)
```

### 3. **Reusability**
Components can be reused in other parts of the application:
- `SkillDatabaseHelper` can be used anywhere skills need to be loaded
- `SkillPrerequisiteChecker` can validate prerequisites in character editing
- `PlaceholderSkillManager` logic can be adapted for item placeholders

### 4. **Maintainability**
- **Smaller files**: Each file has a single, clear responsibility
- **Clear interfaces**: Public methods document what each component does
- **Reduced complexity**: Easier to understand and modify individual components
- **Better navigation**: Find the code you need faster

### 5. **Type Safety**
All new components include proper type hints:
```python
def check_prerequisites(
    self,
    skill_id: str,
    req_level: int,
    req_percent: int,
    current_skills: dict[str, dict[str, Any]],
    attributes: dict[str, int],
) -> tuple[bool, list[str]]:
```

## Migration Path

### Before Refactoring
`skills_step.py` was 681 lines with:
- UI building
- Database access
- Prerequisite checking
- Placeholder management
- Table rendering
- Event handling

### After Refactoring
`skills_step.py` will be ~300-400 lines focusing on:
- UI orchestration
- Event handling
- Coordinating between helpers and widgets

The extracted logic is now in:
- `skill_db_helper.py` (~150 lines)
- `skill_prerequisites.py` (~140 lines)
- `placeholder_skill_manager.py` (~120 lines)

## Usage Example

```python
from ui.character_creation.helpers.skill_db_helper import SkillDatabaseHelper
from ui.character_creation.helpers.skill_prerequisites import SkillPrerequisiteChecker
from ui.character_creation.widgets.placeholder_skill_manager import PlaceholderSkillManager

class SkillsStepWidget(QtWidgets.QWidget):
    def __init__(self, base_dir, placeholder_mgr, ...):
        # Initialize helpers
        self.db_helper = SkillDatabaseHelper(base_dir)
        self.prereq_checker = SkillPrerequisiteChecker(self.db_helper)
        self.placeholder_manager = PlaceholderSkillManager(
            placeholder_mgr, 
            self.prereq_checker
        )
        
    def _load_skills(self):
        # Use database helper
        skills = self.db_helper.fetch_class_skills(class_id, spec_id)
        entries, fixed = self.db_helper.process_skill_entries(skills)
        
        # Update placeholder manager
        self.placeholder_manager.set_fixed_skills(fixed)
        
        # Use prerequisite checker
        ok, reasons = self.prereq_checker.check_prerequisites(...)
```

## Next Steps

1. ✅ Created helper modules (`skill_db_helper.py`, `skill_prerequisites.py`)
2. ✅ Created widget module (`placeholder_skill_manager.py`)
3. ⏳ Refactor `skills_step.py` to use new components
4. ⏳ Test end-to-end functionality
5. ⏳ Consider further splitting of table rendering logic

## Future Enhancements

### Possible Additional Splits
- `skills_table_widget.py` - Dedicated widget for skills table rendering
- `skill_row_renderer.py` - Extract row rendering logic
- `skill_export_helper.py` - Extract skill export/serialization

### Performance Optimizations
- Cache database connections
- Batch prerequisite checks
- Lazy loading of skill data

### Error Handling
- Add comprehensive error logging
- User-friendly error messages
- Graceful degradation on DB errors
