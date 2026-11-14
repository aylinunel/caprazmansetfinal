from copy import deepcopy

import pytest

from mechanisms import recency_effect


def make_context(**overrides):
    context = {
        "observation": "B",
        "sequence_ordered": True,
        "state": {"history": ["A"], "choice": None},
        "peer_states": [],
        "round_index": 1,
        "agent_index": 0,
        "uniform": 0.5,
    }
    context.update(overrides)
    return context


def run_sequence(contexts, strength, initial_state=None):
    state = deepcopy(initial_state or {"history": [], "choice": None})
    results = []
    for round_index, task_fields in enumerate(contexts):
        context = {
            **task_fields,
            "state": deepcopy(state),
            "peer_states": [],
            "round_index": round_index,
            "agent_index": 0,
            "uniform": 0.5,
        }
        result = recency_effect.evaluate(context, strength)
        state = result["state"]
        results.append(result)
    return results


def test_numeric_choice_oracle_recent_B_overturns_equal_count_reference():
    context = make_context()
    result = recency_effect.evaluate(context, 0.8)
    # One older A has weight .2 + .8*.55 = .64; newest B has weight 1.
    # Weighted evidence therefore selects B, while equal counts tie to A.
    assert result["state"]["history"] == ["A", "B"]
    assert "Weighted support A=0.64, B=1" in result["trace"][0]
    assert result["state"]["choice"] == "B"
    assert result["metric"] == 1.0
    assert result["active"] is True


def test_positive_chronological_sequence_moves_final_choice_toward_recent_B():
    contexts = [
        {"observation": item, "sequence_ordered": True}
        for item in ["A", "A", "A", "A", "B", "B", "B"]
    ]
    intervention = run_sequence(contexts, 0.8)
    reference = run_sequence(contexts, 0.0)
    assert intervention[-1]["metric"] == 1.0
    assert reference[-1]["metric"] == 0.0
    assert intervention[-1]["metric"] > reference[-1]["metric"]
    assert intervention[-1]["state"]["history"] == ["A", "A", "A", "A", "B", "B", "B"]


def test_unordered_boundary_removes_serial_position_condition():
    contexts = [
        {"observation": item, "sequence_ordered": False}
        for item in ["A", "A", "A", "A", "B", "B", "B"]
    ]
    intervention = run_sequence(contexts, 0.8)
    reference = run_sequence(contexts, 0.0)
    assert intervention[-1]["metric"] == reference[-1]["metric"] == 0.0
    assert intervention[-1]["active"] is False
    assert "unordered" in intervention[-1]["trace"][0]


def test_zero_strength_is_equal_count_reference_and_does_not_activate():
    result = recency_effect.evaluate(make_context(), 0.0)
    assert result["metric"] == 0.0  # equal-count tie resolves to A
    assert result["state"]["choice"] == "A"
    assert result["active"] is False
    assert "equal-count reference chooses A" in result["trace"][0]


def test_missing_or_invalid_phase_inputs_and_strength_are_rejected():
    missing = make_context()
    del missing["sequence_ordered"]
    with pytest.raises(ValueError, match="missing required task input sequence_ordered"):
        recency_effect.evaluate(missing, 0.8)

    with pytest.raises(ValueError, match="observation"):
        recency_effect.evaluate(make_context(observation="C"), 0.8)
    with pytest.raises(ValueError, match="sequence_ordered"):
        recency_effect.evaluate(make_context(sequence_ordered=1), 0.8)
    with pytest.raises(ValueError, match="state.history"):
        recency_effect.evaluate(make_context(state={"history": ["A", "C"]}), 0.8)
    with pytest.raises(ValueError, match="state.choice"):
        recency_effect.evaluate(make_context(state={"history": [], "choice": []}), 0.8)
    with pytest.raises(ValueError, match="strength"):
        recency_effect.evaluate(make_context(), float("nan"))


def test_repeated_evaluation_is_deterministic_and_does_not_mutate_inputs():
    context = make_context(state={"history": ["A"], "choice": None})
    before = deepcopy(context)
    first = recency_effect.evaluate(context, 0.8)
    second = recency_effect.evaluate(context, 0.8)
    assert first == second
    assert context == before
    assert first["state"]["history"] == ["A", "B"]
    assert first["state"]["choice"] == "B"
