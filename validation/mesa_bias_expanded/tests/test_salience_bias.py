from copy import deepcopy
import math

import pytest

from mechanisms import salience_bias


def context(items=None, budget=10.0, state=None):
    if items is None:
        items = [
            {"id": "quiet_diagnostic", "relevance": 0.9, "prominence": 0.0},
            {"id": "conspicuous_weak", "relevance": 0.1, "prominence": 1.0},
        ]
    return {
        "attention_items": items,
        "attention_budget": budget,
        "state": {} if state is None else state,
        "peer_states": [],
        "round_index": 0,
        "agent_index": 0,
        "uniform": 0.5,
    }


def test_positive_salience_diverts_attention_with_numeric_quality_oracle():
    ctx = context()
    reference = salience_bias.evaluate(ctx, 0.0)
    biased = salience_bias.evaluate(ctx, 0.8)
    # Reference shares are 0.9/0.1 (quality .82). At strength .8 the
    # prominence bonus is .8*.9*(1-.5)=.36: weights .9/.46, quality .856/1.36.
    assert reference["metric"] == pytest.approx(0.82)
    assert biased["metric"] == pytest.approx(0.856 / 1.36)
    assert biased["metric"] < reference["metric"]
    assert biased["state"]["last_attention_shares"]["conspicuous_weak"] > 0.1
    assert biased["active"] is True


def test_equal_prominence_boundary_matches_strength_zero():
    ctx = context(items=[
        {"id": "high_relevance", "relevance": 0.9, "prominence": 0.7},
        {"id": "low_relevance", "relevance": 0.1, "prominence": 0.7},
    ])
    biased = salience_bias.evaluate(ctx, 0.8)
    reference = salience_bias.evaluate(ctx, 0.0)
    assert biased["metric"] == pytest.approx(reference["metric"])
    assert biased["state"]["last_attention_shares"] == pytest.approx(
        reference["state"]["last_attention_shares"]
    )
    assert biased["active"] is False


def test_zero_strength_is_relevance_proportional_reference_and_conserves_budget():
    ctx = context(items=[
        {"id": "diagnostic", "relevance": 0.6, "prominence": 0.0},
        {"id": "other", "relevance": 0.3, "prominence": 1.0},
        {"id": "irrelevant", "relevance": 0.1, "prominence": 0.4},
    ], budget=12.0)
    result = salience_bias.evaluate(ctx, 0.0)
    assert result["metric"] == pytest.approx((0.6**2 + 0.3**2 + 0.1**2) / 1.0)
    assert result["state"]["last_attention_shares"] == pytest.approx(
        {"diagnostic": 0.6, "other": 0.3, "irrelevant": 0.1}
    )
    assert sum(result["state"]["last_attention_shares"].values()) == pytest.approx(1.0)
    assert sum(ctx["attention_budget"] * share for share in result["state"]["last_attention_shares"].values()) == pytest.approx(12.0)
    assert result["active"] is False


def test_missing_relevance_evidence_is_rejected_not_defaulted_to_zero():
    ctx = context(items=[
        {"id": "one", "prominence": 0.2},
        {"id": "two", "relevance": 0.2, "prominence": 0.8},
    ])
    with pytest.raises(ValueError, match="missing relevance evidence"):
        salience_bias.evaluate(ctx, 0.8)


def test_invalid_input_types_and_ranges_are_rejected():
    with pytest.raises(ValueError, match="strength"):
        salience_bias.evaluate(context(), float("nan"))
    with pytest.raises(ValueError, match="strength"):
        salience_bias.evaluate(context(), 1.01)
    with pytest.raises(ValueError, match="relevance scores"):
        salience_bias.evaluate(context(items=[
            {"id": "one", "relevance": 1.1, "prominence": 0.0},
            {"id": "two", "relevance": 0.2, "prominence": 0.8},
        ]), 0.5)
    with pytest.raises(ValueError, match="positive"):
        salience_bias.evaluate(context(budget=0.0), 0.5)


def test_deterministic_and_nonmutating_for_context_nested_state_and_result():
    original = context(state={
        "custom": {"keep": [1, {"nested": True}]},
        "attention_history": [{"earlier": {"metric": 0.4}}],
    })
    before = deepcopy(original)
    first = salience_bias.evaluate(original, 0.8)
    second = salience_bias.evaluate(original, 0.8)
    assert original == before
    assert first == second
    first["state"]["custom"]["keep"][1]["nested"] = False
    first["state"]["attention_history"][0]["earlier"]["metric"] = -1
    assert original == before
    assert math.isfinite(second["metric"])
    assert second["state"]["attention_history"][-1]["round_index"] == 0


def test_contract_scenarios_have_expected_strength_effects():
    cases = {scenario["name"]: scenario for scenario in salience_bias.scenarios()}
    assert {"positive", "boundary"} <= set(cases)
    for name, expectation in (("positive", "decrease"), ("boundary", "equal")):
        scenario = cases[name]
        state = deepcopy(scenario["initial_state"])
        for round_index, task_context in enumerate(scenario["contexts"]):
            full = {**task_context, "state": state, "round_index": round_index,
                    "peer_states": [], "agent_index": 0, "uniform": 0.5}
            actual = salience_bias.evaluate(full, 0.8)
            reference = salience_bias.evaluate(full, 0.0)
            state = actual["state"]
        if expectation == "decrease":
            assert actual["metric"] < reference["metric"]
        else:
            assert actual["metric"] == pytest.approx(reference["metric"])
