"""
Error handling utilities for Gamemaster Tools (PySide6).

Provides:
- User-friendly error dialogs
- Safe file loading with recovery
- Validation error display
"""

from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QMessageBox, QWidget
from utils.log.logger import get_logger

logger = get_logger(__name__)


def show_error_dialog(
    parent: Optional[QWidget],
    title: str,
    message: str,
    details: Optional[str] = None,
) -> None:
    """
    Show an error dialog to the user.

    Args:
        parent: Parent widget
        title: Dialog title
        message: Main error message
        details: Optional detailed error info (shown in expandable section)
    """
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setIcon(QMessageBox.Icon.Critical)

    if details:
        msg_box.setDetailedText(details)

    logger.error(f"{title}: {message}")
    if details:
        logger.error(f"Details: {details}")

    msg_box.exec()


def show_warning_dialog(
    parent: Optional[QWidget],
    title: str,
    message: str,
) -> None:
    """Show a warning dialog to the user."""
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setIcon(QMessageBox.Icon.Warning)
    logger.warning(f"{title}: {message}")
    msg_box.exec()


def safe_load_json_file(
    file_path: Path | str,
    parent: Optional[QWidget] = None,
    description: str = "data",
) -> Optional[dict]:
    """
    Safely load a JSON file with user error handling.

    Shows error dialog on failure.

    Args:
        file_path: Path to JSON file
        parent: Parent widget for dialog
        description: Human-readable description (e.g., "character data")

    Returns:
        Parsed JSON dict, or None if file doesn't exist or error occurred
    """
    import json

    file_path = Path(file_path)

    if not file_path.exists():
        logger.debug(f"File not found: {file_path}")
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        show_error_dialog(
            parent,
            "Invalid Data File",
            f"Could not read {description}. File is corrupted or has invalid format.",
            f"File: {file_path}\nError: {e.msg} at line {e.lineno}, column {e.colno}",
        )
        return None
    except (IOError, OSError) as e:
        show_error_dialog(
            parent,
            "File Read Error",
            f"Could not read {description} file.",
            f"File: {file_path}\nError: {e.strerror}",
        )
        return None
    except Exception as e:
        show_error_dialog(
            parent,
            "Unexpected Error",
            f"An unexpected error occurred while loading {description}.",
            f"Error: {type(e).__name__}: {str(e)}",
        )
        return None


def safe_save_json_file(
    file_path: Path | str,
    data: dict,
    parent: Optional[QWidget] = None,
    description: str = "data",
) -> bool:
    """
    Safely save data to a JSON file.

    Shows error dialog on failure.

    Args:
        file_path: Path where to save JSON file
        data: Data to serialize
        parent: Parent widget for dialog
        description: Human-readable description

    Returns:
        True if save succeeded, False otherwise
    """
    import json

    file_path = Path(file_path)

    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.debug(f"Saved {description} to {file_path.name}")
        return True
    except (IOError, OSError) as e:
        show_error_dialog(
            parent,
            "Save Failed",
            f"Could not save {description}.",
            f"File: {file_path}\nError: {e.strerror}",
        )
        return False
    except Exception as e:
        show_error_dialog(
            parent,
            "Unexpected Error",
            f"An error occurred while saving {description}.",
            f"Error: {type(e).__name__}: {str(e)}",
        )
        return False


def wrap_with_error_handling(func, parent: Optional[QWidget] = None):
    """
    Decorator to wrap a function with error handling.

    Catches exceptions and shows error dialog.

    Args:
        func: Function to wrap
        parent: Parent widget for error dialogs

    Returns:
        Wrapped function
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            show_error_dialog(
                parent,
                f"Error in {func.__name__}",
                "An error occurred during this operation.",
                f"{type(e).__name__}: {str(e)}",
            )
            logger.error(f"Error in {func.__name__}", exc_info=True)
            return None

    return wrapper
