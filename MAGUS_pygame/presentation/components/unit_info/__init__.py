"""
Unit info popup component - modular tab-based UI for displaying unit details.

Modules:
- popup_style: Centralized styling constants and fonts
- unit_info_popup: Main coordinator class
- tab_stats: Health, combat stats, and weapon info
- tab_attributes: Character properties with MGT impact
- tab_equipment: Current equipped gear
- tab_skills: Learned skills display
- tab_conditions: Status effects and penalties
"""

from .popup_style import PopupStyle
from .unit_info_popup import UnitInfoPopup

__all__ = ["UnitInfoPopup", "PopupStyle"]
