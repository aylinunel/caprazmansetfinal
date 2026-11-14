from copy import deepcopy

import pytest

from mechanisms import accountability_diffusion_in_ai as mechanism


INITIAL = {"task_count": 0, "unresolved_count": 0, "owner_history": [], "last_owner": None}


def run(contexts, strength, initial=None, uniform=0.5):
    state = deepcopy(INITIAL if initial is None else initial)
    outputs = []
    for round_index, task in enumerate(contexts):
        context = deepcopy(task)
        context.update(
            state=deepcopy(state),
            peer_states=[],
            round_index=round_index,
            agent_index=0,
            uniform=uniform,
        )
        result = mechanism.evaluate(context, strength)
        state = result["state"]
        outputs.append(result)
    return outputs


POSITIVE = {
    "action_required": True,
    "stakeholders": [
        {"id": "model_team", "role_fit": 0.9, "decision": "disclaim", "refers_to": "deploy_team"},
        {"id": "deploy_team", "role_fit": 0.7, "decision": "disclaim", "refers_to": None},
    ],
}
BOUNDARY = {
    "action_required": True,
    "stakeholders": [
        {"id": "model_team", "role_fit": 0.9, "decision": "accept"},
        {"id": "deploy_team", "role_fit": 0.7, "decision": "accept"},
    ],
}


def test_positive_cascade_leaves_required_action_unowned_at_strength_point_eight():
    baseline = run([POSITIVE], 0.0)[-1]
    diffused = run([POSITIVE], 0.8)[-1]
    assert baseline["state"]["last_owner"] == "model_team"  # role-fit argmax reference
    assert baseline["metric"] == 0.0
    assert diffused["metric"] == 1.0  # numeric task-specific oracle: terminal disclaimers -> unowned
    assert diffused["state"]["last_owner"] is None
    assert diffused["state"]["unresolved_count"] == 1
    assert diffused["active"] is True


def test_boundary_without_disclaimers_matches_reference_metric():
    baseline = run([BOUNDARY], 0.0)[-1]
    at_strength = run([BOUNDARY], 0.8)[-1]
    assert baseline["metric"] == 0.0
    assert at_strength["metric"] == baseline["metric"]
    assert at_strength["state"]["last_owner"] == "model_team"
    assert at_strength["active"] is False


def test_zero_strength_uses_role_fit_reference_even_if_lead_disclaims():
    result = run([POSITIVE], 0.0)[-1]
    assert result["metric"] == 0.0
    assert result["state"]["last_owner"] == "model_team"
    assert "role-based reference lead 'model_team' retained" in result["trace"][2]


def test_explicit_referral_to_accepting_stakeholder_changes_owner_but_not_metric():
    task = {
        "action_required": True,
        "stakeholders": [
            {"id": "builder", "role_fit": 0.8, "decision": "disclaim", "refers_to": "operator"},
            {"id": "operator", "role_fit": 0.6, "decision": "accept"},
        ],
    }
    result = run([task], 0.8)[-1]
    assert result["metric"] == 0.0
    assert result["state"]["last_owner"] == "operator"
    assert result["active"] is True


def test_chronological_state_accumulates_tasks_and_keeps_complete_history():
    outputs = run([POSITIVE, BOUNDARY], 0.8)
    state = outputs[-1]["state"]
    assert outputs[0]["metric"] == 1.0
    assert outputs[1]["metric"] == 0.0
    assert state == {
        "task_count": 2,
        "unresolved_count": 1,
        "owner_history": [None, "model_team"],
        "last_owner": "model_team",
    }


def test_evaluation_is_deterministic_and_does_not_mutate_input_or_nested_state():
    context = deepcopy(POSITIVE)
    context.update(
        state=deepcopy(INITIAL), peer_states=[{"neighbor": {"tag": "unchanged"}}],
        round_index=0, agent_index=2, uniform=0.5,
    )
    before = deepcopy(context)
    first = mechanism.evaluate(context, 0.8)
    second = mechanism.evaluate(context, 0.8)
    assert context == before
    assert first == second
    assert first["metric"] == 1.0


def test_missing_or_impossible_task_evidence_is_rejected_not_scored_as_zero():
    context = {"action_required": True, "stakeholders": []}
    context.update(state=deepcopy(INITIAL), peer_states=[], round_index=0, agent_index=0, uniform=0.5)
    with pytest.raises(ValueError, match="non-empty"):
        mechanism.evaluate(context, 0.8)
    context["stakeholders"] = deepcopy(BOUNDARY["stakeholders"])
    context["action_required"] = False
    with pytest.raises(ValueError, match="must be true"):
        mechanism.evaluate(context, 0.8)


def test_invalid_strength_and_missing_disclaimer_referral_are_rejected():
    context = deepcopy(POSITIVE)
    context.update(state=deepcopy(INITIAL), peer_states=[], round_index=0, agent_index=0, uniform=0.5)
    with pytest.raises(ValueError, match="strength"):
        mechanism.evaluate(context, float("nan"))
    context["stakeholders"][0].pop("refers_to")
    with pytest.raises(ValueError, match="explicitly provide refers_to"):
        mechanism.evaluate(context, 0.8)
