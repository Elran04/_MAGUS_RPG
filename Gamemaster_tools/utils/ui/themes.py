"""
Centralized color theme for Gamemaster Tools UI.
Provides consistent color palette across all editors and character creation.
"""


class CharacterCreationTheme:
    """Color palette for character creation wizard."""

    # Success colors (green)
    SUCCESS_GREEN = "#4caf50"
    SUCCESS_GREEN_HOVER = "#388e3c"
    SUCCESS_GREEN_DARK = "#2e7d32"
    SUCCESS_GREEN_LIGHT = "#45a049"

    # Error colors (red)
    ERROR_RED = "#c62828"
    ERROR_RED_LIGHT = "#f44336"

    # Warning colors (orange/yellow)
    WARNING_ORANGE = "#cc8800"
    WARNING_ORANGE_BG = "rgba(200,150,50,30)"
    HIGHLIGHT_YELLOW = "#ffe082"
    HIGHLIGHT_YELLOW_HOVER = "#ffd54f"

    # Neutral colors
    TEXT_GRAY = "#888"
    TEXT_DARK = "#333"
    BACKGROUND_GRAY = "rgba(100,100,120,50)"

    # Action icon button states (light vs dark gray)
    ACTION_BUTTON_ENABLED_BG = "#d0d0d0"  # light gray
    ACTION_BUTTON_ENABLED_HOVER_BG = "#c6c6c6"  # slightly darker on hover
    ACTION_BUTTON_DISABLED_BG = "#8a8a8a"  # dark gray
    ACTION_BUTTON_TEXT = "#111"


class EditorTheme:
    """Color palette for data editors (skills, classes, equipment, races)."""

    # Primary action colors
    PRIMARY_BLUE = "#2196f3"
    PRIMARY_BLUE_HOVER = "#1976d2"

    # Success/validation
    SUCCESS_GREEN = "#4caf50"
    SUCCESS_GREEN_HOVER = "#388e3c"

    # Danger/delete
    DANGER_RED = "#f44336"
    DANGER_RED_HOVER = "#d32f2f"

    # Warning
    WARNING_AMBER = "#ff9800"
    WARNING_AMBER_HOVER = "#f57c00"

    # Neutral
    NEUTRAL_GRAY = "#757575"
    NEUTRAL_GRAY_HOVER = "#616161"


# Convenience functions for common UI patterns
def success_button_style() -> str:
    """Returns stylesheet for success/save buttons."""
    return (
        f"QPushButton {{ "
        f"font-size: 14px; font-weight: bold; padding: 8px; border-radius: 6px; "
        f"background-color: {CharacterCreationTheme.SUCCESS_GREEN}; color: white; "
        f"}} "
        f"QPushButton:hover {{ background-color: {CharacterCreationTheme.SUCCESS_GREEN_HOVER}; }}"
    )


def highlight_button_style() -> str:
    """Returns stylesheet for highlight/alternative buttons."""
    return (
        f"QPushButton {{ "
        f"font-size: 14px; font-weight: bold; padding: 8px; border-radius: 6px; "
        f"background-color: {CharacterCreationTheme.HIGHLIGHT_YELLOW}; "
        f"color: {CharacterCreationTheme.TEXT_DARK}; "
        f"}} "
        f"QPushButton:hover {{ background-color: {CharacterCreationTheme.HIGHLIGHT_YELLOW_HOVER}; }}"
    )


def warning_label_style() -> str:
    """Returns stylesheet for warning labels/messages."""
    return (
        f"color: {CharacterCreationTheme.WARNING_ORANGE}; "
        f"font-size: 10pt; padding: 12px; "
        f"background-color: {CharacterCreationTheme.WARNING_ORANGE_BG}; "
        f"border-radius: 4px;"
    )


def info_label_style() -> str:
    """Returns stylesheet for info/help text."""
    return f"color: {CharacterCreationTheme.TEXT_GRAY}; " f"font-size: 9pt; padding: 8px;"


def header_label_style() -> str:
    """Returns stylesheet for section headers with background."""
    return (
        f"font-size: 12pt; padding: 8px; "
        f"background-color: {CharacterCreationTheme.BACKGROUND_GRAY}; "
        f"border-radius: 4px;"
    )


def action_icon_button_style() -> str:
    """Small square +/- buttons with clear enabled/disabled colors.

    - Enabled: light gray
    - Disabled: dark gray
    """
    return (
        f"QPushButton {{"
        f"  border: 1px solid #666; border-radius: 4px; padding: 2px 6px;"
        f"  color: {CharacterCreationTheme.ACTION_BUTTON_TEXT};"
        f"}}"
        f"QPushButton:enabled {{ background-color: {CharacterCreationTheme.ACTION_BUTTON_ENABLED_BG}; }}"
        f"QPushButton:disabled {{ background-color: {CharacterCreationTheme.ACTION_BUTTON_DISABLED_BG}; color: #222; }}"
        f"QPushButton:hover:enabled {{ background-color: {CharacterCreationTheme.ACTION_BUTTON_ENABLED_HOVER_BG}; }}"
    )
