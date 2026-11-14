import copy
import math

import pytest

from mechanisms import hot_hand_fallacy as mechanism


INITIAL = {"success_streak": 0, "last_outcome": None, "last_forecast": None}


def run_sequence(contexts, strength):
    state = copy.deepcopy(INITIAL)
    result = None
    for index, task_input in enumerate(contexts):
        context = {
            **copy.deepcopy(task_input),
            "state": copy.deepcopy(state),
            "peer_states": [],
            "round_index": index,
            "agent_index": 0,
            "uniform": 0.5,
        }
        result = mechanism.evaluate(context, strength)
        state = result["state"]
    return result


def test_unsupported_success_streak_increases_forecast_with_numeric_oracle():
    contexts = [
        {"outcome": True, "base_rate": 0.5, "supported_persistence_delta": 0.0},
        {"outcome": True, "base_rate": 0.5, "supported_persistence_delta": 0.0},
    ]
    reference = run_sequence(contexts, 0.0)
    biased = run_sequence(contexts, 0.8)
    # Two successes give raw uplift 0.12*(2-1)/(2+1)=0.04;
    # strength .8 scales this to .032 above the .5 reference.
    assert reference["metric"] == pytest.approx(0.5)
    assert biased["metric"] == pytest.approx(0.532)
    assert biased["metric"] > reference["metric"]
    assert biased["active"] is True


def test_supported_persistence_boundary_matches_reference():
    contexts = [
        {"outcome": True, "base_rate": 0.5, "supported_persistence_delta": 0.1},
        {"outcome": True, "base_rate": 0.5, "supported_persistence_delta": 0.1},
    ]
    reference = run_sequence(contexts, 0.0)
    at_strength = run_sequence(contexts, 0.8)
    assert reference["metric"] == pytest.approx(0.6)
    assert at_strength["metric"] == pytest.approx(reference["metric"])
    assert at_strength["active"] is False


def test_zero_strength_is_the_explicit_reference_rule():
    result = run_sequence(
        [{"outcome": True, "base_rate": 0.37, "supported_persistence_delta": 0.08}],
        0.0,
    )
    assert result["metric"] == pytest.approx(0.45)
    assert result["active"] is False


def test_broken_streak_does_not_produce_fallacy_uplift():
    contexts = [
        {"outcome": True, "base_rate": 0.4, "supported_persistence_delta": 0.0},
        {"outcome": False, "base_rate": 0.4, "supported_persistence_delta": 0.0},
    ]
    assert run_sequence(contexts, 0.8)["metric"] == pytest.approx(0.4)


def test_missing_or_impossible_task_evidence_is_rejected():
    base = {"outcome": True, "base_rate": 0.5, "supported_persistence_delta": 0.0, "state": {}}
    missing = dict(base)
    del missing["supported_persistence_delta"]
    with pytest.raises(ValueError, match="missing required input"):
        mechanism.evaluate(missing, 0.8)
    impossible = dict(base, supported_persistence_delta=0.6)
    with pytest.raises(ValueError, match="cannot exceed 1"):
        mechanism.evaluate(impossible, 0.8)
    with pytest.raises(ValueError, match="outcome must be a bool"):
        mechanism.evaluate(dict(base, outcome=1), 0.8)
    with pytest.raises(ValueError, match="base_rate"):
        mechanism.evaluate(dict(base, base_rate=float("nan")), 0.8)


def test_strength_validation_rejects_nonfinite_and_out_of_range():
    context = {
        "outcome": True,
        "base_rate": 0.5,
        "supported_persistence_delta": 0.0,
        "state": {},
    }
    for value in (-0.01, 1.01, float("inf"), float("nan")):
        with pytest.raises(ValueError, match="strength"):
            mechanism.evaluate(context, value)


def test_deterministic_and_nonmutating_context_and_state():
    context = {
        "outcome": True,
        "base_rate": 0.5,
        "supported_persistence_delta": 0.0,
        "state": {"success_streak": 1, "last_outcome": True, "last_forecast": 0.51},
        "peer_states": [{"success_streak": 8}],
        "round_index": 1,
        "agent_index": 2,
        "uniform": 0.37,
    }
    before = copy.deepcopy(context)
    first = mechanism.evaluate(context, 0.8)
    second = mechanism.evaluate(context, 0.8)
    assert context == before
    assert first == second
    assert first["state"] is not context["state"]
    assert math.isfinite(first["metric"])
    assert first["metric"] == pytest.approx(0.532)
    assert set(first["state"]) == {"success_streak", "last_outcome", "last_forecast"}
    assert first["state"]["success_streak"] == 2
