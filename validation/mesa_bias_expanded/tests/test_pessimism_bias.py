from copy import deepcopy
import math

import pytest

from mechanisms import pessimism_bias as plugin


def direct(context, strength, state=None):
    supplied = deepcopy(context)
    supplied.update({
        "state": deepcopy(state or {}),
        "peer_states": [],
        "round_index": 0,
        "agent_index": 0,
        "uniform": 0.5,
    })
    return plugin.evaluate(supplied, strength)


def logistic(value):
    if value >= 0:
        return 1.0 / (1.0 + math.exp(-value))
    exp_value = math.exp(value)
    return exp_value / (1.0 + exp_value)


def test_numeric_oracle_matches_asymmetric_log_odds_formula():
    context = {
        "base_adverse_rate": 0.35,
        "favorable_evidence": 0.80,
        "adverse_evidence": 0.15,
    }
    result = direct(context, 0.8)
    ref_log_odds = math.log(0.35 / 0.65) + 1.2 * (0.15 - 0.80)
    bias = 0.8 * 1.4 * 0.80 * (1.0 - 0.15 / 0.60)
    assert result["state"]["bias_log_odds"] == pytest.approx(bias)
    assert result["state"]["last_reference_probability"] == pytest.approx(logistic(ref_log_odds))
    assert result["metric"] == pytest.approx(logistic(ref_log_odds + bias))
    assert 0.0 <= result["metric"] <= 1.0
    assert result["active"] is True
    assert len(result["trace"]) >= 1


def test_positive_scenario_increases_adverse_forecast():
    scenario = plugin.scenarios()[0]
    context = scenario["contexts"][0]
    reference = direct(context, 0.0)["metric"]
    biased = direct(context, 0.8)["metric"]
    assert biased > reference
    assert scenario["expectation"] == "increase"


def test_supported_adverse_forecast_removes_necessary_condition():
    scenario = plugin.scenarios()[1]
    context = scenario["contexts"][0]
    reference = direct(context, 0.0)
    intervention = direct(context, 0.8)
    assert context["adverse_evidence"] >= 0.60
    assert intervention["metric"] == pytest.approx(reference["metric"])
    assert intervention["state"]["bias_log_odds"] == 0.0
    assert intervention["active"] is False


def test_zero_strength_is_explicit_reference_with_no_bias():
    context = plugin.scenarios()[0]["contexts"][0]
    result = direct(context, 0.0)
    expected = logistic(
        math.log(0.35 / 0.65) + 1.2 * (0.15 - 0.80)
    )
    assert result["metric"] == pytest.approx(expected)
    assert result["state"]["last_adverse_probability"] == pytest.approx(expected)
    assert result["state"]["bias_log_odds"] == 0.0
    assert result["active"] is False


@pytest.mark.parametrize(
    "context",
    [
        {"favorable_evidence": 0.2, "adverse_evidence": 0.1},
        {"base_adverse_rate": 0.5, "favorable_evidence": float("nan"), "adverse_evidence": 0.1},
        {"base_adverse_rate": 0.5, "favorable_evidence": True, "adverse_evidence": 0.1},
        {"base_adverse_rate": 0.5, "favorable_evidence": 0.1, "adverse_evidence": 1.1},
    ],
)
def test_missing_or_invalid_required_inputs_rejected(context):
    with pytest.raises(ValueError):
        direct(context, 0.8)


@pytest.mark.parametrize("strength", [-0.1, 1.1, float("nan"), float("inf"), True])
def test_invalid_strength_rejected(strength):
    with pytest.raises(ValueError):
        direct(plugin.scenarios()[0]["contexts"][0], strength)


def test_deterministic_nonmutation_and_complete_state():
    context = plugin.scenarios()[0]["contexts"][0]
    prior_state = {"earlier_note": {"kept": True}}
    original_context = deepcopy(context)
    original_state = deepcopy(prior_state)
    first = direct(context, 0.8, prior_state)
    second = direct(context, 0.8, prior_state)
    assert first == second
    assert context == original_context
    assert prior_state == original_state
    assert set(first["state"]) == set(plugin.METADATA["state_fields"])
    assert all(math.isfinite(first["state"][key]) for key in plugin.METADATA["state_fields"])
