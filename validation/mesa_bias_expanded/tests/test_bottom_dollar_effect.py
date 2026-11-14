from copy import deepcopy

import pytest

from mechanisms import bottom_dollar_effect as effect


def context(**overrides):
    data = {
        "item_satisfaction": 0.8,
        "funds_before": 100.0,
        "purchase_cost": 100.0,
        "budget_secure_after": True,
        "state": {"earlier": "preserved"},
        "peer_states": [],
        "round_index": 0,
        "agent_index": 2,
        "uniform": 0.5,
    }
    data.update(overrides)
    return data


def test_positive_case_has_task_specific_numeric_oracle():
    result = effect.evaluate(context(), 0.8)
    assert result["metric"] == pytest.approx(0.16)
    assert result["active"] is True
    assert result["state"]["last_funds_after"] == 0.0


def test_boundary_non_depleted_budget_matches_reference():
    inputs = context(purchase_cost=99.0)
    assert effect.evaluate(inputs, 0.8)["metric"] == effect.evaluate(inputs, 0.0)["metric"] == 0.8
    assert effect.evaluate(inputs, 0.8)["active"] is False


def test_rational_budget_concern_is_not_misreported_as_item_dissatisfaction():
    inputs = context(budget_secure_after=False)
    result = effect.evaluate(inputs, 0.8)
    assert result["metric"] == 0.8
    assert result["active"] is False
    assert "rational" in " ".join(result["trace"]).lower() or "secure" in " ".join(result["trace"]).lower()


def test_zero_strength_is_explicit_reference_policy():
    result = effect.evaluate(context(), 0.0)
    assert result["metric"] == pytest.approx(0.8)
    assert result["active"] is False
    assert result["state"]["last_item_satisfaction"] == pytest.approx(0.8)


def test_missing_or_impossible_evidence_is_rejected():
    missing = context()
    del missing["budget_secure_after"]
    with pytest.raises(ValueError, match="budget_secure_after"):
        effect.evaluate(missing, 0.8)
    with pytest.raises(ValueError, match="cannot exceed"):
        effect.evaluate(context(purchase_cost=101.0), 0.8)


def test_input_ranges_and_strength_are_validated():
    with pytest.raises(ValueError, match="item_satisfaction"):
        effect.evaluate(context(item_satisfaction=1.1), 0.8)
    with pytest.raises(ValueError, match="strength"):
        effect.evaluate(context(), float("nan"))
    with pytest.raises(ValueError, match="strength"):
        effect.evaluate(context(), 1.01)


def test_deterministic_and_does_not_mutate_context_or_nested_state():
    inputs = context(state={"history": {"note": [1, 2]}})
    before = deepcopy(inputs)
    first = effect.evaluate(inputs, 0.8)
    second = effect.evaluate(inputs, 0.8)
    assert first == second
    assert inputs == before
    first["state"]["history"]["note"].append(3)
    assert inputs["state"]["history"]["note"] == [1, 2]


def test_scenarios_include_required_positive_and_boundary_contract():
    scenarios = {item["name"]: item for item in effect.scenarios()}
    assert {"positive", "boundary"} <= scenarios.keys()
    assert scenarios["positive"]["expectation"] == "decrease"
    assert scenarios["boundary"]["expectation"] == "equal"
    assert scenarios["positive"]["contexts"]
    assert scenarios["boundary"]["contexts"]
