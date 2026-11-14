from copy import deepcopy

import pytest

from mechanisms import availability_heuristic as mechanism


POSITIVE = {
    "cases": [
        {"event": True, "recall_ease": 1.0},
        {"event": False, "recall_ease": 0.1},
        {"event": False, "recall_ease": 0.1},
        {"event": False, "recall_ease": 0.1},
    ]
}
BOUNDARY = {
    "cases": [
        {"event": True, "recall_ease": 0.7},
        {"event": False, "recall_ease": 0.7},
        {"event": False, "recall_ease": 0.7},
        {"event": False, "recall_ease": 0.7},
    ]
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


def test_positive_accessibility_substitution_has_numeric_probability_oracle():
    result = mechanism.evaluate(context(POSITIVE), 0.8)
    evidence_rate = 1 / 4
    availability_rate = 1.0 / (1.0 + 0.1 + 0.1 + 0.1)
    expected = 0.2 * evidence_rate + 0.8 * availability_rate
    assert result["metric"] == pytest.approx(expected)
    assert result["metric"] > evidence_rate
    assert result["active"] is True
    assert result["state"]["last_judgment"] == pytest.approx(expected)
    assert result["trace"] and "accessibility-weighted frequency" in result["trace"][0]


def test_boundary_equal_accessibility_matches_strength_zero_reference():
    reference = mechanism.evaluate(context(BOUNDARY), 0.0)
    boundary = mechanism.evaluate(context(BOUNDARY), 0.8)
    assert reference["metric"] == pytest.approx(0.25)
    assert boundary["metric"] == pytest.approx(reference["metric"])
    assert boundary["active"] is False


def test_zero_strength_is_observed_frequency_reference():
    result = mechanism.evaluate(context(POSITIVE), 0.0)
    assert result["metric"] == pytest.approx(0.25)
    assert result["active"] is False
    assert result["state"]["last_evidence_rate"] == pytest.approx(0.25)
    assert result["state"]["last_availability_rate"] == pytest.approx(10 / 13)


def test_missing_or_impossible_evidence_is_rejected():
    with pytest.raises(ValueError, match="cases"):
        mechanism.evaluate(context({}), 0.8)
    with pytest.raises(ValueError, match="recall_ease"):
        mechanism.evaluate(context({"cases": [{"event": True}]}), 0.8)
    with pytest.raises(ValueError, match="at least one recall-accessible"):
        mechanism.evaluate(
            context({"cases": [{"event": True, "recall_ease": 0.0}]}), 0.8
        )
    with pytest.raises(ValueError, match="event must be a boolean"):
        mechanism.evaluate(
            context({"cases": [{"event": 1, "recall_ease": 0.5}]}), 0.8
        )


def test_determinism_nonmutation_and_state_preservation():
    previous_state = {"prior_note": {"keep": ["unchanged"]}}
    supplied = context(POSITIVE, previous_state)
    before = deepcopy(supplied)
    first = mechanism.evaluate(supplied, 0.8)
    second = mechanism.evaluate(supplied, 0.8)
    assert supplied == before
    assert first == second
    assert first["state"]["prior_note"] == previous_state["prior_note"]
    assert first["state"] is not supplied["state"]
    assert first["state"]["prior_note"] is not supplied["state"]["prior_note"]


def test_strength_must_be_finite_and_in_unit_interval():
    for invalid in (-0.01, 1.01, float("nan"), float("inf"), True):
        with pytest.raises(ValueError, match="strength"):
            mechanism.evaluate(context(POSITIVE), invalid)


def test_scenarios_provide_required_positive_and_boundary_contract_cases():
    scenarios = {scenario["name"]: scenario for scenario in mechanism.scenarios()}
    assert set(("positive", "boundary")) <= set(scenarios)
    positive = scenarios["positive"]
    boundary = scenarios["boundary"]
    assert len(positive["contexts"]) >= 1 and positive["expectation"] == "increase"
    assert len(boundary["contexts"]) >= 1 and boundary["expectation"] == "equal"
    base = mechanism.evaluate(context(positive["contexts"][0]), 0.0)["metric"]
    effect = mechanism.evaluate(context(positive["contexts"][0]), 0.8)["metric"]
    boundary_base = mechanism.evaluate(context(boundary["contexts"][0]), 0.0)["metric"]
    boundary_effect = mechanism.evaluate(context(boundary["contexts"][0]), 0.8)["metric"]
    assert effect > base
    assert boundary_effect == pytest.approx(boundary_base)
