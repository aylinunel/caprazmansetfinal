from copy import deepcopy

import pytest

from mechanisms import parasocial_trust_in_ai as plugin


BASE = {
    "ai_capability": 0.20,
    "task_requirement": 0.80,
    "task_value": 0.80,
    "disclosure_cost": 0.25,
    "relational_trust": 0.95,
    "interaction_warmth": 0.95,
}


def evaluate(context, strength=0.8, state=None, round_index=0):
    full = dict(context)
    full.update({
        "state": {} if state is None else state,
        "peer_states": [],
        "round_index": round_index,
        "agent_index": 0,
        "uniform": 0.5,
    })
    return plugin.evaluate(full, strength)


def test_numeric_oracle_and_concept_specific_choice():
    result = evaluate(BASE, 0.8)
    # adequacy=.20/.80=.25; reference=.80*.25-.25=-.05.
    # gap=.75; bonus=.8*.95*.95*.75*.8=.4332; adjusted utility=.3832.
    assert result["state"]["last_capability_gap"] == pytest.approx(0.75)
    assert result["state"]["last_relational_bonus"] == pytest.approx(0.4332)
    assert result["metric"] == 1.0
    assert result["active"] is True
    assert "reference utility" in " ".join(result["trace"]).lower()


def test_positive_strength_increases_disclosure_against_reference():
    assert evaluate(BASE, 0.8)["metric"] > evaluate(BASE, 0.0)["metric"]


def test_warmth_without_relational_trust_is_boundary_equal_to_reference():
    boundary = dict(BASE, relational_trust=0.0)
    result = evaluate(boundary, 0.8)
    reference = evaluate(boundary, 0.0)
    assert result["metric"] == reference["metric"] == 0.0
    assert result["active"] is False
    assert result["state"]["last_relational_bonus"] == 0.0


def test_capability_sufficient_boundary_prevents_unsupported_trust_uplift():
    context = dict(BASE, ai_capability=0.80)
    result = evaluate(context, 0.8)
    assert result["state"]["last_capability_gap"] == 0.0
    assert result["state"]["last_relational_bonus"] == 0.0
    assert result["metric"] == evaluate(context, 0.0)["metric"]


def test_zero_strength_is_explicit_reference_choice_and_state_is_complete():
    result = evaluate(BASE, 0.0, {"steps": 2, "sensitive_disclosures": 1})
    assert result["metric"] == 0.0
    assert result["active"] is False
    assert result["state"] == {
        "steps": 3,
        "sensitive_disclosures": 1,
        "last_disclosed": False,
        "last_reference_disclosed": False,
        "last_capability_gap": pytest.approx(0.75),
        "last_relational_bonus": 0.0,
    }


def test_missing_and_invalid_phase_inputs_are_rejected():
    missing = dict(BASE)
    del missing["relational_trust"]
    with pytest.raises(ValueError, match="missing required input"):
        evaluate(missing)
    with pytest.raises(ValueError, match="task_requirement must be greater"):
        evaluate(dict(BASE, task_requirement=0.0))
    with pytest.raises(ValueError, match="finite number"):
        evaluate(dict(BASE, interaction_warmth=float("nan")))
    with pytest.raises(ValueError, match="strength"):
        evaluate(BASE, 1.1)


def test_repeated_evaluation_is_deterministic_and_does_not_mutate_context_or_state():
    initial_state = {"steps": 4, "sensitive_disclosures": 2, "metadata": {"tag": "keep"}}
    context = dict(BASE, state=initial_state, peer_states=[{"x": [1, 2]}],
                   round_index=5, agent_index=3, uniform=0.25)
    before = deepcopy(context)
    first = plugin.evaluate(context, 0.8)
    second = plugin.evaluate(context, 0.8)
    assert first == second
    assert context == before
    assert initial_state == before["state"]
    assert first["state"]["steps"] == 5
    assert first["state"]["sensitive_disclosures"] == 3


def test_chronological_state_carries_decision_count_across_contexts():
    state = {"steps": 0, "sensitive_disclosures": 0}
    for round_index, context in enumerate((BASE, dict(BASE, relational_trust=0.0))):
        result = evaluate(context, 0.8, state, round_index)
        state = result["state"]
    assert state["steps"] == 2
    assert state["sensitive_disclosures"] == 1
    assert state["last_disclosed"] is False
