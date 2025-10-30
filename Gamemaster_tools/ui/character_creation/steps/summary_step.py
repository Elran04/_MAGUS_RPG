from PySide6 import QtWidgets
from typing import Callable

class SummaryStepWidget(QtWidgets.QWidget):
    """
    Summary step widget to display the aggregated character data.

    Contract:
    - constructor accepts get_data: Callable[[], dict]
    - refresh(): recompute and display summary from current data
    - get_result(): return the same data (future hook for finalized payload)
    """
    def __init__(self, get_data: Callable[[], dict], parent=None):
        super().__init__(parent)
        self._get_data = get_data
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        title = QtWidgets.QLabel("Karakter összegzés")
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title)

        self.summary_view = QtWidgets.QTextEdit(self)
        self.summary_view.setReadOnly(True)
        layout.addWidget(self.summary_view)

        layout.addStretch(1)

    def refresh(self):
        data = self._get_data() or {}
        # Build a simple key: value listing; nested dicts pretty-printed lightly
        lines = []
        for k, v in data.items():
            if isinstance(v, dict):
                lines.append(f"{k}:")
                for sk, sv in v.items():
                    lines.append(f"  - {sk}: {sv}")
            else:
                lines.append(f"{k}: {v}")
        self.summary_view.setPlainText("\n".join(lines))

    def get_result(self) -> dict:
        """Return the current data for downstream save/finish operations."""
        return dict(self._get_data() or {})
