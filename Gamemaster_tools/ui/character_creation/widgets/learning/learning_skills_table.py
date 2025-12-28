"""
Learning Skills Table Renderer
Handles rendering and UI state for skill rows in the learning step.
Extends/reuses patterns from skills_table.py but without placeholder logic.
"""

from collections.abc import Callable

from PySide6 import QtWidgets
from ui.character_creation.widgets.learning.learning_row import LearningRow
from utils.ui.themes import action_icon_button_style


class LearningSkillsTableRenderer:
    """
    Renders skill rows for the learning step with +/− controls and tooltips.
    Delegates business logic (KP checks, prereqs) to caller.
    """

    def __init__(
        self,
        table: QtWidgets.QTableWidget,
        can_increase_cb: Callable[[str, int, int, int], tuple[bool, str, int]],
        on_increase_cb: Callable[[str], None],
        on_decrease_cb: Callable[[str], None],
    ) -> None:
        """
        Args:
            table: The QTableWidget to render into.
            can_increase_cb: (skill_id, skill_type, level, percent) -> (can, tooltip, next_kp_cost)
            on_increase_cb: Callback when + is clicked.
            on_decrease_cb: Callback when − is clicked.
        """
        self.table = table
        self._can_increase = can_increase_cb
        self._on_increase = on_increase_cb
        self._on_decrease = on_decrease_cb

    def clear(self) -> None:
        """Clear all rows."""
        self.table.setRowCount(0)

    def add_row(self, row_data: LearningRow) -> None:
        """Add a single skill row to the table."""
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Skill name
        name_item = QtWidgets.QTableWidgetItem(row_data.display_name)
        self.table.setItem(row, 0, name_item)

        # Érték (unified level/percent column)
        if row_data.skill_type == 1:  # Level-based
            value_text = f"{row_data.level}. fok"
        else:  # Percent-based
            value_text = f"{row_data.percent}%"
        value_item = QtWidgets.QTableWidgetItem(value_text)
        self.table.setItem(row, 1, value_item)

        # KP cost (only what's spent in this step)
        kp_item = QtWidgets.QTableWidgetItem(str(row_data.kp_cost))
        self.table.setItem(row, 2, kp_item)

        # Action column: +/− buttons
        action_widget = QtWidgets.QWidget()
        action_layout = QtWidgets.QHBoxLayout(action_widget)
        action_layout.setContentsMargins(2, 2, 2, 2)
        action_layout.setSpacing(2)

        # Decrease button
        minus_btn = QtWidgets.QPushButton("➖")
        minus_btn.setMaximumWidth(30)
        minus_btn.setProperty("skill_id", row_data.skill_id)
        minus_btn.setStyleSheet(action_icon_button_style())
        minus_btn.clicked.connect(
            lambda checked=False, sid=row_data.skill_id: self._on_decrease(sid)
        )

        # Disable if at mandatory minimum
        if row_data.is_mandatory:
            can_decrease = (
                row_data.skill_type == 1 and row_data.level > row_data.mandatory_level
            ) or (row_data.skill_type == 2 and row_data.percent > row_data.mandatory_percent)
        else:
            # Learned skills can always be decreased (will remove at minimum)
            can_decrease = True

        minus_btn.setEnabled(can_decrease)
        if not can_decrease and row_data.is_mandatory:
            minus_btn.setToolTip("Nem csökkenthető a kötelező minimum alá")
        action_layout.addWidget(minus_btn)

        # Increase button
        plus_btn = QtWidgets.QPushButton("➕")
        plus_btn.setMaximumWidth(30)
        plus_btn.setProperty("skill_id", row_data.skill_id)
        plus_btn.setStyleSheet(action_icon_button_style())
        plus_btn.clicked.connect(
            lambda checked=False, sid=row_data.skill_id: self._on_increase(sid)
        )

        # Check if can increase
        can, tooltip, next_cost = self._can_increase(
            row_data.skill_id, row_data.skill_type, row_data.level, row_data.percent
        )

        if can:
            # Show KP cost on hover when increaseable
            plus_btn.setToolTip(f"KP költség: {next_cost}")
            plus_btn.setEnabled(True)
        else:
            # Show reason why not
            plus_btn.setToolTip(tooltip)
            # For level-based at max, hide; otherwise disable
            if row_data.skill_type == 1 and "maximális" in tooltip.lower():
                plus_btn.setVisible(False)
            else:
                plus_btn.setEnabled(False)

        action_layout.addWidget(plus_btn)
        self.table.setCellWidget(row, 3, action_widget)
