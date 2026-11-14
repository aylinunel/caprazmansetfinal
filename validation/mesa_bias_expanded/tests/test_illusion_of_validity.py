import copy
import math

import pytest

from mechanisms import illusion_of_validity as mechanism


def evaluate_sequence(contexts, strength, initial_state=None):
    state = copy.deepcopy(initial_state or {})
    outputs = []
    for index, item in enumerate(contexts):
        context = copy.deepcopy(item)
        context.update(
            state=state,
            peer_states=[],
            round_index=index,
            agent_index=0,
            uniform=0.5,
        )
        result = mechanism.evaluate(context, strength)
        state = result["state"]
        outputs.append(result)
    return outputs


def test_positive_unanimous_overclaimed_cues_raise_confidence_with_numeric_oracle():
    scenario = mechanism.scenarios()[0]
    context = scenario["contexts"][0]
    reference = mechanism.evaluate(context, 0.0)
    result = mechanism.evaluate(context, 0.8)

    # Three + cues at 0.8 claimed accuracy give log odds 3*ln(4); with
    # neutral prior, the reference confidence is 64/65. The mechanism's
    # task-specific headroom/gap equation then has an independently checked value.
    expected_reference = 64.0 / 65.0
    expected_metric = expected_reference + 0.8 * 1.0 * (0.8 - 0.55) * (1.0 - expected_reference)
    assert reference["metric"] == pytest.approx(expected_reference)
    assert result["metric"] == pytest.approx(expected_metric)
    assert result["metric"] > reference["metric"]
    assert result["state"]["predicted_label"] == 1
    assert result["active"] is True


def test_boundary_disagreement_matches_reference_after_unanimity_removed():
    scenario = mechanism.scenarios()[1]
    context = scenario["contexts"][0]
    reference = mechanism.evaluate(context, 0.0)
    result = mechanism.evaluate(context, 0.8)
    assert result["state"]["coherence"] == pytest.approx(2 / 3)
    assert result["metric"] == reference["metric"]
    assert result["active"] is False


def test_zero_strength_is_explicit_claimed_accuracy_reference_rule():
    context = {
        "cue_signs": [-1, -1],
        "claimed_accuracy": 0.75,
        "validated_accuracy": 0.6,
        "base_rate": 0.5,
    }
    result = mechanism.evaluate(context, 0.0)
    assert result["metric"] == pytest.approx(0.9)
    assert result["state"]["predicted_label"] == -1
    assert result["active"] is False


def test_missing_or_impossible_evidence_is_rejected_not_zeroed():
    with pytest.raises(ValueError, match="missing required evidence"):
        mechanism.evaluate({"cue_signs": [1], "claimed_accuracy": 0.8}, 0.5)
    bad = {
        "cue_signs": [1, 0],
        "claimed_accuracy": 0.8,
        "validated_accuracy": 0.6,
        "base_rate": 0.5,
    }
    with pytest.raises(ValueError, match="cue_sign"):
        mechanism.evaluate(bad, 0.5)


def test_strength_must_be_finite_and_in_unit_interval():
    context = mechanism.scenarios()[0]["contexts"][0]
    for invalid in (-0.01, 1.01, math.inf, math.nan, True):
        with pytest.raises(ValueError, match="strength"):
            mechanism.evaluate(context, invalid)


def test_deterministic_and_does_not_mutate_context_or_nested_state():
    context = {
        "cue_signs": [1, 1, 1],
        "claimed_accuracy": 0.8,
        "validated_accuracy": 0.55,
        "base_rate": 0.5,
        "state": {"history": ["prior"], "keep": 7},
        "peer_states": [{"x": [1]}],
    }
    original = copy.deepcopy(context)
    first = mechanism.evaluate(context, 0.8)
    second = mechanism.evaluate(context, 0.8)
    assert context == original
    assert first == second
    assert first["state"]["keep"] == 7
    assert first["state"]["history"] is context["state"]["history"]
    assert isinstance(first["trace"], list) and len(first["trace"]) >= 2
    assert math.isfinite(first["metric"])


def test_overclaimed_condition_is_necessary_even_with_unanimity():
    context = {
        "cue_signs": [-1, -1],
        "claimed_accuracy": 0.75,
        "validated_accuracy": 0.9,
        "base_rate": 0.5,
    }
    baseline = mechanism.evaluate(context, 0.0)
    result = mechanism.evaluate(context, 1.0)
    assert result["metric"] == baseline["metric"]
    assert result["active"] is False
