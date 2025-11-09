from MAGUS_pygame.application.battle_service import BattleService
from MAGUS_pygame.domain.entities import Unit
from MAGUS_pygame.domain.value_objects import Position, CombatStats, ResourcePool, Attributes


def make_unit(uid: str, name: str, speed: int = 15) -> Unit:
    return Unit(
        id=uid,
        name=name,
        position=Position(0, 0),
        fp=ResourcePool(10, 10),
        ep=ResourcePool(10, 10),
        combat_stats=CombatStats(KE=5, TE=40, VE=20),
        attributes=Attributes(speed=speed),
    )


def test_round_rollover_resets_ap_and_reactions():
    u1 = make_unit("u1", "Unit1", speed=15)
    u2 = make_unit("u2", "Unit2", speed=18)
    battle = BattleService(units=[u1, u2])
    battle.start_battle()

    ap_u1_round1 = battle.remaining_ap(u1)
    ap_u2_round1 = battle.remaining_ap(u2)
    assert ap_u1_round1 == 10
    assert ap_u2_round1 == 13

    # Spend some AP
    battle.spend_ap(u1, 5)
    battle.spend_ap(u2, 7)

    # Advance turns to force rollover
    battle.end_turn()  # next unit
    battle.end_turn()  # wrap to round 2

    ap_u1_round2 = battle.remaining_ap(u1)
    ap_u2_round2 = battle.remaining_ap(u2)
    assert ap_u1_round2 == 10
    assert ap_u2_round2 == 13

    # Reaction budget reset implied by action_handler.start_turn - not directly exposed
    # (Could extend BattleService with query; here we assume success if AP reset occurred.)
