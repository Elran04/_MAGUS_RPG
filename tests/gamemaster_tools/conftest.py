"""
Pytest configuration for Gamemaster_tools tests.
Located at tests/gamemaster_tools/conftest.py

This conftest runs AFTER the root conftest.py and reorders sys.path
to prioritize Gamemaster_tools when tests in this directory are run.
"""

import sys
from pathlib import Path

# Get the root and package paths
root = Path(__file__).parent.parent.parent
magus_path = str(root / "MAGUS_pygame")
tools_path = str(root / "Gamemaster_tools")

# For Gamemaster_tools tests, ensure tools_path is first
# This runs after root conftest; order here is a safety net for IDE runners
sys.path = [p for p in sys.path if p not in (magus_path, tools_path)]
sys.path.insert(0, tools_path)
sys.path.insert(1, magus_path)
