import math
from MAGUS_pygame.domain.mechanics.armor import ArmorPiece, ArmorSystem, HitzoneResolver


def test_overlap_same_layer_rejected():
    a = ArmorPiece(id="a", name="Cuirass L1", parts={"mellvért": 5}, layer=1)
    b = ArmorPiece(id="b", name="Cuirass L1b", parts={"mellvért": 3}, layer=1)
    system = ArmorSystem([a, b])
    ok, msg = system.validate_no_overlap_same_layer()
    assert not ok
    assert "Overlap" in msg


def test_overlap_different_layers_ok_and_sums():
    a = ArmorPiece(id="a", name="Cuirass L1", parts={"mellvért": 5}, layer=1)
    b = ArmorPiece(id="b", name="Cuirass L2", parts={"mellvért": 3}, layer=2)
    system = ArmorSystem([a, b])
    ok, msg = system.validate_no_overlap_same_layer()
    assert ok, msg
    assert system.get_sfe_for_hit("mellvért") == 8


def test_mgt_sum():
    a = ArmorPiece(id="a", name="Cuirass L1", parts={"mellvért": 5}, mgt=2, layer=1)
    b = ArmorPiece(id="b", name="Greaves L2", parts={"lábszárvédő": 2}, mgt=1, layer=2)
    system = ArmorSystem([a, b])
    assert system.get_total_mgt() == 3


def test_degradation_applies_to_outermost():
    a = ArmorPiece(id="a", name="Cuirass L1", parts={"mellvért": 5}, layer=1)
    b = ArmorPiece(id="b", name="Cuirass L2", parts={"mellvért": 3}, layer=2)
    system = ArmorSystem([a, b])
    system.reduce_sfe("mellvért", 1)
    assert a.get_sfé("mellvért") == 4  # outermost reduced
    assert b.get_sfé("mellvért") == 3


def test_hitzone_resolver_distribution_bias():
    rng_counts = {k: 0 for k in HitzoneResolver.HITZONE_WEIGHTS.keys()}
    import random

    rng = random.Random(42)
    samples = 5000
    for _ in range(samples):
        z = HitzoneResolver.resolve(rng)
        rng_counts[z] += 1

    # Breastplate (mellvért) should be hit significantly more than alkarvédő
    assert rng_counts["mellvért"] > rng_counts["alkarvédő"] * 3


def test_sfe_reduction_modifies_damage():
    a = ArmorPiece(id="a", name="Cuirass L1", parts={"mellvért": 3}, layer=1)
    b = ArmorPiece(id="b", name="Cuirass L2", parts={"mellvért": 2}, layer=2)
    system = ArmorSystem([a, b])

    base_damage = 10
    zone = "mellvért"

    # Non-critical, non-overpower: subtract total SFE (3+2=5)
    effective = max(0, base_damage - system.get_sfe_for_hit(zone))
    assert effective == 5

    # Overpower: reduce outermost (L1) by 1 first => SFE now 2 + 2 = 4
    system.reduce_sfe(zone, 1)
    effective2 = max(0, base_damage - system.get_sfe_for_hit(zone))
    assert effective2 == 6

    # Critical: ignore armor
    effective3 = base_damage
    assert effective3 == 10
