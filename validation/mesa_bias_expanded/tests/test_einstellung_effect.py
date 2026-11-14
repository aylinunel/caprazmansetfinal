import copy

import pytest

from mechanisms import einstellung_effect as mechanism


def run_sequence(contexts, strength, initial_state=None):
    state = copy.deepcopy(initial_state or {})
    outputs = []
    for round_index, context in enumerate(contexts):
        call_context = copy.deepcopy(context)
        call_context.update(
            state=copy.deepcopy(state),
            peer_states=[],
            round_index=round_index,
            agent_index=0,
            uniform=0.5,
        )
        output = mechanism.evaluate(call_context, strength)
        state = copy.deepcopy(output["state"])
        outputs.append(output)
    return outputs


def positive_contexts():
    return mechanism.scenarios()[0]["contexts"]


def boundary_contexts():
    return mechanism.scenarios()[1]["contexts"]


def test_repeated_learned_method_blocks_lower_action_alternative_numeric_oracle():
    contexts = positive_contexts()
    reference = run_sequence(contexts, 0.0)
    fixed = run_sequence(contexts, 0.8)
    assert reference[-1]["metric"] == 2.0
    assert fixed[-1]["metric"] == 8.0
    assert fixed[-1]["active"] is True
    assert fixed[-1]["state"]["last_choice_id"] == "learned-sequence"
    assert reference[-1]["state"]["last_choice_id"] == "short-alternative"


def test_boundary_task_family_mismatch_matches_strength_zero():
    contexts = boundary_contexts()
    baseline = run_sequence(contexts, 0.0)[-1]
    result = run_sequence(contexts, 0.8)[-1]
    assert baseline["metric"] == result["metric"] == 2.0
    assert baseline["state"]["last_choice_id"] == result["state"]["last_choice_id"] == "short-alternative"
    assert result["active"] is False


def test_strength_zero_is_explicit_full_budget_minimum_action_reference():
    context = positive_contexts()[-1]
    result = mechanism.evaluate(context, 0.0)
    assert result["metric"] == 2.0
    assert result["state"]["last_choice_id"] == "short-alternative"
    assert result["state"]["last_effective_search_budget"] == 5.0
    assert result["active"] is False


def test_missing_or_impossible_evidence_is_rejected():
    context = positive_contexts()[-1]
    missing = dict(context)
    del missing["search_budget"]
    with pytest.raises(ValueError, match="search_budget"):
        mechanism.evaluate(missing, 0.8)

    impossible = copy.deepcopy(context)
    impossible["solutions"][1]["action_count"] = 0
    with pytest.raises(ValueError, match="positive integer"):
        mechanism.evaluate(impossible, 0.8)

    no_learned_option = copy.deepcopy(context)
    no_learned_option["solutions"] = [no_learned_option["solutions"][1]]
    with pytest.raises(ValueError, match="learned_solution_id"):
        mechanism.evaluate(no_learned_option, 0.8)


def test_strength_validation_rejects_nonfinite_and_out_of_range():
    context = positive_contexts()[-1]
    for invalid in (-0.01, 1.01, float("nan"), float("inf"), True):
        with pytest.raises(ValueError):
            mechanism.evaluate(context, invalid)


def test_evaluation_is_deterministic_and_does_not_mutate_nested_context_or_state():
    context = copy.deepcopy(positive_contexts()[-1])
    context["state"] = {"learned_successes_by_key": {"measure-vessel\u241flearned-sequence": 2}, "custom": [1, 2]}
    context["peer_states"] = [{"nested": [3]}]
    original = copy.deepcopy(context)
    first = mechanism.evaluate(context, 0.8)
    second = mechanism.evaluate(context, 0.8)
    assert first == second
    assert context == original
    assert first["state"]["custom"] == [1, 2]
    first["state"]["custom"].append(9)
    assert context["state"]["custom"] == [1, 2]


def test_no_prior_successful_use_means_no_fixation_even_in_same_family():
    context = positive_contexts()[-1]
    result = mechanism.evaluate(context, 0.8)
    assert result["metric"] == 2.0
    assert result["active"] is False
