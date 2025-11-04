"""
JSON I/O Utility Module
Provides centralized JSON file reading and writing with consistent error handling.
"""

import json
import os
from typing import Any
from utils.log.logger import get_logger

logger = get_logger(__name__)


def load_json(file_path: str, default: Any = None) -> Any:
    """
    Load JSON data from a file.
    
    Args:
        file_path: Absolute path to the JSON file
        default: Default value to return if file doesn't exist or on error
        
    Returns:
        Loaded JSON data or default value
        
    Raises:
        json.JSONDecodeError: If JSON is malformed
        IOError, OSError: If file cannot be read
    """
    if not os.path.exists(file_path):
        logger.info(f"JSON file not found, returning default: {file_path}")
        return default if default is not None else []
    
    try:
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError, OSError) as e:
        logger.error(f"Failed to load JSON from {file_path}: {e}")
        raise


def save_json(file_path: str, data: Any, create_dirs: bool = True) -> None:
    """
    Save data to a JSON file.
    
    Args:
        file_path: Absolute path to the JSON file
        data: Data to save (must be JSON-serializable)
        create_dirs: Whether to create parent directories if they don't exist
        
    Raises:
        IOError, OSError: If file cannot be written
        TypeError: If data is not JSON-serializable
    """
    try:
        if create_dirs:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        logger.debug(f"Successfully saved JSON to {file_path}")
        
    except (IOError, OSError, TypeError) as e:
        logger.error(f"Failed to save JSON to {file_path}: {e}")
        raise


def load_json_safe(file_path: str, default: Any = None) -> Any:
    """
    Load JSON data from a file, returning default on any error (safe version).
    
    This version never raises exceptions - suitable for initialization where
    missing or corrupt files should not crash the application.
    
    Args:
        file_path: Absolute path to the JSON file
        default: Default value to return if file doesn't exist or on error
        
    Returns:
        Loaded JSON data or default value
    """
    try:
        return load_json(file_path, default)
    except (json.JSONDecodeError, IOError, OSError) as e:
        logger.warning(f"Using default value due to error loading {file_path}: {e}")
        return default if default is not None else []
