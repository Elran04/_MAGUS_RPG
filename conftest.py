"""
Root pytest configuration for MAGUS_RPG tests.

This project has tests for two separate packages:
- tests/pygame/ for MAGUS_pygame tests (198 tests)
- tests/gamemaster_tools/ for Gamemaster_tools tests (6 tests)

Each package has config/ and utils/ namespaces that collide if both are on sys.path
with wrong priority. We detect the target test directory from pytest args and set
the correct priority before test collection begins.

RECOMMENDED USAGE:
  pytest tests/pygame          # Run pygame tests only (198 tests)
  pytest tests/gamemaster_tools # Run gamemaster_tools tests only (6 tests)
  pytest tests/pygame tests/gamemaster_tools  # Run both sequentially

Running "pytest tests" will fail due to namespace collision - use one of the above instead.
"""

import sys
from pathlib import Path


def pytest_configure(config):
    """
    Configure sys.path based on which test suite is being run.
    This hook runs before test collection starts.
    """
    root = Path(__file__).parent
    magus_path = str(root / "MAGUS_pygame")
    tools_path = str(root / "Gamemaster_tools")
    
    # Clean up any existing conflicting paths
    sys.path = [p for p in sys.path if p not in (magus_path, tools_path)]
    
    # Check command line arguments to determine which test suite is target
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    args_str = " ".join(args)
    
    # Detect which test paths are being run
    has_gamemaster = "gamemaster_tools" in args_str
    has_pygame = "pygame" in args_str or ("tests" in args_str and "gamemaster_tools" not in args_str)
    
    # If both are being run, pygame runs first so it should be prioritized
    if has_pygame:
        sys.path.insert(0, magus_path)
        sys.path.insert(1, tools_path)
    elif has_gamemaster:
        sys.path.insert(0, tools_path)
        sys.path.insert(1, magus_path)
    else:
        # Fallback: pygame first
        sys.path.insert(0, magus_path)
        sys.path.insert(1, tools_path)






