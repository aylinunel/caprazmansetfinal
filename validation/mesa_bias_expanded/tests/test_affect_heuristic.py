from copy import deepcopy

import pytest

from mechanisms import affect_heuristic as mechanism


POSITIVE = {
    "decision_frame": "factual_evaluation",
    "options": [
        {"id": "steady", "benefit": 0.7, "risk": 0.1, "affect": -0.8, "preference_score": 0.4},
        {"id": "thrilling", "benefit": 0.5, "risk": 0.4, "affect": 0.9, "preference_score": 0.8},
    ],
}
BOUNDARY = {
    "decision_frame": "subjective_preference",
    "options": [
        {"id": "calm", "benefit": 0.7, "risk": 0.1, "affect": -0.9, "preference_score": 0.9},
        {"id": "thrilling", "benefit": 0.5, "risk": 0.4, "affect": 0.9, "preference_score": 0.2},
    ],
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


def test_positive_affect_substitution_changes_choice_with_numeric_oracle():
    result = mechanism.evaluate(context(POSITIVE), 0.8)
    # Blended score: steady=.2*.6+.8*(-.8)=-.52;
    # thrilling=.2*.1+.8*.9=.74. Metric is selected factual utility.
    assert result["state"]["last_choice"] == "thrilling"
    assert result["metric"] == pytest.approx(0.1)
    assert result["metric"] < 0.6  # reference utility of steady
    assert result["active"] is True
    assert "(1-strength)*(benefit-risk)+strength*affect" in result["trace"][0]


def test_subjective_preference_boundary_matches_reference_at_strength_point_eight():
    reference = mechanism.evaluate(context(BOUNDARY), 0.0)
    boundary = mechanism.evaluate(context(BOUNDARY), 0.8)
    assert reference["state"]["last_choice"] == "calm"
    assert reference["metric"] == pytest.approx(0.9)
    assert boundary["metric"] == pytest.approx(reference["metric"])
    assert boundary["state"]["last_choice"] == reference["state"]["last_choice"]
    assert boundary["active"] is False


def test_zero_strength_is_explicit_maximum_benefit_minus_risk_reference():
    result = mechanism.evaluate(context(POSITIVE), 0.0)
    assert result["state"]["last_choice"] == "steady"
    assert result["metric"] == pytest.approx(0.7 - 0.1)
    assert result["active"] is False
    assert result["state"]["last_frame"] == "factual_evaluation"


def test_missing_or_out_of_range_task_evidence_is_rejected():
    with pytest.raises(ValueError, match="decision_frame"):
        mechanism.evaluate(context({"options": POSITIVE["options"]}), 0.8)
    with pytest.raises(ValueError, match="options"):
        mechanism.evaluate(context({"decision_frame": "factual_evaluation", "options": []}), 0.8)
    incomplete = deepcopy(POSITIVE)
    del incomplete["options"][0]["affect"]
    with pytest.raises(ValueError, match=r"options\[0\]\.affect"):
        mechanism.evaluate(context(incomplete), 0.8)
    impossible = deepcopy(POSITIVE)
    impossible["options"][0]["risk"] = 1.2
    with pytest.raises(ValueError, match=r"options\[0\]\.risk"):
        mechanism.evaluate(context(impossible), 0.8)


def test_strength_requires_finite_value_in_unit_interval():
    for strength in (-0.01, 1.01, float("nan"), float("inf"), True):
        with pytest.raises(ValueError, match="strength"):
            mechanism.evaluate(context(POSITIVE), strength)


def test_determinism_nonmutation_and_nested_state_preservation():
    previous_state = {"custom": {"keep": ["unchanged"]}, "decision_history": []}
    supplied = context(POSITIVE, previous_state)
    before = deepcopy(supplied)
    first = mechanism.evaluate(supplied, 0.8)
    second = mechanism.evaluate(supplied, 0.8)
    assert supplied == before
    assert first == second
    assert first["state"]["custom"] == previous_state["custom"]
    assert first["state"]["custom"] is not supplied["state"]["custom"]
    assert first["state"]["decision_history"] == [
        {"frame": "factual_evaluation", "choice": "thrilling", "metric": pytest.approx(0.1)}
    ]


def test_scenario_contract_includes_effect_and_boundary_equivalence():
    scenarios = {item["name"]: item for item in mechanism.scenarios()}
    assert {"positive", "boundary"} <= set(scenarios)
    positive = scenarios["positive"]
    boundary = scenarios["boundary"]
    assert positive["expectation"] == "decrease"
    assert boundary["expectation"] == "equal"
    base = mechanism.evaluate(context(positive["contexts"][0]), 0.0)["metric"]
    effect = mechanism.evaluate(context(positive["contexts"][0]), 0.8)["metric"]
    boundary_base = mechanism.evaluate(context(boundary["contexts"][0]), 0.0)["metric"]
    boundary_effect = mechanism.evaluate(context(boundary["contexts"][0]), 0.8)["metric"]
    assert effect < base
    assert boundary_effect == pytest.approx(boundary_base)
