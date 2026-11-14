from copy import deepcopy
import math

import pytest

from mechanisms import heuristics


def context(options, state=None):
    return {
        "options": options,
        "state": {} if state is None else state,
        "peer_states": [],
        "round_index": 0,
        "agent_index": 0,
        "uniform": 0.5,
    }


POSITIVE_OPTIONS = [
    {"name": "quick-leader", "attributes": [0.9, 0.0, 0.0]},
    {"name": "balanced", "attributes": [0.7, 0.9, 0.9]},
]


def test_positive_unique_cue_leader_reduces_work_and_selects_cue_winner():
    data = context(POSITIVE_OPTIONS)
    shortcut = heuristics.evaluate(data, 0.8)
    reference = heuristics.evaluate(data, 0.0)

    assert shortcut["active"] is True
    assert shortcut["metric"] == 2.0  # two options, first cue only
    assert reference["metric"] == 6.0  # two options by three attributes
    assert shortcut["metric"] < reference["metric"]
    assert shortcut["state"]["last_choice"] == "quick-leader"
    assert reference["state"]["last_choice"] == "balanced"
    assert math.isfinite(shortcut["metric"])


def test_zero_strength_is_full_mean_utility_reference_choice():
    data = context(POSITIVE_OPTIONS)
    result = heuristics.evaluate(data, 0.0)

    # Means are 0.3 and 2.5/3: the explicit full-information reference picks balanced.
    assert result["active"] is False
    assert result["state"]["last_choice"] == "balanced"
    assert result["metric"] == 6.0
    assert result["state"]["cumulative_attribute_evaluations"] == 6


def test_boundary_tied_first_cue_matches_zero_strength_reference_metric_and_choice():
    boundary = context([
        {"name": "lower-mean", "attributes": [0.8, 0.2]},
        {"name": "higher-mean", "attributes": [0.8, 0.8]},
    ])
    shortcut_strength = heuristics.evaluate(boundary, 0.8)
    reference = heuristics.evaluate(boundary, 0.0)

    assert shortcut_strength["active"] is False
    assert shortcut_strength["metric"] == reference["metric"] == 4.0
    assert shortcut_strength["state"]["last_choice"] == reference["state"]["last_choice"] == "higher-mean"


def test_rejects_missing_or_impossible_evidence():
    with pytest.raises(ValueError, match="missing required input"):
        heuristics.evaluate({"state": {}, "peer_states": [], "round_index": 0, "agent_index": 0, "uniform": 0.5}, 0.8)
    with pytest.raises(ValueError, match="at least two"):
        heuristics.evaluate(context([{"name": "only", "attributes": [0.5, 0.5]}]), 0.8)
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        heuristics.evaluate(context([
            {"name": "a", "attributes": [0.5, 1.2]},
            {"name": "b", "attributes": [0.4, 0.2]},
        ]), 0.8)


def test_strength_must_be_finite_and_in_range():
    data = context(POSITIVE_OPTIONS)
    for invalid in (-0.01, 1.01, float("nan"), float("inf")):
        with pytest.raises(ValueError, match="strength"):
            heuristics.evaluate(data, invalid)


def test_deterministic_and_does_not_mutate_nested_context_or_state():
    data = context(POSITIVE_OPTIONS, {"decisions": 4, "cumulative_attribute_evaluations": 11, "extra": {"tag": [1]}})
    before = deepcopy(data)
    first = heuristics.evaluate(data, 0.8)
    second = heuristics.evaluate(data, 0.8)

    assert data == before
    assert first == second
    assert first["state"]["decisions"] == 5
    assert first["state"]["cumulative_attribute_evaluations"] == 13
    assert first["state"]["extra"] == {"tag": [1]}


def test_scenario_contract_declares_positive_and_boundary_cases():
    cases = {item["name"]: item for item in heuristics.scenarios()}
    assert set(cases) >= {"positive", "boundary"}
    assert cases["positive"]["expectation"] == "decrease"
    assert cases["boundary"]["expectation"] == "equal"
    assert cases["positive"]["contexts"] and cases["boundary"]["contexts"]
