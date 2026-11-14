from copy import deepcopy

import pytest

from mechanisms import decision_fatigue as mechanism


OPTIONS = [
    {"id": "thorough", "utility": 10.0, "effort": 0.9},
    {"id": "defer", "utility": 6.0, "effort": 0.1},
]
RESERVED = {"peer_states": [], "round_index": 0, "agent_index": 0, "uniform": 0.5}


def run_sequence(contexts, strength, initial_state=None):
    state = deepcopy(initial_state or {})
    results = []
    for index, task_context in enumerate(contexts):
        context = deepcopy(task_context)
        context.update(RESERVED)
        context["round_index"] = index
        context["state"] = state
        result = mechanism.evaluate(context, strength)
        state = result["state"]
        results.append(result)
    return results


def test_positive_repeated_load_causes_measurable_avoidant_regret():
    contexts = [
        {"options": OPTIONS, "decision_load": 0.8},
        {"options": OPTIONS, "decision_load": 0.8},
        {"options": OPTIONS, "decision_load": 0.8},
    ]
    affected = run_sequence(contexts, 0.8)
    reference = run_sequence(contexts, 0.0)
    assert [row["metric"] for row in reference] == [0.0, 0.0, 0.0]
    assert [row["metric"] for row in affected] == [0.0, 4.0, 4.0]
    assert affected[1]["state"]["last_choice"] == "defer"
    assert affected[1]["active"] is True


def test_boundary_without_load_matches_strength_zero():
    contexts = [{"options": OPTIONS, "decision_load": 0.0} for _ in range(3)]
    assert [r["metric"] for r in run_sequence(contexts, 0.8)] == [
        r["metric"] for r in run_sequence(contexts, 0.0)
    ]
    assert all(not r["active"] for r in run_sequence(contexts, 0.8))


def test_zero_strength_is_explicit_max_utility_reference_even_with_loaded_state():
    context = {
        **RESERVED,
        "options": OPTIONS,
        "decision_load": 0.2,
        "state": {"accumulated_load": 2.0, "decisions_seen": 4, "last_choice": "defer"},
    }
    result = mechanism.evaluate(context, 0.0)
    assert result["metric"] == 0.0
    assert result["state"]["last_choice"] == "thorough"
    assert result["active"] is False


def test_missing_evidence_and_impossible_values_are_rejected():
    base = {**RESERVED, "state": {}}
    with pytest.raises(ValueError, match="missing required"):
        mechanism.evaluate({**base, "options": OPTIONS}, 0.8)
    with pytest.raises(ValueError, match="decision_load"):
        mechanism.evaluate({**base, "options": OPTIONS, "decision_load": 1.1}, 0.8)
    with pytest.raises(ValueError, match="effort"):
        mechanism.evaluate(
            {**base, "options": [{"id": "a", "utility": 1, "effort": -0.1}, OPTIONS[1]], "decision_load": 0.5},
            0.8,
        )
    with pytest.raises(ValueError, match="strength"):
        mechanism.evaluate({**base, "options": OPTIONS, "decision_load": 0.5}, float("nan"))


def test_determinism_and_nested_input_nonmutation():
    context = {
        **RESERVED,
        "options": deepcopy(OPTIONS),
        "decision_load": 0.8,
        "state": {"accumulated_load": 0.8, "decisions_seen": 1, "last_choice": "thorough"},
    }
    original = deepcopy(context)
    first = mechanism.evaluate(context, 0.8)
    second = mechanism.evaluate(context, 0.8)
    assert first == second
    assert context == original
    assert first["metric"] == 4.0
    assert first["active"] is True


def test_current_decision_load_is_not_enough_without_prior_decision():
    context = {**RESERVED, "options": OPTIONS, "decision_load": 1.0, "state": {}}
    result = mechanism.evaluate(context, 1.0)
    assert result["metric"] == 0.0
    assert result["state"]["decisions_seen"] == 1
    assert result["active"] is False


def test_declared_scenarios_obey_contract_at_strength_point_eight():
    declared = {scenario["name"]: scenario for scenario in mechanism.scenarios()}
    assert {"positive", "boundary"}.issubset(declared)
    positive = declared["positive"]
    boundary = declared["boundary"]
    for scenario in (positive, boundary):
        assert len(scenario["contexts"]) > 1
    pos_at_strength = run_sequence(positive["contexts"], 0.8, positive["initial_state"])[-1]["metric"]
    pos_at_zero = run_sequence(positive["contexts"], 0.0, positive["initial_state"])[-1]["metric"]
    bound_at_strength = run_sequence(boundary["contexts"], 0.8, boundary["initial_state"])[-1]["metric"]
    bound_at_zero = run_sequence(boundary["contexts"], 0.0, boundary["initial_state"])[-1]["metric"]
    assert pos_at_strength > pos_at_zero
    assert bound_at_strength == bound_at_zero
