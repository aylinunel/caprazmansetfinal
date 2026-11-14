from copy import deepcopy

import pytest

from mechanisms import cashless_effect as mechanism


POSITIVE = {
    "willingness_margin": 3.0,
    "purchase_amount": 10.0,
    "budget": 20.0,
    "payment_mode": "cashless",
    "cash_salience": 0.8,
    "cashless_salience": 0.1,
    "salience_sensitivity": 0.5,
}
BOUNDARY = {**POSITIVE, "cashless_salience": 0.8}


def context(data, state=None):
    return {
        **deepcopy(data),
        "state": {} if state is None else state,
        "peer_states": [],
        "round_index": 0,
        "agent_index": 0,
        "uniform": 0.5,
    }


def test_positive_cashless_salience_gap_changes_choice_with_numeric_oracle():
    reference = mechanism.evaluate(context(POSITIVE), 0.0)
    result = mechanism.evaluate(context(POSITIVE), 0.8)
    # Reference margin = 3 - .5*10*.8 = -1 (decline).
    # At .8, effective salience=.8-.8*(.8-.1)=.24; margin=1.8 (buy).
    assert reference["metric"] == 0.0
    assert result["state"]["last_willingness_margin"] == pytest.approx(1.8)
    assert result["metric"] == pytest.approx(10.0)
    assert result["active"] is True
    assert "effective_salience=0.24" in result["trace"][0]


def test_equal_salience_boundary_matches_cash_reference_at_strength_point_8():
    reference = mechanism.evaluate(context(BOUNDARY), 0.0)
    boundary = mechanism.evaluate(context(BOUNDARY), 0.8)
    assert reference["metric"] == 0.0
    assert boundary["metric"] == pytest.approx(reference["metric"])
    assert boundary["state"]["last_willingness_margin"] == pytest.approx(-1.0)
    assert boundary["active"] is False


def test_zero_strength_is_explicit_physical_cash_reference_policy():
    result = mechanism.evaluate(context(POSITIVE), 0.0)
    assert result["metric"] == 0.0
    assert result["state"]["last_reference_willingness_margin"] == pytest.approx(-1.0)
    assert result["state"]["last_willingness_margin"] == pytest.approx(-1.0)
    assert result["state"]["cumulative_spend"] == pytest.approx(0.0)
    assert result["active"] is False


def test_required_inputs_ranges_and_impossible_payment_mode_are_rejected():
    with pytest.raises(ValueError, match="missing required input"):
        mechanism.evaluate(context({}), 0.8)
    with pytest.raises(ValueError, match="purchase_amount"):
        mechanism.evaluate(context({**POSITIVE, "purchase_amount": 0}), 0.8)
    with pytest.raises(ValueError, match="payment_mode"):
        mechanism.evaluate(context({**POSITIVE, "payment_mode": "contactless-ish"}), 0.8)
    with pytest.raises(ValueError, match="cash_salience"):
        mechanism.evaluate(context({**POSITIVE, "cash_salience": 1.1}), 0.8)
    with pytest.raises(ValueError, match="budget"):
        mechanism.evaluate(context({**POSITIVE, "budget": -1}), 0.8)


def test_unaffordable_offer_cannot_become_spending_despite_willingness_change():
    data = {**POSITIVE, "budget": 5.0}
    reference = mechanism.evaluate(context(data), 0.0)
    result = mechanism.evaluate(context(data), 0.8)
    assert reference["metric"] == result["metric"] == 0.0
    assert result["state"]["last_willingness_margin"] > result["state"]["last_reference_willingness_margin"]
    assert result["active"] is True


def test_determinism_nonmutation_and_nested_state_preservation():
    previous = {"cumulative_spend": 2.0, "memo": {"tags": ["keep"]}}
    supplied = context(POSITIVE, previous)
    before = deepcopy(supplied)
    first = mechanism.evaluate(supplied, 0.8)
    second = mechanism.evaluate(supplied, 0.8)
    assert supplied == before
    assert first == second
    assert first["state"]["memo"] == previous["memo"]
    assert first["state"]["cumulative_spend"] == pytest.approx(12.0)
    assert first["state"] is not supplied["state"]
    assert first["state"]["memo"] is not supplied["state"]["memo"]


def test_scenario_contract_positive_and_boundary_outcomes():
    items = {item["name"]: item for item in mechanism.scenarios()}
    assert {"positive", "boundary"} <= items.keys()
    assert items["positive"]["expectation"] == "increase"
    assert items["boundary"]["expectation"] == "equal"
    for name, expected in (("positive", "increase"), ("boundary", "equal")):
        task = items[name]["contexts"][0]
        zero = mechanism.evaluate(context(task), 0.0)["metric"]
        effect = mechanism.evaluate(context(task), 0.8)["metric"]
        if expected == "increase":
            assert effect > zero
        else:
            assert effect == pytest.approx(zero)


def test_invalid_strengths_are_rejected():
    for value in (-0.01, 1.01, float("nan"), float("inf"), True):
        with pytest.raises(ValueError, match="strength"):
            mechanism.evaluate(context(POSITIVE), value)
