"""
Armor system for MAGUS combat (layered, zone-based).

Handles:
- ArmorPiece: multi-zone SFÉ per main armor part, with layer and MGT
- ArmorSystem: aggregation, validation, total SFÉ/MGT, and targeted degradation
- HitzoneResolver: weighted selection of hit zones (main parts)

Legacy helper shims removed; all integrations must use ArmorSystem and zone-based APIs.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

# ------------------------------
# ArmorPiece (layered, zone-based)
# ------------------------------


MAIN_PARTS = (
    "sisak",
    "mellvért",
    "vállvédő",
    "felkarvédő",
    "alkarvédő",
    "combvédő",
    "lábszárvédő",
    "csizma",
)


@dataclass
class ArmorPiece:
    """Represents one armor item across main parts and a specific layer.

    parts: mapping of main part -> base SFÉ (e.g., {"mellvért": 8})
    layer: 1 is outermost; higher numbers are inner layers
    current_parts: mutable per-part current SFÉ values
    """

    id: str
    name: str
    parts: dict[str, int]
    mgt: int = 0
    armor_type: str = "leather"
    layer: int = 3
    protection_overrides: dict[str, int] = field(default_factory=dict)
    current_parts: dict[str, int] = field(init=False)

    def __post_init__(self) -> None:
        # Initialize current per-part SFÉ
        self.current_parts = {k: max(0, int(v)) for k, v in (self.parts or {}).items()}

    # API per spec
    def covers(self, zone: str) -> bool:
        return self.parts.get(zone, 0) > 0

    def get_sfé(self, zone: str) -> int:
        return int(self.current_parts.get(zone, 0))

    def get_mgt(self) -> int:
        return int(self.mgt)

    # Degrade only the specified zone
    def degrade_zone(self, zone: str, amount: int = 1) -> None:
        if zone in self.current_parts:
            self.current_parts[zone] = max(0, self.current_parts[zone] - amount)

    def total_current_sfe(self) -> int:
        return sum(self.current_parts.values())


# ------------------------------
# ArmorSystem (aggregation)
# ------------------------------


@dataclass
class ArmorSystem:
    """Aggregates all equipped armor and provides queries/validation."""

    pieces: list[ArmorPiece] = field(default_factory=list)

    def validate_no_overlap_same_layer(self) -> tuple[bool, str]:
        """Ensure no two pieces cover the same main part on the same layer."""
        seen: dict[tuple[int, str], str] = {}
        for p in self.pieces:
            for part, v in p.parts.items():
                if v <= 0:
                    continue
                key = (p.layer, part)
                if key in seen:
                    return (
                        False,
                        f"Overlap on layer {p.layer} for zone {part} ({seen[key]} vs {p.name})",
                    )
                seen[key] = p.name
        return True, ""

    def get_sfe_for_hit(self, hit_zone: str) -> int:
        """Sum SFÉ from all layers covering the given main part."""
        total = 0
        for p in self.pieces:
            total += p.get_sfé(hit_zone)
        return total

    def get_total_mgt(self) -> int:
        return sum(p.get_mgt() for p in self.pieces)

    def reduce_sfe(self, hit_zone: str, amount: int = 1) -> None:
        """Reduce SFÉ at hit_zone on the outermost covering layer (lowest layer index)."""
        # Find covering pieces sorted by layer ascending (outermost first)
        covering = [p for p in self.pieces if p.covers(hit_zone) and p.get_sfé(hit_zone) > 0]
        if not covering:
            return
        covering.sort(key=lambda p: p.layer)  # layer 1 first
        covering[0].degrade_zone(hit_zone, amount)

    # Convenience for applying global degradation (fallback legacy behavior)
    def degrade_all(self, amount: int = 1) -> None:
        for p in self.pieces:
            for part in list(p.current_parts.keys()):
                p.degrade_zone(part, amount)


# ------------------------------
# HitzoneResolver (weighted)
# ------------------------------


class HitzoneResolver:
    """Selects a main hit zone based on static weights.

    Later can be extended with facing/height modifiers.
    """

    HITZONE_WEIGHTS: dict[str, int] = {
        "sisak": 10,
        "mellvért": 40,
        "vállvédő": 10,
        "felkarvédő": 5,
        "alkarvédő": 5,
        "combvédő": 10,
        "lábszárvédő": 10,
        "csizma": 10,
    }

    @classmethod
    def resolve(cls, rng: random.Random | None = None) -> str:
        r = rng or random
        items = list(cls.HITZONE_WEIGHTS.items())
        parts, weights = zip(*items, strict=False)
        total = sum(weights)
        roll = r.randint(1, total)
        acc = 0
        for part, w in items:
            acc += w
            if roll <= acc:
                return part
        return parts[-1]
