from copy import deepcopy

import pytest

from mechanisms import peak_end_rule


def run_chronology(contexts, strength, initial_state=None):
    state = deepcopy(initial_state or {})
    results = []
    for round_index, task_inputs in enumerate(contexts):
        context = deepcopy(task_inputs)
        context.update({
            "state": deepcopy(state),
            "peer_states": [],
            "round_index": round_index,
            "agent_index": 0,
            "uniform": 0.5,
        })
        result = peak_end_rule.evaluate(context, strength)
        state = deepcopy(result["state"])
        results.append(result)
    return results


def test_numeric_oracle_uses_mean_peak_and_ending_weights():
    contexts = [
        {"moment_score": 2, "episode_end": False},
        {"moment_score": 4, "episode_end": False},
        {"moment_score": 10, "episode_end": False},
        {"moment_score": 8, "episode_end": True},
    ]
    result = run_chronology(contexts, 0.5)[-1]
    # Mean=6; peak/end summary=(10+8)/2=9; mixture weight=.6*.5=.3.
    assert result["metric"] == pytest.approx((1 - 0.3) * 6 + 0.3 * 9)
    assert result["state"]["observed_scores"] == [2.0, 4.0, 10.0, 8.0]
    assert result["state"]["retrospective_rating"] == pytest.approx(6.9)
    assert "peak=max(history)=10" in result["trace"][0]
    assert result["active"] is True


def test_positive_completed_episode_increases_rating_at_strength_point_8():
    scenario = peak_end_rule.scenarios()[0]
    reference = run_chronology(scenario["contexts"], 0.0)
    intervention = run_chronology(scenario["contexts"], 0.8)
    assert intervention[-1]["metric"] > reference[-1]["metric"]
    assert intervention[-1]["metric"] == pytest.approx(7.44)
    assert intervention[-1]["state"]["episode_ended"] is True
    assert sum(result["active"] for result in intervention) == 1


def test_missing_explicit_episode_end_removes_necessary_condition():
    scenario = peak_end_rule.scenarios()[1]
    assert all(context["episode_end"] is False for context in scenario["contexts"])
    reference = run_chronology(scenario["contexts"], 0.0)
    intervention = run_chronology(scenario["contexts"], 0.8)
    assert intervention[-1]["metric"] == pytest.approx(reference[-1]["metric"])
    assert intervention[-1]["metric"] == pytest.approx(6.0)
    assert not any(result["active"] for result in intervention)
    assert intervention[-1]["state"]["episode_ended"] is False


def test_strength_zero_is_arithmetic_mean_reference_even_at_episode_end():
    contexts = peak_end_rule.scenarios()[0]["contexts"]
    result = run_chronology(contexts, 0.0)[-1]
    assert result["metric"] == pytest.approx(6.0)
    assert result["active"] is False
    assert result["state"]["retrospective_rating"] == pytest.approx(6.0)


@pytest.mark.parametrize("field", peak_end_rule.METADATA["required_inputs"])
def test_missing_required_evidence_is_rejected(field):
    context = {"moment_score": 5, "episode_end": False, "state": {}}
    del context[field]
    with pytest.raises(ValueError, match="required task input"):
        peak_end_rule.evaluate(context, 0.8)


@pytest.mark.parametrize(
    "update",
    [
        {"moment_score": -1},
        {"moment_score": 11},
        {"moment_score": float("nan")},
        {"moment_score": True},
        {"episode_end": 1},
    ],
)
def test_invalid_evidence_is_rejected(update):
    context = {"moment_score": 5, "episode_end": False, "state": {}}
    context.update(update)
    with pytest.raises(ValueError):
        peak_end_rule.evaluate(context, 0.8)


def test_strength_and_impossible_temporal_state_are_rejected():
    context = {"moment_score": 5, "episode_end": False, "state": {}}
    for strength in (-0.1, 1.1, float("inf"), True):
        with pytest.raises(ValueError):
            peak_end_rule.evaluate(context, strength)
    with pytest.raises(ValueError, match="at least two"):
        peak_end_rule.evaluate({"moment_score": 5, "episode_end": True, "state": {}}, 0.8)

    completed = run_chronology(
        [{"moment_score": 4, "episode_end": False}, {"moment_score": 5, "episode_end": True}],
        0.8,
    )[-1]["state"]
    with pytest.raises(ValueError, match="after the episode"):
        peak_end_rule.evaluate({"moment_score": 6, "episode_end": False, "state": completed}, 0.8)


def test_deterministic_nonmutation_and_nested_prior_state_preservation():
    context = {
        "moment_score": 8,
        "episode_end": True,
        "state": {"observed_scores": [2, 4, 10], "episode_ended": False,
                  "retrospective_rating": None, "annotation": {"keep": ["prior"]}},
        "peer_states": [{"observed_scores": [9]}],
        "round_index": 3,
        "agent_index": 1,
        "uniform": 0.5,
    }
    before = deepcopy(context)
    first = peak_end_rule.evaluate(context, 0.8)
    second = peak_end_rule.evaluate(context, 0.8)
    assert context == before
    assert first == second
    assert first["state"]["annotation"] == {"keep": ["prior"]}
    first["state"]["annotation"]["keep"].append("changed")
    assert context["state"]["annotation"]["keep"] == ["prior"]


def test_scenarios_use_exact_common_inputs_and_no_reserved_context_keys():
    assert peak_end_rule.METADATA["required_inputs"] == ["moment_score", "episode_end"]
    reserved = {"state", "peer_states", "uniform", "round_index", "agent_index"}
    for scenario in peak_end_rule.scenarios():
        assert all(set(context) == {"moment_score", "episode_end"} for context in scenario["contexts"])
        assert not any(reserved.intersection(context) for context in scenario["contexts"])
