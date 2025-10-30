from PySide6 import QtWidgets
from typing import Callable, Optional

class EquipmentStepWidget(QtWidgets.QWidget):
    """
    Placeholder equipment step. Encapsulates future equipment selection UI.
    Exposes a small contract so the wizard can validate and collect data later.

    Contract:
    - set_context(get_class_id, get_spec_data, get_data): optional callbacks to access upstream selections
    - validate() -> bool: step-specific validation before moving forward
    - get_data() -> dict: returns equipment-related data to merge into wizard data
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._get_class_id: Optional[Callable[[], Optional[int]]] = None
        self._get_spec_data: Optional[Callable[[], dict]] = None
        self._get_data: Optional[Callable[[], dict]] = None

        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        title = QtWidgets.QLabel("Felszerelés kiválasztása")
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title)

        placeholder = QtWidgets.QLabel("Felszerelések szerkesztése (később)")
        placeholder.setStyleSheet("color: #888;")
        layout.addWidget(placeholder)
        layout.addStretch(1)

    def set_context(self,
                    get_class_id: Optional[Callable[[], Optional[int]]] = None,
                    get_spec_data: Optional[Callable[[], dict]] = None,
                    get_data: Optional[Callable[[], dict]] = None):
        """Optionally provide callbacks to access earlier wizard data."""
        self._get_class_id = get_class_id
        self._get_spec_data = get_spec_data
        self._get_data = get_data

    def validate(self) -> bool:
        """Return True if the step is valid to proceed. Placeholder always True."""
        return True

    def get_data(self) -> dict:
        """Return equipment-related data to merge into the wizard's data dict."""
        # Placeholder: return an empty structure for now
        return {"Felszerelés": {}}
