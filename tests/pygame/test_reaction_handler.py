
from application.reaction_handler import ReactionBudget, ReactionHandler
from domain.entities import Unit
from domain.mechanics import ReactionResult
from domain.value_objects import Attributes, CombatStats, Position, ResourcePool


def make_unit(uid: str, name: str) -> Unit:
    return Unit(
        id=uid,
        name=name,
        position=Position(0, 0),
        fp=ResourcePool(10, 10),
        ep=ResourcePool(10, 10),
        combat_stats=CombatStats(TE=40, VE=30),
        attributes=Attributes(speed=15),
    )


class TestReactionBudget:
    def test_reset_and_consume(self):
        u1, u2 = make_unit("u1", "Unit1"), make_unit("u2", "Unit2")
        budget = ReactionBudget(max_reactions_per_turn=2)

        budget.reset_for_units([u1, u2])
        assert budget.remaining == {"u1": 2, "u2": 2}

        assert budget.consume(u1) is True
        assert budget.remaining["u1"] == 1
        assert budget.consume(u1) is True
        assert budget.remaining["u1"] == 0

        assert budget.consume(u1) is False  # exhausted
        assert budget.consume(u2) is True  # independent counter


def test_handle_opportunity_no_intersection(monkeypatch):
    """When movement path does not intersect reactor's zone, no trigger occurs."""
    handler = ReactionHandler()
    mover = make_unit("m", "Mover")  # at Position(0, 0)
    reactor = make_unit("r", "Reactor")  # at Position(0, 0), facing 0 (NE)
    
    # Reactor's zone: facing 0 means NE direction (1, -1)
    # Mover path (0,0) -> (1,0) does NOT intersect zone (1,-1)
    # should_trigger will be called but return False

    called = {"trigger": 0}

    class FakeReaction:
        def should_trigger(self, **_):
            called["trigger"] += 1
            return False, "Path does not intersect"  # Return False since path doesn't intersect zone

        def execute(self, **_):  # pragma: no cover - should not run
            raise AssertionError("execute should not be called")

    monkeypatch.setattr("application.reaction_handler.OpportunityAttackReaction", FakeReaction)

    results = handler.handle_opportunity_attacks(
        movers_path=[(0, 0), (1, 0)],
        intersects_zoc=False,
        intersection_index=None,
        mover=mover,
        potential_reactors=[reactor],
    )

    assert results == []
    assert called["trigger"] == 1  # should_trigger IS called even though path doesn't intersect


def test_handle_opportunity_applies_and_consumes(monkeypatch):
    handler = ReactionHandler()
    mover = make_unit("m", "Mover")
    reactor = make_unit("r", "Reactor")  # at Position(0, 0), facing 0, zone at (1, -1)

    captured = {}

    class FakeReaction:
        def should_trigger(self, **context):
            captured["trigger_context"] = context
            return True, ""

        def execute(self, **context):
            captured["execute_context"] = context
            return ReactionResult(
                success=True,
                data={"attack_result": "ATTACK"},
                interrupts_movement=False,
                interrupt_index=None,
                message="ok",
            )

    applied = []

    def fake_apply(result, mover_arg):
        applied.append((result, mover_arg.id))

    monkeypatch.setattr("application.reaction_handler.OpportunityAttackReaction", FakeReaction)
    monkeypatch.setattr("application.reaction_handler.apply_attack_result", fake_apply)

    # Use path that intersects reactor's zone
    results = handler.handle_opportunity_attacks(
        movers_path=[(0, 0), (1, -1)],  # Changed to pass through zone (1, -1)
        intersects_zoc=True,
        intersection_index=1,
        mover=mover,
        potential_reactors=[reactor],
        rng_overrides={"attack_roll": 42, "base_damage_roll": 7},
        mover_shield_ve=3,
        mover_dodge_mod=5,
    )

    assert len(results) == 1
    assert applied == [("ATTACK", "m")]
    # Budget should decrement for reactor
    assert handler.budget.remaining[reactor.id] == 0

    # Verify overrides and arguments forwarded to execute
    exec_ctx = captured["execute_context"]
    assert exec_ctx["attack_roll"] == 42
    assert exec_ctx["base_damage_roll"] == 7
    assert exec_ctx["shield_ve"] == 3
    assert exec_ctx["dodge_modifier"] == 5


def test_handle_opportunity_stops_on_interrupt(monkeypatch):
    budget = ReactionBudget()
    budget.remaining = {"r1": 1, "r2": 1}
    handler = ReactionHandler(budget=budget)

    mover = make_unit("m", "Mover")
    r1 = make_unit("r1", "Reactor1")  # at Position(0, 0), zone at (1, -1)
    r2 = make_unit("r2", "Reactor2")  # at Position(0, 0), zone at (1, -1)

    calls = []

    class InterruptingReaction:
        def should_trigger(self, **context):
            calls.append(("should", context["attacker"].id))
            return True, ""

        def execute(self, **context):
            calls.append(("execute", context["attacker"].id))
            return ReactionResult(
                success=True,
                interrupts_movement=True,
                interrupt_index=context["intersection_index"],
            )

    monkeypatch.setattr(
        "application.reaction_handler.OpportunityAttackReaction", InterruptingReaction
    )

    # Use path that intersects both reactors' zones
    results = handler.handle_opportunity_attacks(
        movers_path=[(0, 0), (1, -1)],  # Changed to pass through zone (1, -1)
        intersects_zoc=True,
        intersection_index=1,
        mover=mover,
        potential_reactors=[r1, r2],
    )

    assert len(results) == 1
    assert calls == [("should", "r1"), ("execute", "r1")]
    # Second reactor never evaluated due to movement interrupt
    assert budget.remaining["r1"] == 0
    assert budget.remaining["r2"] == 1
