import contextlib
from collections.abc import Callable

from PySide6 import QtWidgets


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
    Tulajdonságok, Képzettségek, Felszerelés, Képzettségpontok (int).
    Excludes: any keys starting with '_', descriptions, etc. (Harci értékek kept, but
    HM/szint removed)
        """
        src = dict(self._get_data() or {})
        allowed_keys = {
            "Név",
            "Nem",
            "Kor",
            "Faj",
            "Kaszt",
            "Specializáció",
            "Tulajdonságok",
            "Képzettségek",
            "Felszerelés",
            "Képzettségpontok",
            "Harci értékek",
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
        out.setdefault("Felszerelés", {"currency": 0, "items": []})

        # Transform skills to minimal schema: only id + (Szint or %)
        minimal_skills: list[dict] = []
        for s in out.get("Képzettségek", []) or []:
            sid = s.get("id")
            if not sid:
                continue
            if int(s.get("Szint", 0) or 0) > 0:
                minimal_skills.append({"id": sid, "Szint": int(s.get("Szint", 0) or 0)})
            elif int(s.get("%", 0) or 0) > 0:
                minimal_skills.append({"id": sid, "%": int(s.get("%", 0) or 0)})
            else:
                # If neither present, still keep id to indicate possession at base
                minimal_skills.append({"id": sid})
        out["Képzettségek"] = minimal_skills

        # Coerce KP to int (remaining). If dict leaked in, squash to 0 or best-effort.
        kp_val = out.get("Képzettségpontok", 0)
        if isinstance(kp_val, dict):
            # Prefer a 'Remaining' field if present, else 0
            kp_val = int(kp_val.get("Remaining", 0) or 0)
        with contextlib.suppress(Exception):
            kp_val = int(kp_val)
        out["Képzettségpontok"] = kp_val

        # Remove HM/szint from Harci értékek (these are DB-derived per-level rules)
        combat = out.get("Harci értékek")
        if isinstance(combat, dict) and "HM/szint" in combat:
            combat = dict(combat)
            combat.pop("HM/szint", None)
            out["Harci értékek"] = combat
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
