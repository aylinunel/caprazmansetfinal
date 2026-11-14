from copy import deepcopy
import math

import pytest

from mechanisms import declinism


def _run(scenario, strength):
    state = deepcopy(scenario["initial_state"])
    outputs = []
    for round_index, step in enumerate(scenario["contexts"]):
        context = {
            **deepcopy(step),
            "state": deepcopy(state),
            "peer_states": [],
            "round_index": round_index,
            "agent_index": 0,
            "uniform": 0.5,
        }
        result = declinism.evaluate(context, strength)
        outputs.append(result)
        state = result["state"]
    return outputs


def _by_name(name):
    return next(item for item in declinism.scenarios() if item["name"] == name)


def test_positive_sequence_increases_domain_decline_share_with_numeric_oracle():
    scenario = _by_name("positive")
    reference = _run(scenario, 0.0)
    modeled = _run(scenario, 0.8)
    assert reference[-1]["metric"] == 0.0
    assert modeled[-1]["metric"] == 1.0
    assert modeled[-1]["metric"] > reference[-1]["metric"]
    assert modeled[-1]["active"] is True
    assert modeled[-1]["state"]["last_idealized_domains"] == ["community", "health", "safety"]


def test_single_supported_measure_boundary_matches_reference_metric():
    scenario = _by_name("boundary")
    reference = _run(scenario, 0.0)
    modeled = _run(scenario, 0.8)
    assert reference[-1]["metric"] == pytest.approx(1 / 3)
    assert modeled[-1]["metric"] == reference[-1]["metric"]
    assert modeled[-1]["active"] is False
    assert modeled[-1]["state"]["last_supported_domains"] == ["health"]
    assert modeled[-1]["state"]["last_idealized_domains"] == []


def test_zero_strength_is_explicit_mean_comparison_reference():
    scenario = _by_name("positive")
    result = _run(scenario, 0.0)[0]
    # First current equals the mean of each domain's two prior observations.
    assert result["metric"] == 0.0
    assert result["active"] is False
    assert "current < prior_mean" in " ".join(result["trace"])


def test_missing_or_impossible_evidence_is_rejected():
    valid_state = {"history": [{"a": 10, "b": 20}, {"a": 20, "b": 30}]}
    with pytest.raises(ValueError, match="missing required input"):
        declinism.evaluate({"state": valid_state}, 0.5)
    with pytest.raises(ValueError, match="at least two"):
        declinism.evaluate({"scores": {"a": 10}, "state": valid_state}, 0.5)
    with pytest.raises(ValueError, match=r"\[0, 100\]"):
        declinism.evaluate({"scores": {"a": 10, "b": 101}, "state": valid_state}, 0.5)
    with pytest.raises(ValueError, match="at least two chronological"):
        declinism.evaluate({"scores": {"a": 10, "b": 20}, "state": {"history": [{"a": 10, "b": 20}]}}, 0.5)


def test_strength_range_and_finiteness_are_validated():
    state = {"history": [{"a": 10, "b": 20}, {"a": 20, "b": 30}]}
    context = {"scores": {"a": 15, "b": 25}, "state": state}
    for bad_strength in (-0.1, 1.1, float("nan"), float("inf"), True):
        with pytest.raises(ValueError):
            declinism.evaluate(context, bad_strength)


def test_deterministic_and_does_not_mutate_input_or_nested_state():
    context = {
        "scores": {"a": 70, "b": 80, "c": 90},
        "state": {"history": [{"a": 60, "b": 70, "c": 80}, {"a": 100, "b": 90, "c": 100}], "tag": {"keep": [1]}},
        "peer_states": [{"untouched": [2]}],
    }
    before = deepcopy(context)
    first = declinism.evaluate(context, 0.8)
    second = declinism.evaluate(context, 0.8)
    assert context == before
    assert first == second
    assert math.isfinite(first["metric"])
    first["state"]["history"][0]["a"] = -1
    assert context["state"]["history"][0]["a"] == 60


def test_temporal_state_appends_each_observation_without_losing_history():
    scenario = _by_name("positive")
    outputs = _run(scenario, 0.8)
    assert len(outputs[0]["state"]["history"]) == 3
    assert len(outputs[1]["state"]["history"]) == 4
    assert outputs[1]["state"]["history"][-1] == scenario["contexts"][-1]["scores"]
