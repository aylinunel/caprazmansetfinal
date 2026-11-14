from copy import deepcopy

import pytest

from mechanisms import dunning_kruger_effect as mechanism


def run_sequence(contexts, strength, initial_state=None):
    state = deepcopy(initial_state or {})
    result = None
    for index, context in enumerate(contexts):
        result = mechanism.evaluate(
            {
                **deepcopy(context),
                "state": deepcopy(state),
                "peer_states": [],
                "round_index": index,
                "agent_index": 0,
                "uniform": 0.5,
            },
            strength,
        )
        state = result["state"]
    return result


def test_positive_direction_and_expected_review_choice():
    positive = next(s for s in mechanism.scenarios() if s["name"] == "positive")
    reference = run_sequence(positive["contexts"], 0.0, positive["initial_state"])
    effect = run_sequence(positive["contexts"], 0.8, positive["initial_state"])
    assert reference["state"]["last_reviewed_ids"] == ["err-critical-next"]
    assert effect["state"]["last_reviewed_ids"] == ["correct-uncertain-next"]
    assert reference["metric"] == 0.0
    assert effect["metric"] == 1.0
    assert effect["metric"] > reference["metric"]
    assert effect["active"] is True


def test_numeric_priority_oracle_matches_declared_equation():
    positive = next(s for s in mechanism.scenarios() if s["name"] == "positive")
    result = mechanism.evaluate(positive["contexts"][0], 0.8)
    # Accuracy=.25, mean confidence=.75; gate=.5*(.75-.25)=.25.
    # Critical error priority=10*(.1-6*.8*.25*.9)=-9.8.
    # Uncertain correct priority=1*(.8-6*.8*.25*.2)=.56.
    assert "gate=product=0.250000" in result["trace"][0]
    assert result["state"]["last_reviewed_ids"] == ["correct-uncertain"]
    assert result["metric"] == 3.0


def test_boundary_removes_low_competence_and_matches_reference():
    boundary = next(s for s in mechanism.scenarios() if s["name"] == "boundary")
    reference = run_sequence(boundary["contexts"], 0.0)
    effect = run_sequence(boundary["contexts"], 0.8)
    assert reference["state"]["correct_count"] / reference["state"]["attempted"] == 4 / 7
    assert reference["state"]["error_count"] == 3  # Errors remain; low accuracy condition is absent.
    assert reference["metric"] == effect["metric"]
    assert reference["state"]["last_reviewed_ids"] == effect["state"]["last_reviewed_ids"]
    assert effect["active"] is False


def test_strength_zero_is_explicit_value_weighted_uncertainty_reference():
    positive = next(s for s in mechanism.scenarios() if s["name"] == "positive")
    reference = mechanism.evaluate(positive["contexts"][0], 0.0)
    assert reference["state"]["last_reviewed_ids"] == ["err-critical"]
    assert reference["metric"] == 2.0
    assert reference["active"] is False
    assert "strength=0 ranks review_value*(1-confidence)" in reference["trace"][0]


def test_rejects_missing_invalid_and_insufficient_task_evidence():
    with pytest.raises(ValueError, match="missing required input: items"):
        mechanism.evaluate({"review_budget": 1}, 0.5)
    with pytest.raises(ValueError, match=r"confidence must be in \[0, 1\]"):
        mechanism.evaluate(
            {
                "items": [{"id": "a", "correct": False, "confidence": 1.2, "review_value": 1}],
                "review_budget": 0,
            },
            0.5,
        )
    with pytest.raises(ValueError, match="review_value must be positive"):
        mechanism.evaluate(
            {
                "items": [{"id": "a", "correct": False, "confidence": 0.9, "review_value": 0}],
                "review_budget": 0,
            },
            0.5,
        )
    with pytest.raises(ValueError, match=r"strength must be in \[0, 1\]"):
        mechanism.evaluate({"items": [], "review_budget": 0}, 1.1)
    with pytest.raises(ValueError, match="at least four scored attempts"):
        mechanism.evaluate(
            {
                "items": [{"id": "a", "correct": False, "confidence": 0.9, "review_value": 1}],
                "review_budget": 0,
            },
            0.5,
        )


def test_deterministic_nonmutation_and_complete_task_state():
    positive = next(s for s in mechanism.scenarios() if s["name"] == "positive")
    context = deepcopy(positive["contexts"][0])
    context["state"] = {
        "attempted": 0,
        "correct_count": 0,
        "confidence_sum": 0.0,
        "error_count": 0,
        "reviewed_error_count": 0,
        "unreviewed_error_count": 0,
        "last_reviewed_ids": [],
    }
    before = deepcopy(context)
    first = mechanism.evaluate(context, 0.8)
    second = mechanism.evaluate(context, 0.8)
    assert context == before
    assert first == second
    assert isinstance(first["metric"], float)
    assert first["active"] is True
    assert set(mechanism.METADATA["state_fields"]).issubset(first["state"])
    assert first["trace"] and all(isinstance(line, str) for line in first["trace"])


def test_carries_chronological_outcome_and_confidence_history():
    first_batch = {
        "items": [
            {"id": "a", "correct": False, "confidence": 0.9, "review_value": 1},
            {"id": "b", "correct": False, "confidence": 0.9, "review_value": 1},
            {"id": "e", "correct": False, "confidence": 0.9, "review_value": 1},
            {"id": "f", "correct": True, "confidence": 0.7, "review_value": 1},
        ],
        "review_budget": 0,
    }
    second_batch = {
        "items": [
            {"id": "c", "correct": True, "confidence": 0.8, "review_value": 1},
            {"id": "d", "correct": False, "confidence": 0.9, "review_value": 1},
        ],
        "review_budget": 0,
    }
    first = mechanism.evaluate(first_batch, 0.8)
    second = mechanism.evaluate({**second_batch, "state": first["state"]}, 0.8)
    assert second["state"]["attempted"] == 6
    assert second["state"]["error_count"] == 4
    assert second["state"]["unreviewed_error_count"] == 4
