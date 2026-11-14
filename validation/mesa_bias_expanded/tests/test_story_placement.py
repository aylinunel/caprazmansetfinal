import copy
import math

import pytest

from mechanisms import story_placement


def run_round(context, strength):
    supplied = copy.deepcopy(context)
    supplied.setdefault("state", {})
    supplied.setdefault("peer_states", [])
    supplied.setdefault("round_index", 0)
    supplied.setdefault("agent_index", 0)
    supplied.setdefault("uniform", 0.5)
    return story_placement.evaluate(supplied, strength)


def by_name(name):
    return next(s for s in story_placement.scenarios() if s["name"] == name)


def test_positive_placement_moves_attention_to_promoted_story():
    scenario = by_name("positive")
    context = scenario["contexts"][0]
    reference = run_round(context, 0.0)["metric"]
    result = run_round(context, 0.8)
    assert result["metric"] > reference
    assert result["active"] is True
    assert result["state"]["steps"] == 1


def test_boundary_uniform_placement_matches_content_only_reference():
    scenario = by_name("boundary")
    context = scenario["contexts"][0]
    reference = run_round(context, 0.0)["metric"]
    result = run_round(context, 0.8)
    assert result["metric"] == pytest.approx(reference, abs=1e-15)
    assert result["active"] is False


def test_positive_scenario_matches_task_specific_softmax_numeric_oracle():
    context = by_name("positive")["contexts"][0]
    result = run_round(context, 0.8)
    # For promoted B, B/A odds = exp(4*(.2-.9) + 4*.8*(1-0)).
    odds = math.exp(4 * (0.2 - 0.9) + 4 * 0.8)
    expected = odds / (1 + odds)
    assert result["metric"] == pytest.approx(expected, rel=1e-13)


def test_zero_strength_is_content_only_reference():
    context = {
        "stories": [
            {"id": "a", "content_importance": 0.7, "placement_prominence": 0.0},
            {"id": "b", "content_importance": 0.1, "placement_prominence": 1.0},
        ],
        "focal_story_id": "b",
    }
    result = run_round(context, 0.0)
    odds = math.exp(4 * (0.1 - 0.7))
    assert result["metric"] == pytest.approx(odds / (1 + odds))
    assert result["active"] is False


def test_missing_or_impossible_evidence_is_rejected():
    with pytest.raises(ValueError, match="at least two"):
        run_round({"stories": [], "focal_story_id": "x"}, 0.8)
    with pytest.raises(ValueError, match="content_importance"):
        run_round({
            "stories": [
                {"id": "a", "placement_prominence": 0.2},
                {"id": "b", "content_importance": 0.4, "placement_prominence": 0.8},
            ],
            "focal_story_id": "a",
        }, 0.8)
    with pytest.raises(ValueError, match="focal_story_id"):
        run_round({
            "stories": [
                {"id": "a", "content_importance": 0.2, "placement_prominence": 0.2},
                {"id": "b", "content_importance": 0.4, "placement_prominence": 0.8},
            ],
            "focal_story_id": "missing",
        }, 0.8)


@pytest.mark.parametrize("strength", [-0.01, 1.01, float("nan"), float("inf"), True])
def test_invalid_strength_is_rejected(strength):
    context = by_name("positive")["contexts"][0]
    with pytest.raises(ValueError, match="strength"):
        run_round(context, strength)


def test_repeat_evaluation_is_deterministic_and_does_not_mutate_nested_inputs():
    context = {
        **by_name("positive")["contexts"][0],
        "state": {
            "steps": 2,
            "cumulative_focal_attention": 0.25,
            "last_attention_shares": {"old": 1.0},
        },
        "extra": {"keep": [1, 2]},
    }
    original = copy.deepcopy(context)
    first = story_placement.evaluate(context, 0.8)
    second = story_placement.evaluate(context, 0.8)
    assert first == second
    assert context == original
    assert first["state"]["steps"] == 3
    assert first["state"]["cumulative_focal_attention"] == pytest.approx(
        0.25 + first["metric"]
    )
    assert first["state"]["last_attention_shares"] is not context["state"]["last_attention_shares"]
