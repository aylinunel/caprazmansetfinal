from copy import deepcopy
import math

import pytest

from mechanisms import lag_effect


def run(contexts, strength, initial_state=None):
    state = deepcopy(initial_state or {})
    results = []
    for index, task_inputs in enumerate(contexts):
        context = {
            **deepcopy(task_inputs),
            "state": deepcopy(state),
            "peer_states": [],
            "round_index": index,
            "agent_index": 0,
            "uniform": 0.5,
        }
        result = lag_effect.evaluate(context, strength)
        results.append(result)
        state = deepcopy(result["state"])
    return results


def test_numeric_oracle_for_two_studies_with_suitable_lag():
    contexts = [
        {"action": "study", "day": 0, "retention_horizon_days": 10},
        {"action": "study", "day": 5, "retention_horizon_days": 10},
    ]
    first_memory = 1 - math.exp(-0.20)
    pre_second = first_memory * math.exp(-0.5)
    gain = 0.20 * (1 + 0.8 * 2.0 * 0.5)
    expected = 1 - (1 - pre_second) * math.exp(-gain)
    results = run(contexts, 0.8)
    assert results[-1]["metric"] == pytest.approx(expected)
    assert results[-1]["active"] is True
    assert any("Suitable spaced-practice interval" in line for line in results[-1]["trace"])


def test_positive_scenario_improves_retention_over_fixed_gain_reference():
    context = lag_effect.scenarios()[0]["contexts"]
    intervention = run(context, 0.8)[-1]["metric"]
    reference = run(context, 0.0)[-1]["metric"]
    assert intervention > reference


def test_boundary_zero_gap_removes_necessary_condition_and_matches_reference():
    context = lag_effect.scenarios()[1]["contexts"]
    intervention = run(context, 0.8)[-1]
    reference = run(context, 0.0)[-1]
    assert intervention["metric"] == pytest.approx(reference["metric"])
    assert intervention["active"] is False
    assert any("No lag enhancement" in line for line in intervention["trace"])


def test_zero_strength_is_the_fixed_gain_reference_even_with_suitable_lag():
    contexts = lag_effect.scenarios()[0]["contexts"]
    zero = run(contexts, 0.0)
    other = run(contexts, 0.0)
    assert [r["metric"] for r in zero] == pytest.approx([r["metric"] for r in other])
    assert not any(r["active"] for r in zero)


def test_phase_specific_missing_or_invalid_evidence_is_rejected():
    with pytest.raises(ValueError, match="missing required input"):
        lag_effect.evaluate({"action": "study", "day": 0, "state": {}}, 0.8)
    with pytest.raises(ValueError, match="prior study"):
        lag_effect.evaluate(
            {"action": "test", "day": 0, "retention_horizon_days": 10, "state": {}}, 0.8
        )
    with pytest.raises(ValueError, match="positive"):
        lag_effect.evaluate(
            {"action": "study", "day": 0, "retention_horizon_days": 0, "state": {}}, 0.8
        )
    with pytest.raises(ValueError, match="strength"):
        lag_effect.evaluate(
            {"action": "study", "day": 0, "retention_horizon_days": 10, "state": {}}, float("nan")
        )


def test_deterministic_and_does_not_mutate_context_or_nested_state():
    context = {
        "action": "study",
        "day": 5,
        "retention_horizon_days": 10,
        "state": {"memory_strength": 0.3, "last_study_day": 0, "study_count": 1},
        "peer_states": [{"memory_strength": 0.7}],
        "round_index": 1,
        "agent_index": 0,
        "uniform": 0.25,
    }
    before = deepcopy(context)
    first = lag_effect.evaluate(context, 0.8)
    second = lag_effect.evaluate(context, 0.8)
    assert context == before
    assert first == second
    assert first["state"]["study_count"] == 2
    assert math.isfinite(first["metric"])


def test_test_event_uses_elapsed_horizon_and_preserves_study_history():
    state = {"memory_strength": 0.6, "last_study_day": 4, "study_count": 2}
    result = lag_effect.evaluate(
        {"action": "test", "day": 9, "retention_horizon_days": 10, "state": state}, 0.8
    )
    assert result["metric"] == pytest.approx(0.6 * math.exp(-0.5))
    assert result["state"] == state
    assert result["active"] is False
