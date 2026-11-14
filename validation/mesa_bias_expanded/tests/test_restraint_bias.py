from copy import deepcopy

import pytest

from mechanisms import restraint_bias as rb


def context(**overrides):
    data = {
        "temptation_reward": 8.0,
        "safe_reward": 1.0,
        "temptation_load": 0.75,
        "actual_resistance": 0.25,
        "self_assessed_resistance": 0.85,
        "lapse_cost": 12.0,
        "state": {},
        "peer_states": [],
        "round_index": 0,
        "agent_index": 0,
        "uniform": 0.5,
    }
    data.update(overrides)
    return data


def test_numeric_choice_oracle_uses_overconfidence_to_change_expected_payoff():
    result = rb.evaluate(context(), 0.8)
    # Estimated capacity=.25+.8*(.85-.25)=.73; p(lapse)=.75-.73=.02.
    assert result["state"]["estimated_resistance"] == pytest.approx(0.73)
    assert result["state"]["predicted_lapse_probability"] == pytest.approx(0.02)
    assert result["metric"] == 1.0
    assert result["state"]["chosen_option"] == "temptation"
    assert result["active"] is True


def test_positive_scenario_moves_toward_temptation_at_strength_point_eight():
    positive = next(s for s in rb.scenarios() if s["name"] == "positive")
    baseline = rb.evaluate({**positive["contexts"][0], "state": {}}, 0.0)
    intervention = rb.evaluate({**positive["contexts"][0], "state": {}}, 0.8)
    assert intervention["metric"] > baseline["metric"]


def test_boundary_without_overconfidence_matches_reference_choice():
    boundary = next(s for s in rb.scenarios() if s["name"] == "boundary")
    task = {**boundary["contexts"][0], "state": {}}
    assert task["self_assessed_resistance"] == task["actual_resistance"]
    assert rb.evaluate(task, 0.8)["metric"] == rb.evaluate(task, 0.0)["metric"]
    assert rb.evaluate(task, 0.8)["active"] is False


def test_zero_strength_uses_actual_capacity_as_explicit_reference():
    result = rb.evaluate(context(), 0.0)
    # Accurate reference has p(lapse)=.75-.25=.50 and expected payoff -2 < safe payoff 1.
    assert result["state"]["estimated_resistance"] == pytest.approx(0.25)
    assert result["state"]["predicted_lapse_probability"] == pytest.approx(0.50)
    assert result["metric"] == 0.0
    assert result["state"]["chosen_option"] == "safe"


def test_missing_and_invalid_phase_inputs_are_rejected():
    missing = context()
    del missing["lapse_cost"]
    with pytest.raises(ValueError, match="lapse_cost"):
        rb.evaluate(missing, 0.8)
    with pytest.raises(ValueError, match="temptation_load"):
        rb.evaluate(context(temptation_load=1.1), 0.8)
    with pytest.raises(ValueError, match="finite number"):
        rb.evaluate(context(self_assessed_resistance=float("nan")), 0.8)
    with pytest.raises(ValueError, match="strength"):
        rb.evaluate(context(), 1.01)


def test_repeatable_and_nonmutating_including_nested_state():
    task = context(state={"memo": {"prior_choice": "safe"}}, peer_states=[{"x": [1, 2]}])
    before = deepcopy(task)
    first = rb.evaluate(task, 0.8)
    second = rb.evaluate(task, 0.8)
    assert task == before
    assert first == second
    assert set(first["state"]) == set(rb.METADATA["state_fields"])
    assert first["trace"] and all(isinstance(line, str) for line in first["trace"])
    assert isinstance(first["active"], bool)
