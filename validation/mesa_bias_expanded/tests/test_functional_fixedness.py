import copy
import math

import pytest

from mechanisms import functional_fixedness as plugin


def context(**kwargs):
    return {
        "state": {},
        "peer_states": [],
        "round_index": 0,
        "agent_index": 0,
        "uniform": 0.5,
        **kwargs,
    }


POSITIVE = {
    "uses": [
        {"id": "customary_container", "utility": 0.80, "customary": True},
        {"id": "alternative_tool", "utility": 0.95, "customary": False},
    ],
}


def test_positive_task_has_specific_numeric_regret_and_retains_customary_use():
    result = plugin.evaluate(context(**copy.deepcopy(POSITIVE)), 0.8)
    assert result["metric"] == pytest.approx(0.15)
    assert result["state"]["last_choice_id"] == "customary_container"
    assert result["active"] is True
    assert "hurdle=0.64" in result["trace"][0]
    assert math.isfinite(result["metric"])


def test_strength_zero_uses_explicit_exhaustive_best_utility_reference():
    result = plugin.evaluate(context(**copy.deepcopy(POSITIVE)), 0.0)
    assert result["metric"] == 0.0
    assert result["state"]["last_choice_id"] == "alternative_tool"
    assert result["active"] is False


def test_boundary_without_customary_use_matches_reference_at_point_8():
    boundary = {
        "uses": [
            {"id": "use_a", "utility": 0.45, "customary": False},
            {"id": "use_b", "utility": 0.90, "customary": False},
        ],
    }
    at_strength = plugin.evaluate(context(**boundary), 0.8)
    reference = plugin.evaluate(context(**boundary), 0.0)
    assert at_strength["metric"] == reference["metric"] == 0.0
    assert at_strength["state"]["last_choice_id"] == reference["state"]["last_choice_id"] == "use_b"
    assert at_strength["active"] is False


def test_alternative_that_clears_customary_margin_is_not_blocked():
    task = {
        "uses": [
            {"id": "customary", "utility": 0.20, "customary": True},
            {"id": "novel_but_useful", "utility": 0.60, "customary": False},
        ],
    }
    result = plugin.evaluate(context(**task), 0.8)
    assert result["state"]["last_choice_id"] == "novel_but_useful"
    assert result["metric"] == 0.0
    assert result["active"] is False


def test_missing_and_impossible_use_evidence_is_rejected():
    with pytest.raises(ValueError, match="uses are required"):
        plugin.evaluate(context(), 0.8)
    with pytest.raises(ValueError, match="at least two"):
        plugin.evaluate(context(uses=[{"id": "only", "utility": 0.5, "customary": True}]), 0.8)
    with pytest.raises(ValueError, match="customary must be a boolean"):
        plugin.evaluate(context(uses=[
            {"id": "a", "utility": 0.5, "customary": "yes"},
            {"id": "b", "utility": 0.7, "customary": False},
        ]), 0.8)
    with pytest.raises(ValueError, match=r"within \[0, 1\]"):
        plugin.evaluate(context(uses=[
            {"id": "a", "utility": 1.1, "customary": True},
            {"id": "b", "utility": 0.7, "customary": False},
        ]), 0.8)


def test_strength_must_be_finite_and_in_range():
    for strength in (-0.01, 1.01, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            plugin.evaluate(context(**copy.deepcopy(POSITIVE)), strength)


def test_evaluation_is_deterministic_and_does_not_mutate_nested_context():
    supplied = context(**copy.deepcopy(POSITIVE))
    supplied["state"] = {"step_count": 3, "custom": {"preserve": [1, 2]}}
    before = copy.deepcopy(supplied)
    first = plugin.evaluate(supplied, 0.8)
    second = plugin.evaluate(supplied, 0.8)
    assert supplied == before
    assert first == second
    assert first["state"]["step_count"] == 4
    assert first["state"]["custom"] == {"preserve": [1, 2]}
    assert math.isfinite(first["metric"])


def test_scenarios_provide_positive_and_necessary_condition_boundary():
    scenarios = {item["name"]: item for item in plugin.scenarios()}
    assert scenarios["positive"]["expectation"] == "increase"
    assert scenarios["boundary"]["expectation"] == "equal"
    assert scenarios["positive"]["contexts"]
    assert scenarios["boundary"]["contexts"]
