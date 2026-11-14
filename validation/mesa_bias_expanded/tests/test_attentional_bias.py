from copy import deepcopy
import math

import pytest

from mechanisms import attentional_bias


def run_rounds(contexts, strength, initial_state=None):
    state = deepcopy(initial_state or {})
    outputs = []
    for index, task_context in enumerate(contexts):
        context = deepcopy(task_context)
        context.update({
            "state": deepcopy(state),
            "peer_states": [],
            "round_index": index,
            "agent_index": 0,
            "uniform": 0.5,
        })
        result = attentional_bias.evaluate(context, strength)
        outputs.append(result)
        state = result["state"]
    return outputs


POSITIVE = {
    "stimuli": [
        {"id": "target", "relevance": 1.0, "capture": 0.0},
        {"id": "distractor", "relevance": 0.4, "capture": 1.0},
    ]
}


def test_positive_attention_capture_reduces_relevant_information_at_point_eight():
    baseline = run_rounds([POSITIVE], 0.0)[0]
    biased = run_rounds([POSITIVE], 0.8)[0]
    assert baseline["state"]["last_attended_id"] == "target"
    assert biased["state"]["last_attended_id"] == "distractor"
    assert baseline["metric"] == 1.0
    assert biased["metric"] == 0.4
    assert biased["metric"] < baseline["metric"]
    assert biased["active"] is True


def test_boundary_equal_capture_preserves_reference_choice_and_metric():
    context = {
        "stimuli": [
            {"id": "target", "relevance": 1.0, "capture": 0.3},
            {"id": "other", "relevance": 0.4, "capture": 0.3},
        ]
    }
    baseline = run_rounds([context], 0.0)[0]
    at_boundary = run_rounds([context], 0.8)[0]
    assert at_boundary["metric"] == baseline["metric"] == 1.0
    assert at_boundary["state"]["last_attended_id"] == baseline["state"]["last_attended_id"]
    assert at_boundary["active"] is False


def test_zero_strength_is_explicit_relevance_only_reference_and_numeric_oracle():
    result = run_rounds([POSITIVE], 0.0)[0]
    assert result["metric"] == max(item["relevance"] for item in POSITIVE["stimuli"])
    assert result["state"]["attention_history"][0]["attended_id"] == "target"
    assert result["state"]["attention_history"][0]["reference_id"] == "target"


def test_missing_or_impossible_evidence_is_rejected():
    with pytest.raises(ValueError, match="missing required input"):
        attentional_bias.evaluate({"state": {}}, 0.5)
    with pytest.raises(ValueError, match="at least two"):
        attentional_bias.evaluate({"stimuli": [{"id": "only", "relevance": 1, "capture": 1}]}, 0.5)
    with pytest.raises(ValueError, match="some task-relevant"):
        attentional_bias.evaluate({"stimuli": [
            {"id": "a", "relevance": 0, "capture": 0},
            {"id": "b", "relevance": 0, "capture": 1},
        ]}, 0.5)


def test_invalid_strength_and_out_of_range_values_are_rejected():
    for strength in (-0.01, 1.01, float("nan"), float("inf"), True):
        with pytest.raises(ValueError):
            attentional_bias.evaluate(POSITIVE, strength)
    malformed = {"stimuli": [
        {"id": "a", "relevance": 1.2, "capture": 0},
        {"id": "b", "relevance": 0.2, "capture": 1},
    ]}
    with pytest.raises(ValueError, match="relevance"):
        attentional_bias.evaluate(malformed, 0.5)


def test_determinism_nonmutation_and_finite_metric():
    context = deepcopy(POSITIVE)
    context["state"] = {"attention_history": [], "unrelated": {"keep": [1, 2]}}
    original = deepcopy(context)
    first = attentional_bias.evaluate(context, 0.8)
    second = attentional_bias.evaluate(context, 0.8)
    assert context == original
    assert first == second
    assert math.isfinite(first["metric"])
    assert set(first) == {"metric", "active", "state", "trace"}
    assert isinstance(first["trace"], list) and first["trace"]
    assert first["state"]["unrelated"] == {"keep": [1, 2]}


def test_state_history_carries_attentional_choices_across_contexts():
    contexts = [POSITIVE, {"stimuli": [
        {"id": "useful", "relevance": 0.8, "capture": 0.9},
        {"id": "weak", "relevance": 0.2, "capture": 0.1},
    ]}]
    results = run_rounds(contexts, 0.8)
    history = results[-1]["state"]["attention_history"]
    assert [entry["round_index"] for entry in history] == [0, 1]
    assert [entry["attended_id"] for entry in history] == ["distractor", "useful"]
