"""
Attribute management system for character creation.
Handles dice rolling, point-buy allocation, and modifier tracking.
"""
import random
from typing import Dict, Optional, Tuple

from data.race.race_age_stat_modifiers import (
    RACE_MODIFIERS,
    apply_age_modifiers,
    apply_race_modifiers,
    get_age_modifiers,
)
from utils.class_db_manager import ClassDBManager


class AttributeManager:
    """
    Manages character attributes with support for:
    - Dice rolling (standard and double-roll for certain stats)
    - Point-buy allocation
    - Race, age, and class modifier tracking
    - Breakdown display for tooltips
    """
    
    ATTRIBUTES = [
        "Erő", "Gyorsaság", "Ügyesség", "Állóképesség", 
        "Egészség", "Karizma", "Intelligencia", "Akaraterő", 
        "Asztrál", "Érzékelés"
    ]
    
    def __init__(self, class_db: ClassDBManager):
        self.class_db = class_db
        self.class_values: Dict[str, int] = {}  # Class rolled/allocated values (before race/age)
        self.original_class_values: Dict[str, int] = {}  # Original rolled values for ±2 hybrid adjustments
        self.final_values: Dict[str, int] = {}  # Final computed values after all modifiers
        self.stat_ranges: Dict[str, Tuple[int, int]] = {}  # Stat ranges from class
        self.double_roll_stats: set = set()  # Stats with double-roll advantage
        self.available_points: int = 0  # Available points for point-buy
        self.race_modifiers: Dict[str, int] = {}  # Race modifiers for breakdown
        self.age_modifiers: Dict[str, int] = {}  # Age modifiers for breakdown
        
    def initialize_for_class(self, class_name: str, race: str, age: int):
        """Initialize attribute system for a given class, race, and age."""
        class_id = self._get_class_id(class_name)
        details = self.class_db.get_class_details(class_id)
        
        # Parse stat ranges and double-roll flags
        self._parse_stat_ranges(details["stats"])
        
        # Store race and age modifiers
        self.race_modifiers = RACE_MODIFIERS.get(race, {}).get("modifiers", {})
        self.age_modifiers = get_age_modifiers(race, age)
        
        # Calculate available points for point-buy mode
        self.available_points = self._calculate_point_pool()
    
    def _get_class_id(self, class_name: str) -> int:
        """Get class ID from class name."""
        classes = self.class_db.list_classes()
        class_id = next((cid for cid, name in classes if name == class_name), None)
        if class_id is None:
            raise ValueError(f"Class '{class_name}' not found in DB")
        return class_id
    
    def _parse_stat_ranges(self, stats_data):
        """Parse stat ranges and double-roll flags from class data."""
        self.stat_ranges = {}
        self.double_roll_stats = set()
        
        for row in stats_data:
            if len(row) >= 3:
                stat, minv, maxv = row[:3]
                double_chance = row[3] if len(row) == 4 else 0
                self.stat_ranges[stat] = (int(minv), int(maxv))
                if double_chance:
                    self.double_roll_stats.add(stat)
        
        # Ensure all attributes have ranges
        for attr in self.ATTRIBUTES:
            if attr not in self.stat_ranges:
                self.stat_ranges[attr] = (8, 18)
        
    def _calculate_point_pool(self) -> int:
        """Calculate total available points based on class stat ranges."""
        total_points = 0
        for attr in self.ATTRIBUTES:
            min_val, max_val = self.stat_ranges.get(attr, (8, 18))
            avg = (min_val + max_val) // 2
            # Cost to raise from class minimum to average using tiered costs
            attr_points = 0
            for v in range(min_val + 1, avg + 1):
                attr_points += 1 if v <= 12 else (2 if v <= 15 else 3)
            # Double points for attributes that have double-roll advantage
            if attr in self.double_roll_stats:
                attr_points *= 2
            total_points += attr_points
        return total_points
    
    def roll_attributes(self, race: str, age: int) -> Dict[str, int]:
        """Roll attributes using dice based on class ranges. Applies race and age modifiers."""
        def normal_like_roll(min_val, max_val, rolls=5):
            return round(sum(random.randint(min_val, max_val) for _ in range(rolls)) / rolls)

        # Roll class values
        self.class_values = {}
        for attr in self.ATTRIBUTES:
            min_val, max_val = self.stat_ranges.get(attr, (8, 18))
            
            if attr in self.double_roll_stats:
                # Roll twice, take higher
                self.class_values[attr] = max(
                    normal_like_roll(min_val, max_val),
                    normal_like_roll(min_val, max_val)
                )
            else:
                self.class_values[attr] = normal_like_roll(min_val, max_val)

        # Capture baseline for hybrid adjustments
        self.original_class_values = self.class_values.copy()
        self._apply_modifiers(race, age)
        return self.final_values.copy()
    
    def set_point_buy_value(self, attr: str, value: int, race: str, age: int) -> bool:
        """Set an attribute value in point-buy mode. Returns True if valid."""
        min_val, max_val = self.stat_ranges.get(attr, (8, 18))
        
        if not (min_val <= value <= max_val):
            return False
        
        # Calculate total cost if we apply this change
        cost = self._calculate_point_cost(attr, value)
        other_cost = sum(
            self._calculate_point_cost(a, self.class_values.get(a, self.stat_ranges[a][0]))
            for a in self.ATTRIBUTES if a != attr
        )
        
        if cost + other_cost > self.available_points:
            return False
        
        self.class_values[attr] = value
        self._apply_modifiers(race, age)
        return True

    # --- Hybrid roll helpers ---
    def get_roll_limits(self, attr: str) -> Tuple[int, int]:
        """Return (min,max) allowed for roll-mode adjustment (±2 from original, within class range)."""
        min_val, max_val = self.stat_ranges.get(attr, (8, 18))
        base = self.original_class_values.get(attr, self.class_values.get(attr, min_val))
        lo = max(min_val, base - 2)
        hi = min(max_val, base + 2)
        return lo, hi

    def set_roll_value(self, attr: str, value: int, race: str, age: int) -> bool:
        """Set an attribute in roll mode with ±2 constraint and hybrid point rules."""
        if attr not in self.stat_ranges:
            return False
        
        lo, hi = self.get_roll_limits(attr)
        if not (lo <= value <= hi):
            return False
        
        # Test if change violates hybrid point budget
        old_val = self.class_values.get(attr)
        self.class_values[attr] = int(value)
        
        if self._hybrid_delta_sum() > 0:
            # Overspent - revert and reject
            if old_val is not None:
                self.class_values[attr] = old_val
            return False
        
        self._apply_modifiers(race, age)
        return True

    def set_original_class_values(self, values: Dict[str, int]):
        """Restore baseline rolled values for enforcing ±2 adjustments."""
        self.original_class_values = values.copy()
    
    def _calculate_point_cost(self, attr: str, value: int) -> int:
        """Calculate point cost for setting an attribute to a specific value."""
        min_val = self.stat_ranges.get(attr, (8, 18))[0]
        
        if value <= min_val:
            return 0
        
        cost = 0
        for v in range(min_val + 1, value + 1):
            cost += 1 if v <= 12 else (2 if v <= 15 else 3)
        return cost
    
    def get_spent_points(self) -> int:
        """Return total points spent in point-buy mode."""
        return sum(
            self._calculate_point_cost(attr, self.class_values.get(attr, self.stat_ranges[attr][0]))
            for attr in self.ATTRIBUTES
        )

    def _get_attr_value(self, attr: str, use_original: bool = False) -> int:
        """Helper to get attribute value from class_values or original_class_values."""
        min_val = self.stat_ranges.get(attr, (8, 18))[0]
        source = self.original_class_values if use_original else self.class_values
        return source.get(attr, min_val)
    
    def _hybrid_delta_sum(self) -> int:
        """Sum of point-cost deltas relative to baseline rolled values."""
        return sum(
            self._calculate_point_cost(attr, self._get_attr_value(attr)) -
            self._calculate_point_cost(attr, self._get_attr_value(attr, use_original=True))
            for attr in self.ATTRIBUTES
        )

    def get_hybrid_remaining_points(self) -> int:
        """Return remaining spendable points in hybrid mode."""
        delta_sum = self._hybrid_delta_sum()
        return 0 if delta_sum > 0 else -delta_sum

    def get_hybrid_spent_and_generated(self) -> tuple[int, int]:
        """Return (spent, generated) points relative to baseline in hybrid mode."""
        spent = generated = 0
        for attr in self.ATTRIBUTES:
            cur_cost = self._calculate_point_cost(attr, self._get_attr_value(attr))
            base_cost = self._calculate_point_cost(attr, self._get_attr_value(attr, use_original=True))
            delta = cur_cost - base_cost
            if delta > 0:
                spent += delta
            elif delta < 0:
                generated += -delta
        return spent, generated
    
    def _apply_modifiers(self, race: str, age: int):
        """Apply race and age modifiers to class values."""
        temp_stats = apply_age_modifiers(self.class_values.copy(), race, age)
        self.final_values = apply_race_modifiers(temp_stats, race)
        
        # Base values are class minimum + race/age modifiers
        self.base_values = {
            attr: self.stat_ranges[attr][0] + 
                  self.race_modifiers.get(attr, 0) + 
                  self.age_modifiers.get(attr, 0)
            for attr in self.ATTRIBUTES
        }
    
    def get_attribute_breakdown(self, attr: str) -> Dict[str, int]:
        """
        Get detailed breakdown of an attribute's value.
        Returns dict with: class_roll, race_mod, age_mod, final
        """
        return {
            "class_value": self.class_values.get(attr, 0),
            "race_modifier": self.race_modifiers.get(attr, 0),
            "age_modifier": self.age_modifiers.get(attr, 0),
            "final": self.final_values.get(attr, 0),
            "min": self.stat_ranges[attr][0],
            "max": self.stat_ranges[attr][1],
            "double_roll": attr in self.double_roll_stats
        }
    
    def get_all_final_values(self) -> Dict[str, int]:
        """Return all final attribute values."""
        return self.final_values.copy()
    
    def set_class_values(self, values: Dict[str, int], race: str, age: int):
        """Directly set class values (for loading saved data)."""
        self.class_values = values.copy()
        self._apply_modifiers(race, age)
    
    def reset_to_minimums(self, race: str, age: int):
        """Reset all attributes to class minimums."""
        self.class_values = {attr: self.stat_ranges[attr][0] for attr in self.ATTRIBUTES}
        self._apply_modifiers(race, age)
