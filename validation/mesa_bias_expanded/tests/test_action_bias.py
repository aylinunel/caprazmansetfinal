import copy
import math

import pytest

from mechanisms import action_bias


def ctx(**updates):
    data = {
        "action_utility": 0.40,
        "wait_utility": 0.50,
        "action_pressure": 0.30,
        "evidence_supported": False,
        "state": {},
        "peer_states": [],
        "round_index": 0,
        "agent_index": 0,
        "uniform": 0.5,
    }
    data.update(updates)
    return data


def test_positive_case_flips_to_unsupported_action_and_accumulates_state():
    case = ctx()
    baseline = action_bias.evaluate(case, 0.0)
    result = action_bias.evaluate(case, 0.8)
    assert baseline["metric"] == 0.0
    assert result["metric"] == 1.0
    assert result["active"] is True
    assert result["state"] == {
        "chosen_action": "act",
        "unsupported_action_count": 1,
        "decision_count": 1,
        "last_utility_gap": pytest.approx(-0.10),
    }
    assert any("gap + strength*action_pressure > 0" in line for line in result["trace"])


def test_boundary_evidence_supported_beneficial_action_matches_reference():
    case = ctx(action_utility=0.70, wait_utility=0.50, evidence_supported=True)
    baseline = action_bias.evaluate(case, 0.0)
    boundary = action_bias.evaluate(case, 0.8)
    assert baseline["metric"] == boundary["metric"] == 1.0
    assert boundary["active"] is False
    assert boundary["state"]["unsupported_action_count"] == 0


def test_strength_zero_is_strict_utility_reference_and_ties_wait():
    assert action_bias.evaluate(ctx(action_utility=0.51, wait_utility=0.50), 0)["metric"] == 1.0
    assert action_bias.evaluate(ctx(action_utility=0.50, wait_utility=0.50), 0)["metric"] == 0.0
    assert action_bias.evaluate(ctx(action_utility=0.49, wait_utility=0.50), 0)["metric"] == 0.0


def test_numeric_oracle_pressure_must_overcome_the_utility_gap():
    # At strength .8, pressure contributes .8*.10=.08: insufficient to overcome .10.
    assert action_bias.evaluate(ctx(action_pressure=0.10), 0.8)["metric"] == 0.0
    # .8*.15=.12 exceeds the same .10 gap, so the choice flips.
    assert action_bias.evaluate(ctx(action_pressure=0.15), 0.8)["metric"] == 1.0


def test_rejects_missing_impossible_and_mistyped_evidence():
    missing = ctx()
    del missing["action_utility"]
    with pytest.raises(ValueError, match="missing required input"):
        action_bias.evaluate(missing, 0.5)
    with pytest.raises(ValueError, match="finite number"):
        action_bias.evaluate(ctx(action_utility=float("nan")), 0.5)
    with pytest.raises(ValueError, match="finite number"):
        action_bias.evaluate(ctx(action_pressure=1.1), 0.5)
    with pytest.raises(ValueError, match="evidence_supported"):
        action_bias.evaluate(ctx(evidence_supported=1), 0.5)
    with pytest.raises(ValueError, match="strength"):
        action_bias.evaluate(ctx(), math.inf)


def test_deterministic_and_nonmutating_including_nested_state():
    prior = {"decision_count": 2, "unsupported_action_count": 1, "custom": {"keep": ["x"]}}
    case = ctx(state=prior)
    before = copy.deepcopy(case)
    first = action_bias.evaluate(case, 0.8)
    second = action_bias.evaluate(case, 0.8)
    assert case == before
    assert first == second
    assert first["state"]["decision_count"] == 3
    assert first["state"]["unsupported_action_count"] == 2
    assert first["state"]["chosen_action"] == "act"


def test_state_can_be_carried_across_decisions_without_losing_counts():
    initial = ctx()
    first = action_bias.evaluate(initial, 0.8)
    second_context = ctx(
        action_utility=0.60,
        wait_utility=0.50,
        evidence_supported=True,
        state=first["state"],
        round_index=1,
    )
    second = action_bias.evaluate(second_context, 0.8)
    assert second["state"]["decision_count"] == 2
    assert second["state"]["unsupported_action_count"] == 1
    assert second["metric"] == 1.0
