from copy import deepcopy

import pytest

from mechanisms import distinction_bias


def _run(contexts, strength, initial_state=None):
    state = deepcopy(initial_state or {})
    outputs = []
    for round_index, scenario in enumerate(contexts):
        context = deepcopy(scenario)
        context.update(
            state=deepcopy(state),
            peer_states=[],
            round_index=round_index,
            agent_index=0,
            uniform=0.5,
        )
        result = distinction_bias.evaluate(context, strength)
        outputs.append(result)
        state = result["state"]
    return outputs


def _ctx(mode="joint", relevance=0.1, use=(60, 55), feature=(20, 80)):
    return {
        "options": [
            {"use_value": use[0], "comparison_value": feature[0]},
            {"use_value": use[1], "comparison_value": feature[1]},
        ],
        "attribute_use_relevance": relevance,
        "evaluation_mode": mode,
    }


def test_positive_joint_evaluation_inflates_gap_with_numeric_oracle():
    result = distinction_bias.evaluate(_ctx(), 0.8)
    # 5-point use gap + .8 * .9 * 60-point declared low-relevance feature gap.
    assert result["metric"] == pytest.approx(48.2)
    assert result["active"] is True
    assert "added_contrast=0.8*0.9*60 (joint)=43.2" in result["trace"][0]


def test_boundary_separate_evaluation_matches_strength_zero_reference():
    context = _ctx(mode="separate")
    biased = distinction_bias.evaluate(context, 0.8)
    reference = distinction_bias.evaluate(context, 0.0)
    assert biased["metric"] == reference["metric"] == 5.0
    assert biased["active"] is False


def test_zero_strength_is_explicit_use_value_gap_reference():
    result = distinction_bias.evaluate(_ctx(use=(72, 41), feature=(0, 100)), 0.0)
    assert result["metric"] == 31.0
    assert result["active"] is False
    assert result["state"]["rounds"] == 1


def test_fully_relevant_attribute_does_not_create_bias_effect():
    context = _ctx(relevance=1.0)
    assert distinction_bias.evaluate(context, 0.8)["metric"] == 5.0
    assert distinction_bias.evaluate(context, 0.8)["active"] is False


def test_missing_or_impossible_evidence_is_rejected():
    with pytest.raises(ValueError, match="attribute_use_relevance"):
        distinction_bias.evaluate({"options": _ctx()["options"], "evaluation_mode": "joint"}, 0.8)
    with pytest.raises(ValueError, match="exactly two"):
        distinction_bias.evaluate({**_ctx(), "options": [_ctx()["options"][0]]}, 0.8)
    with pytest.raises(ValueError, match="finite number"):
        distinction_bias.evaluate(_ctx(relevance=float("nan")), 0.8)
    with pytest.raises(ValueError, match=r"\[0.0, 1.0\]"):
        distinction_bias.evaluate(_ctx(), 1.1)


def test_repeated_evaluation_is_deterministic_and_nonmutating():
    context = _ctx()
    original = deepcopy(context)
    first = distinction_bias.evaluate(context, 0.8)
    second = distinction_bias.evaluate(context, 0.8)
    assert first == second
    assert context == original
    assert first["state"] is not context


def test_state_is_carried_through_chronological_contexts():
    outputs = _run([_ctx(), _ctx(mode="separate")], 0.8)
    assert [r["state"]["rounds"] for r in outputs] == [1, 2]
    assert outputs[1]["state"]["cumulative_metric"] == pytest.approx(53.2)
    assert outputs[1]["state"]["last_metric"] == pytest.approx(5.0)
    assert outputs[1]["state"]["last_active"] is False
