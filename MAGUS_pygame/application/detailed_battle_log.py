"""
Detailed battle log manager - stores and retrieves comprehensive battle event history.
"""

import time
from collections import deque

from domain.battle_log_entry import (
    BattleLogEntry,
    DetailedActionData,
    DetailedAttackData,
    DetailedMoveData,
    InitiativeData,
)


class DetailedBattleLog:
    """Manages detailed battle log entries with comprehensive event data."""

    def __init__(self, max_entries: int = 500):
        """Initialize battle log.

        Args:
            max_entries: Maximum number of entries to keep (older entries are discarded)
        """
        self.entries: deque[BattleLogEntry] = deque(maxlen=max_entries)
        self.current_round: int = 1

    def set_round(self, round_number: int) -> None:
        """Update current round number.

        Args:
            round_number: The current battle round
        """
        if round_number != self.current_round:
            self.current_round = round_number
            # Log round start
            entry = BattleLogEntry(
                entry_type="round_start",
                round_number=round_number,
                timestamp=time.time(),
                message=f"=== Round {round_number} ==="
            )
            self.entries.append(entry)

    def log_attack(self, message: str, attack_data: DetailedAttackData) -> None:
        """Log an attack with full details.

        Args:
            message: Short message for simple display
            attack_data: Detailed attack breakdown
        """
        entry = BattleLogEntry(
            entry_type="attack",
            round_number=self.current_round,
            timestamp=time.time(),
            message=message,
            attack_data=attack_data
        )
        self.entries.append(entry)

    def log_move(self, message: str, move_data: DetailedMoveData) -> None:
        """Log a movement with full details.

        Args:
            message: Short message for simple display
            move_data: Detailed move breakdown
        """
        entry = BattleLogEntry(
            entry_type="move",
            round_number=self.current_round,
            timestamp=time.time(),
            message=message,
            move_data=move_data
        )
        self.entries.append(entry)

    def log_action(self, message: str, action_data: DetailedActionData) -> None:
        """Log a generic action (charge, weapon switch, rotation, etc.).

        Args:
            message: Short message for simple display
            action_data: Detailed action breakdown
        """
        entry = BattleLogEntry(
            entry_type="action",
            round_number=self.current_round,
            timestamp=time.time(),
            message=message,
            action_data=action_data
        )
        self.entries.append(entry)

    def log_initiative(self, unit_name: str, total: int, base_ke: int, roll: int, position: int) -> None:
        """Log initiative roll data for a unit.

        Args:
            unit_name: Name of the unit
            total: Total initiative value
            base_ke: Base KÉ (initiative modifier)
            roll: D100 roll
            position: Turn order position (1st, 2nd, etc.)
        """
        init_data = InitiativeData(
            unit_name=unit_name,
            total_initiative=total,
            base_ke=base_ke,
            roll=roll,
            order_position=position
        )
        # Use current_round, but if it's 1 and we haven't started yet, use 0 for pre-battle
        round_num = 0 if self.current_round == 1 and len(self.entries) == 0 else self.current_round
        entry = BattleLogEntry(
            entry_type="initiative",
            round_number=round_num,
            timestamp=time.time(),
            message=f"{unit_name}: KÉ {base_ke} + {roll}D = {total}",
            initiative_data=init_data,
            unit_name=unit_name
        )
        self.entries.append(entry)

    def log_turn_start(self, unit_name: str) -> None:
        """Log the start of a unit's turn.

        Args:
            unit_name: Name of the unit starting their turn
        """
        entry = BattleLogEntry(
            entry_type="turn_start",
            round_number=self.current_round,
            timestamp=time.time(),
            message=f"{unit_name}'s turn",
            unit_name=unit_name
        )
        self.entries.append(entry)

    def get_all_entries(self) -> list[BattleLogEntry]:
        """Get all log entries in chronological order.

        Returns:
            List of all battle log entries
        """
        return list(self.entries)

    def get_entries_for_round(self, round_number: int) -> list[BattleLogEntry]:
        """Get all entries for a specific round.

        Args:
            round_number: The round to filter by

        Returns:
            List of entries from that round
        """
        return [entry for entry in self.entries if entry.round_number == round_number]

    def get_recent_entries(self, count: int = 10) -> list[BattleLogEntry]:
        """Get the most recent entries.

        Args:
            count: Number of recent entries to return

        Returns:
            List of recent entries (newest first)
        """
        recent = list(self.entries)[-count:]
        return list(reversed(recent))

    def clear(self) -> None:
        """Clear all log entries."""
        self.entries.clear()
        self.current_round = 1
