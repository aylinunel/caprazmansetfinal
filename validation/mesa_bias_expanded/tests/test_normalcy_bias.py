from copy import deepcopy
import math

import pytest

from mechanisms import normalcy_bias as nb


def phase(context, strength, state=None, round_index=0):
    ctx = deepcopy(context)
    ctx.update({
        "state": deepcopy({} if state is None else state),
        "peer_states": [],
        "round_index": round_index,
        "agent_index": 0,
        "uniform": 0.25,
    })
    return nb.evaluate(ctx, strength)


def run_scenario(scenario, strength):
    state = deepcopy(scenario["initial_state"])
    result = None
    for index, context in enumerate(scenario["contexts"]):
        result = phase(context, strength, state, index)
        state = result["state"]
    return result


def test_numeric_choice_oracle_selectively_discounts_warning_evidence():
    ctx = {
        "base_disruption_probability": 0.1,
        "warning_credible": True,
        "warning_likelihood_ratio": 9.0,
        "disruption_loss": 100.0,
        "precaution_cost": 40.0,
    }
    reference = phase(ctx, 0.0)
    biased = phase(ctx, 0.8)
    # Prior odds=1/9. Full LR=9 yields p=.5; the reference prepares at
    # expected loss 50>=40. At .8, the LR exponent is 1-.8*.8=.36.
    expected_perceived = (1.0 / 9.0 * (9.0 ** 0.36)) / (1.0 + 1.0 / 9.0 * (9.0 ** 0.36))
    assert reference["state"]["objective_log_odds"] == pytest.approx(0.0)
    assert biased["state"]["perceived_log_odds"] == pytest.approx(math.log(1 / 9) + 0.36 * math.log(9))
    assert 1 / (1 + math.exp(-biased["state"]["perceived_log_odds"])) == pytest.approx(expected_perceived)
    assert reference["state"]["prepared"] is True
    assert biased["state"]["prepared"] is False
    assert reference["metric"] == pytest.approx(40.0)
    assert biased["metric"] == pytest.approx(50.0)
    assert biased["active"] is True


def test_positive_chronological_scenario_increases_final_loss_at_strength_point8():
    positive = next(s for s in nb.scenarios() if s["name"] == "positive")
    assert len(positive["contexts"]) >= 2
    reference = run_scenario(positive, 0.0)
    intervention = run_scenario(positive, 0.8)
    assert intervention["metric"] > reference["metric"]
    assert intervention["state"]["credible_warning_count"] == 2
    assert intervention["state"]["perceived_log_odds"] < intervention["state"]["objective_log_odds"]


def test_boundary_without_credible_warning_equals_strength_zero():
    boundary = next(s for s in nb.scenarios() if s["name"] == "boundary")
    assert all(not ctx["warning_credible"] and ctx["warning_likelihood_ratio"] > 1
               for ctx in boundary["contexts"])
    reference = run_scenario(boundary, 0.0)
    intervention = run_scenario(boundary, 0.8)
    assert intervention["metric"] == pytest.approx(reference["metric"])
    assert intervention["state"] == reference["state"]
    assert intervention["state"]["credible_warning_count"] == 0


def test_zero_strength_is_explicit_full_evidence_reference():
    context = {
        "base_disruption_probability": 0.2,
        "warning_credible": True,
        "warning_likelihood_ratio": 4.0,
        "disruption_loss": 80.0,
        "precaution_cost": 30.0,
    }
    result = phase(context, 0.0)
    assert result["state"]["objective_log_odds"] == pytest.approx(result["state"]["perceived_log_odds"])
    assert result["active"] is False
    assert "perceived log-odds" in result["trace"][0]


def test_missing_and_invalid_phase_specific_inputs_are_rejected():
    good = {
        "base_disruption_probability": 0.1,
        "warning_credible": True,
        "warning_likelihood_ratio": 3.0,
        "disruption_loss": 20.0,
        "precaution_cost": 5.0,
    }
    for missing in ("warning_credible", "warning_likelihood_ratio", "disruption_loss", "precaution_cost"):
        invalid = dict(good)
        del invalid[missing]
        with pytest.raises(ValueError):
            phase(invalid, 0.5)
    for key, value in (("base_disruption_probability", 1.0),
                       ("warning_likelihood_ratio", 0.5),
                       ("disruption_loss", float("nan")),
                       ("warning_credible", "yes")):
        invalid = dict(good)
        invalid[key] = value
        with pytest.raises(ValueError):
            phase(invalid, 0.5)
    with pytest.raises(ValueError):
        phase(good, float("inf"))


def test_deterministic_and_nonmutating_for_nested_inputs_and_prior_state():
    context = {
        "base_disruption_probability": 0.05,
        "warning_credible": True,
        "warning_likelihood_ratio": 8.0,
        "disruption_loss": 100.0,
        "precaution_cost": 55.0,
        "state": {},
        "peer_states": [{"memo": [1, 2]}],
        "round_index": 2,
        "agent_index": 1,
        "uniform": 0.75,
    }
    before = deepcopy(context)
    first = nb.evaluate(context, 0.8)
    second = nb.evaluate(context, 0.8)
    assert context == before
    assert first == second
    assert first["state"] is not context["state"]
    # A later phase advances a copied state without modifying the prior snapshot.
    prior = deepcopy(first["state"])
    later = phase({k: v for k, v in before.items() if k not in {"state", "peer_states", "round_index", "agent_index", "uniform"}},
                  0.8, prior, 3)
    assert prior == first["state"]
    assert later["state"]["credible_warning_count"] == 2
