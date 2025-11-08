"""
Hex Grid Utilities - Coordinate conversion and distance calculation.
"""

import math
from typing import Tuple

from domain.value_objects import Position


# Hex grid constants (will be moved to config if needed)
HEX_SIZE = 40
HEX_OFFSET_X = 400
HEX_OFFSET_Y = 300


def hex_to_pixel(position: Position) -> Tuple[int, int]:
    """
    Convert hex cube coordinates to pixel coordinates (pointy-top hexagons).
    
    Args:
        position: Hex position
        
    Returns:
        (x, y) pixel coordinates
    """
    q, r = position.q, position.r
    x = HEX_SIZE * (3/2 * q) + HEX_OFFSET_X
    y = HEX_SIZE * (math.sqrt(3)/2 * q + math.sqrt(3) * r) + HEX_OFFSET_Y
    return int(x), int(y)


def pixel_to_hex(x: int, y: int) -> Position:
    """
    Convert pixel coordinates to hex cube coordinates.
    
    Args:
        x: Pixel x coordinate
        y: Pixel y coordinate
        
    Returns:
        Position in hex coordinates
    """
    x = (x - HEX_OFFSET_X) / HEX_SIZE
    y = (y - HEX_OFFSET_Y) / HEX_SIZE
    
    q = (2/3) * x
    r = (-1/3 * x + math.sqrt(3)/3 * y)
    
    return hex_round(q, r)


def hex_round(q: float, r: float) -> Position:
    """
    Round fractional hex coordinates to nearest hex.
    
    Args:
        q: Fractional q coordinate
        r: Fractional r coordinate
        
    Returns:
        Rounded Position
    """
    s = -q - r
    
    q_round = round(q)
    r_round = round(r)
    s_round = round(s)
    
    q_diff = abs(q_round - q)
    r_diff = abs(r_round - r)
    s_diff = abs(s_round - s)
    
    if q_diff > r_diff and q_diff > s_diff:
        q_round = -r_round - s_round
    elif r_diff > s_diff:
        r_round = -q_round - s_round
    
    return Position(q=q_round, r=r_round)


def get_hex_neighbors(position: Position) -> list[Position]:
    """
    Get all 6 adjacent hex positions.
    
    Args:
        position: Center hex position
        
    Returns:
        List of 6 neighboring positions
    """
    # Hex cube coordinate directions (pointy-top)
    directions = [
        (1, 0),   # East
        (1, -1),  # North-East
        (0, -1),  # North-West
        (-1, 0),  # West
        (-1, 1),  # South-West
        (0, 1),   # South-East
    ]
    
    return [
        Position(q=position.q + dq, r=position.r + dr)
        for dq, dr in directions
    ]


def get_hex_range(center: Position, radius: int) -> list[Position]:
    """
    Get all hexes within a given range.
    
    Args:
        center: Center position
        radius: Maximum distance
        
    Returns:
        List of positions within range (including center)
    """
    results = []
    for q in range(-radius, radius + 1):
        r1 = max(-radius, -q - radius)
        r2 = min(radius, -q + radius)
        for r in range(r1, r2 + 1):
            pos = Position(q=center.q + q, r=center.r + r)
            results.append(pos)
    return results


def line_to_hex(start: Position, end: Position) -> list[Position]:
    """
    Get all hexes along a line between two positions.
    
    Args:
        start: Starting position
        end: Ending position
        
    Returns:
        List of positions forming the line
    """
    distance = start.distance_to(end)
    if distance == 0:
        return [start]
    
    results = []
    for i in range(distance + 1):
        t = i / distance
        q = start.q + (end.q - start.q) * t
        r = start.r + (end.r - start.r) * t
        results.append(hex_round(q, r))
    
    return results
