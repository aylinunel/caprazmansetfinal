from copy import deepcopy

import pytest

from mechanisms import delegation_creep


def run_sequence(contexts, strength, initial_state=None):
    state = deepcopy(initial_state or {})
    result = None
    for round_index, task in enumerate(contexts):
        context = deepcopy(task)
        context.update(
            state=state,
            peer_states=[],
            round_index=round_index,
            agent_index=0,
            uniform=0.5,
        )
        result = delegation_creep.evaluate(context, strength)
        state = result["state"]
    return result


def test_positive_temporal_expansion_numeric_oracle():
    positive = next(s for s in delegation_creep.scenarios() if s["name"] == "positive")
    at_zero = run_sequence(positive["contexts"], 0.0, positive["initial_state"])
    at_eight = run_sequence(positive["contexts"], 0.8, positive["initial_state"])
    assert at_zero["metric"] == pytest.approx(2.0)
    assert at_eight["metric"] == pytest.approx(2.8)
    assert at_eight["state"]["unreviewed_expansion_work"] == pytest.approx(0.8)
    assert at_eight["active"] is True


def test_boundary_matches_reference_after_review_removes_unreviewed_condition():
    boundary = next(s for s in delegation_creep.scenarios() if s["name"] == "boundary")
    reference = run_sequence(boundary["contexts"], 0.0, boundary["initial_state"])
    at_eight = run_sequence(boundary["contexts"], 0.8, boundary["initial_state"])
    assert reference["metric"] == pytest.approx(2.0)
    assert at_eight["metric"] == pytest.approx(reference["metric"])
    assert at_eight["active"] is False


def test_zero_strength_is_explicit_review_gated_reference():
    reviewed = {
        "task_domain": "existing",
        "consequence": 0.8,
        "suitability_reviewed": True,
        "suitability_approved": True,
    }
    unreviewed = {
        "task_domain": "new",
        "consequence": 0.9,
        "suitability_reviewed": False,
        "suitability_approved": None,
    }
    first = delegation_creep.evaluate({**reviewed, "state": {}}, 0.0)
    second = delegation_creep.evaluate({**unreviewed, "state": first["state"]}, 0.0)
    assert first["metric"] == pytest.approx(1.0)
    assert second["metric"] == pytest.approx(1.0)
    assert second["state"]["total_opportunities"] == 2


def test_missing_evidence_and_invalid_ranges_raise():
    with pytest.raises(ValueError, match="missing required inputs"):
        delegation_creep.evaluate({"task_domain": "x", "state": {}}, 0.5)
    context = {
        "task_domain": "x",
        "consequence": 1.1,
        "suitability_reviewed": False,
        "suitability_approved": None,
        "state": {},
    }
    with pytest.raises(ValueError, match="consequence"):
        delegation_creep.evaluate(context, 0.5)
    with pytest.raises(ValueError, match="strength"):
        delegation_creep.evaluate({**context, "consequence": 0.5}, float("nan"))


def test_deterministic_and_does_not_mutate_context_or_nested_state():
    context = {
        "task_domain": "new",
        "consequence": 0.9,
        "suitability_reviewed": False,
        "suitability_approved": None,
        "state": {
            "seen_domains": ["old"],
            "approved_delegations": 2,
            "total_opportunities": 2,
            "delegated_work": 2.0,
            "unreviewed_expansion_work": 0.0,
            "annotation": {"keep": [1, 2]},
        },
        "peer_states": [{"nested": [3]}],
        "round_index": 4,
        "agent_index": 7,
        "uniform": 0.5,
    }
    before = deepcopy(context)
    one = delegation_creep.evaluate(context, 0.8)
    two = delegation_creep.evaluate(context, 0.8)
    assert context == before
    assert one == two
    assert one["state"]["annotation"] == {"keep": [1, 2]}
    one["state"]["annotation"]["keep"].append(9)
    assert context["state"]["annotation"] == {"keep": [1, 2]}


def test_unreviewed_nonexpansion_is_not_creep():
    context = {
        "task_domain": "existing",
        "consequence": 0.2,
        "suitability_reviewed": False,
        "suitability_approved": None,
        "state": {
            "seen_domains": ["existing"],
            "approved_delegations": 1,
            "total_opportunities": 1,
            "delegated_work": 1.0,
            "unreviewed_expansion_work": 0.0,
        },
    }
    result = delegation_creep.evaluate(context, 0.8)
    assert result["metric"] == pytest.approx(1.0)
    assert result["active"] is False


def test_strength_validation_rejects_out_of_range():
    context = {
        "task_domain": "x",
        "consequence": 0.4,
        "suitability_reviewed": False,
        "suitability_approved": None,
        "state": {},
    }
    with pytest.raises(ValueError, match="strength"):
        delegation_creep.evaluate(context, 1.01)
