from copy import deepcopy

import pytest

from mechanisms import reactive_devaluation as rd


POSITIVE = {
    "proposal_utility": 0.78,
    "status_quo_utility": 0.45,
    "source_dislike": 0.90,
    "credible_risk": 0.08,
}


def run(context, strength, state=None):
    """Direct one-step task invocation with runner-style reserved defaults."""
    supplied = deepcopy(context)
    supplied.update({"state": deepcopy(state or {}), "peer_states": [], "round_index": 0,
                     "agent_index": 0, "uniform": 0.5})
    return rd.evaluate(supplied, strength)


def test_numeric_choice_oracle_and_separate_risk_calculation():
    # Baseline value=.70, source penalty=.8*.5*.9=.36, adjusted=.34 < .45.
    out = run(POSITIVE, 0.8)
    assert out["state"]["last_reference_choice"] == 1
    assert out["state"]["last_adjusted_score"] == pytest.approx(0.34)
    assert out["metric"] == 0.0
    assert out["active"] is True


def test_positive_scenario_lowers_acceptance_vs_strength_zero():
    scenario = rd.scenarios()[0]
    context = scenario["contexts"][0]
    assert scenario["expectation"] == "decrease"
    assert run(context, 0.8)["metric"] < run(context, 0.0)["metric"]


def test_boundary_removes_source_dislike_condition_and_matches_reference():
    scenario = rd.scenarios()[1]
    context = scenario["contexts"][0]
    assert scenario["expectation"] == "equal"
    assert context["source_dislike"] == 0.0
    assert run(context, 0.8)["metric"] == run(context, 0.0)["metric"] == 1.0
    assert run(context, 0.8)["active"] is False


def test_strength_zero_is_explicit_source_neutral_reference():
    out = run(POSITIVE, 0.0)
    assert out["metric"] == 1.0
    assert out["state"]["last_adjusted_score"] == pytest.approx(0.70)
    assert out["active"] is False


def test_missing_and_invalid_phase_inputs_are_rejected():
    missing = dict(POSITIVE)
    del missing["credible_risk"]
    with pytest.raises(ValueError, match="credible_risk"):
        run(missing, 0.8)
    for key, value in [("source_dislike", 1.1), ("proposal_utility", float("nan")),
                       ("credible_risk", True), ("status_quo_utility", "0.4")]:
        invalid = dict(POSITIVE, **{key: value})
        with pytest.raises(ValueError, match=key):
            run(invalid, 0.8)
    for invalid_strength in (-0.1, 1.1, float("inf"), True):
        with pytest.raises(ValueError, match="strength"):
            run(POSITIVE, invalid_strength)


def test_determinism_and_nonmutation_of_nested_context_and_prior_state():
    context = dict(POSITIVE, evidence={"source_record": ["explicit hypothetical attribution"]})
    state = {"older": {"choices": [1, 0]}}
    before_context, before_state = deepcopy(context), deepcopy(state)
    first = run(context, 0.8, state)
    second = run(context, 0.8, state)
    assert first == second
    assert context == before_context
    assert state == before_state
    assert first["state"]["older"] == state["older"]


def test_substantive_risk_can_decide_rejection_with_no_source_penalty():
    context = dict(POSITIVE, source_dislike=0.0, credible_risk=0.40)
    out = run(context, 0.8)
    assert out["metric"] == 0.0
    assert out["state"]["last_reference_choice"] == 0
    assert out["active"] is False
