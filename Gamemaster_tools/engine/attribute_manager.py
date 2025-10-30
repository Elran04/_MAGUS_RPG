"""
Attribute management system for character creation.
Handles dice rolling, point-buy allocation, and modifier tracking.
"""
import random
from typing import Dict, Tuple, Optional
from utils.class_db_manager import ClassDBManager
from data.race.race_age_stat_modifiers import (
    apply_age_modifiers, 
    apply_race_modifiers,
    get_age_modifiers,
    RACE_MODIFIERS
)


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
        # Storage for base values (class min + modifiers applied)
        self.base_values: Dict[str, int] = {}
        # Storage for class rolled/allocated values (before race/age)
        self.class_values: Dict[str, int] = {}
        # Final computed values
        self.final_values: Dict[str, int] = {}
        # Stat ranges from class
        self.stat_ranges: Dict[str, Tuple[int, int]] = {}
        # Double-roll stats
        self.double_roll_stats: set = set()
        # Available points for point-buy
        self.available_points: int = 0
        # Track modifiers for breakdown
        self.race_modifiers: Dict[str, int] = {}
        self.age_modifiers: Dict[str, int] = {}
        
    def initialize_for_class(self, class_name: str, race: str, age: int):
        """Initialize attribute system for a given class, race, and age."""
        # Get class details
        classes = self.class_db.list_classes()
        class_id = next((cid for cid, name in classes if name == class_name), None)
        if class_id is None:
            raise ValueError(f"Class '{class_name}' not found in DB")
        
        details = self.class_db.get_class_details(class_id)
        
        # Parse stat ranges and double-roll flags
        self.stat_ranges = {}
        self.double_roll_stats = set()
        
        for row in details["stats"]:
            if len(row) == 4:
                stat, minv, maxv, double_chance = row
            elif len(row) == 3:
                stat, minv, maxv = row
                double_chance = 0
            else:
                continue
            self.stat_ranges[stat] = (int(minv), int(maxv))
            if double_chance:
                self.double_roll_stats.add(stat)
        
        # Ensure all attributes have ranges
        for attr in self.ATTRIBUTES:
            if attr not in self.stat_ranges:
                self.stat_ranges[attr] = (8, 18)
        
        # Store race and age modifiers
        race_data = RACE_MODIFIERS.get(race, {})
        self.race_modifiers = race_data.get("modifiers", {})
        self.age_modifiers = get_age_modifiers(race, age)
        
        # Calculate available points for point-buy mode
        self.available_points = self._calculate_point_pool()
        
    def _calculate_point_pool(self) -> int:
        """
        Calculate total available points based on class stat ranges.
        
        Formula:
        - For each attribute range:
          - avg = floor((min + max) / 2)
          - base_points = avg - min (if avg <= 12)
          - bonus_points_13_15 = +2 * (avg - 12) for each point 13-15
          - bonus_points_16+ = +3 * (avg - 15) for each point 16+
        """
        total_points = 0
        
        for attr in self.ATTRIBUTES:
            min_val, max_val = self.stat_ranges.get(attr, (8, 18))
            avg = (min_val + max_val) // 2  # Floor division
            
            # Base points if avg <= 12
            if avg <= 12:
                total_points += (avg - min_val)
            
            # Bonus points for 13-15 range
            if avg >= 13:
                points_in_13_15 = min(avg, 15) - 12
                total_points += points_in_13_15 * 2
            
            # Bonus points for 16+ range
            if avg >= 16:
                points_above_15 = avg - 15
                total_points += points_above_15 * 3
        
        return total_points
    
    def roll_attributes(self, race: str, age: int) -> Dict[str, int]:
        """
        Roll attributes using dice based on class ranges.
        Applies race and age modifiers.
        """
        # Roll class values
        self.class_values = {}
        for attr in self.ATTRIBUTES:
            min_val, max_val = self.stat_ranges.get(attr, (8, 18))
            
            if attr in self.double_roll_stats:
                # Roll twice, take higher
                roll1 = random.randint(min_val, max_val)
                roll2 = random.randint(min_val, max_val)
                self.class_values[attr] = max(roll1, roll2)
            else:
                self.class_values[attr] = random.randint(min_val, max_val)
        
        # Apply modifiers to get base and final values
        self._apply_modifiers(race, age)
        return self.final_values.copy()
    
    def set_point_buy_value(self, attr: str, value: int, race: str, age: int) -> bool:
        """
        Set an attribute value in point-buy mode.
        Returns True if valid, False if out of range or insufficient points.
        """
        min_val, max_val = self.stat_ranges.get(attr, (8, 18))
        
        if value < min_val or value > max_val:
            return False
        
        # Calculate point cost for this value
        cost = self._calculate_point_cost(attr, value)
        
        # Calculate total spent on other attributes
        current_spent = sum(
            self._calculate_point_cost(a, self.class_values.get(a, self.stat_ranges[a][0]))
            for a in self.ATTRIBUTES if a != attr
        )
        
        if current_spent + cost > self.available_points:
            return False
        
        self.class_values[attr] = value
        self._apply_modifiers(race, age)
        return True
    
    def _calculate_point_cost(self, attr: str, value: int) -> int:
        """Calculate point cost for setting an attribute to a specific value."""
        min_val, _ = self.stat_ranges.get(attr, (8, 18))
        
        if value <= min_val:
            return 0
        
        cost = 0
        for v in range(min_val + 1, value + 1):
            if v <= 12:
                cost += 1
            elif v <= 15:
                cost += 2
            else:
                cost += 3
        
        return cost
    
    def get_spent_points(self) -> int:
        """Return total points spent in point-buy mode."""
        return sum(
            self._calculate_point_cost(attr, self.class_values.get(attr, self.stat_ranges[attr][0]))
            for attr in self.ATTRIBUTES
        )
    
    def _apply_modifiers(self, race: str, age: int):
        """Apply race and age modifiers to class values."""
        # Start with class values
        temp_stats = self.class_values.copy()
        
        # Apply age modifiers
        temp_stats = apply_age_modifiers(temp_stats, race, age)
        
        # Apply race modifiers
        temp_stats = apply_race_modifiers(temp_stats, race)
        
        self.final_values = temp_stats
        
        # Base values are class minimum + race/age modifiers
        self.base_values = {}
        for attr in self.ATTRIBUTES:
            min_val = self.stat_ranges[attr][0]
            base = min_val
            base += self.race_modifiers.get(attr, 0)
            base += self.age_modifiers.get(attr, 0)
            self.base_values[attr] = base
    
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
        self.class_values = {
            attr: self.stat_ranges[attr][0] 
            for attr in self.ATTRIBUTES
        }
        self._apply_modifiers(race, age)
