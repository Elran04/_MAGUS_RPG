"""
Magic system for MAGUS Pygame.
Manages spells, mana, and magical effects.
"""

from typing import Any, Optional, Callable
from enum import Enum, auto


class MagicSchool(Enum):
    """Schools of magic."""
    ELEMENTAL = auto()
    MENTAL = auto()
    DIVINE = auto()
    NECROMANCY = auto()
    ILLUSION = auto()
    TRANSMUTATION = auto()


class SpellTarget(Enum):
    """Target types for spells."""
    SELF = auto()
    SINGLE_ENEMY = auto()
    SINGLE_ALLY = auto()
    AREA = auto()
    LINE = auto()
    CONE = auto()


class Spell:
    """Represents a magic spell."""

    def __init__(
        self,
        spell_id: str,
        name: str,
        description: str,
        school: MagicSchool,
        target_type: SpellTarget,
        mana_cost: int,
        cast_time: int = 1,
        cooldown: int = 0,
        range_tiles: int = 5,
        area_radius: int = 0
    ) -> None:
        """Initialize a spell.
        
        Args:
            spell_id: Unique spell identifier
            name: Display name
            description: Spell description
            school: School of magic
            target_type: Targeting type
            mana_cost: Mana cost to cast
            cast_time: Rounds required to cast
            cooldown: Cooldown in rounds after casting
            range_tiles: Range in hex tiles
            area_radius: Radius for area spells
        """
        self.spell_id = spell_id
        self.name = name
        self.description = description
        self.school = school
        self.target_type = target_type
        self.mana_cost = mana_cost
        self.cast_time = cast_time
        self.cooldown = cooldown
        self.range_tiles = range_tiles
        self.area_radius = area_radius
        
        # Runtime state
        self.current_cooldown = 0
        self.is_learned = False

    def is_available(self) -> bool:
        """Check if spell is available to cast.
        
        Returns:
            True if not on cooldown
        """
        return self.current_cooldown == 0

    def cast(self) -> None:
        """Cast the spell, putting it on cooldown."""
        self.current_cooldown = self.cooldown

    def tick_cooldown(self) -> None:
        """Reduce cooldown by 1 round."""
        if self.current_cooldown > 0:
            self.current_cooldown -= 1

    def reset_cooldown(self) -> None:
        """Reset cooldown to 0."""
        self.current_cooldown = 0


class ManaSystem:
    """Manages mana for spellcasting."""

    def __init__(self, max_mana: int = 100) -> None:
        """Initialize the mana system.
        
        Args:
            max_mana: Maximum mana points
        """
        self.max_mana = max_mana
        self.current_mana = max_mana
        self.mana_regen = 5  # Mana regenerated per round
        
        # Callbacks
        self._on_mana_changed: list[Callable[[int, int], None]] = []

    def can_afford(self, cost: int) -> bool:
        """Check if unit has enough mana.
        
        Args:
            cost: Mana cost
            
        Returns:
            True if cost can be afforded
        """
        return self.current_mana >= cost

    def spend(self, cost: int) -> bool:
        """Spend mana.
        
        Args:
            cost: Amount of mana to spend
            
        Returns:
            True if mana was spent, False if insufficient
        """
        if self.current_mana >= cost:
            old_mana = self.current_mana
            self.current_mana -= cost
            self._notify_mana_changed(old_mana, self.current_mana)
            return True
        return False

    def restore(self, amount: Optional[int] = None) -> None:
        """Restore mana.
        
        Args:
            amount: Amount to restore (None = passive regen)
        """
        if amount is None:
            amount = self.mana_regen
            
        old_mana = self.current_mana
        self.current_mana = min(self.max_mana, self.current_mana + amount)
        
        if old_mana != self.current_mana:
            self._notify_mana_changed(old_mana, self.current_mana)

    def get_mana_percentage(self) -> float:
        """Get current mana as a percentage.
        
        Returns:
            Mana percentage (0.0 to 1.0)
        """
        return self.current_mana / self.max_mana if self.max_mana > 0 else 0.0

    def register_on_changed(self, callback: Callable[[int, int], None]) -> None:
        """Register a callback for mana changes.
        
        Args:
            callback: Function called with (old_mana, new_mana)
        """
        self._on_mana_changed.append(callback)

    def _notify_mana_changed(self, old_value: int, new_value: int) -> None:
        """Notify listeners of mana change.
        
        Args:
            old_value: Previous mana value
            new_value: New mana value
        """
        for callback in self._on_mana_changed:
            callback(old_value, new_value)


class MagicSystem:
    """Manages magic spells and casting for a unit."""

    def __init__(self, max_mana: int = 100) -> None:
        """Initialize the magic system.
        
        Args:
            max_mana: Maximum mana points
        """
        self.mana_system = ManaSystem(max_mana)
        self.known_spells: dict[str, Spell] = {}
        self.prepared_spells: list[str] = []  # Spell IDs
        self.max_prepared = 6
        
        # Casting state
        self.is_casting = False
        self.current_spell: Optional[str] = None
        self.cast_progress = 0
        
        # Callbacks
        self._on_spell_cast: list[Callable[[Spell], None]] = []
        self._on_spell_learned: list[Callable[[Spell], None]] = []

    def learn_spell(self, spell: Spell) -> bool:
        """Learn a new spell.
        
        Args:
            spell: The spell to learn
            
        Returns:
            True if spell was learned
        """
        if spell.spell_id in self.known_spells:
            return False
            
        spell.is_learned = True
        self.known_spells[spell.spell_id] = spell
        
        for callback in self._on_spell_learned:
            callback(spell)
        
        return True

    def prepare_spell(self, spell_id: str) -> bool:
        """Prepare a spell for use.
        
        Args:
            spell_id: ID of spell to prepare
            
        Returns:
            True if spell was prepared
        """
        if spell_id not in self.known_spells:
            return False
            
        if spell_id in self.prepared_spells:
            return False
            
        if len(self.prepared_spells) >= self.max_prepared:
            return False
            
        self.prepared_spells.append(spell_id)
        return True

    def unprepare_spell(self, spell_id: str) -> bool:
        """Unprepare a spell.
        
        Args:
            spell_id: ID of spell to unprepare
            
        Returns:
            True if spell was unprepared
        """
        if spell_id in self.prepared_spells:
            self.prepared_spells.remove(spell_id)
            return True
        return False

    def can_cast_spell(self, spell_id: str) -> bool:
        """Check if a spell can be cast.
        
        Args:
            spell_id: The spell ID
            
        Returns:
            True if spell can be cast
        """
        if spell_id not in self.known_spells:
            return False
            
        spell = self.known_spells[spell_id]
        
        if not spell.is_available():
            return False
            
        if not self.mana_system.can_afford(spell.mana_cost):
            return False
            
        return True

    def begin_cast(self, spell_id: str) -> bool:
        """Begin casting a spell.
        
        Args:
            spell_id: ID of spell to cast
            
        Returns:
            True if casting began successfully
        """
        if not self.can_cast_spell(spell_id):
            return False
            
        self.is_casting = True
        self.current_spell = spell_id
        self.cast_progress = 0
        return True

    def update_casting(self) -> bool:
        """Update casting progress for one round.
        
        Returns:
            True if spell was completed this round
        """
        if not self.is_casting or not self.current_spell:
            return False
            
        spell = self.known_spells[self.current_spell]
        self.cast_progress += 1
        
        if self.cast_progress >= spell.cast_time:
            # Spell complete
            self.mana_system.spend(spell.mana_cost)
            spell.cast()
            
            for callback in self._on_spell_cast:
                callback(spell)
            
            self.is_casting = False
            self.current_spell = None
            self.cast_progress = 0
            return True
            
        return False

    def interrupt_casting(self) -> None:
        """Interrupt current spell casting."""
        self.is_casting = False
        self.current_spell = None
        self.cast_progress = 0

    def tick_cooldowns(self) -> None:
        """Tick down all spell cooldowns."""
        for spell in self.known_spells.values():
            spell.tick_cooldown()

    def regenerate_mana(self) -> None:
        """Regenerate mana for one round."""
        self.mana_system.restore()

    def get_spell(self, spell_id: str) -> Optional[Spell]:
        """Get a spell by ID.
        
        Args:
            spell_id: The spell ID
            
        Returns:
            The spell if known, None otherwise
        """
        return self.known_spells.get(spell_id)

    def get_prepared_spells(self) -> list[Spell]:
        """Get all prepared spells.
        
        Returns:
            List of prepared spells
        """
        spells: list[Spell] = []
        for spell_id in self.prepared_spells:
            if spell_id in self.known_spells:
                spells.append(self.known_spells[spell_id])
        return spells

    def register_on_spell_cast(self, callback: Callable[[Spell], None]) -> None:
        """Register a callback for spell casting.
        
        Args:
            callback: Function called when spell is cast
        """
        self._on_spell_cast.append(callback)

    def register_on_spell_learned(self, callback: Callable[[Spell], None]) -> None:
        """Register a callback for spell learning.
        
        Args:
            callback: Function called when spell is learned
        """
        self._on_spell_learned.append(callback)
