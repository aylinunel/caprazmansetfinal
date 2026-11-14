from copy import deepcopy

import pytest

from mechanisms import episodic_framing


def make_context(**overrides):
    context = {
        "context_budget": 100.0,
        "event_relevance": 3.0,
        "structural_relevance": 2.0,
        "single_event_focus": True,
        "structural_cause_evidence": True,
        "state": {},
        "peer_states": [],
        "round_index": 0,
        "agent_index": 0,
        "uniform": 0.5,
    }
    context.update(overrides)
    return context


def test_positive_condition_reduces_structural_allocation_with_numeric_oracle():
    context = make_context()
    result = episodic_framing.evaluate(context, 0.8)
    # E' = 3*(1+.8) = 5.4, so 100*2/(2+5.4) = 27.027...
    assert result["metric"] == pytest.approx(2000 / 74)
    reference = episodic_framing.evaluate(context, 0.0)["metric"]
    assert result["metric"] < reference
    assert result["active"] is True


def test_removing_single_event_necessary_condition_matches_reference():
    context = make_context(single_event_focus=False)
    result = episodic_framing.evaluate(context, 0.8)
    reference = episodic_framing.evaluate(context, 0.0)
    assert result["metric"] == pytest.approx(reference["metric"])
    assert result["active"] is False


def test_removing_causal_structure_evidence_matches_reference():
    context = make_context(structural_cause_evidence=False)
    result = episodic_framing.evaluate(context, 0.8)
    reference = episodic_framing.evaluate(context, 0.0)
    assert result["metric"] == pytest.approx(reference["metric"])
    assert result["active"] is False


def test_zero_strength_reproduces_proportional_reference_rule():
    result = episodic_framing.evaluate(make_context(), 0.0)
    assert result["metric"] == pytest.approx(100 * 2 / (2 + 3))
    assert result["state"]["last_reference_units"] == pytest.approx(40.0)
    assert result["active"] is False


def test_missing_or_impossible_evidence_is_rejected():
    missing = make_context()
    del missing["structural_cause_evidence"]
    with pytest.raises(ValueError, match="missing required evidence"):
        episodic_framing.evaluate(missing, 0.8)
    with pytest.raises(ValueError, match="event_relevance"):
        episodic_framing.evaluate(make_context(event_relevance=float("nan")), 0.8)
    with pytest.raises(ValueError, match="single_event_focus"):
        episodic_framing.evaluate(make_context(single_event_focus=1), 0.8)
    with pytest.raises(ValueError, match="strength"):
        episodic_framing.evaluate(make_context(), 1.01)


def test_determinism_nonmutation_and_chronological_state_carry():
    initial = {
        "steps": 2,
        "cumulative_structural_units": 10.0,
        "last_structural_units": 4.0,
        "last_reference_units": 5.0,
        "other_note": "preserve me",
    }
    context = make_context(state=initial)
    snapshot = deepcopy(context)
    first = episodic_framing.evaluate(context, 0.8)
    second = episodic_framing.evaluate(context, 0.8)
    assert first == second
    assert context == snapshot
    assert first["state"]["steps"] == 3
    assert first["state"]["cumulative_structural_units"] == pytest.approx(10 + first["metric"])
    assert first["state"]["other_note"] == "preserve me"

    next_context = make_context(state=first["state"], round_index=1)
    next_result = episodic_framing.evaluate(next_context, 0.8)
    assert next_result["state"]["steps"] == 4
    assert next_result["state"]["cumulative_structural_units"] == pytest.approx(
        first["state"]["cumulative_structural_units"] + next_result["metric"]
    )
