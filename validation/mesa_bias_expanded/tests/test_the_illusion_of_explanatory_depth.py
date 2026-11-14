from copy import deepcopy

import pytest

from mechanisms import the_illusion_of_explanatory_depth as mechanism


def direct(context, strength, state=None, round_index=0):
    supplied = deepcopy(context)
    supplied.setdefault("state", deepcopy(state or {}))
    supplied.setdefault("peer_states", [])
    supplied.setdefault("round_index", round_index)
    supplied.setdefault("agent_index", 0)
    supplied.setdefault("uniform", 0.5)
    return mechanism.evaluate(supplied, strength)


def test_numeric_oracle_is_specific_to_claimed_vs_explained_depth():
    context = {"mechanism_parts": 8, "explained_parts": 2, "self_assessed_parts": 7}
    result = direct(context, 0.8)
    # Demonstrated=.25; claimed=.875; reported=.25 + .8*(.875-.25)=.75.
    assert result["state"]["last_demonstrated_depth"] == 0.25
    assert result["state"]["last_reported_depth"] == 0.75
    assert result["metric"] == pytest.approx(0.5)
    assert "gap=max(0" in result["trace"][0]
    assert result["active"] is True


def test_positive_scenario_increases_excess_over_strength_zero():
    scenario = mechanism.scenarios()[0]
    context = scenario["contexts"][0]
    reference = direct(context, 0.0)
    intervention = direct(context, 0.8)
    assert scenario["expectation"] == "increase"
    assert reference["metric"] == 0
    assert intervention["metric"] > reference["metric"]


def test_boundary_removes_positive_explanation_depth_gap():
    scenario = mechanism.scenarios()[1]
    context = scenario["contexts"][0]
    assert context["self_assessed_parts"] < context["explained_parts"]
    reference = direct(context, 0.0)
    intervention = direct(context, 0.8)
    assert scenario["expectation"] == "equal"
    assert reference["metric"] == intervention["metric"] == 0
    assert intervention["active"] is False
    assert intervention["state"]["last_reported_depth"] == intervention["state"]["last_demonstrated_depth"]


def test_zero_strength_is_demonstrated_depth_reference_not_perfect_task_claim():
    result = direct({"mechanism_parts": 5, "explained_parts": 3, "self_assessed_parts": 5}, 0.0)
    assert result["state"]["last_reported_depth"] == pytest.approx(0.6)
    assert result["metric"] == 0
    assert result["active"] is False


@pytest.mark.parametrize(
    "context,strength",
    [
        ({"mechanism_parts": 8, "explained_parts": 2}, 0.8),
        ({"mechanism_parts": 0, "explained_parts": 0, "self_assessed_parts": 0}, 0.8),
        ({"mechanism_parts": 8, "explained_parts": 9, "self_assessed_parts": 7}, 0.8),
        ({"mechanism_parts": 8, "explained_parts": 2, "self_assessed_parts": True}, 0.8),
        ({"mechanism_parts": 8, "explained_parts": 2, "self_assessed_parts": 7}, float("nan")),
        ({"mechanism_parts": 8, "explained_parts": 2, "self_assessed_parts": 7}, 1.01),
    ],
)
def test_missing_or_invalid_task_evidence_and_strength_are_rejected(context, strength):
    with pytest.raises(ValueError):
        direct(context, strength)


def test_deterministic_nonmutating_and_state_is_carried_forward():
    context = {
        "mechanism_parts": 10,
        "explained_parts": 4,
        "self_assessed_parts": 9,
        "state": {"rounds": 2, "cumulative_excess": 0.1, "caller_tag": "keep"},
    }
    before = deepcopy(context)
    first = direct(context, 0.5, round_index=2)
    second = direct(context, 0.5, round_index=2)
    assert context == before
    assert first == second
    assert first["state"]["rounds"] == 3
    assert first["state"]["cumulative_excess"] == pytest.approx(0.35)
    assert first["state"]["caller_tag"] == "keep"


def test_scenario_contexts_only_use_common_task_inputs():
    reserved = {"state", "peer_states", "round_index", "agent_index", "uniform"}
    for scenario in mechanism.scenarios():
        assert scenario["contexts"]
        assert all(not reserved.intersection(context) for context in scenario["contexts"])
        assert all(set(mechanism.METADATA["required_inputs"]).issubset(context) for context in scenario["contexts"])
