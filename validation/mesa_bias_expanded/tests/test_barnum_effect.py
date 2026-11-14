import copy
import math

import pytest

from mechanisms import barnum_effect


BASE = {
    "agreement": True,
    "description_vagueness": 0.9,
    "population_applicability": 0.9,
    "perceived_personal_specificity": 0.9,
    "verified_individual_fit": 0.2,
}


def evaluate(data, strength, state=None):
    context = copy.deepcopy(data)
    context.update(
        state={} if state is None else copy.deepcopy(state),
        peer_states=[],
        round_index=0,
        agent_index=0,
        uniform=0.5,
    )
    return barnum_effect.evaluate(context, strength)


def test_positive_cue_has_numeric_oracle_and_crosses_unique_choice_threshold():
    result = evaluate(BASE, 0.8)
    # Reference=.2; cue=.9*.9*.9=.729; .2 + .8*.729*(1-.2).
    assert result["metric"] == pytest.approx(0.66656)
    assert result["metric"] >= 0.5
    assert result["state"]["accepted_unique_count"] == 1
    assert result["active"] is True
    assert math.isfinite(result["metric"])


def test_specificity_boundary_matches_strength_zero_reference():
    boundary = {**BASE, "perceived_personal_specificity": 0.4}
    biased = evaluate(boundary, 0.8)
    reference = evaluate(boundary, 0.0)
    assert biased["metric"] == reference["metric"] == 0.2
    assert biased["active"] is False


def test_zero_strength_is_explicit_verified_fit_reference():
    result = evaluate(BASE, 0.0)
    assert result["metric"] == 0.2
    assert result["active"] is False
    assert result["state"] == {
        "evaluations": 1,
        "last_unique_attribution": 0.2,
        "accepted_unique_count": 0,
    }


def test_general_agreement_without_perceived_specificity_is_not_barnum_effect():
    general = {**BASE, "perceived_personal_specificity": 0.0, "verified_individual_fit": 0.0}
    result = evaluate(general, 1.0)
    assert result["metric"] == 0.0
    assert result["active"] is False


def test_missing_required_evidence_is_rejected_not_scored_as_zero():
    incomplete = dict(BASE)
    del incomplete["perceived_personal_specificity"]
    with pytest.raises(ValueError, match="missing required input"):
        evaluate(incomplete, 0.8)


@pytest.mark.parametrize("strength", [-0.01, 1.01, float("nan"), float("inf")])
def test_invalid_strength_is_rejected(strength):
    with pytest.raises(ValueError, match="strength"):
        evaluate(BASE, strength)


def test_nonfinite_and_wrong_type_ratings_are_rejected():
    for value in (float("nan"), 1.1, True, "0.9"):
        bad = {**BASE, "description_vagueness": value}
        with pytest.raises(ValueError, match="description_vagueness"):
            evaluate(bad, 0.8)


def test_determinism_and_nonmutation_with_nested_prior_state():
    state = {"evaluations": 3, "last_unique_attribution": 0.1,
             "accepted_unique_count": 0, "annotation": {"tags": ["kept"]}}
    data = copy.deepcopy(BASE)
    context_before = copy.deepcopy(data)
    state_before = copy.deepcopy(state)
    first = evaluate(data, 0.8, state)
    second = evaluate(data, 0.8, state)
    assert first == second
    assert data == context_before
    assert state == state_before
    assert first["state"]["evaluations"] == 4
    assert first["state"]["annotation"] == {"tags": ["kept"]}
    first["state"]["annotation"]["tags"].append("local")
    assert state["annotation"]["tags"] == ["kept"]


def test_scenario_definitions_express_positive_and_necessary_condition_boundary():
    by_name = {scenario["name"]: scenario for scenario in barnum_effect.scenarios()}
    assert set(by_name) == {"positive", "boundary"}
    assert by_name["positive"]["expectation"] == "increase"
    assert by_name["boundary"]["expectation"] == "equal"
    assert by_name["boundary"]["contexts"][0]["perceived_personal_specificity"] < 0.5
