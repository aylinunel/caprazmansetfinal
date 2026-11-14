from copy import deepcopy

import pytest

from mechanisms import commission_and_omission_of_information as mechanism


POSITIVE = {
    "items": [
        {"id": "support_high", "stance": 1, "evidence_weight": 1.0},
        {"id": "support_low", "stance": 1, "evidence_weight": 0.9},
        {"id": "counter_high", "stance": -1, "evidence_weight": 1.2},
    ],
    "capacity": 2,
    "target_perspective": 1,
    "bias_gain": 0.75,
}


def evaluate_with_state(data, strength, state=None):
    context = deepcopy(data)
    context.update(
        {
            "state": deepcopy(state or {}),
            "peer_states": [],
            "round_index": 0,
            "agent_index": 0,
            "uniform": 0.5,
        }
    )
    return mechanism.evaluate(context, strength)


def test_positive_direction_and_exact_task_choice_oracle():
    reference = evaluate_with_state(POSITIVE, 0.0)
    affected = evaluate_with_state(POSITIVE, 0.8)

    assert reference["state"]["last_presented_ids"] == ["counter_high", "support_high"]
    assert reference["metric"] == pytest.approx(-0.2)
    assert affected["state"]["last_presented_ids"] == ["support_high", "support_low"]
    assert affected["metric"] == pytest.approx(1.9)
    assert affected["metric"] > reference["metric"]
    assert affected["active"] is True
    assert "relative_commission_ids=['support_low']" in affected["trace"][2]
    assert "relative_omission_ids=['counter_high']" in affected["trace"][2]


def test_boundary_without_counter_aligned_evidence_matches_reference():
    boundary = {
        "items": [
            {"id": "s1", "stance": 1, "evidence_weight": 1.0},
            {"id": "s2", "stance": 1, "evidence_weight": 0.9},
            {"id": "s3", "stance": 1, "evidence_weight": 0.6},
        ],
        "capacity": 2,
        "target_perspective": 1,
        "bias_gain": 0.75,
    }
    neutral = evaluate_with_state(boundary, 0.0)
    intervention = evaluate_with_state(boundary, 0.8)
    assert intervention["metric"] == neutral["metric"] == pytest.approx(1.9)
    assert intervention["state"]["last_presented_ids"] == neutral["state"]["last_presented_ids"]
    assert intervention["active"] is False


def test_zero_strength_is_the_explicit_relevance_reference_policy():
    result = evaluate_with_state(POSITIVE, 0.0)
    assert result["state"]["last_presented_ids"] == ["counter_high", "support_high"]
    assert result["state"]["cumulative_target_evidence"] == pytest.approx(-0.2)
    assert result["active"] is False
    assert "Reference package: rank by evidence_weight descending" in result["trace"][0]


def test_missing_or_impossible_evidence_is_rejected_not_scored_as_zero():
    missing = deepcopy(POSITIVE)
    del missing["items"]
    with pytest.raises(ValueError, match="missing required input: items"):
        evaluate_with_state(missing, 0.8)

    invalid = deepcopy(POSITIVE)
    invalid["items"][2]["evidence_weight"] = float("nan")
    with pytest.raises(ValueError, match="finite number"):
        evaluate_with_state(invalid, 0.8)


def test_strength_and_capacity_ranges_are_validated():
    with pytest.raises(ValueError, match=r"strength must be in \[0, 1\]"):
        evaluate_with_state(POSITIVE, 1.01)
    invalid = deepcopy(POSITIVE)
    invalid["capacity"] = 4
    with pytest.raises(ValueError, match="capacity"):
        evaluate_with_state(invalid, 0.8)


def test_deterministic_and_nonmutating_across_carried_state():
    context = {**deepcopy(POSITIVE), "state": {"rounds": 2, "cumulative_target_evidence": 3.0,
                                                "last_presented_ids": ["prior"]},
               "peer_states": [], "round_index": 2, "agent_index": 3, "uniform": 0.5}
    before = deepcopy(context)
    first = mechanism.evaluate(context, 0.8)
    second = mechanism.evaluate(context, 0.8)
    assert context == before
    assert first == second
    assert first["state"]["rounds"] == 3
    assert first["state"]["cumulative_target_evidence"] == pytest.approx(4.9)
    assert first["state"]["last_presented_ids"] == ["support_high", "support_low"]
    assert context["state"]["last_presented_ids"] == ["prior"]


def test_required_named_scenarios_have_contract_expectations():
    cases = {case["name"]: case for case in mechanism.scenarios()}
    assert set(cases) >= {"positive", "boundary"}
    assert cases["positive"]["expectation"] == "increase"
    assert cases["boundary"]["expectation"] == "equal"
    assert cases["positive"]["contexts"]
    assert cases["boundary"]["contexts"]
