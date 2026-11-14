from copy import deepcopy

import pytest

from mechanisms import picture_explanation as mechanism


def context(**overrides):
    data = {
        "interpretations": [
            {"id": "waiting", "visual_support": 0.60},
            {"id": "watching_departure", "visual_support": 0.45},
        ],
        "caption_target": "watching_departure",
        "caption_specificity": 1.0,
        "state": {"reader_tag": {"kept": True}},
        "peer_states": [],
        "round_index": 0,
        "agent_index": 0,
        "uniform": 0.5,
    }
    data.update(overrides)
    return data


def run_sequence(contexts, strength, initial_state=None):
    state = deepcopy(initial_state or {})
    outputs = []
    for index, item in enumerate(contexts):
        current = deepcopy(item)
        current.update({"state": deepcopy(state), "peer_states": [], "round_index": index,
                        "agent_index": 0, "uniform": 0.5})
        result = mechanism.evaluate(current, strength)
        outputs.append(result)
        state = result["state"]
    return outputs


def test_positive_caption_anchor_changes_choice_and_metric_with_numeric_oracle():
    sample = context()
    reference = mechanism.evaluate(deepcopy(sample), 0.0)
    anchored = mechanism.evaluate(deepcopy(sample), 0.8)
    # 0.45 + 0.8 * 1.0 = 1.25 > the competing visual support 0.60.
    assert reference["state"]["last_interpretation"] == "waiting"
    assert reference["metric"] == 0.0
    assert anchored["state"]["last_interpretation"] == "watching_departure"
    assert anchored["metric"] == 1.0
    assert anchored["active"] is True
    assert anchored["state"]["last_visual_only_interpretation"] == "waiting"


def test_missing_candidate_boundary_matches_visual_only_reference():
    boundary = context(caption_target="storm_approaching")
    reference = mechanism.evaluate(deepcopy(boundary), 0.0)
    result = mechanism.evaluate(deepcopy(boundary), 0.8)
    assert result["metric"] == reference["metric"] == 0.0
    assert result["state"]["last_interpretation"] == reference["state"]["last_interpretation"] == "waiting"
    assert result["active"] is False


def test_zero_strength_is_explicit_visual_support_reference_rule():
    sample = context(caption_specificity=0.95)
    result = mechanism.evaluate(sample, 0.0)
    assert result["state"]["last_interpretation"] == "waiting"
    assert result["metric"] == 0.0
    assert "argmax(visual_support)" in result["trace"][0]


def test_required_evidence_and_ranges_are_validated():
    with pytest.raises(ValueError, match="missing required"):
        mechanism.evaluate({"caption_target": "waiting", "caption_specificity": 1.0}, 0.8)
    with pytest.raises(ValueError, match="visual_support"):
        mechanism.evaluate(context(interpretations=[{"id": "waiting", "visual_support": float("nan")}]), 0.8)
    with pytest.raises(ValueError, match="caption_specificity"):
        mechanism.evaluate(context(caption_specificity=1.2), 0.8)
    with pytest.raises(ValueError, match="strength"):
        mechanism.evaluate(context(), float("inf"))


def test_deterministic_and_nonmutating_with_nested_context_and_state():
    sample = context()
    before = deepcopy(sample)
    first = mechanism.evaluate(sample, 0.8)
    second = mechanism.evaluate(sample, 0.8)
    assert sample == before
    assert first == second
    assert first["state"]["reader_tag"] == {"kept": True}
    assert first["trace"] == second["trace"]


def test_chronological_helper_carries_complete_result_state():
    sequence = [context(), context(caption_target="not_in_image", round_index=1)]
    outputs = run_sequence(sequence, 0.8, {"session": "illustrative"})
    assert len(outputs) == 2
    assert outputs[0]["state"]["last_interpretation"] == "watching_departure"
    assert outputs[1]["state"]["last_interpretation"] == "waiting"
    assert outputs[1]["state"]["session"] == "illustrative"
    assert outputs[1]["state"]["last_caption_alignment"] == 0.0
