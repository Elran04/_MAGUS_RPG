"""
Pytest configuration for MAGUS_pygame tests.
"""
import sys
from pathlib import Path

# Add MAGUS_pygame to Python path for imports
magus_dir = Path(__file__).parent.parent
sys.path.insert(0, str(magus_dir))
