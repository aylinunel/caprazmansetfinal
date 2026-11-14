from copy import deepcopy

import pytest

from mechanisms.automation_bias import evaluate, scenarios


POSITIVE = {
    "task_scores": {"validated_option": 8.0, "automated_option": 7.5},
    "automation_recommendation": "automated_option",
    "verification_available": True,
}
BOUNDARY = {
    "task_scores": {"validated_option": 8.0, "automated_option": 7.5},
    "automation_recommendation": "automated_option",
    "verification_available": False,
}


def run(contexts, strength, initial_state=None):
    state = deepcopy(initial_state or {})
    outputs = []
    for index, task in enumerate(contexts):
        context = deepcopy(task)
        context.update(state=deepcopy(state), peer_states=[], round_index=index,
                       agent_index=0, uniform=0.5)
        result = evaluate(context, strength)
        state = deepcopy(result["state"])
        outputs.append(result)
    return outputs


def test_positive_task_choice_oracle_shows_inferior_recommendation_selected():
    # gap=.5; at .8 the adjusted recommendation score is 7.5+.8*(.5+.5)=8.3,
    # which exceeds the verified alternative's 8.0; metric is raw task score.
    baseline = evaluate({**POSITIVE, "state": {}}, 0.0)
    biased = evaluate({**POSITIVE, "state": {}}, 0.8)
    assert baseline["state"]["last_choice"] == "validated_option"
    assert baseline["metric"] == 8.0
    assert biased["state"]["last_choice"] == "automated_option"
    assert biased["metric"] == 7.5
    assert biased["active"] is True


def test_boundary_without_independent_check_equals_reference_metric():
    reference = evaluate({**BOUNDARY, "state": {}}, 0.0)
    at_boundary_strength = evaluate({**BOUNDARY, "state": {}}, 0.8)
    assert reference["metric"] == at_boundary_strength["metric"] == 7.5
    assert reference["state"]["last_choice"] == at_boundary_strength["state"]["last_choice"]
    assert at_boundary_strength["active"] is False


def test_zero_strength_reproduces_reference_rule_when_recommendation_is_contradicted():
    result = evaluate({**POSITIVE, "state": {}}, 0.0)
    assert result["metric"] == 8.0
    assert result["state"]["last_choice"] == "validated_option"
    assert result["active"] is False


def test_missing_or_invalid_required_evidence_is_rejected():
    missing = dict(POSITIVE)
    del missing["task_scores"]
    with pytest.raises(ValueError, match="missing required"):
        evaluate(missing, 0.8)
    invalid = {**POSITIVE, "verification_available": 1}
    with pytest.raises(ValueError, match="must be a bool"):
        evaluate(invalid, 0.8)
    out_of_range = {**POSITIVE, "task_scores": {"a": 101, "b": 0}}
    with pytest.raises(ValueError, match=r"\[0, 100\]"):
        evaluate(out_of_range, 0.8)


def test_determinism_nonmutation_and_complete_chronological_state():
    original = {**POSITIVE, "state": {"decisions": 2, "deference_overrides": 0,
                                       "last_choice": "previous", "custom": ["keep"]}}
    before = deepcopy(original)
    first = evaluate(original, 0.8)
    second = evaluate(original, 0.8)
    assert original == before
    assert first == second
    assert first["state"] == {
        "decisions": 3,
        "deference_overrides": 1,
        "last_choice": "automated_option",
        "custom": ["keep"],
    }
    sequence = run([POSITIVE, BOUNDARY], 0.8)
    assert [item["state"]["decisions"] for item in sequence] == [1, 2]
    assert sequence[-1]["state"]["deference_overrides"] == 1


def test_strength_and_nonfinite_values_are_rejected():
    for strength in (-0.01, 1.01, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            evaluate({**POSITIVE, "state": {}}, strength)
    invalid_score = {**POSITIVE, "task_scores": {"a": 5, "b": float("nan")}}
    with pytest.raises(ValueError, match="finite"):
        evaluate(invalid_score, 0.8)


def test_scenario_contract_directions_hold():
    cases = {case["name"]: case for case in scenarios()}
    assert {"positive", "boundary"}.issubset(cases)
    positive = cases["positive"]
    boundary = cases["boundary"]
    assert run(positive["contexts"], 0.8, positive["initial_state"])[-1]["metric"] < run(
        positive["contexts"], 0.0, positive["initial_state"]
    )[-1]["metric"]
    assert run(boundary["contexts"], 0.8, boundary["initial_state"])[-1]["metric"] == run(
        boundary["contexts"], 0.0, boundary["initial_state"]
    )[-1]["metric"]
