"""
Read-only attributes display widget.
Shows finalized attributes (with race/age modifiers) as information only.
Used in skill learning step and other views where attributes should not be editable.
"""

from collections.abc import Callable
from typing import Any

from PySide6 import QtCore, QtWidgets


class AttributesReadOnlyWidget(QtWidgets.QWidget):
    """
    Display finalized character attributes in a read-only format.
    Shows attribute names and their final values (including race/age modifiers).
    """

    # Attribute names in display order
    ATTRIBUTE_ORDER = [
        ("Erő", "Erő"),
        ("Gyorsaság", "Gyorsaság"),
        ("Ügyesség", "Ügyesség"),
        ("Állóképesség", "Állóképesség"),
        ("Egészség", "Egészség"),
        ("Karizma", "Karizma"),
        ("Intelligencia", "Intelligencia"),
        ("Akaraterő", "Akaraterő"),
        ("Asztrál", "Asztrál"),
        ("Érzékelés", "Érzékelés"),
    ]

    def __init__(
        self,
        get_character_data: Callable[[], dict[str, int] | dict[str, Any]],
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._get_character_data = get_character_data
        self.value_labels: dict[str, QtWidgets.QLabel] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the read-only attributes display UI."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Title
        title = QtWidgets.QLabel("Tulajdonságok")
        title.setStyleSheet("font-weight: bold; font-size: 14px; padding: 4px;")
        layout.addWidget(title)

        # Info message
        info = QtWidgets.QLabel("<i>Végleges értékek (faj és kor módosítókkal)</i>")
        info.setWordWrap(True)
        info.setStyleSheet("color: #888; font-size: 9pt; padding: 4px;")
        layout.addWidget(info)

        # Attributes grid
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(6)
        grid.setContentsMargins(4, 4, 4, 4)
        grid.setColumnStretch(0, 1)  # attribute labels stretch
        grid.setColumnStretch(1, 0)  # values stay compact

        for idx, (key, display_name) in enumerate(self.ATTRIBUTE_ORDER):
            # Label
            name_label = QtWidgets.QLabel(f"{display_name}:")
            name_label.setStyleSheet("font-weight: bold; color: #aaa;")
            name_label.setAlignment(
                QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter
            )
            grid.addWidget(name_label, idx, 0)

            # Value
            value_label = QtWidgets.QLabel("-")
            value_label.setAlignment(
                QtCore.Qt.AlignmentFlag.AlignCenter | QtCore.Qt.AlignmentFlag.AlignVCenter
            )
            value_label.setStyleSheet(
                "font-size: 13px; font-weight: bold; padding: 4px 8px; "
                "background-color: #2a2a2a; border-radius: 3px; min-width: 30px;"
            )
            grid.addWidget(value_label, idx, 1)
            self.value_labels[key] = value_label

        layout.addLayout(grid)
        layout.addStretch(1)

    def refresh(self) -> None:
        """Update displayed attribute values from character data."""
        data = self._get_character_data() or {}
        raw_val: object = data.get("Tulajdonságok", {})
        raw_attrs: dict[Any, Any] = dict(raw_val) if isinstance(raw_val, dict) else {}
        # Ensure we work with a typed dict[str, int]
        attributes: dict[str, int] = {}
        if isinstance(raw_attrs, dict):
            for k, v in raw_attrs.items():
                try:
                    attributes[str(k)] = int(v)
                except (TypeError, ValueError):
                    continue

        for key, label in self.value_labels.items():
            value = attributes.get(key, 10)
            label.setText(str(value))

            # Optional: color-code based on value range
            if value >= 16:
                label.setStyleSheet(
                    "font-size: 13px; font-weight: bold; padding: 4px 8px; "
                    "background-color: #2a5a2a; border-radius: 3px; min-width: 30px; "
                    "color: #90ee90;"
                )
            elif value <= 8:
                label.setStyleSheet(
                    "font-size: 13px; font-weight: bold; padding: 4px 8px; "
                    "background-color: #5a2a2a; border-radius: 3px; min-width: 30px; "
                    "color: #ff9090;"
                )
            else:
                label.setStyleSheet(
                    "font-size: 13px; font-weight: bold; padding: 4px 8px; "
                    "background-color: #2a2a2a; border-radius: 3px; min-width: 30px;"
                )

    def get_attributes(self) -> dict[str, int]:
        """Return current attribute values from character data."""
        data = self._get_character_data() or {}
        raw_val: object = data.get("Tulajdonságok", {})
        if isinstance(raw_val, dict):
            result: dict[str, int] = {}
            for k, v in raw_val.items():
                try:
                    result[str(k)] = int(v)
                except (TypeError, ValueError):
                    continue
            return result
        return {}
