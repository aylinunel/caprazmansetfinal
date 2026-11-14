from copy import deepcopy

import pytest

from mechanisms import hard_easy_effect


def run_sequence(contexts, strength):
    state = {}
    results = []
    for index, observation in enumerate(contexts):
        context = deepcopy(observation)
        context.update({
            "state": deepcopy(state),
            "peer_states": [],
            "round_index": index,
            "agent_index": 0,
            "uniform": 0.5,
        })
        result = hard_easy_effect.evaluate(context, strength)
        state = result["state"]
        results.append(result)
    return results


POSITIVE = [
    {"difficulty": "hard", "reference_confidence": 0.5, "outcome": 0},
    {"difficulty": "easy", "reference_confidence": 0.5, "outcome": 1},
]


def test_positive_sequence_increases_cross_difficulty_calibration_contrast():
    baseline = run_sequence(POSITIVE, 0.0)[-1]
    affected = run_sequence(POSITIVE, 0.8)[-1]
    assert affected["metric"] > baseline["metric"]
    assert affected["active"] is True
    assert affected["state"]["last_confidence"] < 0.5


def test_numeric_oracle_matches_easy_task_adjustment_and_metric():
    baseline = run_sequence(POSITIVE, 0.0)[-1]
    affected = run_sequence(POSITIVE, 0.8)[-1]
    # 0.8 * 0.25 * 0.5 = 0.1 confidence reduction on the easy task.
    assert baseline["metric"] == pytest.approx(1.0)
    assert affected["state"]["last_confidence"] == pytest.approx(0.4)
    assert affected["metric"] == pytest.approx(1.1)
    assert affected["metric"] - baseline["metric"] == pytest.approx(0.1)


def test_single_difficulty_boundary_equals_strength_zero_reference():
    boundary = [
        {"difficulty": "hard", "reference_confidence": 0.6, "outcome": 0},
        {"difficulty": "hard", "reference_confidence": 0.4, "outcome": 1},
    ]
    baseline = run_sequence(boundary, 0.0)[-1]
    affected = run_sequence(boundary, 0.8)[-1]
    assert affected["metric"] == baseline["metric"] == 0.0
    assert affected["active"] is False
    assert affected["state"]["last_confidence"] == pytest.approx(0.4)


def test_zero_strength_preserves_reference_confidence_and_observable():
    results = run_sequence(POSITIVE, 0.0)
    assert results[-1]["state"]["last_confidence"] == pytest.approx(0.5)
    assert results[-1]["metric"] == pytest.approx(1.0)
    assert all(not item["active"] for item in results)


@pytest.mark.parametrize("bad_strength", [-0.01, 1.01, float("nan"), float("inf"), True])
def test_invalid_strength_is_rejected(bad_strength):
    with pytest.raises(ValueError):
        hard_easy_effect.evaluate(
            {"difficulty": "hard", "reference_confidence": 0.5, "outcome": 0},
            bad_strength,
        )


def test_missing_or_impossible_required_evidence_is_rejected():
    with pytest.raises(ValueError, match="missing required"):
        hard_easy_effect.evaluate({"difficulty": "hard", "outcome": 0}, 0.8)
    with pytest.raises(ValueError, match="reference_confidence"):
        hard_easy_effect.evaluate(
            {"difficulty": "easy", "reference_confidence": 1.2, "outcome": 0}, 0.8
        )
    with pytest.raises(ValueError, match="outcome"):
        hard_easy_effect.evaluate(
            {"difficulty": "easy", "reference_confidence": 0.5, "outcome": 0.5}, 0.8
        )
    with pytest.raises(ValueError, match="difficulty"):
        hard_easy_effect.evaluate(
            {"difficulty": "medium", "reference_confidence": 0.5, "outcome": 0}, 0.8
        )


def test_determinism_and_nonmutation_of_context_and_nested_state():
    context = {
        "difficulty": "easy",
        "reference_confidence": 0.5,
        "outcome": 1,
        "state": {
            "observations": [
                {"difficulty": "hard", "reference_confidence": 0.5, "outcome": 0, "confidence": 0.5}
            ],
            "last_confidence": 0.5,
        },
        "peer_states": [{"observations": []}],
        "round_index": 1,
        "agent_index": 0,
        "uniform": 0.5,
    }
    before = deepcopy(context)
    first = hard_easy_effect.evaluate(context, 0.8)
    second = hard_easy_effect.evaluate(context, 0.8)
    assert context == before
    assert first == second
    assert first["state"] is not context["state"]
    assert first["state"]["observations"] is not context["state"]["observations"]


def test_scenarios_meet_temporal_contract():
    scenarios = hard_easy_effect.scenarios()
    assert {item["name"] for item in scenarios} >= {"positive", "boundary"}
    assert all(item["contexts"] for item in scenarios)
    assert len(scenarios[0]["contexts"]) >= 2
