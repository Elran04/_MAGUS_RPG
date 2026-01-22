"""
Skills value object for normalized skill lookups.

Supports rank-based skills ("Szint") and percent-based skills ("%"),
merged from character data plus scenario overrides.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


def _norm(skill_id: str | None) -> str:
    """Normalize skill identifier for consistent lookup."""
    return (skill_id or "").strip().lower()


@dataclass(frozen=True)
class Skills:
    """Immutable skills container with rank/percent lookups."""

    _ranks: Dict[str, int]
    _percents: Dict[str, int]

    @staticmethod
    def empty() -> "Skills":
        """Return an empty skills container."""
        return Skills({}, {})

    @staticmethod
    def from_sources(
        character_skills: list[dict] | None = None,
        overrides: dict[str, int] | None = None,
    ) -> "Skills":
        """Build skills from character list plus optional override mapping.

        character_skills: list of dicts with keys {"id", "Szint"} or {"id", "%"}
        overrides: mapping skill_id -> rank (used for scenario overrides)
        """
        ranks: Dict[str, int] = {}
        percents: Dict[str, int] = {}

        # Parse base character skill entries
        for entry in character_skills or []:
            if not isinstance(entry, dict):
                continue
            sid = _norm(entry.get("id"))
            if not sid:
                continue
            if "Szint" in entry:
                try:
                    value = int(entry.get("Szint", 0))
                except (TypeError, ValueError):
                    value = 0
                ranks[sid] = max(ranks.get(sid, 0), value)
            if "%" in entry:
                try:
                    value = int(entry.get("%", 0))
                except (TypeError, ValueError):
                    value = 0
                percents[sid] = max(percents.get(sid, 0), value)

        # Apply overrides as ranks (scenario-provided values)
        for sid_raw, value_raw in (overrides or {}).items():
            sid = _norm(sid_raw)
            if not sid:
                continue
            try:
                value = int(value_raw)
            except (TypeError, ValueError):
                value = 0
            ranks[sid] = max(ranks.get(sid, 0), value)

        return Skills(ranks, percents)

    def get_rank(self, skill_id: str, default: int = 0) -> int:
        """Return rank-based skill value (Szint)."""
        return self._ranks.get(_norm(skill_id), default)

    def get_percent(self, skill_id: str, default: int = 0) -> int:
        """Return percent-based skill value (% based)."""
        return self._percents.get(_norm(skill_id), default)

    def has_at_least(self, skill_id: str, minimum: int) -> bool:
        """Check if skill rank meets or exceeds a threshold."""
        return self.get_rank(skill_id, 0) >= minimum

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self._ranks) + len(self._percents)

    def __iter__(self):  # pragma: no cover - convenience
        yield from {**self._ranks, **self._percents}

    def to_dict(self) -> dict:
        """Return shallow copy for debugging/serialization."""
        return {"ranks": dict(self._ranks), "percents": dict(self._percents)}
