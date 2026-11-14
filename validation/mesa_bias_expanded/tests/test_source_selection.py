import copy

import pytest

from mechanisms import source_selection


BALANCED = [
    {"source_id": "s1", "view": "supports", "eligible": True},
    {"source_id": "s2", "view": "supports", "eligible": True},
    {"source_id": "s3", "view": "challenges", "eligible": True},
    {"source_id": "s4", "view": "challenges", "eligible": True},
]


def context(sources=BALANCED, budget=2, state=None):
    return {
        "sources": copy.deepcopy(sources),
        "target_view": "supports",
        "selection_budget": budget,
        "state": copy.deepcopy(state or {}),
        "peer_states": [],
        "round_index": 0,
        "agent_index": 0,
        "uniform": 0.5,
    }


def run_sequence(contexts, strength, initial_state=None):
    state = copy.deepcopy(initial_state or {})
    outputs = []
    for index, item in enumerate(contexts):
        current = copy.deepcopy(item)
        current.update({
            "state": copy.deepcopy(state),
            "peer_states": [],
            "round_index": index,
            "agent_index": 0,
            "uniform": 0.5,
        })
        result = source_selection.evaluate(current, strength)
        outputs.append(result)
        state = result["state"]
    return outputs


def test_positive_effect_and_numeric_choice_oracle():
    baseline = source_selection.evaluate(context(), 0.0)
    biased = source_selection.evaluate(context(), 0.8)

    # Exact process oracle: proportional reference selects one per view; 0.8
    # weights supporters 4.2x and allocates both slots to the target view.
    assert baseline["state"]["selected_source_ids_by_round"] == [["s1", "s3"]]
    assert baseline["metric"] == 0.5
    assert biased["state"]["selected_source_ids_by_round"] == [["s1", "s2"]]
    assert biased["metric"] == 1.0
    assert biased["metric"] > baseline["metric"]
    assert biased["active"] is True


def test_boundary_without_competing_eligible_view_matches_reference():
    only_support = [
        {"source_id": "a", "view": "supports", "eligible": True},
        {"source_id": "b", "view": "supports", "eligible": True},
        {"source_id": "c", "view": "supports", "eligible": True},
    ]
    baseline = source_selection.evaluate(context(only_support), 0.0)
    at_boundary = source_selection.evaluate(context(only_support), 0.8)
    assert at_boundary["metric"] == baseline["metric"] == 1.0
    assert at_boundary["state"]["selected_source_ids_by_round"] == baseline["state"]["selected_source_ids_by_round"]
    assert at_boundary["active"] is False


def test_strength_zero_is_the_explicit_proportional_reference():
    result = source_selection.evaluate(context(), 0.0)
    assert result["state"]["selected_source_ids_by_round"] == [["s1", "s3"]]
    assert result["metric"] == 0.5
    assert result["active"] is False
    assert all("weight" in line or "reference" in line or "Eligible" in line for line in result["trace"])


def test_missing_or_impossible_evidence_is_rejected_not_zeroed():
    missing = context()
    del missing["sources"]
    with pytest.raises(ValueError, match="missing required input"):
        source_selection.evaluate(missing, 0.8)

    no_eligible = [{"source_id": "x", "view": "supports", "eligible": False}]
    with pytest.raises(ValueError, match="at least one eligible source"):
        source_selection.evaluate(context(no_eligible), 0.8)


def test_strength_and_input_ranges_are_validated():
    for strength in (-0.01, 1.01, 10**1000, float("nan"), float("inf"), True):
        with pytest.raises(ValueError, match="strength"):
            source_selection.evaluate(context(), strength)
    with pytest.raises(ValueError, match="positive integer"):
        source_selection.evaluate(context(budget=0), 0.5)


def test_deterministic_and_nonmutating_with_nested_state():
    original = context(state={"rounds": 1, "selected_source_ids_by_round": [["prior"]], "last_metric": 0.25})
    snapshot = copy.deepcopy(original)
    first = source_selection.evaluate(original, 0.8)
    second = source_selection.evaluate(original, 0.8)
    assert original == snapshot
    assert first == second
    assert first["state"]["rounds"] == 2
    assert first["state"]["selected_source_ids_by_round"] == [["prior"], ["s1", "s2"]]
    first["state"]["selected_source_ids_by_round"][0].append("mutated")
    assert original["state"]["selected_source_ids_by_round"] == [["prior"]]


def test_chronological_state_is_carried_for_each_source_selection_round():
    contexts = [
        {"sources": BALANCED, "target_view": "supports", "selection_budget": 2},
        {"sources": BALANCED, "target_view": "supports", "selection_budget": 2},
    ]
    outputs = run_sequence(contexts, 0.8)
    assert outputs[-1]["state"]["rounds"] == 2
    assert outputs[-1]["state"]["selected_source_ids_by_round"] == [["s1", "s2"], ["s1", "s2"]]
    assert outputs[-1]["state"]["last_metric"] == 1.0


def test_scenario_contract_includes_positive_and_boundary():
    scenarios = source_selection.scenarios()
    assert {s["name"] for s in scenarios} >= {"positive", "boundary"}
    by_name = {s["name"]: s for s in scenarios}
    assert by_name["positive"]["expectation"] == "increase"
    assert by_name["boundary"]["expectation"] == "equal"
    for scenario in scenarios:
        assert scenario["contexts"]
