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

    def _filtered_data(self) -> dict:
        """Return only the fields we want to present and save.
        Includes: base info (Név, Nem, Kor, Faj, Kaszt, Specializáció),
        Tulajdonságok, Képzettségek, Felszerelés.
        Excludes: any keys starting with '_', descriptions, KP/Harci értékek, etc.
        """
        src = dict(self._get_data() or {})
        allowed_keys = {
            "Név", "Nem", "Kor", "Faj", "Kaszt", "Specializáció",
            "Tulajdonságok", "Képzettségek", "Felszerelés",
            "Képzettségpontok", "Harci értékek",
        }
        out = {}
        for k, v in src.items():
            if k.startswith("_"):
                continue
            if k == "Spec_leírás":
                continue
            if k in ("Fejleszthető",):
                continue
            if k in allowed_keys:
                out[k] = v
        # Ensure required collections exist
        out.setdefault("Képzettségek", [])
        out.setdefault("Felszerelés", [])
        return out

    def refresh(self):
        data = self._filtered_data()
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
        """Return filtered data for downstream save/finish operations."""
        return self._filtered_data()
