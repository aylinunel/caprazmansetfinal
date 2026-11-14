from copy import deepcopy

import pytest

from mechanisms import empathy_gap


def _run(contexts, strength, initial_state=None):
    state = deepcopy(initial_state or {})
    outputs = []
    for round_index, task_context in enumerate(contexts):
        context = deepcopy(task_context)
        context.update({
            "state": state,
            "peer_states": [],
            "round_index": round_index,
            "agent_index": 0,
            "uniform": 0.5,
        })
        result = empathy_gap.evaluate(context, strength)
        outputs.append(result)
        state = result["state"]
    return outputs


def test_positive_state_projection_increases_forecast_error_with_numeric_oracle():
    case = empathy_gap.scenarios()[0]
    baseline = _run(case["contexts"], 0.0, case["initial_state"])[-1]
    projected = _run(case["contexts"], 0.8, case["initial_state"])[-1]

    # At .8, projected delta = .2*(-1) + .8*(2) = 1.4, so A is forecast;
    # the target-state reference chooses B. This is a task-specific oracle.
    assert baseline["metric"] == 0.0
    assert projected["metric"] == 1.0
    assert projected["state"]["last_forecast_choice"] == "A"
    assert projected["state"]["last_reference_choice"] == "B"
    assert projected["active"] is True


def test_boundary_identical_states_equals_strength_zero_reference():
    case = empathy_gap.scenarios()[1]
    baseline = _run(case["contexts"], 0.0, case["initial_state"])[-1]
    at_strength = _run(case["contexts"], 0.8, case["initial_state"])[-1]

    assert at_strength["metric"] == baseline["metric"] == 0.0
    assert at_strength["state"]["last_forecast_choice"] == "A"
    assert at_strength["active"] is False


def test_zero_strength_is_target_state_conditioned_reference_policy():
    context = {
        "forecaster_state": "hungry",
        "target_state": "sated",
        "utility_delta_by_state": {"hungry": 4.0, "sated": -0.25},
        "state": {},
    }
    result = empathy_gap.evaluate(context, 0.0)
    assert result["state"]["last_forecast_choice"] == "B"
    assert result["metric"] == 0.0
    assert result["active"] is False
    assert "Reference choice uses target state" in result["trace"][0]


def test_missing_or_unavailable_state_evidence_is_rejected():
    with pytest.raises(ValueError, match="missing required evidence"):
        empathy_gap.evaluate({"forecaster_state": "hungry", "target_state": "sated"}, 0.8)
    with pytest.raises(ValueError, match="include both supplied states"):
        empathy_gap.evaluate({
            "forecaster_state": "hungry",
            "target_state": "sated",
            "utility_delta_by_state": {"hungry": 1.0},
        }, 0.8)


def test_invalid_strength_and_nonfinite_utility_are_rejected():
    base = {
        "forecaster_state": "hungry",
        "target_state": "sated",
        "utility_delta_by_state": {"hungry": 1.0, "sated": -1.0},
    }
    for invalid in (-0.01, 1.01, float("nan"), float("inf")):
        with pytest.raises(ValueError, match="strength"):
            empathy_gap.evaluate(base, invalid)
    bad_utility = {**base, "utility_delta_by_state": {"hungry": 1.0, "sated": float("nan")}}
    with pytest.raises(ValueError, match="finite real number"):
        empathy_gap.evaluate(bad_utility, 0.8)


def test_determinism_and_nonmutation_with_nested_prior_state():
    context = {
        "forecaster_state": "hungry",
        "target_state": "sated",
        "utility_delta_by_state": {"hungry": 2.0, "sated": -1.0},
        "state": {"steps": 3, "cumulative_error": 1.0, "custom": {"history": ["kept"]}},
        "peer_states": [{"nested": [1, 2]}],
        "round_index": 4,
        "agent_index": 1,
        "uniform": 0.2,
    }
    before = deepcopy(context)
    first = empathy_gap.evaluate(context, 0.8)
    second = empathy_gap.evaluate(context, 0.8)

    assert context == before
    assert first == second
    assert first["state"]["steps"] == 4
    assert first["state"]["cumulative_error"] == 2.0
    assert first["state"]["custom"] == {"history": ["kept"]}
    assert len(first["trace"]) == 3


def test_chronological_calls_accumulate_real_decision_errors():
    contexts = [
        {"forecaster_state": "hungry", "target_state": "sated",
         "utility_delta_by_state": {"hungry": 2.0, "sated": -1.0}},
        {"forecaster_state": "hungry", "target_state": "sated",
         "utility_delta_by_state": {"hungry": 2.0, "sated": -1.0}},
    ]
    outputs = _run(contexts, 0.8)
    assert [item["metric"] for item in outputs] == [1.0, 1.0]
    assert outputs[-1]["state"]["steps"] == 2
    assert outputs[-1]["state"]["cumulative_error"] == 2.0
