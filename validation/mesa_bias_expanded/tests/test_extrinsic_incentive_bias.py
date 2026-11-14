from copy import deepcopy
from math import isfinite

import pytest

from mechanisms import extrinsic_incentive_bias as mechanism


BASE = {
    "self_reward_signal": 0.4,
    "self_intrinsic_signal": 0.6,
    "other_reward_signal": 0.4,
    "other_intrinsic_signal": 0.6,
    "other_motive_documentation": 0.0,
}


def run(context, strength):
    """Supply the runner-reserved fields while exercising evaluate directly."""
    prepared = deepcopy(context)
    prepared.setdefault("state", {})
    prepared.setdefault("peer_states", [])
    prepared.setdefault("round_index", 0)
    prepared.setdefault("agent_index", 0)
    prepared.setdefault("uniform", 0.5)
    return mechanism.evaluate(prepared, strength)


def test_positive_numeric_oracle_is_reward_cue_overweighting():
    baseline = run(BASE, 0.0)
    biased = run(BASE, 0.8)
    assert baseline["metric"] == pytest.approx(0.4)
    # Reward signal .4 is weighted by 1 + .8*(1-0) = 1.8:
    # (.4*1.8) / ((.4*1.8)+.6) = 6/11.
    assert biased["metric"] == pytest.approx(6 / 11)
    assert biased["metric"] > baseline["metric"]
    assert biased["active"] is True


def test_complete_documentation_boundary_matches_reference():
    context = {**BASE, "other_motive_documentation": 1.0}
    baseline = run(context, 0.0)
    result = run(context, 0.8)
    assert result["metric"] == baseline["metric"]
    assert result["active"] is False


def test_zero_strength_is_explicit_proportional_reference_rule():
    context = {
        "self_reward_signal": 0.2,
        "self_intrinsic_signal": 0.8,
        "other_reward_signal": 0.3,
        "other_intrinsic_signal": 0.7,
        "other_motive_documentation": 0.25,
    }
    result = run(context, 0.0)
    assert result["metric"] == pytest.approx(0.3)
    assert result["active"] is False
    assert result["state"]["steps"] == 1
    assert result["state"]["last_self_extrinsic_share"] == pytest.approx(0.2)
    assert result["state"]["last_other_extrinsic_share"] == pytest.approx(0.3)


def test_missing_and_impossible_evidence_are_rejected():
    with pytest.raises(ValueError, match="missing required input"):
        run({key: value for key, value in BASE.items() if key != "other_reward_signal"}, 0.8)
    impossible = {**BASE, "other_reward_signal": 0.0, "other_intrinsic_signal": 0.0}
    with pytest.raises(ValueError, match="cannot both be zero"):
        run(impossible, 0.8)
    with pytest.raises(ValueError, match="finite number"):
        run({**BASE, "other_motive_documentation": float("nan")}, 0.8)


def test_result_is_deterministic_and_inputs_are_not_mutated():
    context = {**BASE, "state": {"steps": 2, "sum_other_extrinsic_share": 0.5}}
    before = deepcopy(context)
    first = run(context, 0.8)
    second = run(context, 0.8)
    assert first == second
    assert context == before
    assert isfinite(first["metric"])
    assert set(first["state"]) == set(mechanism.METADATA["state_fields"])
    assert isinstance(first["trace"], list) and first["trace"]


def test_zero_reward_signal_does_not_create_an_incentive_bias():
    context = {**BASE, "other_reward_signal": 0.0, "other_intrinsic_signal": 0.7}
    baseline = run(context, 0.0)
    result = run(context, 0.8)
    assert result["metric"] == baseline["metric"] == 0.0
    assert result["active"] is False


def test_strength_out_of_range_is_rejected():
    with pytest.raises(ValueError, match="strength"):
        run(BASE, 1.01)
