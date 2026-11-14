from copy import deepcopy
import math

import pytest

from mechanisms import one_sided_sourcing as plugin


POSITIVE = {
    "full_story_reviewed": True,
    "focus_side": "support",
    "claims": [
        {"source_id": "support_a", "side": "support", "relevant": True, "quality": 0.99},
        {"source_id": "support_b", "side": "support", "relevant": True, "quality": 0.95},
        {"source_id": "counter_a", "side": "counter", "relevant": True, "quality": 0.30},
    ],
}


def invoke(context, strength):
    supplied = deepcopy(context)
    supplied.setdefault("state", {})
    supplied.setdefault("peer_states", [])
    supplied.setdefault("round_index", 0)
    supplied.setdefault("agent_index", 0)
    supplied.setdefault("uniform", 0.5)
    return plugin.evaluate(supplied, strength)


def test_positive_direction_and_task_specific_numeric_choice_oracle():
    reference = invoke(POSITIVE, 0.0)
    biased = invoke(POSITIVE, 0.8)
    assert reference["metric"] == 0.0
    assert reference["state"]["selected_source_ids"] == ["support_a", "counter_a"]
    assert biased["metric"] == 1.0
    assert biased["state"]["selected_source_ids"] == ["support_a", "support_b"]
    assert biased["active"] is True
    # q(second focus)-q(counter)=.65 exceeds 2*(1-.8)=.4.
    assert 0.95 - 0.30 > 2.0 * (1.0 - 0.8)


def test_boundary_without_relevant_counterview_equals_reference():
    boundary = {
        "full_story_reviewed": True,
        "focus_side": "support",
        "claims": [
            {"source_id": "support_a", "side": "support", "relevant": True, "quality": 0.9},
            {"source_id": "support_b", "side": "support", "relevant": True, "quality": 0.6},
            {"source_id": "irrelevant_counter", "side": "counter", "relevant": False, "quality": 1.0},
        ],
    }
    at_zero = invoke(boundary, 0.0)
    at_strength = invoke(boundary, 0.8)
    assert at_zero["metric"] == at_strength["metric"] == 0.0
    assert at_zero["state"]["selected_source_ids"] == at_strength["state"]["selected_source_ids"]
    assert at_strength["active"] is False


def test_strength_zero_is_coverage_first_reference_rule():
    result = invoke(POSITIVE, 0.0)
    assert result["state"]["selected_source_ids"] == ["support_a", "counter_a"]
    assert result["state"]["represented_sides"] == ["counter", "support"]
    assert result["metric"] == 0.0
    assert result["active"] is False


def test_rejects_missing_or_excerpt_only_evidence_and_invalid_ranges():
    with pytest.raises(ValueError, match="full_story_reviewed"):
        invoke({**POSITIVE, "full_story_reviewed": False}, 0.8)
    with pytest.raises(ValueError, match="claims"):
        invoke({**POSITIVE, "claims": []}, 0.8)
    with pytest.raises(ValueError, match="quality"):
        invoke({**POSITIVE, "claims": [dict(POSITIVE["claims"][0], quality=float("nan"))]}, 0.8)
    with pytest.raises(ValueError, match="strength"):
        invoke(POSITIVE, 1.01)


def test_deterministic_and_nonmutating_for_context_and_nested_state():
    context = deepcopy(POSITIVE)
    context["state"] = {"editor_note": {"tags": ["reviewed"]}}
    before = deepcopy(context)
    first = plugin.evaluate(context, 0.8)
    second = plugin.evaluate(context, 0.8)
    assert context == before
    assert first == second
    assert first["state"]["editor_note"] == {"tags": ["reviewed"]}
    assert first["state"] is not context["state"]


def test_returns_finite_metric_complete_state_and_explanatory_trace():
    result = invoke(POSITIVE, 0.8)
    assert math.isfinite(result["metric"])
    assert set(("selected_source_ids", "represented_sides", "source_slots_filled", "one_sided_sourcing")) <= set(result["state"])
    assert result["state"]["source_slots_filled"] == 2
    assert result["state"]["one_sided_sourcing"] == result["metric"]
    assert result["trace"] and all(isinstance(line, str) for line in result["trace"])
