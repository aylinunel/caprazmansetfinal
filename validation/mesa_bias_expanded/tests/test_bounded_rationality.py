from copy import deepcopy

import pytest

from mechanisms import bounded_rationality as br


CHOICE = {
    "options": [
        {"id": "acceptable-first", "utility": 6.0},
        {"id": "best-later", "utility": 10.0},
        {"id": "middle", "utility": 8.0},
    ],
    "evaluation_capacity": 1,
    "aspiration_threshold": 5.0,
}


def test_positive_constrained_satisficing_has_exact_choice_and_regret_oracle():
    result = br.evaluate(CHOICE, 0.8)
    assert result["state"]["last_choice"] == "acceptable-first"
    assert result["state"]["last_evaluated_ids"] == ["acceptable-first"]
    assert result["metric"] == pytest.approx(4.0)  # 10 best utility - 6 chosen utility
    assert result["active"] is True
    assert "threshold 5.0" in result["trace"][0]


def test_nonbinding_capacity_boundary_matches_exhaustive_reference_metric():
    boundary = {**CHOICE, "evaluation_capacity": 3}
    actual = br.evaluate(boundary, 0.8)
    reference = br.evaluate(boundary, 0.0)
    assert actual["state"]["last_choice"] == "best-later"
    assert actual["metric"] == reference["metric"] == 0.0
    assert actual["active"] is False


def test_zero_strength_is_explicit_exhaustive_maximum_reference():
    result = br.evaluate(CHOICE, 0.0)
    assert result["state"]["last_choice"] == "best-later"
    assert result["state"]["last_evaluated_ids"] == ["acceptable-first", "best-later", "middle"]
    assert result["metric"] == 0.0
    assert "strength-zero reference" in result["trace"][0]


def test_missing_or_impossible_evidence_is_rejected():
    with pytest.raises(ValueError, match="missing required input"):
        br.evaluate({"options": CHOICE["options"]}, 0.8)
    with pytest.raises(ValueError, match="evaluation_capacity"):
        br.evaluate({**CHOICE, "evaluation_capacity": 4}, 0.8)
    with pytest.raises(ValueError, match="finite number"):
        br.evaluate({**CHOICE, "options": [{"id": "x", "utility": float("nan")}]}, 0.8)


def test_repeat_call_is_deterministic_and_does_not_mutate_context_or_nested_state():
    context = deepcopy(CHOICE)
    context["state"] = {
        "decision_count": 2,
        "history": [{"choice": "previous", "detail": [1, 2]}],
    }
    before = deepcopy(context)
    first = br.evaluate(context, 0.8)
    second = br.evaluate(context, 0.8)
    assert context == before
    assert first == second
    assert first["state"]["decision_count"] == 3
    first["state"]["last_evaluated_ids"].append("local mutation")
    assert context == before
    assert second["state"]["last_evaluated_ids"] == ["acceptable-first"]


def test_strength_and_threshold_ranges_are_validated():
    for strength in (-0.01, 1.01, float("inf"), float("nan"), True):
        with pytest.raises(ValueError):
            br.evaluate(CHOICE, strength)
    with pytest.raises(ValueError, match="aspiration_threshold"):
        br.evaluate({**CHOICE, "aspiration_threshold": float("inf")}, 0.8)


def test_scenario_contract_has_positive_and_boundary_expectations():
    scenarios = {scenario["name"]: scenario for scenario in br.scenarios()}
    assert scenarios["positive"]["expectation"] == "increase"
    assert scenarios["boundary"]["expectation"] == "equal"
    assert len(scenarios["positive"]["contexts"]) >= 1
