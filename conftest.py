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

    # Use pytest invocation args (more reliable with IDE/VSCode runners)
    args = [str(a) for a in getattr(config, "args", sys.argv[1:])]

    def _contains_token(arg: str, token: str) -> bool:
        return token in arg.replace("\\", "/")

    has_gamemaster = any(_contains_token(a, "gamemaster_tools") for a in args)
    has_pygame = any(_contains_token(a, "pygame") for a in args)

    # If args are empty (e.g., IDE discovery) fall back to defaults
    if not args:
        has_pygame = True

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
