import copy
import math

import pytest

from mechanisms import bikeshedding


def context_for(agenda, budget=10.0, state=None):
    return {
        "agenda": agenda,
        "discussion_budget": budget,
        "state": {} if state is None else state,
        "peer_states": [],
        "round_index": 0,
        "agent_index": 0,
        "uniform": 0.5,
    }


def positive_agenda():
    return [
        {"id": "easy_minor_format", "consequence": 0.15, "ease": 0.95},
        {"id": "hard_safety_review", "consequence": 0.85, "ease": 0.15},
    ]


def test_positive_case_shifts_budget_to_easy_low_consequence_issue():
    context = context_for(positive_agenda())
    baseline = bikeshedding.evaluate(context, 0.0)
    result = bikeshedding.evaluate(context, 0.8)

    assert result["active"] is True
    assert result["metric"] < baseline["metric"]
    assert result["state"]["last_attention"]["easy_minor_format"] > baseline["state"]["last_attention"]["easy_minor_format"]
    assert result["state"]["last_attention"]["hard_safety_review"] < baseline["state"]["last_attention"]["hard_safety_review"]
    assert sum(result["state"]["last_attention"].values()) == pytest.approx(10.0)


def test_numeric_choice_oracle_matches_stated_allocation_formula():
    context = context_for(positive_agenda())
    result = bikeshedding.evaluate(context, 0.8)
    low_weight = 0.15 * math.exp(0.8 * 0.95 * (1.0 - 0.15))
    high_weight = 0.85 * math.exp(0.8 * 0.15 * (1.0 - 0.85))
    expected_low_attention = 10.0 * low_weight / (low_weight + high_weight)
    expected_metric = (
        expected_low_attention * 0.15
        + (10.0 - expected_low_attention) * 0.85
    ) / 10.0

    assert result["state"]["last_attention"]["easy_minor_format"] == pytest.approx(expected_low_attention)
    assert result["metric"] == pytest.approx(expected_metric)


def test_boundary_without_inverse_ease_consequence_pair_matches_reference():
    agenda = [
        {"id": "small_but_important_detail", "consequence": 0.7, "ease": 0.9},
        {"id": "major_decision", "consequence": 0.9, "ease": 0.9},
    ]
    result = bikeshedding.evaluate(context_for(agenda), 0.8)
    baseline = bikeshedding.evaluate(context_for(agenda), 0.0)

    assert result["active"] is False
    assert result["metric"] == pytest.approx(baseline["metric"])
    assert result["state"]["last_attention"] == pytest.approx(baseline["state"]["last_attention"])


def test_zero_strength_is_the_proportional_consequence_reference_rule():
    result = bikeshedding.evaluate(context_for(positive_agenda()), 0.0)

    assert result["active"] is False
    assert result["state"]["last_attention"]["easy_minor_format"] == pytest.approx(10 * 0.15 / (0.15 + 0.85))
    assert result["state"]["last_attention"]["hard_safety_review"] == pytest.approx(10 * 0.85 / (0.15 + 0.85))
    assert result["metric"] == pytest.approx(0.15 * 0.15 + 0.85 * 0.85)


@pytest.mark.parametrize(
    "bad_context",
    [
        {"discussion_budget": 3.0},
        {"agenda": [], "discussion_budget": 3.0},
        {"agenda": [{"id": "missing_evidence", "ease": 0.9}], "discussion_budget": 3.0},
        {"agenda": [{"id": "bad_rating", "consequence": 0.0, "ease": 0.9}], "discussion_budget": 3.0},
        {"agenda": [{"id": "bad_ease", "consequence": 0.7, "ease": float("nan")}], "discussion_budget": 3.0},
        {"agenda": [{"id": "one", "consequence": 0.6, "ease": 0.4}, {"id": "one", "consequence": 0.9, "ease": 0.2}], "discussion_budget": 3.0},
    ],
)
def test_missing_or_impossible_task_evidence_is_rejected(bad_context):
    with pytest.raises(ValueError):
        bikeshedding.evaluate(bad_context, 0.8)


def test_strength_must_be_finite_and_in_range():
    valid = context_for(positive_agenda())
    for strength in (-0.01, 1.01, float("inf"), float("nan"), True):
        with pytest.raises(ValueError):
            bikeshedding.evaluate(valid, strength)


def test_deterministic_and_does_not_mutate_context_or_nested_state():
    state = {
        "rounds": 2,
        "cumulative_budget": 4.0,
        "cumulative_attention": {"prior_issue": 4.0},
        "last_attention": {"prior_issue": 4.0},
    }
    context = context_for(positive_agenda(), budget=5.0, state=state)
    before = copy.deepcopy(context)

    first = bikeshedding.evaluate(context, 0.8)
    second = bikeshedding.evaluate(context, 0.8)

    assert context == before
    assert first == second
    assert first["state"]["rounds"] == 3
    assert first["state"]["cumulative_budget"] == pytest.approx(9.0)
    assert first["state"]["cumulative_attention"]["prior_issue"] == pytest.approx(4.0)
    assert first["state"]["cumulative_attention"]["easy_minor_format"] == pytest.approx(first["state"]["last_attention"]["easy_minor_format"])
    assert first["state"] is not context["state"]


def test_scenarios_provide_required_positive_and_boundary_cases():
    cases = {case["name"]: case for case in bikeshedding.scenarios()}
    assert {"positive", "boundary"} <= set(cases)
    assert len(cases["positive"]["contexts"]) >= 1
    assert len(cases["boundary"]["contexts"]) >= 1
