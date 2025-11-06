"""
Animation system for sprite animations in MAGUS Pygame.
"""

from typing import Any, Optional
import pygame


class Animation:
    """Represents a single animation sequence."""

    def __init__(
        self,
        frames: list[pygame.Surface],
        frame_duration: int = 100,
        loop: bool = True
    ) -> None:
        """Initialize an animation.
        
        Args:
            frames: List of surfaces representing animation frames
            frame_duration: Duration of each frame in milliseconds
            loop: Whether the animation should loop
        """
        self.frames = frames
        self.frame_duration = frame_duration
        self.loop = loop
        
        self.current_frame = 0
        self.time_accumulated = 0
        self.is_playing = False
        self.is_finished = False

    def update(self, dt: int) -> None:
        """Update the animation state.
        
        Args:
            dt: Delta time in milliseconds
        """
        if not self.is_playing or self.is_finished:
            return
            
        self.time_accumulated += dt
        
        if self.time_accumulated >= self.frame_duration:
            self.time_accumulated = 0
            self.current_frame += 1
            
            if self.current_frame >= len(self.frames):
                if self.loop:
                    self.current_frame = 0
                else:
                    self.current_frame = len(self.frames) - 1
                    self.is_finished = True
                    self.is_playing = False

    def get_current_frame(self) -> pygame.Surface:
        """Get the current animation frame.
        
        Returns:
            The current frame surface
        """
        return self.frames[self.current_frame]

    def play(self) -> None:
        """Start playing the animation."""
        self.is_playing = True
        self.is_finished = False

    def pause(self) -> None:
        """Pause the animation."""
        self.is_playing = False

    def reset(self) -> None:
        """Reset the animation to the beginning."""
        self.current_frame = 0
        self.time_accumulated = 0
        self.is_finished = False


class AnimationManager:
    """Manages multiple animations for entities."""

    def __init__(self) -> None:
        """Initialize the animation manager."""
        self.animations: dict[str, Animation] = {}
        self.current_animation: Optional[str] = None

    def add_animation(self, name: str, animation: Animation) -> None:
        """Add a named animation.
        
        Args:
            name: Unique name for the animation
            animation: The animation to add
        """
        self.animations[name] = animation

    def play(self, name: str) -> None:
        """Play a named animation.
        
        Args:
            name: Name of the animation to play
        """
        if name not in self.animations:
            return
            
        # Stop current animation
        if self.current_animation and self.current_animation in self.animations:
            self.animations[self.current_animation].pause()
            
        # Start new animation
        self.current_animation = name
        self.animations[name].reset()
        self.animations[name].play()

    def update(self, dt: int) -> None:
        """Update the current animation.
        
        Args:
            dt: Delta time in milliseconds
        """
        if self.current_animation and self.current_animation in self.animations:
            self.animations[self.current_animation].update(dt)

    def get_current_frame(self) -> Optional[pygame.Surface]:
        """Get the current frame of the active animation.
        
        Returns:
            The current frame surface, or None if no animation is active
        """
        if self.current_animation and self.current_animation in self.animations:
            return self.animations[self.current_animation].get_current_frame()
        return None

    def is_playing(self) -> bool:
        """Check if an animation is currently playing.
        
        Returns:
            True if an animation is playing, False otherwise
        """
        if self.current_animation and self.current_animation in self.animations:
            return self.animations[self.current_animation].is_playing
        return False
