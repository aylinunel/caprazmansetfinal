from copy import deepcopy

import pytest

from mechanisms import contextual_omission


def make_context(**overrides):
    context = {
        "base_comparison": 12.0,
        "full_text_available": True,
        "evidence": [
            {
                "id": "denominator_context",
                "adjustment": -8.0,
                "accessible": True,
                "relevant": True,
                "counter_evidence": True,
                "included": False,
            }
        ],
        "state": {"comparison_history": [], "cumulative_omitted_adjustment": 0.0},
        "peer_states": [],
        "round_index": 0,
        "agent_index": 0,
        "uniform": 0.5,
    }
    context.update(overrides)
    return context


def run_contexts(contexts, strength, initial_state=None):
    state = deepcopy(initial_state or {"comparison_history": [], "cumulative_omitted_adjustment": 0.0})
    result = None
    for round_index, raw in enumerate(contexts):
        current = deepcopy(raw)
        current.update(
            state=state,
            peer_states=[],
            round_index=round_index,
            agent_index=0,
            uniform=0.5,
        )
        result = contextual_omission.evaluate(current, strength)
        state = result["state"]
    return result


def test_positive_numeric_oracle_and_direction():
    context = make_context()
    reference = contextual_omission.evaluate(context, 0.0)
    affected = contextual_omission.evaluate(context, 0.8)

    # Full-text contrast is 12 + (-8) = 4; at .8, reader contrast is 4 - .8*(-8) = 10.4.
    assert reference["metric"] == pytest.approx(4.0)
    assert affected["metric"] == pytest.approx(10.4)
    assert affected["metric"] > reference["metric"]
    assert affected["active"] is True
    assert affected["state"]["comparison_history"][0]["omitted_counter_evidence_ids"] == ["denominator_context"]


def test_boundary_without_relevant_counter_evidence_matches_reference():
    boundary = contextual_omission.scenarios()[1]["contexts"]
    reference = run_contexts(boundary, 0.0)
    at_strength = run_contexts(boundary, 0.8)

    assert reference["metric"] == pytest.approx(12.0)
    assert at_strength["metric"] == pytest.approx(reference["metric"])
    assert at_strength["active"] is False


def test_strength_zero_is_explicit_full_text_reference():
    result = contextual_omission.evaluate(make_context(), 0)
    assert result["metric"] == pytest.approx(12.0 - 8.0)
    assert "strength zero is the full-text reference" in result["trace"][3]


def test_missing_or_incomplete_evidence_is_rejected_not_scored_as_zero():
    with pytest.raises(ValueError, match="full_text_available"):
        contextual_omission.evaluate(make_context(full_text_available=False), 0.8)
    with pytest.raises(ValueError, match="non-empty list"):
        contextual_omission.evaluate(make_context(evidence=[]), 0.8)
    no_accessible = make_context(
        evidence=[{
            "id": "inaccessible",
            "adjustment": -8.0,
            "accessible": False,
            "relevant": True,
            "counter_evidence": True,
            "included": False,
        }]
    )
    with pytest.raises(ValueError, match="no accessible relevant context"):
        contextual_omission.evaluate(no_accessible, 0.8)


def test_strength_and_numeric_ranges_are_validated():
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        contextual_omission.evaluate(make_context(), 1.01)
    with pytest.raises(ValueError, match="finite"):
        contextual_omission.evaluate(make_context(), float("nan"))
    with pytest.raises(ValueError, match="base_comparison"):
        contextual_omission.evaluate(make_context(base_comparison=float("inf")), 0.5)


def test_deterministic_and_does_not_mutate_input_or_nested_values():
    context = make_context()
    context["state"]["comparison_history"] = [{"prior": {"label": "unchanged"}}]
    before = deepcopy(context)

    first = contextual_omission.evaluate(context, 0.8)
    second = contextual_omission.evaluate(context, 0.8)

    assert context == before
    assert first == second
    assert first["state"]["comparison_history"][0] == {"prior": {"label": "unchanged"}}
    first["state"]["comparison_history"][0]["prior"]["label"] = "changed output only"
    assert context == before


def test_chronological_state_carries_observations_without_extra_steps():
    contexts = [make_context(), make_context(base_comparison=20.0)]
    result = run_contexts(contexts, 0.5)

    assert len(result["state"]["comparison_history"]) == 2
    assert [item["round_index"] for item in result["state"]["comparison_history"]] == [0, 1]
    assert result["metric"] == pytest.approx(16.0)  # 12 - .5*(-8)
    assert result["state"]["cumulative_omitted_adjustment"] == pytest.approx(-16.0)
    assert result["state"]["last_comparison"] == pytest.approx(16.0)


def test_contract_positive_scenario_has_expected_direction_at_point_8():
    positive = contextual_omission.scenarios()[0]["contexts"]
    reference = run_contexts(positive, 0.0)
    treated = run_contexts(positive, 0.8)
    assert treated["metric"] != pytest.approx(reference["metric"])
    assert treated["metric"] > reference["metric"]
