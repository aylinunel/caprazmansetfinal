from copy import deepcopy
import math

import pytest

from mechanisms import present_bias as pb


def direct(context, strength, state=None, round_index=0):
    supplied = deepcopy(context)
    supplied.update({
        "state": deepcopy(state if state is not None else {"choice_history": []}),
        "peer_states": [],
        "round_index": round_index,
        "agent_index": 0,
        "uniform": 0.25,
    })
    return pb.evaluate(supplied, strength)


def run_scenario(scenario, strength):
    state = deepcopy(scenario["initial_state"])
    result = None
    for i, phase in enumerate(scenario["contexts"]):
        result = direct(phase, strength, state, i)
        state = result["state"]
    return result


def test_numeric_choice_oracle_matches_quasi_hyperbolic_equation():
    phase = {
        "options": [{"id": "now", "payoff": 8, "delay": 0}, {"id": "later", "payoff": 10, "delay": 1}],
        "discount_rate": 0.1,
        "present_weight": 0.5,
    }
    # At strength .8, beta_s=.6: later value is 10*exp(-.1)*.6 < 8.
    intervention = direct(phase, 0.8)
    reference = direct(phase, 0.0)
    assert 10 * math.exp(-0.1) * 0.6 < 8 < 10 * math.exp(-0.1)
    assert intervention["state"]["choice_history"][-1]["choice"] == "now"
    assert intervention["metric"] == 1.0
    assert intervention["active"] is True
    assert reference["state"]["choice_history"][-1]["choice"] == "later"
    assert reference["metric"] == 0.0


def test_positive_scenario_moves_immediate_choice_metric_up():
    positive = next(s for s in pb.scenarios() if s["name"] == "positive")
    high = run_scenario(positive, 0.8)
    baseline = run_scenario(positive, 0.0)
    assert high["metric"] > baseline["metric"]
    assert high["state"]["choice_history"][-1]["round"] == 1
    assert len(high["state"]["choice_history"]) == 2


def test_boundary_removes_temporal_contrast_and_matches_reference():
    boundary = next(s for s in pb.scenarios() if s["name"] == "boundary")
    for phase in boundary["contexts"]:
        assert phase["options"][0]["delay"] == phase["options"][1]["delay"]
    assert run_scenario(boundary, 0.8)["metric"] == run_scenario(boundary, 0.0)["metric"]
    # The shared discount factor still determines a real nonzero-delay choice.
    got = run_scenario(boundary, 0.8)
    assert got["state"]["choice_history"][-1]["choice"] == "larger"


def test_zero_strength_is_the_exponential_reference_policy():
    phase = pb.scenarios()[0]["contexts"][0]
    result = direct(phase, 0.0)
    assert result["state"]["choice_history"][-1]["choice"] == "later"
    assert result["metric"] == 0.0
    assert result["active"] is False
    assert "strength-zero reference selects later" in result["trace"][0]


def test_missing_and_invalid_task_evidence_are_rejected():
    phase = pb.scenarios()[0]["contexts"][0]
    incomplete = deepcopy(phase)
    del incomplete["present_weight"]
    with pytest.raises(ValueError, match="missing required"):
        direct(incomplete, 0.8)
    invalid = deepcopy(phase)
    invalid["options"][1]["delay"] = -1
    with pytest.raises(ValueError, match="delay"):
        direct(invalid, 0.8)
    invalid_pair = deepcopy(phase)
    invalid_pair["options"][1]["payoff"] = float("nan")
    with pytest.raises(ValueError, match="finite"):
        direct(invalid_pair, 0.8)


def test_strength_must_be_finite_and_in_range():
    phase = pb.scenarios()[0]["contexts"][0]
    for invalid in (-0.01, 1.01, float("inf"), float("nan"), True):
        with pytest.raises(ValueError, match="strength"):
            direct(phase, invalid)


def test_deterministic_nonmutation_and_chronological_state_copy():
    phase = pb.scenarios()[0]["contexts"][0]
    prior = {"choice_history": [{"round": 0, "choice": "earlier_record"}]}
    context = deepcopy(phase)
    context.update({"state": prior, "peer_states": [], "round_index": 1, "agent_index": 2, "uniform": 0.7})
    frozen = deepcopy(context)
    first = pb.evaluate(context, 0.8)
    second = pb.evaluate(context, 0.8)
    assert context == frozen
    assert first == second
    assert len(prior["choice_history"]) == 1
    assert first["state"]["choice_history"] == prior["choice_history"] + [
        {"round": 1, "choice": "now", "delay": 0.0, "payoff": 8.0}
    ]
    assert first["trace"] and isinstance(first["active"], bool)
