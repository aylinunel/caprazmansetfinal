import copy
import math

import pytest

from mechanisms import gamblers_fallacy as gf


def run_sequence(contexts, strength, initial_state=None):
    state = copy.deepcopy(initial_state or {})
    results = []
    for round_index, task_context in enumerate(contexts):
        context = copy.deepcopy(task_context)
        context.update(
            state=state,
            peer_states=[],
            round_index=round_index,
            agent_index=0,
            uniform=0.5,
        )
        result = gf.evaluate(context, strength)
        state = result["state"]
        results.append(result)
    return results


def fair_streak(independent=True, length=5):
    return [
        {"outcome": 1, "base_probability_one": 0.5, "independent": independent}
        for _ in range(length)
    ]


def test_positive_streak_shifts_fair_coin_forecast_to_reversal():
    results = run_sequence(fair_streak(), 0.8)
    # Four prior 1s produce p(1)=0.5 - .8*.12*4=.116, below the .5 choice threshold.
    assert results[-1]["metric"] == 0.0
    assert results[-1]["active"] is True
    assert "adjusted p1=0.116" in results[-1]["trace"][2]


def test_boundary_nonindependent_sequence_matches_reference_at_strength_point_eight():
    results = run_sequence(fair_streak(independent=False), 0.8)
    baseline = run_sequence(fair_streak(independent=False), 0.0)
    assert results[-1]["metric"] == baseline[-1]["metric"] == 1.0
    assert results[-1]["active"] is False


def test_strength_zero_is_explicit_base_rate_reference_policy():
    contexts = [
        {"outcome": 0, "base_probability_one": 0.7, "independent": True},
        {"outcome": 1, "base_probability_one": 0.7, "independent": True},
    ]
    results = run_sequence(contexts, 0.0)
    assert [item["metric"] for item in results] == [1.0, 1.0]
    assert all(item["active"] is False for item in results)


def test_requires_all_evidence_inputs_and_validates_ranges():
    with pytest.raises(ValueError, match="missing required input: independent"):
        gf.evaluate({"outcome": 1, "base_probability_one": 0.5}, 0.8)
    with pytest.raises(ValueError, match="base_probability_one"):
        gf.evaluate(
            {"outcome": 1, "base_probability_one": float("nan"), "independent": True},
            0.8,
        )
    with pytest.raises(ValueError, match="strength"):
        gf.evaluate(
            {"outcome": 1, "base_probability_one": 0.5, "independent": True},
            1.01,
        )


def test_stable_probability_is_required_after_history():
    first = gf.evaluate(
        {"outcome": 1, "base_probability_one": 0.5, "independent": True, "state": {}}, 0.8
    )
    with pytest.raises(ValueError, match="remain stable"):
        gf.evaluate(
            {
                "outcome": 1,
                "base_probability_one": 0.6,
                "independent": True,
                "state": first["state"],
            },
            0.8,
        )


def test_deterministic_and_nonmutating_for_context_and_nested_state():
    state = {"observed_outcomes": [1, 1, 1, 1], "base_probability_one": 0.5, "last_forecast": 1}
    context = {
        "outcome": 0,
        "base_probability_one": 0.5,
        "independent": True,
        "state": state,
        "peer_states": [{"nested": [3]}],
        "round_index": 4,
        "agent_index": 0,
        "uniform": 0.25,
    }
    original = copy.deepcopy(context)
    one = gf.evaluate(context, 0.8)
    two = gf.evaluate(context, 0.8)
    assert context == original
    assert one == two
    assert math.isfinite(one["metric"])
    assert one["state"]["observed_outcomes"] == [1, 1, 1, 1, 0]


def test_scenarios_provide_multiround_positive_and_boundary_sequences():
    scenarios = {item["name"]: item for item in gf.scenarios()}
    assert set(("positive", "boundary")).issubset(scenarios)
    assert len(scenarios["positive"]["contexts"]) >= 2
    assert run_sequence(scenarios["positive"]["contexts"], 0.8)[-1]["metric"] != run_sequence(
        scenarios["positive"]["contexts"], 0.0
    )[-1]["metric"]
