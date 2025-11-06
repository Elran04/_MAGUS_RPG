"""
Visual effects system for combat animations and particle effects in MAGUS Pygame.
"""

from typing import Tuple, Optional
import pygame
import random


class Particle:
    """Represents a single particle in a particle effect."""

    def __init__(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        color: Tuple[int, int, int],
        lifetime: int,
        size: int = 2
    ) -> None:
        """Initialize a particle.
        
        Args:
            x: Initial x position
            y: Initial y position
            vx: X velocity
            vy: Y velocity
            color: RGB color tuple
            lifetime: Particle lifetime in milliseconds
            size: Particle size in pixels
        """
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = size
        self.alpha = 255

    def update(self, dt: int) -> bool:
        """Update particle position and lifetime.
        
        Args:
            dt: Delta time in milliseconds
            
        Returns:
            True if particle is still alive, False otherwise
        """
        self.x += self.vx * (dt / 1000.0)
        self.y += self.vy * (dt / 1000.0)
        self.lifetime -= dt
        
        # Fade out as lifetime decreases
        self.alpha = int(255 * (self.lifetime / self.max_lifetime))
        
        return self.lifetime > 0

    def draw(self, surface: pygame.Surface, camera_offset: Tuple[int, int] = (0, 0)) -> None:
        """Draw the particle.
        
        Args:
            surface: Surface to draw on
            camera_offset: Camera offset (x, y)
        """
        if self.alpha <= 0:
            return
            
        screen_x = int(self.x - camera_offset[0])
        screen_y = int(self.y - camera_offset[1])
        
        # Create surface with alpha
        particle_surface = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        color_with_alpha = (*self.color, self.alpha)
        pygame.draw.circle(particle_surface, color_with_alpha, (self.size, self.size), self.size)
        
        surface.blit(particle_surface, (screen_x - self.size, screen_y - self.size))


class ParticleEffect:
    """Manages a particle effect system."""

    def __init__(self) -> None:
        """Initialize the particle effect system."""
        self.particles: list[Particle] = []

    def emit_burst(
        self,
        x: float,
        y: float,
        count: int,
        color: Tuple[int, int, int],
        speed_range: Tuple[float, float] = (50, 150),
        lifetime: int = 1000
    ) -> None:
        """Emit a burst of particles.
        
        Args:
            x: Emission x position
            y: Emission y position
            count: Number of particles to emit
            color: RGB color tuple
            speed_range: Min/max speed for particles
            lifetime: Particle lifetime in milliseconds
        """
        for _ in range(count):
            angle = random.uniform(0, 360)
            speed = random.uniform(*speed_range)
            vx = speed * pygame.math.Vector2(1, 0).rotate(angle).x
            vy = speed * pygame.math.Vector2(1, 0).rotate(angle).y
            
            particle = Particle(x, y, vx, vy, color, lifetime)
            self.particles.append(particle)

    def emit_hit_effect(self, x: float, y: float, color: Tuple[int, int, int] = (255, 0, 0)) -> None:
        """Emit a hit effect at the specified position.
        
        Args:
            x: Hit x position
            y: Hit y position
            color: Effect color (default red)
        """
        self.emit_burst(x, y, count=15, color=color, speed_range=(30, 100), lifetime=500)

    def update(self, dt: int) -> None:
        """Update all particles.
        
        Args:
            dt: Delta time in milliseconds
        """
        self.particles = [p for p in self.particles if p.update(dt)]

    def draw(self, surface: pygame.Surface, camera_offset: Tuple[int, int] = (0, 0)) -> None:
        """Draw all particles.
        
        Args:
            surface: Surface to draw on
            camera_offset: Camera offset (x, y)
        """
        for particle in self.particles:
            particle.draw(surface, camera_offset)


class VisualEffect:
    """Base class for visual effects."""

    def __init__(self, x: float, y: float, duration: int) -> None:
        """Initialize a visual effect.
        
        Args:
            x: Effect x position
            y: Effect y position
            duration: Effect duration in milliseconds
        """
        self.x = x
        self.y = y
        self.duration = duration
        self.elapsed = 0
        self.is_finished = False

    def update(self, dt: int) -> None:
        """Update the effect.
        
        Args:
            dt: Delta time in milliseconds
        """
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.is_finished = True

    def draw(self, surface: pygame.Surface, camera_offset: Tuple[int, int] = (0, 0)) -> None:
        """Draw the effect.
        
        Args:
            surface: Surface to draw on
            camera_offset: Camera offset (x, y)
        """
        pass  # Override in subclasses


class EffectsManager:
    """Manages all visual effects in the game."""

    def __init__(self) -> None:
        """Initialize the effects manager."""
        self.effects: list[VisualEffect] = []
        self.particle_system = ParticleEffect()

    def add_effect(self, effect: VisualEffect) -> None:
        """Add a visual effect.
        
        Args:
            effect: The effect to add
        """
        self.effects.append(effect)

    def update(self, dt: int) -> None:
        """Update all effects.
        
        Args:
            dt: Delta time in milliseconds
        """
        self.particle_system.update(dt)
        self.effects = [e for e in self.effects if not e.is_finished]
        for effect in self.effects:
            effect.update(dt)

    def draw(self, surface: pygame.Surface, camera_offset: Tuple[int, int] = (0, 0)) -> None:
        """Draw all effects.
        
        Args:
            surface: Surface to draw on
            camera_offset: Camera offset (x, y)
        """
        for effect in self.effects:
            effect.draw(surface, camera_offset)
        self.particle_system.draw(surface, camera_offset)
