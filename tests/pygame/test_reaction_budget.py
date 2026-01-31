from MAGUS_pygame.application.reaction_handler import ReactionHandler
from MAGUS_pygame.domain.entities import Unit
from MAGUS_pygame.domain.value_objects import Attributes, CombatStats, Position, ResourcePool


def make_unit(uid: str, name: str) -> Unit:
    return Unit(
        id=uid,
        name=name,
        position=Position(0, 0),
        fp=ResourcePool(10, 10),
        ep=ResourcePool(10, 10),
        combat_stats=CombatStats(TE=50, VE=10),
        attributes=Attributes(),
    )


def test_reaction_budget_allows_only_one_per_turn():
    handler = ReactionHandler()
    reactor = make_unit("r1", "Reactor")  # at Position(0, 0), facing 0
    mover = make_unit("m1", "Mover")
    handler.start_turn([reactor, mover])

    # Reactor facing 0 has zone at NE direction: (1, -1)
    # Path must pass through (1, -1) to trigger OA
    path = [(0, 0), (1, -1)]  # Changed from [(0, 0), (1, 0)] to intersect zone
    intersects = True
    ix = 1

    # First call should produce a reaction
    results1 = handler.handle_opportunity_attacks(
        movers_path=path,
        intersects_zoc=intersects,
        intersection_index=ix,
        mover=mover,
        potential_reactors=[reactor],
        mover_shield_ve=0,
        mover_dodge_mod=0,
        rng_overrides={"attack_roll": 80, "base_damage_roll": 1},
    )
    assert len(results1) == 1

    # Second call in same turn should be blocked by budget
    results2 = handler.handle_opportunity_attacks(
        movers_path=path,
        intersects_zoc=intersects,
        intersection_index=ix,
        mover=mover,
        potential_reactors=[reactor],
        mover_shield_ve=0,
        mover_dodge_mod=0,
        rng_overrides={"attack_roll": 80, "base_damage_roll": 1},
    )
    assert len(results2) == 0
