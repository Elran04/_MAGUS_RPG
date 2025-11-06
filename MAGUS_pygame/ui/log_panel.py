"""
Combat log panel for MAGUS Pygame.
Displays combat messages, dice rolls, and event history.
"""

from typing import Tuple, Optional
import pygame
from collections import deque


class LogMessage:
    """Represents a single log message."""

    def __init__(self, text: str, color: Tuple[int, int, int] = (255, 255, 255)) -> None:
        """Initialize a log message.
        
        Args:
            text: Message text
            color: Text color RGB tuple
        """
        self.text = text
        self.color = color
        self.timestamp = pygame.time.get_ticks()


class LogPanel:
    """Combat log display panel."""

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        max_messages: int = 100
    ) -> None:
        """Initialize the log panel.
        
        Args:
            x: Panel x position
            y: Panel y position
            width: Panel width
            height: Panel height
            max_messages: Maximum messages to keep in history
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.max_messages = max_messages
        
        # Message storage
        self.messages: deque[LogMessage] = deque(maxlen=max_messages)
        
        # Display settings
        self.font = pygame.font.Font(None, 20)
        self.line_height = 22
        self.padding = 10
        self.scroll_offset = 0
        
        # Colors
        self.bg_color = (0, 0, 0, 200)  # Semi-transparent black
        self.border_color = (100, 100, 100)
        self.default_text_color = (255, 255, 255)
        
        # Message type colors
        self.color_attack = (255, 100, 100)  # Light red
        self.color_damage = (255, 50, 50)  # Red
        self.color_heal = (100, 255, 100)  # Light green
        self.color_skill = (100, 200, 255)  # Light blue
        self.color_info = (200, 200, 200)  # Gray
        self.color_important = (255, 215, 0)  # Gold

    def add_message(self, text: str, color: Optional[Tuple[int, int, int]] = None) -> None:
        """Add a message to the log.
        
        Args:
            text: Message text
            color: Optional text color (uses default if None)
        """
        if color is None:
            color = self.default_text_color
            
        message = LogMessage(text, color)
        self.messages.append(message)
        
        # Auto-scroll to bottom
        self.scroll_to_bottom()

    def add_attack(self, attacker: str, defender: str, hit: bool) -> None:
        """Add an attack message.
        
        Args:
            attacker: Attacker name
            defender: Defender name
            hit: Whether attack hit
        """
        if hit:
            text = f"{attacker} attacks {defender}!"
            self.add_message(text, self.color_attack)
        else:
            text = f"{attacker} attacks {defender} but misses!"
            self.add_message(text, self.color_info)

    def add_damage(self, target: str, damage: int, damage_type: str = "damage") -> None:
        """Add a damage message.
        
        Args:
            target: Target name
            damage: Damage amount
            damage_type: Type of damage
        """
        text = f"{target} takes {damage} {damage_type}!"
        self.add_message(text, self.color_damage)

    def add_heal(self, target: str, amount: int) -> None:
        """Add a healing message.
        
        Args:
            target: Target name
            amount: Healing amount
        """
        text = f"{target} recovers {amount} HP!"
        self.add_message(text, self.color_heal)

    def add_skill_use(self, user: str, skill_name: str) -> None:
        """Add a skill usage message.
        
        Args:
            user: Skill user name
            skill_name: Skill name
        """
        text = f"{user} uses {skill_name}!"
        self.add_message(text, self.color_skill)

    def add_turn_start(self, unit_name: str, round_num: int) -> None:
        """Add a turn start message.
        
        Args:
            unit_name: Unit whose turn is starting
            round_num: Current round number
        """
        text = f"--- Round {round_num}: {unit_name}'s turn ---"
        self.add_message(text, self.color_important)

    def add_dice_roll(self, purpose: str, roll: int, modifier: int = 0) -> None:
        """Add a dice roll message.
        
        Args:
            purpose: What the roll is for
            roll: Dice result
            modifier: Modifier applied
        """
        if modifier != 0:
            sign = "+" if modifier >= 0 else ""
            text = f"{purpose}: Rolled {roll} {sign}{modifier} = {roll + modifier}"
        else:
            text = f"{purpose}: Rolled {roll}"
        self.add_message(text, self.color_info)

    def scroll(self, amount: int) -> None:
        """Scroll the log.
        
        Args:
            amount: Scroll amount (positive = down, negative = up)
        """
        self.scroll_offset += amount
        
        # Clamp scroll
        max_scroll = max(0, len(self.messages) * self.line_height - self.height + self.padding * 2)
        self.scroll_offset = max(0, min(max_scroll, self.scroll_offset))

    def scroll_to_bottom(self) -> None:
        """Scroll to the bottom of the log."""
        max_scroll = max(0, len(self.messages) * self.line_height - self.height + self.padding * 2)
        self.scroll_offset = max_scroll

    def scroll_to_top(self) -> None:
        """Scroll to the top of the log."""
        self.scroll_offset = 0

    def clear(self) -> None:
        """Clear all messages."""
        self.messages.clear()
        self.scroll_offset = 0

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle input events for scrolling.
        
        Args:
            event: Pygame event
        """
        if event.type == pygame.MOUSEWHEEL:
            # Check if mouse is over panel
            mouse_pos = pygame.mouse.get_pos()
            if self.is_point_inside(mouse_pos[0], mouse_pos[1]):
                self.scroll(-event.y * self.line_height)

    def is_point_inside(self, px: int, py: int) -> bool:
        """Check if a point is inside the panel.
        
        Args:
            px: Point x coordinate
            py: Point y coordinate
            
        Returns:
            True if point is inside panel
        """
        return (self.x <= px <= self.x + self.width and
                self.y <= py <= self.y + self.height)

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the log panel.
        
        Args:
            surface: Surface to draw on
        """
        # Draw background
        bg_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        bg_surface.fill(self.bg_color)
        surface.blit(bg_surface, (self.x, self.y))
        
        # Draw border
        border_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.border_color, border_rect, 2)
        
        # Draw messages
        visible_height = self.height - self.padding * 2
        y_offset = self.y + self.padding - self.scroll_offset
        
        for message in self.messages:
            # Only draw if in visible area
            if y_offset + self.line_height >= self.y and y_offset <= self.y + self.height:
                text_surface = self.font.render(message.text, True, message.color)
                
                # Clip to panel width
                max_width = self.width - self.padding * 2
                if text_surface.get_width() > max_width:
                    # Create clipped subsurface
                    clip_rect = pygame.Rect(0, 0, max_width, text_surface.get_height())
                    text_surface = text_surface.subsurface(clip_rect)
                
                surface.blit(text_surface, (self.x + self.padding, y_offset))
            
            y_offset += self.line_height

    def get_message_count(self) -> int:
        """Get the number of messages in the log.
        
        Returns:
            Message count
        """
        return len(self.messages)
