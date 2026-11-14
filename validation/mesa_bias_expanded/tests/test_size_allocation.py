from copy import deepcopy
import math

import pytest

from mechanisms import size_allocation


def context(stories=None, focal="lead", budget=100, state=None):
    return {
        "stories": stories or [
            {"id": "lead", "editorial_priority": 8},
            {"id": "other", "editorial_priority": 2},
        ],
        "focal_story_id": focal,
        "total_units": budget,
        "state": {} if state is None else state,
        "peer_states": [],
        "round_index": 0,
        "agent_index": 0,
        "uniform": 0.5,
    }


def test_positive_priority_increases_focal_size_with_numeric_oracle():
    ctx = context(budget=100)
    result = size_allocation.evaluate(ctx, 0.8)
    # Equal reference is 50; full score-weighted size is 80; interpolation is 74.
    assert result["metric"] == pytest.approx(74.0)
    assert result["metric"] > size_allocation.evaluate(ctx, 0.0)["metric"]
    assert result["active"] is True


def test_equal_priority_boundary_matches_strength_zero():
    ctx = context(
        stories=[
            {"id": "lead", "editorial_priority": 4},
            {"id": "other", "editorial_priority": 4},
            {"id": "third", "editorial_priority": 4},
        ],
        focal="lead",
        budget=90,
    )
    at_boundary = size_allocation.evaluate(ctx, 0.8)
    reference = size_allocation.evaluate(ctx, 0.0)
    assert at_boundary["metric"] == pytest.approx(reference["metric"])
    assert at_boundary["metric"] == pytest.approx(30.0)
    assert at_boundary["active"] is False


def test_zero_strength_is_explicit_equal_share_reference_and_conserves_budget():
    ctx = context(
        stories=[
            {"id": "lead", "editorial_priority": 0},
            {"id": "other", "editorial_priority": 3},
            {"id": "third", "editorial_priority": 17},
        ],
        focal="lead",
        budget=90,
    )
    result = size_allocation.evaluate(ctx, 0.0)
    assert result["metric"] == pytest.approx(30.0)
    assert sum(result["state"]["last_allocations"].values()) == pytest.approx(90.0)
    assert result["active"] is False


def test_missing_priority_evidence_is_rejected_not_treated_as_zero():
    ctx = context(stories=[{"id": "lead"}, {"id": "other", "editorial_priority": 1}])
    with pytest.raises(ValueError, match="missing editorial_priority"):
        size_allocation.evaluate(ctx, 0.8)


def test_deterministic_and_nonmutating_for_context_and_nested_state():
    original = context(state={"custom": {"keep": [1]}, "allocation_history": [{"old": 1}]})
    before = deepcopy(original)
    first = size_allocation.evaluate(original, 0.8)
    second = size_allocation.evaluate(original, 0.8)
    assert original == before
    assert first == second
    first["state"]["allocation_history"][0]["old"] = 999
    assert original["state"]["allocation_history"] == [{"old": 1}]


def test_invalid_strength_and_budget_are_rejected():
    with pytest.raises(ValueError, match="strength"):
        size_allocation.evaluate(context(), float("nan"))
    bad_budget = context(budget=0)
    with pytest.raises(ValueError, match="positive"):
        size_allocation.evaluate(bad_budget, 0.5)


def test_scenarios_obey_contract_expectations():
    cases = {scenario["name"]: scenario for scenario in size_allocation.scenarios()}
    assert set(cases) >= {"positive", "boundary"}
    for name, direction in (("positive", "increase"), ("boundary", "equal")):
        scenario = cases[name]
        assert len(scenario["contexts"]) >= 1
        ctx = {**scenario["contexts"][0], "state": scenario["initial_state"]}
        measured = size_allocation.evaluate(ctx, 0.8)["metric"]
        reference = size_allocation.evaluate(ctx, 0.0)["metric"]
        if direction == "increase":
            assert measured > reference
        else:
            assert math.isclose(measured, reference, rel_tol=1e-12, abs_tol=1e-12)
