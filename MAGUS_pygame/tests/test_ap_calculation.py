from MAGUS_pygame.application.battle_service import compute_unit_ap
from MAGUS_pygame.domain.entities import Unit
from MAGUS_pygame.domain.value_objects import Position, CombatStats, ResourcePool, Attributes


def make_unit_with_speed(speed: int) -> Unit:
    return Unit(
        id="u1",
        name="Test",
        position=Position(0, 0),
        fp=ResourcePool(10, 10),
        ep=ResourcePool(10, 10),
        combat_stats=CombatStats(),
        attributes=Attributes(speed=speed),
    )


def test_ap_at_speed_15_is_10():
    u = make_unit_with_speed(15)
    assert compute_unit_ap(u) == 10


def test_ap_at_speed_18_is_13():
    u = make_unit_with_speed(18)
    assert compute_unit_ap(u) == 13
