from copy import deepcopy

import pytest

from mechanisms import planning_fallacy as plugin


def _run(contexts, strength):
    state = {"history": []}
    results = []
    for round_index, task in enumerate(contexts):
        context = deepcopy(task)
        context.update({
            "state": deepcopy(state),
            "peer_states": [],
            "round_index": round_index,
            "agent_index": 0,
            "uniform": 0.5,
        })
        result = plugin.evaluate(context, strength)
        results.append(result)
        state = result["state"]
    return results


def _scenario(name):
    return next(s for s in plugin.scenarios() if s["name"] == name)


def test_numeric_oracle_discount_of_same_class_overrun():
    scenario = _scenario("positive")
    results = _run(scenario["contexts"], 0.8)
    # Prior ratio=12/8=1.5; forecast=20*(1+(1-.8)*(.5))=22.
    assert results[-1]["state"]["last_forecast_hours"] == pytest.approx(22)
    assert results[-1]["metric"] == pytest.approx(8)
    assert results[-1]["active"] is True


def test_positive_scenario_underestimation_increases_at_strength_point_eight():
    scenario = _scenario("positive")
    reference = _run(scenario["contexts"], 0.0)[-1]["metric"]
    intervention = _run(scenario["contexts"], 0.8)[-1]["metric"]
    assert intervention > reference


def test_boundary_without_comparable_prior_evidence_matches_reference():
    scenario = _scenario("boundary")
    reference = _run(scenario["contexts"], 0.0)[-1]
    intervention = _run(scenario["contexts"], 0.8)[-1]
    assert reference["metric"] == intervention["metric"] == 10
    assert reference["state"]["last_forecast_hours"] == intervention["state"]["last_forecast_hours"] == 20
    assert intervention["active"] is False


def test_zero_strength_uses_full_reference_ratio_correction():
    scenario = _scenario("positive")
    result = _run(scenario["contexts"], 0.0)[-1]
    assert result["state"]["last_forecast_hours"] == pytest.approx(30)
    assert result["metric"] == 0
    assert result["active"] is True


def test_missing_or_invalid_phase_inputs_are_rejected():
    context = {
        "task_class": "build",
        "planned_hours": 10,
        "actual_hours": 15,
        "state": {"history": []},
    }
    for missing in ("task_class", "planned_hours", "actual_hours"):
        invalid = deepcopy(context)
        del invalid[missing]
        with pytest.raises(ValueError):
            plugin.evaluate(invalid, 0.5)
    for key, value in (("task_class", "  "), ("planned_hours", 0), ("actual_hours", float("nan"))):
        invalid = deepcopy(context)
        invalid[key] = value
        with pytest.raises(ValueError):
            plugin.evaluate(invalid, 0.5)


def test_invalid_strength_and_malformed_history_are_rejected():
    context = {"task_class": "build", "planned_hours": 10, "actual_hours": 15, "state": {"history": []}}
    for strength in (-0.01, 1.01, float("inf"), True):
        with pytest.raises(ValueError):
            plugin.evaluate(context, strength)
    bad_history = deepcopy(context)
    bad_history["state"] = {"history": [{"task_class": "build", "planned_hours": 0, "actual_hours": 2}]}
    with pytest.raises(ValueError):
        plugin.evaluate(bad_history, 0.5)


def test_deterministic_and_nonmutating_with_nested_state():
    context = {
        "task_class": "build",
        "planned_hours": 20,
        "actual_hours": 30,
        "state": {"history": [{"task_class": "build", "planned_hours": 8, "actual_hours": 12}]},
        "peer_states": [{"nested": [1, 2]}],
        "round_index": 1,
        "agent_index": 0,
        "uniform": 0.37,
    }
    before = deepcopy(context)
    first = plugin.evaluate(context, 0.8)
    second = plugin.evaluate(context, 0.8)
    assert context == before
    assert first == second
