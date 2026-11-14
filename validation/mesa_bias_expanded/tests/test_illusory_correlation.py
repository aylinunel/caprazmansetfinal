"""Behavioral checks for the hypothetical illusory-correlation process."""
from copy import deepcopy
import math

import pytest

from mechanisms import illusory_correlation as plugin


def run_history(contexts, strength):
    state = {}
    outputs = []
    for round_index, task_inputs in enumerate(contexts):
        context = deepcopy(task_inputs)
        context.update({
            "state": deepcopy(state),
            "peer_states": [],
            "round_index": round_index,
            "agent_index": 0,
            "uniform": 0.5,
        })
        result = plugin.evaluate(context, strength)
        state = result["state"]
        outputs.append(result)
    return outputs


def phi_from_counts(n00, n01, n10, n11):
    denom = math.sqrt((n10 + n11) * (n00 + n01) * (n01 + n11) * (n00 + n10))
    return (n11 * n00 - n10 * n01) / denom


def test_numeric_oracle_for_first_joint_occurrence_weighting():
    context = {
        "paired_observations": [[1, 1], [1, 0], [0, 1], [0, 0]],
        "state": {}, "peer_states": [], "round_index": 0,
        "agent_index": 0, "uniform": 0.5,
    }
    result = plugin.evaluate(context, 0.8)
    # One additional 0.8 count goes only to cell 11: phi=.8/5.6=1/7.
    assert result["metric"] == pytest.approx(1 / 7)
    assert result["state"]["observed_cells"] == {"00": 1, "01": 1, "10": 1, "11": 1}
    assert result["state"]["memory_cells"] == {"00": 1.0, "01": 1.0, "10": 1.0, "11": 1.8}
    assert result["active"] is True
    assert result["trace"] and all(isinstance(line, str) for line in result["trace"])


def test_positive_scenario_increases_memory_weighted_association():
    scenario = next(s for s in plugin.scenarios() if s["name"] == "positive")
    base = run_history(scenario["contexts"], 0.0)[-1]["metric"]
    intervention = run_history(scenario["contexts"], 0.8)[-1]["metric"]
    assert intervention > base
    assert scenario["expectation"] == "increase"


def test_boundary_removes_joint_occurrence_and_equals_reference():
    scenario = next(s for s in plugin.scenarios() if s["name"] == "boundary")
    assert all(pair != [1, 1] for c in scenario["contexts"] for pair in c["paired_observations"])
    base = run_history(scenario["contexts"], 0.0)[-1]["metric"]
    intervention = run_history(scenario["contexts"], 0.8)[-1]["metric"]
    assert intervention == pytest.approx(base)
    assert run_history(scenario["contexts"], 0.8)[-1]["active"] is False


def test_zero_strength_is_ordinary_observed_table_phi():
    pairs = [[1, 1], [1, 0], [0, 1], [0, 0], [1, 0]]
    context = {"paired_observations": pairs, "state": {}, "peer_states": [],
               "round_index": 0, "agent_index": 0, "uniform": 0.5}
    result = plugin.evaluate(context, 0.0)
    assert result["metric"] == pytest.approx(phi_from_counts(1, 1, 2, 1))
    assert result["active"] is False


def test_missing_or_invalid_observations_are_rejected():
    defaults = {"state": {}, "peer_states": [], "round_index": 0,
                "agent_index": 0, "uniform": 0.5}
    with pytest.raises(ValueError, match="missing required input"):
        plugin.evaluate(defaults, 0.5)
    for pairs in ([], [[1]], [[1, 2]], [[True, 0]], "11"):
        context = {**defaults, "paired_observations": pairs}
        with pytest.raises(ValueError):
            plugin.evaluate(context, 0.5)


def test_degenerate_evidence_and_invalid_strength_are_rejected():
    context = {"paired_observations": [[0, 0], [0, 1]], "state": {},
               "peer_states": [], "round_index": 0, "agent_index": 0, "uniform": 0.5}
    with pytest.raises(ValueError, match="insufficient or degenerate"):
        plugin.evaluate(context, 0.5)
    valid = {**context, "paired_observations": [[0, 0], [0, 1], [1, 0], [1, 1]]}
    for strength in (-0.1, 1.1, float("nan"), float("inf"), True):
        with pytest.raises(ValueError):
            plugin.evaluate(valid, strength)


def test_deterministic_and_nonmutating_with_nested_state():
    context = {"paired_observations": [[1, 1], [0, 0], [1, 0], [0, 1]],
               "state": {}, "peer_states": [{"unrelated": [1, 2]}],
               "round_index": 0, "agent_index": 0, "uniform": 0.25}
    before = deepcopy(context)
    first = plugin.evaluate(context, 0.8)
    second = plugin.evaluate(context, 0.8)
    assert context == before
    assert first == second
    assert first["state"] is not context["state"]


def test_metadata_and_scenarios_use_exact_top_level_required_key():
    assert plugin.METADATA["required_inputs"] == ["paired_observations"]
    scenarios = plugin.scenarios()
    assert {s["name"] for s in scenarios} >= {"positive", "boundary"}
    reserved = {"state", "peer_states", "uniform", "round_index", "agent_index"}
    assert all(not (reserved & set(context)) for s in scenarios for context in s["contexts"])
