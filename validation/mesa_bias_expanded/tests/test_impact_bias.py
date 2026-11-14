from copy import deepcopy

import pytest

from mechanisms import impact_bias


def run_chronology(contexts, strength, initial_state=None):
    state = deepcopy(initial_state or {})
    results = []
    for round_index, task_inputs in enumerate(contexts):
        context = deepcopy(task_inputs)
        context.update({
            "state": deepcopy(state),
            "peer_states": [],
            "round_index": round_index,
            "agent_index": 0,
            "uniform": 0.5,
        })
        result = impact_bias.evaluate(context, strength)
        state = deepcopy(result["state"])
        results.append(result)
    return results


def test_numeric_oracle_for_peak_and_duration_exaggeration():
    context = {
        "event_id": "oracle",
        "forecast_peak": 8,
        "forecast_duration": 6,
        "observed_trajectory": [6, 4, 2, 0],
        "state": {},
        "peer_states": [],
        "round_index": 0,
        "agent_index": 0,
        "uniform": 0.5,
    }
    result = impact_bias.evaluate(context, 0.5)
    # Positive excesses are 2 intensity units and 3 steps; modeled burden is
    # (8 + .5*2) * (6 + .5*3) = 67.5, less observed area 12 = 55.5.
    assert result["metric"] == pytest.approx(55.5)
    assert result["active"] is True
    assert result["state"]["event_ids"] == ["oracle"]
    assert result["state"]["event_count"] == 1
    assert any("positive peak excess=2, duration excess=3" in line for line in result["trace"])


def test_positive_chronological_scenario_increases_error_at_strength_point_8():
    scenario = impact_bias.scenarios()[0]
    reference = run_chronology(scenario["contexts"], 0.0)
    intervention = run_chronology(scenario["contexts"], 0.8)
    assert intervention[-1]["metric"] > reference[-1]["metric"]
    assert intervention[-1]["state"]["event_ids"] == ["loss-a", "loss-b"]
    assert len(intervention) == len(scenario["contexts"])


def test_boundary_without_either_overestimate_equals_strength_zero():
    scenario = impact_bias.scenarios()[1]
    reference = run_chronology(scenario["contexts"], 0.0)
    intervention = run_chronology(scenario["contexts"], 0.8)
    assert intervention[-1]["metric"] == pytest.approx(reference[-1]["metric"])
    assert not any(result["active"] for result in intervention)
    assert all(
        context["forecast_peak"] <= max(context["observed_trajectory"])
        and context["forecast_duration"] <= sum(v > 0 for v in context["observed_trajectory"])
        for context in scenario["contexts"]
    )


def test_strength_zero_is_the_explicit_unamplified_forecast_reference():
    context = {
        "event_id": "reference",
        "forecast_peak": 8,
        "forecast_duration": 6,
        "observed_trajectory": [6, 4, 2, 0],
        "state": {},
        "peer_states": [],
        "round_index": 0,
        "agent_index": 0,
        "uniform": 0.5,
    }
    result = impact_bias.evaluate(context, 0.0)
    assert result["metric"] == pytest.approx(8 * 6 - (6 + 4 + 2))
    assert result["active"] is False
    assert result["state"]["event_count"] == 1


@pytest.mark.parametrize("field", impact_bias.METADATA["required_inputs"])
def test_missing_required_evidence_is_rejected(field):
    context = {
        "event_id": "missing",
        "forecast_peak": 8,
        "forecast_duration": 6,
        "observed_trajectory": [6, 4, 2, 0],
        "state": {},
    }
    del context[field]
    with pytest.raises(ValueError):
        impact_bias.evaluate(context, 0.8)


@pytest.mark.parametrize(
    "update",
    [
        {"forecast_peak": 11},
        {"forecast_peak": float("nan")},
        {"forecast_duration": 0},
        {"forecast_duration": True},
        {"observed_trajectory": []},
        {"observed_trajectory": [5, 0, 1]},
    ],
)
def test_invalid_task_evidence_is_rejected(update):
    context = {
        "event_id": "invalid",
        "forecast_peak": 8,
        "forecast_duration": 6,
        "observed_trajectory": [6, 4, 2, 0],
        "state": {},
    }
    context.update(update)
    with pytest.raises(ValueError):
        impact_bias.evaluate(context, 0.8)


def test_strength_validation_and_duplicate_event_rejection():
    context = {
        "event_id": "same",
        "forecast_peak": 8,
        "forecast_duration": 6,
        "observed_trajectory": [6, 4, 2, 0],
        "state": {},
    }
    for strength in (-0.1, 1.1, float("inf"), True):
        with pytest.raises(ValueError):
            impact_bias.evaluate(context, strength)
    first = impact_bias.evaluate(context, 0.8)
    repeated = deepcopy(context)
    repeated["state"] = first["state"]
    with pytest.raises(ValueError, match="new"):
        impact_bias.evaluate(repeated, 0.8)


def test_repeated_call_is_deterministic_and_input_and_nested_state_are_unchanged():
    context = {
        "event_id": "immutable",
        "forecast_peak": 8,
        "forecast_duration": 6,
        "observed_trajectory": [6, 4, 2, 0],
        "state": {"event_ids": ["prior"], "event_count": 1,
                  "cumulative_forecast_error": 3.5, "extra": {"keep": [1, 2]}},
        "peer_states": [{"event_ids": ["peer"]}],
        "round_index": 1,
        "agent_index": 0,
        "uniform": 0.5,
    }
    before = deepcopy(context)
    first = impact_bias.evaluate(context, 0.8)
    second = impact_bias.evaluate(context, 0.8)
    assert context == before
    assert first == second
    assert first["state"]["event_ids"] == ["prior", "immutable"]
    first["state"]["extra"]["keep"].append(3)
    assert context["state"]["extra"]["keep"] == [1, 2]
