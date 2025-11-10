"""Test armor validation integration.

Quick test to verify armor conflict detection works correctly.
"""

from application.equipment_validation_service import EquipmentValidationService
from infrastructure.repositories import EquipmentRepository


def test_armor_validation():
    """Test armor conflict detection."""
    print("Testing Armor Validation System")
    print("=" * 60)
    
    # Initialize repository and service
    repo = EquipmentRepository()
    service = EquipmentValidationService(repo)
    
    # Test 1: No conflicts (different layers)
    print("\nTest 1: No conflicts (different layers)")
    armor_ids_1 = ["full_plate", "padded_armor"]  # Layer 1 and 3
    is_valid, warnings, conflicts = service.validate_armor_compatibility(armor_ids_1)
    print(f"  Valid: {is_valid}")
    print(f"  Warnings: {warnings}")
    print(f"  Conflicts: {conflicts}")
    
    # Test 2: Conflict on same layer
    print("\nTest 2: Conflict on same layer (two helmets)")
    # Note: Need actual armor IDs from your data
    armor_ids_2 = ["plated_gloves", "plated_gloves"]  # Same item twice
    is_valid, warnings, conflicts = service.validate_armor_compatibility(armor_ids_2)
    print(f"  Valid: {is_valid}")
    print(f"  Warnings: {warnings}")
    print(f"  Conflicts: {conflicts}")
    
    # Test 3: Empty list
    print("\nTest 3: Empty armor list")
    armor_ids_3 = []
    is_valid, warnings, conflicts = service.validate_armor_compatibility(armor_ids_3)
    print(f"  Valid: {is_valid}")
    print(f"  Warnings: {warnings}")
    print(f"  Conflicts: {conflicts}")
    
    # Test 4: Single armor piece
    print("\nTest 4: Single armor piece")
    armor_ids_4 = ["full_plate"]
    is_valid, warnings, conflicts = service.validate_armor_compatibility(armor_ids_4)
    print(f"  Valid: {is_valid}")
    print(f"  Warnings: {warnings}")
    print(f"  Conflicts: {conflicts}")
    
    print("\n" + "=" * 60)
    print("Testing complete!")


if __name__ == "__main__":
    test_armor_validation()
