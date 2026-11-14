from copy import deepcopy

import pytest

from mechanisms import event_selection


CANDIDATES = [
    {"id": "A", "public_value": 0.9, "editorial_salience": 0.0},
    {"id": "B", "public_value": 0.8, "editorial_salience": 0.1},
    {"id": "C", "public_value": 0.2, "editorial_salience": 1.0},
]


def context(candidates=None, capacity=1, state=None):
    return {
        "candidates": deepcopy(CANDIDATES if candidates is None else candidates),
        "capacity": capacity,
        "state": {} if state is None else deepcopy(state),
        "peer_states": [],
        "round_index": 0,
        "agent_index": 0,
        "uniform": 0.5,
    }


def test_positive_selection_differs_from_public_value_reference_with_numeric_oracle():
    base = event_selection.evaluate(context(), 0.0)
    changed = event_selection.evaluate(context(), 0.8)
    assert base["state"]["last_selected_ids"] == ["A"]
    assert changed["state"]["last_selected_ids"] == ["C"]
    assert changed["metric"] == 1.0
    assert base["metric"] == 0.0
    assert changed["metric"] > base["metric"]
    assert changed["active"] is True


def test_boundary_with_capacity_for_every_event_matches_reference():
    input_context = context(capacity=len(CANDIDATES))
    at_zero = event_selection.evaluate(deepcopy(input_context), 0.0)
    at_strength = event_selection.evaluate(deepcopy(input_context), 0.8)
    assert set(at_strength["state"]["last_selected_ids"]) == set(
        at_zero["state"]["last_selected_ids"]
    )
    assert at_strength["metric"] == at_zero["metric"] == 0.0
    assert at_strength["active"] is False


def test_strength_zero_is_explicit_public_value_reference_and_state_is_completed():
    result = event_selection.evaluate(context(state={"selection_count": 4, "kept": "yes"}), 0)
    assert result["state"] == {
        "selection_count": 5,
        "kept": "yes",
        "last_selected_ids": ["A"],
        "last_selection_divergence": 0.0,
    }
    assert len(result["trace"]) >= 1
    assert isinstance(result["metric"], float)


@pytest.mark.parametrize("strength", [-0.01, 1.01, float("nan"), float("inf"), True])
def test_invalid_strength_is_rejected(strength):
    with pytest.raises(ValueError):
        event_selection.evaluate(context(), strength)


def test_missing_or_impossible_evidence_is_rejected():
    missing_score = [{"id": "A", "editorial_salience": 0.2}]
    with pytest.raises(ValueError, match="public_value"):
        event_selection.evaluate(context(missing_score), 0.5)
    with pytest.raises(ValueError, match="capacity"):
        event_selection.evaluate(context(capacity=0), 0.5)
    with pytest.raises(ValueError, match="candidates"):
        event_selection.evaluate(context(candidates=[]), 0.5)


def test_evaluation_is_deterministic_and_does_not_mutate_inputs_or_nested_state():
    original = context(state={"selection_count": 2, "nested": {"unchanged": [1, 2]}})
    before = deepcopy(original)
    first = event_selection.evaluate(original, 0.8)
    second = event_selection.evaluate(original, 0.8)
    assert first == second
    assert original == before
    assert first["state"]["nested"] == {"unchanged": [1, 2]}
    first["state"]["nested"]["unchanged"].append(3)
    assert original == before


def test_scenarios_include_required_contract_cases_and_real_competition():
    cases = {scenario["name"]: scenario for scenario in event_selection.scenarios()}
    assert {"positive", "boundary"}.issubset(cases)
    assert cases["positive"]["expectation"] == "increase"
    assert cases["boundary"]["expectation"] == "equal"
    assert len(cases["positive"]["contexts"]) >= 1
    assert len(cases["boundary"]["contexts"]) >= 1
