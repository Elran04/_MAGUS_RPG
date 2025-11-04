from typing import Callable, Any
from PySide6 import QtCore, QtGui, QtWidgets
import sqlite3

from utils.log.logger import get_logger

logger = get_logger(__name__)


class AddSkillDialog(QtWidgets.QDialog):
    """
    Dialog to select and add a new skill for learning.
    Highlights unmet prerequisites in red and disables adding when unmet.

    Dependencies are injected to avoid tight coupling with the step widget.
    """

    def __init__(
        self,
        parent: QtWidgets.QWidget,
        db_path_getter: Callable[[str], str],
        prereq_checker,
        get_current_map: Callable[[], dict[str, dict[str, int]]],
        get_attributes: Callable[[], dict[str, Any]],
        get_current_skill_ids: Callable[[], set[str]],
        kp_cost_getter: Callable[[str, int, int], Any],
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Új képzettség tanulása")
        self.setMinimumSize(900, 600)

        self._get_db_path = db_path_getter
        self._prereq_checker = prereq_checker
        self._get_current_map = get_current_map
        self._get_attributes = get_attributes
        self._get_current_skill_ids = get_current_skill_ids
        self._kp_cost_getter = kp_cost_getter

        self._selected: tuple[str, int] | None = None

        self._build_ui()
        self._load_categories()
        self._load_table()
        self._update_ok_button()

    # ---- Public API ----

    def get_selected(self) -> tuple[str, int] | None:
        return self._selected

    # ---- UI construction ----

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)

        # Filters
        filter_layout = QtWidgets.QHBoxLayout()
        filter_layout.addWidget(QtWidgets.QLabel("Kategória:"))
        self.category_combo = QtWidgets.QComboBox()
        self.category_combo.addItem("Minden kategória", None)
        filter_layout.addWidget(self.category_combo, stretch=1)

        filter_layout.addWidget(QtWidgets.QLabel("Keresés:"))
        self.search_box = QtWidgets.QLineEdit()
        self.search_box.setPlaceholderText("Képzettség neve...")
        filter_layout.addWidget(self.search_box, stretch=1)
        layout.addLayout(filter_layout)

        # Table
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Képzettség", "Kategória", "Típus", "Min. KP", "Előfeltételek",
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        self.table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.table.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.SingleSelection
        )
        layout.addWidget(self.table)

        # Buttons
        self.button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        ok_button = self.button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)
        ok_button.setText("Hozzáadás")

        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        # Events
        self.category_combo.currentIndexChanged.connect(self._load_table)
        self.search_box.textChanged.connect(self._load_table)
        self.table.selectionModel().selectionChanged.connect(self._update_ok_button)

    def _load_categories(self) -> None:
        try:
            with sqlite3.connect(self._get_db_path("skill")) as conn:
                cursor = conn.execute(
                    "SELECT DISTINCT category FROM skills WHERE placeholder = 0 AND category IS NOT NULL ORDER BY category"
                )
                for (category,) in cursor.fetchall():
                    if category:
                        self.category_combo.addItem(category, category)
        except Exception as e:
            logger.error(f"Error loading categories: {e}", exc_info=True)

    # ---- Data loading ----

    def _load_table(self) -> None:
        self.table.setRowCount(0)
        category_filter = self.category_combo.currentData()
        search_filter = (self.search_box.text() or "").lower()
        current_skill_ids = self._get_current_skill_ids()
        current_map = self._get_current_map()
        attributes = self._get_attributes()

        try:
            with sqlite3.connect(self._get_db_path("skill")) as conn:
                query = "SELECT id, name, parameter, category, type FROM skills WHERE placeholder = 0"
                params: list[Any] = []
                if category_filter:
                    query += " AND category = ?"
                    params.append(category_filter)
                query += " ORDER BY category, name"

                cursor = conn.execute(query, params)
                for skill_id, name, parameter, category, skill_type in cursor.fetchall():
                    if skill_id in current_skill_ids:
                        continue

                    display_name = f"{name} ({parameter})" if parameter else name
                    if search_filter and search_filter not in display_name.lower():
                        continue

                    check_level = 1 if skill_type == 1 else 0
                    check_percent = 3 if skill_type == 2 else 0

                    prereq_ok, _ = self._prereq_checker.check_prerequisites(
                        skill_id, check_level, check_percent, current_map, attributes
                    )

                    prereq_text = "-"
                    if not prereq_ok:
                        prereq_rows = conn.execute(
                            (
                                """
                                SELECT required_skill_id, min_level, level
                                FROM skill_prerequisites_skills
                                WHERE skill_id = ?
                                """
                            ),
                            (skill_id,),
                        ).fetchall()
                        if prereq_rows:
                            parts = []
                            for req_skill_id, min_level, for_level in prereq_rows:
                                if for_level and int(for_level) > check_level:
                                    continue
                                req_row = conn.execute(
                                    "SELECT name, parameter FROM skills WHERE id=?",
                                    (req_skill_id,),
                                ).fetchone()
                                if req_row:
                                    req_name, req_param = req_row
                                    disp = f"{req_name} ({req_param})" if req_param else req_name
                                    parts.append(f"{disp} - Szint/%%: {min_level}")
                            prereq_text = "; ".join(parts) if parts else "-"

                    row = self.table.rowCount()
                    self.table.insertRow(row)

                    name_item = QtWidgets.QTableWidgetItem(display_name)
                    name_item.setData(QtCore.Qt.ItemDataRole.UserRole, (skill_id, skill_type, prereq_ok))
                    if not prereq_ok:
                        name_item.setForeground(QtGui.QBrush(QtGui.QColor("#ff6b6b")))
                    self.table.setItem(row, 0, name_item)

                    cat_item = QtWidgets.QTableWidgetItem(category or "")
                    if not prereq_ok:
                        cat_item.setForeground(QtGui.QBrush(QtGui.QColor("#ff6b6b")))
                    self.table.setItem(row, 1, cat_item)

                    type_text = "Szint" if skill_type == 1 else ("%" if skill_type == 2 else "Mindkettő")
                    type_item = QtWidgets.QTableWidgetItem(type_text)
                    if not prereq_ok:
                        type_item.setForeground(QtGui.QBrush(QtGui.QColor("#ff6b6b")))
                    self.table.setItem(row, 2, type_item)

                    kp_cost = self._calc_int_cost(skill_id, check_level, check_percent)
                    kp_item = QtWidgets.QTableWidgetItem(str(kp_cost if kp_cost is not None else "?"))
                    if not prereq_ok:
                        kp_item.setForeground(QtGui.QBrush(QtGui.QColor("#ff6b6b")))
                    self.table.setItem(row, 3, kp_item)

                    prereq_item = QtWidgets.QTableWidgetItem(prereq_text)
                    if not prereq_ok:
                        prereq_item.setForeground(QtGui.QBrush(QtGui.QColor("#ff6b6b")))
                    self.table.setItem(row, 4, prereq_item)
        except Exception as e:
            logger.error(f"Error loading skills in dialog: {e}", exc_info=True)

    # ---- Events ----

    def _update_ok_button(self) -> None:
        ok_button = self.button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)
        selected_rows = self.table.selectionModel().selectedRows() if self.table.selectionModel() else []
        if not selected_rows:
            ok_button.setEnabled(False)
            ok_button.setToolTip("Válassz ki egy képzettséget!")
            return
        row = selected_rows[0].row()
        name_item = self.table.item(row, 0)
        _, _, prereq_ok = name_item.data(QtCore.Qt.ItemDataRole.UserRole)
        ok_button.setEnabled(bool(prereq_ok))
        ok_button.setToolTip("" if prereq_ok else "Előfeltételek nem teljesülnek")

    def _on_accept(self) -> None:
        selected_rows = self.table.selectionModel().selectedRows() if self.table.selectionModel() else []
        if not selected_rows:
            self.reject()
            return
        row = selected_rows[0].row()
        name_item = self.table.item(row, 0)
        skill_id, skill_type, prereq_ok = name_item.data(QtCore.Qt.ItemDataRole.UserRole)
        if not prereq_ok:
            self.reject()
            return
        self._selected = (skill_id, skill_type)
        self.accept()

    # ---- Helpers ----

    def _calc_int_cost(self, skill_id: str, level: int, percent: int) -> int | None:
        try:
            raw = self._kp_cost_getter(skill_id, level, percent)
            if raw is None:
                return None
            return int(raw)
        except Exception:
            return None
