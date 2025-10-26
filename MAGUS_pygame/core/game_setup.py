"""
Game initialization and setup utilities.
"""
import os
from typing import Tuple, Optional
import pygame
from config import WIDTH, HEIGHT
from rendering.sprite_manager import load_and_mask_sprite
from core.unit_manager import Unit
from systems.character_loader import load_character_json
from systems.equipment_loader import find_weapon_by_id, get_weapon_combat_stats


def setup_game() -> Tuple[Unit, Unit, Optional[pygame.Surface]]:
    """
    Initialize game resources: load sprites, create units, load character data.
    
    Returns:
        Tuple of (warrior, goblin, background_image)
    """
    
    # Build a robust relative path to the sprites folder
    # __file__ is in core/, so go up one level to MAGUS_pygame/, then into sprites/
    magus_pygame_dir = os.path.dirname(os.path.dirname(__file__))
    sprites_dir = os.path.join(magus_pygame_dir, "sprites")
    
    # Load sprites
    warrior_sprite = load_and_mask_sprite(os.path.join(sprites_dir, "warrior.png"))
    goblin_sprite = load_and_mask_sprite(os.path.join(sprites_dir, "goblin.png"))
    
    # Create units with default positions
    warrior = Unit(3, 3, warrior_sprite)
    goblin = Unit(6, 3, goblin_sprite)
    
    # Try to attach demo combat stats from repo characters/*.json
    try:
        warrior_json = load_character_json("Teszt.json")
        warrior.name = warrior_json.get("Név", "Warrior")
        warrior.set_combat(warrior_json.get("Harci értékek", {}))
        warrior.set_attributes(warrior_json.get("Tulajdonságok", {}))
        
        # Load equipped weapon
        equipment = warrior_json.get("Felszerelés", [])
        if equipment and len(equipment) > 0:
            weapon_id = equipment[0]  # Use first item as main weapon
            weapon_data = find_weapon_by_id(weapon_id)
            if weapon_data:
                weapon_stats = get_weapon_combat_stats(weapon_data)
                warrior.set_weapon(weapon_stats)
            else:
                pass
    except Exception:
        pass
    
    try:
        goblin_json = load_character_json("Teszt_Goblin.json")
        goblin.name = goblin_json.get("Név", "Goblin")
        goblin.set_combat(goblin_json.get("Harci értékek", {}))
        goblin.set_attributes(goblin_json.get("Tulajdonságok", {}))
        
        # Load equipped weapon
        equipment = goblin_json.get("Felszerelés", [])
        if equipment and len(equipment) > 0:
            weapon_id = equipment[0]  # Use first item as main weapon
            weapon_data = find_weapon_by_id(weapon_id)
            if weapon_data:
                weapon_stats = get_weapon_combat_stats(weapon_data)
                goblin.set_weapon(weapon_stats)
            else:
                pass
    except Exception:
        pass
    
    # Load background image and scale to window size
    background = None
    try:
        bg_img = pygame.image.load(os.path.join(sprites_dir, "grass_bg.jpg")).convert()
        background = pygame.transform.smoothscale(bg_img, (WIDTH, HEIGHT))
    except Exception:
        pass
    
    return warrior, goblin, background
