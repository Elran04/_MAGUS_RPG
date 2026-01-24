"""
Pytest configuration for MAGUS_pygame tests.
Located at tests/pygame/conftest.py
This conftest ensures MAGUS_pygame is prioritized on sys.path during test collection.
"""

import sys
from pathlib import Path

# Get the root and package paths
root = Path(__file__).parent.parent.parent
magus_path = str(root / "MAGUS_pygame")
tools_path = str(root / "Gamemaster_tools")

# Ensure MAGUS_pygame is at the front of sys.path
# Remove both from path first to clean up
sys.path = [p for p in sys.path if p not in (magus_path, tools_path)]

# Add MAGUS_pygame first for pygame tests
sys.path.insert(0, magus_path)
sys.path.insert(1, tools_path)
