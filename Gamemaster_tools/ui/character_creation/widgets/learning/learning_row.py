"""
View model for a skill row in the learning step.
Simplifies passing data to the table renderer.
"""

from dataclasses import dataclass


@dataclass
class LearningRow:
    """Represents a single skill row in the learning step table."""

    skill_id: str
    display_name: str
    level: int
    percent: int
    kp_cost: int
    skill_type: int  # 1 = level, 2 = percent
    prereq_text: str
    prereq_met: bool
    is_mandatory: bool
    mandatory_level: int
    mandatory_percent: int
