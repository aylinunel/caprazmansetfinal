from copy import deepcopy

import pytest

from mechanisms import ambiguity_effect as mechanism


POSITIVE = {
    "known_probability": 0.55,
    "ambiguous_probability_min": 0.30,
    "ambiguous_probability_max": 0.90,
    "success_payoff": 10.0,
    "failure_payoff": 0.0,
}
BOUNDARY = {
    "known_probability": 0.55,
    "ambiguous_probability_min": 0.60,
    "ambiguous_probability_max": 0.60,
    "success_payoff": 10.0,
    "failure_payoff": 0.0,
}


def context(data, state=None):
    return {
        **deepcopy(data),
        "state": {} if state is None else state,
        "peer_states": [],
        "round_index": 0,
        "agent_index": 0,
        "uniform": 0.5,
    }


def test_positive_interval_changes_choice_with_task_specific_eu_oracle():
    result = mechanism.evaluate(context(POSITIVE), 0.8)
    # Reference: ambiguous midpoint EU=6.0 versus known EU=5.5.
    # At strength .8, adjusted p=.2*.6+.8*.3=.36, giving EU=3.6.
    assert result["state"]["last_reference_choice"] == 1
    assert result["state"]["last_adjusted_ambiguous_probability"] == pytest.approx(0.36)
    assert result["state"]["last_ambiguous_expected_utility"] == pytest.approx(3.6)
    assert result["state"]["last_known_expected_utility"] == pytest.approx(5.5)
    assert result["metric"] == 0.0
    assert result["active"] is True
    assert "interval=[0.3,0.9]" in result["trace"][0]


def test_collapsed_interval_boundary_matches_strength_zero_reference():
    baseline = mechanism.evaluate(context(BOUNDARY), 0.0)
    effect = mechanism.evaluate(context(BOUNDARY), 0.8)
    assert baseline["metric"] == 1.0
    assert effect["metric"] == baseline["metric"]
    assert effect["active"] is False
    assert effect["state"]["last_ambiguous_expected_utility"] == pytest.approx(6.0)


def test_zero_strength_is_explicit_midpoint_expected_utility_reference():
    result = mechanism.evaluate(context(POSITIVE), 0.0)
    assert result["metric"] == 1.0
    assert result["state"]["last_ambiguous_expected_utility"] == pytest.approx(6.0)
    assert result["state"]["last_known_expected_utility"] == pytest.approx(5.5)
    assert result["state"]["last_adjusted_ambiguous_probability"] == pytest.approx(0.6)
    assert result["active"] is False


def test_missing_invalid_and_impossible_inputs_are_rejected():
    with pytest.raises(ValueError, match="known_probability is required"):
        mechanism.evaluate(context({}), 0.8)
    missing = deepcopy(POSITIVE)
    del missing["ambiguous_probability_max"]
    with pytest.raises(ValueError, match="ambiguous_probability_max is required"):
        mechanism.evaluate(context(missing), 0.8)
    for field, value in (("known_probability", 1.1), ("ambiguous_probability_min", float("nan")), ("success_payoff", True)):
        invalid = deepcopy(POSITIVE)
        invalid[field] = value
        with pytest.raises(ValueError):
            mechanism.evaluate(context(invalid), 0.8)
    reversed_interval = deepcopy(POSITIVE)
    reversed_interval["ambiguous_probability_min"] = 0.91
    with pytest.raises(ValueError, match="must not exceed"):
        mechanism.evaluate(context(reversed_interval), 0.8)
    reversed_outcomes = deepcopy(POSITIVE)
    reversed_outcomes["success_payoff"] = -1
    with pytest.raises(ValueError, match="success_payoff"):
        mechanism.evaluate(context(reversed_outcomes), 0.8)


def test_determinism_nonmutation_and_nested_state_preservation():
    supplied = context(POSITIVE, {"notes": {"tags": ["retained"]}})
    before = deepcopy(supplied)
    first = mechanism.evaluate(supplied, 0.8)
    second = mechanism.evaluate(supplied, 0.8)
    assert supplied == before
    assert first == second
    assert first["state"]["notes"] == {"tags": ["retained"]}
    assert first["state"] is not supplied["state"]
    assert first["state"]["notes"] is not supplied["state"]["notes"]
    assert isinstance(first["metric"], (int, float))
    assert first["trace"] and isinstance(first["trace"][0], str)


def test_strength_validation_and_state_validation():
    for invalid in (-0.01, 1.01, float("nan"), float("inf"), True):
        with pytest.raises(ValueError, match="strength"):
            mechanism.evaluate(context(POSITIVE), invalid)
    with pytest.raises(ValueError, match="state"):
        mechanism.evaluate({**POSITIVE, "state": []}, 0.5)


def test_scenarios_supply_positive_decrease_and_boundary_equivalence():
    scenarios = {item["name"]: item for item in mechanism.scenarios()}
    assert {"positive", "boundary"} <= scenarios.keys()
    positive = scenarios["positive"]
    boundary = scenarios["boundary"]
    assert positive["expectation"] == "decrease"
    assert boundary["expectation"] == "equal"
    assert mechanism.evaluate(context(positive["contexts"][0]), 0.8)["metric"] < mechanism.evaluate(context(positive["contexts"][0]), 0.0)["metric"]
    assert mechanism.evaluate(context(boundary["contexts"][0]), 0.8)["metric"] == mechanism.evaluate(context(boundary["contexts"][0]), 0.0)["metric"]
