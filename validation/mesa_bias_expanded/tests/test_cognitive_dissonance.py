from copy import deepcopy
import math

import pytest

from mechanisms import cognitive_dissonance as mechanism


def run(contexts, strength, initial_state=None):
    state = deepcopy(initial_state or {"rounds": 0})
    results = []
    for index, task_input in enumerate(contexts):
        context = deepcopy(task_input)
        context.update(
            state=deepcopy(state),
            peer_states=[],
            round_index=index,
            agent_index=0,
            uniform=0.5,
        )
        result = mechanism.evaluate(context, strength)
        state = result["state"]
        results.append(result)
    return results


def test_positive_conflict_pulls_belief_toward_freely_chosen_action_with_numeric_oracle():
    result = run(mechanism.scenarios()[0]["contexts"], 0.8)[0]
    # b_ref=.12; D=.7*.9*1=.63; displacement=.8*.63*(.9-.12)=.39312.
    assert result["metric"] == pytest.approx(0.51312)
    assert result["metric"] > result["state"]["reference_belief"]
    assert result["state"]["discomfort"] == pytest.approx(0.63)
    assert result["active"] is True


def test_boundary_without_choice_freedom_matches_reference_metric():
    context = mechanism.scenarios()[1]["contexts"]
    at_strength = run(context, 0.8)[0]
    reference = run(context, 0.0)[0]
    assert at_strength["metric"] == pytest.approx(reference["metric"])
    assert at_strength["metric"] == pytest.approx(0.12)
    assert at_strength["active"] is False


def test_zero_strength_reproduces_explicit_evidence_weighted_reference():
    context = mechanism.scenarios()[0]["contexts"]
    result = run(context, 0.0)[0]
    assert result["metric"] == pytest.approx((1 - 0.8) * 0.2 + 0.8 * 0.1)
    assert result["state"]["resolution_shift"] == pytest.approx(0.0)
    assert result["active"] is False


def test_missing_evidence_and_impossible_values_are_rejected():
    base = mechanism.scenarios()[0]["contexts"][0]
    without_evidence = dict(base)
    del without_evidence["evidence_position"]
    with pytest.raises(ValueError, match="evidence_position"):
        mechanism.evaluate(without_evidence, 0.8)
    impossible = dict(base, evidence_weight=1.2)
    with pytest.raises(ValueError, match="evidence_weight"):
        mechanism.evaluate(impossible, 0.8)
    with pytest.raises(ValueError, match="strength"):
        mechanism.evaluate(base, math.inf)


def test_evaluation_is_deterministic_and_does_not_mutate_nested_context():
    context = mechanism.scenarios()[0]["contexts"][0]
    context = dict(context, state={"rounds": 2, "history": [{"tag": "keep"}]})
    before = deepcopy(context)
    first = mechanism.evaluate(context, 0.8)
    second = mechanism.evaluate(context, 0.8)
    assert first == second
    assert context == before
    assert first["state"]["rounds"] == 3
    first["state"]["history"][0]["tag"] = "changed"
    assert context["state"]["history"][0]["tag"] == "keep"


def test_sequential_calls_carry_complete_state_without_inventing_extra_rounds():
    first_input = mechanism.scenarios()[0]["contexts"][0]
    second_input = dict(first_input, prior_belief=0.51312)
    results = run([first_input, second_input], 0.8)
    assert len(results) == 2
    assert results[-1]["state"]["rounds"] == 2
    assert results[-1]["state"]["prior_belief"] == pytest.approx(0.51312)
    assert math.isfinite(results[-1]["metric"])


def test_strength_bounds_and_context_types_are_validated():
    base = mechanism.scenarios()[0]["contexts"][0]
    with pytest.raises(ValueError, match="strength"):
        mechanism.evaluate(base, -0.01)
    with pytest.raises(ValueError, match="prior_belief"):
        mechanism.evaluate(dict(base, prior_belief=True), 0.5)
    with pytest.raises(ValueError, match="context"):
        mechanism.evaluate([], 0.5)
