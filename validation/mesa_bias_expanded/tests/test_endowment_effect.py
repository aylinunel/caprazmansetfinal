from copy import deepcopy

import pytest

from mechanisms import endowment_effect as mechanism


POSITIVE = {
    "same_item": True,
    "is_owner": True,
    "pre_ownership_value": 10.0,
    "pre_ownership_market_value": 10.0,
    "current_market_value": 10.0,
    "acquisition_reference_value": 16.0,
    "sale_offer": 13.0,
    "transaction_cost": 0.0,
}
BOUNDARY = {**POSITIVE, "is_owner": False}


def context(data, state=None):
    return {
        **deepcopy(data),
        "state": {} if state is None else state,
        "peer_states": [],
        "round_index": 0,
        "agent_index": 0,
        "uniform": 0.5,
    }


def test_positive_ownership_reference_changes_sale_choice_with_numeric_oracle():
    result = mechanism.evaluate(context(POSITIVE), 0.8)
    # Baseline reserve is 10; the explicit ownership gap is 16-10=6.
    # At strength .8 the threshold is 10 + .8*6 = 14.8, above the offer of 13.
    assert result["state"]["last_reference_reservation_value"] == pytest.approx(10.0)
    assert result["state"]["last_ownership_premium"] == pytest.approx(4.8)
    assert result["state"]["last_reservation_value"] == pytest.approx(14.8)
    assert result["state"]["last_reference_sale_accepted"] == 1
    assert result["metric"] == 0.0
    assert result["active"] is True
    assert "premium=0.8*gap=4.8" in result["trace"][0]


def test_no_ownership_boundary_matches_strength_zero_reference_choice():
    baseline = mechanism.evaluate(context(BOUNDARY), 0.0)
    effect = mechanism.evaluate(context(BOUNDARY), 0.8)
    assert baseline["metric"] == 1.0
    assert effect["metric"] == baseline["metric"]
    assert effect["state"]["last_ownership_premium"] == 0.0
    assert effect["active"] is False


def test_zero_strength_is_explicit_market_and_transaction_adjusted_reference():
    data = {
        **POSITIVE,
        "pre_ownership_value": 10.0,
        "pre_ownership_market_value": 8.0,
        "current_market_value": 11.0,
        "transaction_cost": 1.0,
    }
    result = mechanism.evaluate(context(data), 0.0)
    # The reference rule is 10 + (11-8) + 1 = 14; the offered 13 is rejected.
    assert result["state"]["last_reference_reservation_value"] == pytest.approx(14.0)
    assert result["state"]["last_reservation_value"] == pytest.approx(14.0)
    assert result["state"]["last_ownership_premium"] == 0.0
    assert result["metric"] == 0.0
    assert result["active"] is False


def test_missing_impossible_and_wrong_type_evidence_is_rejected():
    with pytest.raises(ValueError, match="same_item is required"):
        mechanism.evaluate(context({}), 0.8)
    missing = deepcopy(POSITIVE)
    del missing["acquisition_reference_value"]
    with pytest.raises(ValueError, match="acquisition_reference_value is required"):
        mechanism.evaluate(context(missing), 0.8)
    for field, value in (("same_item", False), ("is_owner", 1),
                         ("sale_offer", -1), ("transaction_cost", float("nan")),
                         ("current_market_value", True)):
        invalid = deepcopy(POSITIVE)
        invalid[field] = value
        with pytest.raises(ValueError):
            mechanism.evaluate(context(invalid), 0.8)


def test_determinism_and_nested_state_nonmutation():
    supplied = context(POSITIVE, {"memo": {"labels": ["kept"]}})
    before = deepcopy(supplied)
    first = mechanism.evaluate(supplied, 0.8)
    second = mechanism.evaluate(supplied, 0.8)
    assert supplied == before
    assert first == second
    assert first["state"]["memo"] == {"labels": ["kept"]}
    assert first["state"] is not supplied["state"]
    assert first["state"]["memo"] is not supplied["state"]["memo"]
    assert isinstance(first["metric"], float)
    assert first["trace"] and isinstance(first["trace"][0], str)


def test_strength_and_state_validation():
    for invalid in (-0.01, 1.01, float("inf"), float("nan"), True):
        with pytest.raises(ValueError, match="strength"):
            mechanism.evaluate(context(POSITIVE), invalid)
    with pytest.raises(ValueError, match="state"):
        mechanism.evaluate({**POSITIVE, "state": []}, 0.5)


def test_scenarios_have_required_names_and_expected_choice_directions():
    supplied = {item["name"]: item for item in mechanism.scenarios()}
    assert {"positive", "boundary"} <= supplied.keys()
    assert supplied["positive"]["expectation"] == "decrease"
    assert supplied["boundary"]["expectation"] == "equal"
    for name in ("positive", "boundary"):
        data = supplied[name]["contexts"][0]
        assert mechanism.evaluate(context(data), 0.8)["metric"] == (
            0.0 if name == "positive" else 1.0
        )
    assert mechanism.evaluate(context(supplied["boundary"]["contexts"][0]), 0.8)["metric"] == mechanism.evaluate(
        context(supplied["boundary"]["contexts"][0]), 0.0
    )["metric"]
