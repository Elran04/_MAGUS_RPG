"""
Combat skills system for MAGUS Pygame.
Manages skill usage, cooldowns, and effects.
"""

from typing import Any, Optional, Callable
from enum import Enum, auto


class SkillType(Enum):
    """Types of combat skills."""
    MELEE_ATTACK = auto()
    RANGED_ATTACK = auto()
    DEFENSIVE = auto()
    MOVEMENT = auto()
    UTILITY = auto()
    SPECIAL = auto()


class SkillTarget(Enum):
    """Target types for skills."""
    SELF = auto()
    SINGLE_ENEMY = auto()
    SINGLE_ALLY = auto()
    AREA = auto()
    LINE = auto()
    CONE = auto()


class Skill:
    """Represents a combat skill."""

    def __init__(
        self,
        skill_id: str,
        name: str,
        description: str,
        skill_type: SkillType,
        target_type: SkillTarget,
        cooldown: int = 0,
        stamina_cost: int = 0,
        range_tiles: int = 1
    ) -> None:
        """Initialize a skill.
        
        Args:
            skill_id: Unique skill identifier
            name: Display name
            description: Skill description
            skill_type: Type of skill
            target_type: Targeting type
            cooldown: Cooldown in rounds (0 = no cooldown)
            stamina_cost: Stamina cost to use
            range_tiles: Range in hex tiles
        """
        self.skill_id = skill_id
        self.name = name
        self.description = description
        self.skill_type = skill_type
        self.target_type = target_type
        self.cooldown = cooldown
        self.stamina_cost = stamina_cost
        self.range_tiles = range_tiles
        
        # Runtime state
        self.current_cooldown = 0
        self.is_learned = False

    def is_available(self) -> bool:
        """Check if skill is available to use.
        
        Returns:
            True if not on cooldown
        """
        return self.current_cooldown == 0

    def use(self) -> None:
        """Use the skill, putting it on cooldown."""
        self.current_cooldown = self.cooldown

    def tick_cooldown(self) -> None:
        """Reduce cooldown by 1 round."""
        if self.current_cooldown > 0:
            self.current_cooldown -= 1

    def reset_cooldown(self) -> None:
        """Reset cooldown to 0."""
        self.current_cooldown = 0


class SkillSystem:
    """Manages combat skills for a unit."""

    def __init__(self) -> None:
        """Initialize the skill system."""
        self.known_skills: dict[str, Skill] = {}
        self.equipped_skills: list[str] = []  # Skill IDs in skill bar
        self.max_equipped = 8  # Max skills that can be equipped at once
        
        # Callbacks
        self._on_skill_used: list[Callable[[Skill], None]] = []
        self._on_skill_learned: list[Callable[[Skill], None]] = []

    def learn_skill(self, skill: Skill) -> bool:
        """Learn a new skill.
        
        Args:
            skill: The skill to learn
            
        Returns:
            True if skill was learned (not already known)
        """
        if skill.skill_id in self.known_skills:
            return False
            
        skill.is_learned = True
        self.known_skills[skill.skill_id] = skill
        
        # Notify listeners
        for callback in self._on_skill_learned:
            callback(skill)
        
        return True

    def equip_skill(self, skill_id: str) -> bool:
        """Equip a skill to the skill bar.
        
        Args:
            skill_id: ID of the skill to equip
            
        Returns:
            True if skill was equipped
        """
        if skill_id not in self.known_skills:
            return False
            
        if skill_id in self.equipped_skills:
            return False  # Already equipped
            
        if len(self.equipped_skills) >= self.max_equipped:
            return False  # Skill bar full
            
        self.equipped_skills.append(skill_id)
        return True

    def unequip_skill(self, skill_id: str) -> bool:
        """Unequip a skill from the skill bar.
        
        Args:
            skill_id: ID of the skill to unequip
            
        Returns:
            True if skill was unequipped
        """
        if skill_id in self.equipped_skills:
            self.equipped_skills.remove(skill_id)
            return True
        return False

    def use_skill(self, skill_id: str) -> bool:
        """Use a skill.
        
        Args:
            skill_id: ID of the skill to use
            
        Returns:
            True if skill was used successfully
        """
        if skill_id not in self.known_skills:
            return False
            
        skill = self.known_skills[skill_id]
        
        if not skill.is_available():
            return False
            
        skill.use()
        
        # Notify listeners
        for callback in self._on_skill_used:
            callback(skill)
        
        return True

    def get_skill(self, skill_id: str) -> Optional[Skill]:
        """Get a skill by ID.
        
        Args:
            skill_id: The skill ID
            
        Returns:
            The skill if known, None otherwise
        """
        return self.known_skills.get(skill_id)

    def get_equipped_skills(self) -> list[Skill]:
        """Get all equipped skills.
        
        Returns:
            List of equipped skills
        """
        skills: list[Skill] = []
        for skill_id in self.equipped_skills:
            if skill_id in self.known_skills:
                skills.append(self.known_skills[skill_id])
        return skills

    def get_available_skills(self) -> list[Skill]:
        """Get all equipped skills that are available to use.
        
        Returns:
            List of available equipped skills
        """
        return [s for s in self.get_equipped_skills() if s.is_available()]

    def tick_cooldowns(self) -> None:
        """Tick down all skill cooldowns by 1 round."""
        for skill in self.known_skills.values():
            skill.tick_cooldown()

    def reset_all_cooldowns(self) -> None:
        """Reset all skill cooldowns to 0."""
        for skill in self.known_skills.values():
            skill.reset_cooldown()

    def register_on_skill_used(self, callback: Callable[[Skill], None]) -> None:
        """Register a callback for when a skill is used.
        
        Args:
            callback: Function called with the used skill
        """
        self._on_skill_used.append(callback)

    def register_on_skill_learned(self, callback: Callable[[Skill], None]) -> None:
        """Register a callback for when a skill is learned.
        
        Args:
            callback: Function called with the learned skill
        """
        self._on_skill_learned.append(callback)


def create_basic_skills() -> list[Skill]:
    """Create a set of basic combat skills.
    
    Returns:
        List of basic skills
    """
    return [
        Skill(
            skill_id="slash",
            name="Slash",
            description="A basic melee attack",
            skill_type=SkillType.MELEE_ATTACK,
            target_type=SkillTarget.SINGLE_ENEMY,
            cooldown=0,
            stamina_cost=15,
            range_tiles=1
        ),
        Skill(
            skill_id="power_strike",
            name="Power Strike",
            description="A powerful melee attack with +50% damage",
            skill_type=SkillType.MELEE_ATTACK,
            target_type=SkillTarget.SINGLE_ENEMY,
            cooldown=2,
            stamina_cost=25,
            range_tiles=1
        ),
        Skill(
            skill_id="defend",
            name="Defend",
            description="Take a defensive stance, reducing damage taken",
            skill_type=SkillType.DEFENSIVE,
            target_type=SkillTarget.SELF,
            cooldown=0,
            stamina_cost=10,
            range_tiles=0
        ),
        Skill(
            skill_id="dodge",
            name="Dodge",
            description="Attempt to dodge the next attack",
            skill_type=SkillType.DEFENSIVE,
            target_type=SkillTarget.SELF,
            cooldown=3,
            stamina_cost=20,
            range_tiles=0
        ),
        Skill(
            skill_id="sprint",
            name="Sprint",
            description="Move twice as far this turn",
            skill_type=SkillType.MOVEMENT,
            target_type=SkillTarget.SELF,
            cooldown=4,
            stamina_cost=30,
            range_tiles=0
        ),
    ]
