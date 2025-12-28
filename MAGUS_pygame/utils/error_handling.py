"""
Error handling utilities for better user experience and debugging.

Provides:
- Safe JSON loading with error context
- Validation error wrapping
- User-friendly error messages
- Automatic logging of errors
"""

import json
from pathlib import Path
from typing import Any, Optional, TypeVar

from logger.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class ValidationError(Exception):
    """Raised when data validation fails."""

    def __init__(self, message: str, context: Optional[dict] = None):
        self.message = message
        self.context = context or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{self.message} ({context_str})"
        return self.message


class DataLoadError(Exception):
    """Raised when data file loading fails."""

    def __init__(
        self, file_path: Path | str, reason: str, original_error: Optional[Exception] = None
    ):
        self.file_path = file_path
        self.reason = reason
        self.original_error = original_error
        super().__init__(str(self))

    def __str__(self) -> str:
        msg = f"Failed to load {self.file_path}: {self.reason}"
        if self.original_error:
            msg += f"\nOriginal error: {self.original_error}"
        return msg


def safe_json_load(file_path: Path | str, description: str = "data") -> dict | None:
    """
    Safely load a JSON file with comprehensive error handling.

    Args:
        file_path: Path to JSON file
        description: Human-readable description (e.g., "character data", "equipment config")

    Returns:
        Parsed JSON dict, or None if file doesn't exist

    Raises:
        DataLoadError: If file exists but can't be parsed
    """
    import json

    file_path = Path(file_path)

    if not file_path.exists():
        logger.warning(f"File not found: {file_path} ({description})")
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.debug(f"Loaded {description} from {file_path.name}")
        return data
    except json.JSONDecodeError as e:
        msg = f"Invalid JSON format (line {e.lineno}, col {e.colno}): {e.msg}"
        logger.error(f"{msg} in {file_path}")
        raise DataLoadError(file_path, msg, e) from e
    except (IOError, OSError) as e:
        msg = f"File I/O error: {e.strerror}"
        logger.error(f"{msg} for {file_path}")
        raise DataLoadError(file_path, msg, e) from e


def validate_required_fields(data: dict, required_fields: list[str], context: str = "") -> None:
    """
    Validate that required fields exist in data dict.

    Args:
        data: Dictionary to validate
        required_fields: List of required field names
        context: Description for error messages (e.g., "character model")

    Raises:
        ValidationError: If any required field is missing
    """
    missing = [f for f in required_fields if f not in data]
    if missing:
        error_context = {"missing_fields": missing}
        if context:
            error_context["context"] = context
        raise ValidationError(f"Missing required fields: {missing}", error_context)


def get_error_description(exception: Exception) -> str:
    """
    Generate a user-friendly error description.

    Args:
        exception: Exception to describe

    Returns:
        Human-readable error description
    """
    if isinstance(exception, ValidationError):
        return f"Data Error: {exception.message}"
    elif isinstance(exception, DataLoadError):
        return f"File Error: {exception.reason}"
    elif isinstance(exception, json.JSONDecodeError):
        return f"Invalid JSON: {exception.msg} (line {exception.lineno})"
    elif isinstance(exception, FileNotFoundError):
        return f"File Not Found: {exception.filename}"
    elif isinstance(exception, TypeError):
        return f"Type Error: {str(exception)}"
    else:
        return f"Unexpected Error: {str(exception)}"


# Convenience function for common patterns
def log_error(exception: Exception, context: str = "") -> str:
    """
    Log error with full context and return user-friendly message.

    Args:
        exception: Exception that occurred
        context: Additional context (e.g., "loading character equipment")

    Returns:
        User-friendly error message
    """
    full_msg = f"{context}: {exception}" if context else str(exception)
    logger.error(full_msg, exc_info=True)
    return get_error_description(exception)
