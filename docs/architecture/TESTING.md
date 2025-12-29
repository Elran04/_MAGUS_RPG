# Testing Guide - MAGUS_RPG Monorepo

This monorepo contains tests for two separate Python packages in a single `tests/` folder:

1. **tests/pygame/** - MAGUS_pygame tests (198 tests)
2. **tests/gamemaster_tools/** - Gamemaster_tools tests (6 tests)

## Quick Start

```bash
# Run pygame tests
pytest tests/pygame

# Run gamemaster_tools tests  
pytest tests/gamemaster_tools

# Run both tests sequentially
pytest tests/pygame tests/gamemaster_tools
```

## Why Separate Test Runs?

Both MAGUS_pygame and Gamemaster_tools have their own `config/` and `utils/` packages. When pytest discovers both test directories simultaneously (`pytest tests`), Python's import system cannot distinguish between:

```python
from config import SOME_CONSTANT  # Which package's config?
```

Even though we use `pytest_configure` hooks to manage `sys.path`, imports happen at module load time during test collection. By the time we could switch sys.path priority, both packages' imports have already failed.

**Solution**: Run test directories separately or explicitly specify both paths in sequence.

## Test Organization

```
tests/
├── __init__.py
├── pygame/              # 198 tests for MAGUS_pygame
│   ├── __init__.py
│   ├── test_armor.py
│   ├── test_attack_resolution.py
│   ├── test_damage.py
│   ├── test_reaction_handler.py
│   ├── test_unit_setup_service.py
│   ├── test_game_flow_service.py
│   └── ... (19 test files total)
│
└── gamemaster_tools/    # 6 tests for Gamemaster_tools
    ├── __init__.py
    ├── test_placeholder_manager.py
    └── test_error_handling_utils.py
```

## Root conftest.py

Located at the project root, this handles sys.path management for both packages:
- Detects which test suite is being run from command line arguments
- Sets package priority appropriately before test collection
- Supports running both suites sequentially

## Coverage Reports

```bash
# Coverage for pygame only
pytest tests/pygame --cov=MAGUS_pygame --cov-report=html

# Coverage for gamemaster_tools only
pytest tests/gamemaster_tools --cov=Gamemaster_tools --cov-report=html

# Both sequentially with separate reports
pytest tests/pygame --cov=MAGUS_pygame
pytest tests/gamemaster_tools --cov=Gamemaster_tools
```

## Test Results

- **Total**: 204 tests
  - pygame: 198 tests ✅
  - gamemaster_tools: 6 tests ✅

All tests pass when run with correct sys.path priority.

## CI/CD Recommendation

```bash
# Run tests separately in your CI pipeline
pytest tests/pygame -v
pytest tests/gamemaster_tools -v
```

Or use a bash/PowerShell script to manage sequential execution and aggregated results.

