import copy

import pytest

from mechanisms import just_world_hypothesis as mechanism


POSITIVE = {
    "outcome_valence": "adverse",
    "action_consequence_supported": False,
    "attributions": [
        {"label": "structural_misfortune", "evidence_support": 0.4, "says_deserved": False},
        {"label": "victim_deserved_outcome", "evidence_support": 0.1, "says_deserved": True},
    ],
}


def call(context, strength):
    prepared = copy.deepcopy(context)
    prepared.setdefault("state", {"decision_count": 0, "desert_attribution_count": 0, "last_choice": None})
    prepared.setdefault("peer_states", [])
    prepared.setdefault("round_index", 0)
    prepared.setdefault("agent_index", 0)
    prepared.setdefault("uniform", 0.5)
    return mechanism.evaluate(prepared, strength)


def test_positive_numeric_choice_oracle_and_direction():
    baseline = call(POSITIVE, 0.0)
    affected = call(POSITIVE, 0.8)
    assert baseline["metric"] == 0.0
    assert baseline["state"]["last_choice"] == "structural_misfortune"
    # At .8 the desert prior contributes .48, taking the .1-support candidate to .58 > .4.
    assert affected["state"]["last_choice"] == "victim_deserved_outcome"
    assert affected["metric"] == 1.0
    assert affected["metric"] > baseline["metric"]
    assert affected["active"] is True


def test_supported_action_consequence_boundary_matches_reference_metric():
    case = {
        "outcome_valence": "adverse",
        "action_consequence_supported": True,
        "attributions": [
            {"label": "supported_specific_consequence", "evidence_support": 0.8, "says_deserved": False},
            {"label": "victim_deserved_outcome", "evidence_support": 0.1, "says_deserved": True},
        ],
    }
    at_zero = call(case, 0.0)
    at_boundary = call(case, 0.8)
    assert at_boundary["metric"] == at_zero["metric"] == 0.0
    assert at_boundary["state"]["last_choice"] == at_zero["state"]["last_choice"]
    assert at_boundary["active"] is False


def test_zero_strength_is_evidence_support_reference_with_stable_tie_order():
    case = {
        "outcome_valence": "beneficial",
        "action_consequence_supported": False,
        "attributions": [
            {"label": "first", "evidence_support": 0.5, "says_deserved": False},
            {"label": "second", "evidence_support": 0.5, "says_deserved": True},
        ],
    }
    result = call(case, 0.0)
    assert result["state"]["last_choice"] == "first"
    assert result["metric"] == 0.0
    assert result["active"] is False
    assert "Reference choice='first'" in result["trace"][1]


def test_invalid_required_evidence_and_ranges_are_rejected():
    with pytest.raises(ValueError, match="outcome_valence"):
        call({**POSITIVE, "outcome_valence": "unknown"}, 0.8)
    with pytest.raises(ValueError, match="action_consequence_supported"):
        call({**POSITIVE, "action_consequence_supported": None}, 0.8)
    with pytest.raises(ValueError, match="evidence_support"):
        call({**POSITIVE, "attributions": [dict(POSITIVE["attributions"][0], evidence_support=float("nan")), POSITIVE["attributions"][1]]}, 0.8)
    with pytest.raises(ValueError, match="attributions"):
        call({**POSITIVE, "attributions": []}, 0.8)
    with pytest.raises(ValueError, match="strength"):
        call(POSITIVE, 1.01)


def test_deterministic_and_nonmutating_for_nested_context_and_state():
    initial_state = {"decision_count": 3, "desert_attribution_count": 1, "last_choice": "previous"}
    case = copy.deepcopy(POSITIVE)
    case["state"] = initial_state
    before = copy.deepcopy(case)
    first = mechanism.evaluate(case, 0.8)
    second = mechanism.evaluate(case, 0.8)
    assert case == before
    assert initial_state == {"decision_count": 3, "desert_attribution_count": 1, "last_choice": "previous"}
    assert first == second
    assert first["state"] == {
        "decision_count": 4,
        "desert_attribution_count": 2,
        "last_choice": "victim_deserved_outcome",
    }


def test_scenario_contract_has_positive_and_boundary_with_expected_behavior():
    cases = {scenario["name"]: scenario for scenario in mechanism.scenarios()}
    assert set(cases) >= {"positive", "boundary"}
    for name, direction in (("positive", "increase"), ("boundary", "equal")):
        scenario = cases[name]
        assert scenario["expectation"] == direction
        assert scenario["contexts"]
        reference = call(scenario["contexts"][0], 0.0)
        result = call(scenario["contexts"][0], 0.8)
        if direction == "increase":
            assert result["metric"] > reference["metric"]
        else:
            assert result["metric"] == reference["metric"]
