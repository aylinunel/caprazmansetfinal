from copy import deepcopy

import pytest

from mechanisms import the_sunk_cost_fallacy as sunk


def run_sequence(contexts, strength, initial_state=None):
    state = deepcopy(initial_state or {})
    outputs = []
    for index, item in enumerate(contexts):
        context = deepcopy(item)
        context.update(
            state=deepcopy(state),
            peer_states=[],
            round_index=index,
            agent_index=0,
            uniform=0.5,
        )
        result = sunk.evaluate(context, strength)
        outputs.append(result)
        state = result["state"]
    return outputs


def test_positive_sunk_cost_changes_choice_and_actual_utility_by_oracle():
    scenario = sunk.scenarios()[0]
    biased = run_sequence(scenario["contexts"], 0.8)[-1]
    reference = run_sequence(scenario["contexts"], 0.0)[-1]
    assert reference["state"]["last_choice"] == "exit"
    assert reference["metric"] == 0.0
    assert biased["state"]["last_choice"] == "continue"
    assert biased["metric"] == -2.0
    assert biased["metric"] < reference["metric"]
    assert biased["active"] is True


def test_fully_recoverable_expenditure_removes_necessary_condition():
    scenario = sunk.scenarios()[1]
    biased = run_sequence(scenario["contexts"], 0.8)[-1]
    reference = run_sequence(scenario["contexts"], 0.0)[-1]
    assert biased["metric"] == reference["metric"] == 0.0
    assert biased["state"]["last_choice"] == "exit"
    assert biased["active"] is False


def test_zero_strength_is_future_value_reference_policy_and_records_complete_state():
    output = sunk.evaluate({
        "past_expenditure": 20,
        "recoverable_amount": 4,
        "future_value_continue": 3,
        "future_value_exit": 1,
        "state": {},
    }, 0.0)
    assert output["metric"] == 3.0
    assert output["state"] == {
        "round_count": 1,
        "choices": ["continue"],
        "actual_utilities": [3.0],
        "cumulative_utility": 3.0,
        "last_choice": "continue",
    }
    assert output["active"] is False
    assert len(output["trace"]) >= 3


def test_missing_or_impossible_evidence_is_rejected():
    with pytest.raises(ValueError, match="missing required input"):
        sunk.evaluate({"past_expenditure": 2}, 0.8)
    with pytest.raises(ValueError, match="recoverable_amount"):
        sunk.evaluate({
            "past_expenditure": 2,
            "recoverable_amount": 3,
            "future_value_continue": 0,
            "future_value_exit": 1,
        }, 0.8)
    with pytest.raises(ValueError, match="nonnegative"):
        sunk.evaluate({
            "past_expenditure": -1,
            "recoverable_amount": 0,
            "future_value_continue": 0,
            "future_value_exit": 1,
        }, 0.8)


@pytest.mark.parametrize("strength", [-0.01, 1.01, float("nan"), float("inf"), True])
def test_strength_must_be_finite_and_in_range(strength):
    with pytest.raises(ValueError):
        sunk.evaluate({
            "past_expenditure": 2,
            "recoverable_amount": 0,
            "future_value_continue": -1,
            "future_value_exit": 0,
        }, strength)


def test_determinism_and_nested_input_immutability_across_real_sequence():
    contexts = [
        {"past_expenditure": 5, "recoverable_amount": 0, "future_value_continue": -2, "future_value_exit": 0},
        {"past_expenditure": 2, "recoverable_amount": 2, "future_value_continue": 4, "future_value_exit": 1},
    ]
    initial = {"round_count": 0, "choices": [], "actual_utilities": [], "cumulative_utility": 0.0, "last_choice": None}
    contexts_before, initial_before = deepcopy(contexts), deepcopy(initial)
    first = run_sequence(contexts, 0.8, initial)
    second = run_sequence(contexts, 0.8, initial)
    assert first == second
    assert contexts == contexts_before
    assert initial == initial_before
    assert first[-1]["state"]["round_count"] == 2
    assert first[-1]["state"]["choices"] == ["continue", "continue"]


def test_invalid_future_value_and_malformed_history_are_rejected():
    base = {
        "past_expenditure": 5,
        "recoverable_amount": 0,
        "future_value_continue": float("nan"),
        "future_value_exit": 0,
    }
    with pytest.raises(ValueError, match="finite number"):
        sunk.evaluate(base, 0.8)
    base["future_value_continue"] = 1
    base["state"] = {"round_count": 1, "choices": [], "actual_utilities": [], "cumulative_utility": 0.0, "last_choice": None}
    with pytest.raises(ValueError, match="history lengths"):
        sunk.evaluate(base, 0.8)
