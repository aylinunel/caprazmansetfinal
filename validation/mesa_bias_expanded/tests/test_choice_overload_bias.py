import copy
import math

import pytest

from mechanisms import choice_overload_bias as plugin


def ctx(**kwargs):
    return {"state": {}, "peer_states": [], "round_index": 0, "agent_index": 0, "uniform": 0.5, **kwargs}


POSITIVE = {
    "options": [
        {"id": "basic", "utility": 0.20, "comparison_difficulty": 0.0},
        {"id": "standard", "utility": 0.70, "comparison_difficulty": 0.5},
        {"id": "premium", "utility": 0.95, "comparison_difficulty": 1.0},
    ],
    "comparison_budget": 0.5,
}


def test_positive_overload_causes_numeric_utility_regret_and_traces_choice():
    result = plugin.evaluate(ctx(**copy.deepcopy(POSITIVE)), 0.8)
    assert result["metric"] == pytest.approx(0.25)
    assert result["state"]["last_choice"] == "standard"
    assert result["state"]["last_examined_ids"] == ["basic", "standard"]
    assert result["active"] is True
    assert "allowance=0.7" in result["trace"][0]


def test_zero_strength_is_exhaustive_max_utility_reference():
    result = plugin.evaluate(ctx(**copy.deepcopy(POSITIVE)), 0.0)
    assert result["metric"] == 0.0
    assert result["active"] is False
    assert result["state"]["last_choice"] == "premium"
    assert result["state"]["last_examined_ids"] == ["basic", "standard", "premium"]


def test_boundary_without_comparison_difficulty_equals_reference_at_point_8():
    boundary = {
        "options": [
            {"id": "a", "utility": 0.25, "comparison_difficulty": 0.0},
            {"id": "b", "utility": 0.60, "comparison_difficulty": 0.0},
            {"id": "c", "utility": 0.90, "comparison_difficulty": 0.0},
        ],
        "comparison_budget": 0.5,
    }
    at_strength = plugin.evaluate(ctx(**boundary), 0.8)
    reference = plugin.evaluate(ctx(**boundary), 0.0)
    assert at_strength["metric"] == reference["metric"] == 0.0
    assert at_strength["state"]["last_choice"] == reference["state"]["last_choice"] == "c"
    assert at_strength["active"] is False


def test_comparison_work_within_budget_does_not_impair_choice():
    sufficient = copy.deepcopy(POSITIVE)
    sufficient["comparison_budget"] = 2.0
    result = plugin.evaluate(ctx(**sufficient), 0.8)
    assert result["metric"] == 0.0
    assert result["state"]["last_choice"] == "premium"


def test_missing_or_invalid_choice_evidence_is_rejected():
    with pytest.raises(ValueError, match="options and comparison_budget"):
        plugin.evaluate(ctx(comparison_budget=1), 0.8)
    malformed = copy.deepcopy(POSITIVE)
    malformed["options"][1].pop("comparison_difficulty")
    with pytest.raises(ValueError, match="comparison_difficulty"):
        plugin.evaluate(ctx(**malformed), 0.8)
    out_of_range = copy.deepcopy(POSITIVE)
    out_of_range["options"][0]["utility"] = 1.1
    with pytest.raises(ValueError, match=r"within \[0, 1\]"):
        plugin.evaluate(ctx(**out_of_range), 0.8)


def test_strength_must_be_finite_and_in_range():
    for strength in (-0.1, 1.1, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            plugin.evaluate(ctx(**copy.deepcopy(POSITIVE)), strength)


def test_evaluation_is_deterministic_and_does_not_mutate_nested_context():
    context = ctx(**copy.deepcopy(POSITIVE))
    context["state"] = {"step_count": 3, "custom_note": {"keep": True}}
    before = copy.deepcopy(context)
    first = plugin.evaluate(context, 0.8)
    second = plugin.evaluate(context, 0.8)
    assert context == before
    assert first == second
    assert first["state"]["step_count"] == 4
    assert first["state"]["custom_note"] == {"keep": True}
    assert math.isfinite(first["metric"])


def test_scenarios_include_positive_and_necessary_condition_boundary():
    scenarios = {scenario["name"]: scenario for scenario in plugin.scenarios()}
    assert {"positive", "boundary"}.issubset(scenarios)
    assert scenarios["positive"]["expectation"] == "increase"
    assert scenarios["boundary"]["expectation"] == "equal"
