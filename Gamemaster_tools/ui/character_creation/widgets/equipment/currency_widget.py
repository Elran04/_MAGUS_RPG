"""
Currency Widget
Displays character's currency with color-coded denominations.
"""

from engine.currency_manager import CurrencyManager
from PySide6 import QtCore, QtWidgets


class CurrencyWidget(QtWidgets.QWidget):
    """Widget for displaying currency with colored denominations."""

    # Currency colors (matching their real-world metallic colors)
    CURRENCY_COLORS = {
        "mithrill": "#E8E8E8",  # Very light metallic
        "arany": "#FFD700",  # Gold
        "ezüst": "#C0C0C0",  # Silver
        "réz": "#B87333",  # Copper
    }

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.currency_manager = CurrencyManager()
        self.currency_base = 0

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the currency display UI."""
        # Use dark mode background
        self.setStyleSheet(
            "CurrencyWidget {"
            "    background-color: #2b2b2b;"
            "    border: 1px solid #555;"
            "    border-radius: 4px;"
            "    padding: 8px;"
            "}"
        )

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Title label
        title_label = QtWidgets.QLabel("Rendelkezésre álló vagyon:")
        title_label.setStyleSheet("font-weight: bold; font-size: 11px; color: #ffffff;")
        layout.addWidget(title_label)

        # Currency display label (will contain colored HTML)
        self.currency_label = QtWidgets.QLabel("")
        self.currency_label.setTextFormat(QtCore.Qt.TextFormat.RichText)
        self.currency_label.setStyleSheet("font-size: 13px; font-weight: bold;")
        layout.addWidget(self.currency_label)

        self._update_display()

    def set_currency(self, amount_base: int) -> None:
        """
        Set currency amount and update display.

        Args:
            amount_base: Amount in base units (copper/réz)
        """
        self.currency_base = amount_base
        self._update_display()

    def _update_display(self) -> None:
        """Update the currency display with colored denominations."""
        if self.currency_base == 0:
            self.currency_label.setText(
                f'<span style="color: {self.CURRENCY_COLORS["réz"]};">0 réz</span>'
            )
            return

        # Break down into denominations using from_base()
        breakdown = self.currency_manager.from_base(self.currency_base)

        # Build colored HTML string in proper order (largest to smallest)
        parts = []
        # Use ORDER from currency_manager to ensure proper ordering
        for denom in reversed(self.currency_manager.ORDER):
            amount = breakdown.get(denom, 0)
            if amount > 0:
                color = self.CURRENCY_COLORS.get(denom, "#ffffff")
                parts.append(f'<span style="color: {color};">{amount} {denom}</span>')

        if parts:
            html = ", ".join(parts)
            self.currency_label.setText(html)
        else:
            self.currency_label.setText(
                f'<span style="color: {self.CURRENCY_COLORS["réz"]};">0 réz</span>'
            )

    def get_currency(self) -> int:
        """Get current currency in base units."""
        return self.currency_base
