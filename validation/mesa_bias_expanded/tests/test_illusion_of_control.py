"""Direct contract and behavior tests for the illustrative effort-choice model."""
from copy import deepcopy

import pytest

from mechanisms.illusion_of_control import METADATA, evaluate, scenarios


def make_context(**overrides):
    context = {
        "actual_effect_per_effort": 0.0,
        "perceived_effect_per_effort": 0.4,
        "outcome_value": 100.0,
        "effort_cost": 30.0,
        "effort_levels": [0, 1, 2],
        "state": {},
        "peer_states": [],
        "round_index": 0,
        "agent_index": 0,
        "uniform": 0.5,
    }
    context.update(overrides)
    return context


def test_numeric_choice_oracle_uses_perceived_return_only_when_action_is_ineffective():
    # At s=.8 the false estimate is .32, giving 100*.32-30 = +2 per
    # effort unit, so level 2 wins. Objective reference slope is -30, so 0 wins.
    result = evaluate(make_context(), 0.8)
    assert result["metric"] == 2
    assert result["state"]["last_effort"] == 2
    assert result["state"]["last_objective_net_utility"] == -60
    assert result["state"]["last_decision_score"] == pytest.approx(4)
    assert result["active"] is True


def test_positive_scenario_increases_selected_effort_vs_reference():
    positive = next(s for s in scenarios() if s["name"] == "positive")
    context = make_context(**positive["contexts"][0])
    assert evaluate(context, 0.8)["metric"] > evaluate(context, 0.0)["metric"]


def test_boundary_actual_causal_influence_suppresses_illusion_and_matches_reference():
    boundary = next(s for s in scenarios() if s["name"] == "boundary")
    context = make_context(**boundary["contexts"][0])
    intervention = evaluate(context, 0.8)
    reference = evaluate(context, 0.0)
    assert context["actual_effect_per_effort"] > 0
    assert intervention["metric"] == reference["metric"] == 2
    assert intervention["active"] is False


def test_zero_strength_is_explicit_objective_net_value_reference():
    result = evaluate(make_context(), 0.0)
    assert result["metric"] == 0
    assert result["state"]["last_objective_net_utility"] == 0
    assert result["active"] is False


def test_missing_and_invalid_task_evidence_are_rejected():
    missing = make_context()
    del missing["effort_cost"]
    with pytest.raises(ValueError, match="missing required input"):
        evaluate(missing, 0.8)

    impossible = make_context(actual_effect_per_effort=float("nan"))
    with pytest.raises(ValueError, match="finite number"):
        evaluate(impossible, 0.8)

    bad_levels = make_context(effort_levels=[1, 2])
    with pytest.raises(ValueError, match="start at zero"):
        evaluate(bad_levels, 0.8)


def test_invalid_strength_is_rejected():
    for strength in (-0.01, 1.01, float("inf"), float("nan"), True):
        with pytest.raises(ValueError):
            evaluate(make_context(), strength)


def test_deterministic_nonmutation_and_complete_state_preservation():
    context = make_context(state={"memo": "keep", "steps": 3, "cumulative_effort": 2,
                                  "effort_history": [0, 1, 1]})
    original = deepcopy(context)
    first = evaluate(context, 0.8)
    second = evaluate(context, 0.8)
    assert context == original
    assert first == second
    assert first["state"]["memo"] == "keep"
    assert first["state"]["steps"] == 4
    assert first["state"]["cumulative_effort"] == 4
    assert first["state"]["effort_history"] == [0, 1, 1, 2]
    assert set(METADATA["state_fields"]).issubset(first["state"])
    assert isinstance(first["trace"], list) and first["trace"]


def test_scenario_contexts_avoid_reserved_runner_fields_and_metadata_keys_are_inputs():
    scenarios_list = scenarios()
    assert {s["name"] for s in scenarios_list} >= {"positive", "boundary"}
    reserved = {"state", "peer_states", "round_index", "agent_index", "uniform"}
    for scenario in scenarios_list:
        assert scenario["contexts"]
        assert all(not reserved.intersection(context) for context in scenario["contexts"])
        assert all(set(METADATA["required_inputs"]).issubset(context) for context in scenario["contexts"])
