from copy import deepcopy
import math

import pytest

from mechanisms import illusory_truth_effect as mechanism


def run_sequence(contexts, strength, initial_state=None):
    state = deepcopy(initial_state or {})
    outputs = []
    for round_index, context in enumerate(contexts):
        full_context = deepcopy(context)
        full_context.update(
            {
                "state": state,
                "peer_states": [],
                "round_index": round_index,
                "agent_index": 0,
                "uniform": 0.5,
            }
        )
        result = mechanism.evaluate(full_context, strength)
        outputs.append(result)
        state = result["state"]
    return outputs


def unsupported_repetitions(n=3):
    return [
        {"claim_id": "claim-A", "exposed": True, "evidence": []}
        for _ in range(n)
    ]


def test_repetition_without_new_evidence_increases_index_by_task_specific_formula():
    strength = 0.8
    results = run_sequence(unsupported_repetitions(3), strength)
    expected_final = 1.0 / (
        1.0 + math.exp(-0.55 * strength * math.log1p(2))
    )

    assert results[0]["metric"] == pytest.approx(0.5)
    assert results[-1]["metric"] == pytest.approx(expected_final)
    assert results[-1]["metric"] > results[0]["metric"]
    assert results[-1]["active"] is True


def test_independent_evidence_boundary_matches_reference_at_every_step():
    contexts = [
        {
            "claim_id": "claim-A",
            "exposed": True,
            "evidence": [{"evidence_id": "study-1", "log_likelihood_ratio": 0.2}],
        },
        {
            "claim_id": "claim-A",
            "exposed": True,
            "evidence": [{"evidence_id": "study-2", "log_likelihood_ratio": 0.3}],
        },
        {
            "claim_id": "claim-A",
            "exposed": True,
            "evidence": [{"evidence_id": "study-3", "log_likelihood_ratio": -0.1}],
        },
    ]
    with_effect = run_sequence(contexts, 0.8)
    reference = run_sequence(contexts, 0.0)

    assert [item["metric"] for item in with_effect] == pytest.approx(
        [item["metric"] for item in reference]
    )
    assert all(not item["active"] for item in with_effect)


def test_zero_strength_is_explicit_evidence_only_reference_rule():
    contexts = unsupported_repetitions(3)
    results = run_sequence(contexts, 0.0)
    assert [item["metric"] for item in results] == pytest.approx([0.5, 0.5, 0.5])
    assert all(item["active"] is False for item in results)


def test_missing_evidence_is_an_error_instead_of_zero_metric():
    with pytest.raises(ValueError, match="missing required input: evidence"):
        mechanism.evaluate({"claim_id": "claim-A", "exposed": True}, 0.8)


def test_invalid_evidence_value_and_invalid_strength_are_rejected():
    bad_evidence = {
        "claim_id": "claim-A",
        "exposed": True,
        "evidence": [{"evidence_id": "study-1", "log_likelihood_ratio": float("nan")}],
    }
    with pytest.raises(ValueError, match="log_likelihood_ratio"):
        mechanism.evaluate(bad_evidence, 0.8)
    with pytest.raises(ValueError, match="strength"):
        mechanism.evaluate(
            {"claim_id": "claim-A", "exposed": True, "evidence": []}, 1.01
        )


def test_repeated_evidence_id_is_not_counted_as_independent_again():
    first = {
        "claim_id": "claim-A",
        "exposed": True,
        "evidence": [{"evidence_id": "same-study", "log_likelihood_ratio": 0.7}],
    }
    second = deepcopy(first)
    outputs = run_sequence([first, second], 0.0)
    expected = 1.0 / (1.0 + math.exp(-0.7))
    assert outputs[0]["metric"] == pytest.approx(expected)
    assert outputs[1]["metric"] == pytest.approx(expected)
    assert outputs[1]["state"]["claim_memory"]["claim-A"]["seen_evidence_ids"] == [
        "same-study"
    ]


def test_evaluate_is_deterministic_and_does_not_mutate_nested_inputs():
    context = {
        "claim_id": "claim-A",
        "exposed": True,
        "evidence": [],
        "state": {
            "custom": {"preserve": [1, 2]},
            "claim_memory": {
                "claim-A": {
                    "exposure_count": 1,
                    "evidence_log_odds": 0.0,
                    "seen_evidence_ids": [],
                }
            },
        },
        "peer_states": [{"sentinel": [3]}],
        "round_index": 1,
        "agent_index": 0,
        "uniform": 0.25,
    }
    before = deepcopy(context)
    first = mechanism.evaluate(context, 0.8)
    second = mechanism.evaluate(context, 0.8)

    assert context == before
    assert first == second
    assert math.isfinite(first["metric"])
    assert isinstance(first["state"], dict)
    assert isinstance(first["trace"], list) and first["trace"]


def test_scenarios_include_temporal_positive_and_boundary_cases():
    cases = {scenario["name"]: scenario for scenario in mechanism.scenarios()}
    assert set(cases) >= {"positive", "boundary"}
    assert len(cases["positive"]["contexts"]) >= 2
    assert len(cases["boundary"]["contexts"]) >= 2
    positive = run_sequence(cases["positive"]["contexts"], 0.8)
    baseline = run_sequence(cases["positive"]["contexts"], 0.0)
    assert positive[-1]["metric"] > baseline[-1]["metric"]
