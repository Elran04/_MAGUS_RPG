#!/usr/bin/env python3
"""Debug script to test unit popup item name lookup."""

import sys
sys.path.insert(0, '/d:/_Projekt/_MAGUS_RPG')

from MAGUS_pygame.data.equipment_repository import EquipmentRepository

# Initialize repository
repo = EquipmentRepository()

# Test weapon lookups
test_weapons = ["sword", "shield", "bow", "longsword"]

for weapon_id in test_weapons:
    weapon_data = repo.find_weapon_by_id(weapon_id)
    if weapon_data:
        print(f"✓ {weapon_id}: {weapon_data.get('name', 'N/A')}")
    else:
        print(f"✗ {weapon_id}: Not found")

print("\nAvailable weapons (first 10):")
weapons = repo.load_weapons()
for i, weapon in enumerate(weapons[:10]):
    print(f"  - {weapon.get('id', 'N/A')}: {weapon.get('name', 'N/A')}")
