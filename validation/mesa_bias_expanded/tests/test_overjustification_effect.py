from copy import deepcopy

import pytest

from mechanisms import overjustification_effect as mechanism


def run(contexts, strength):
    state = deepcopy(mechanism.scenarios()[0]["initial_state"])
    outputs = []
    for index, task_input in enumerate(contexts):
        context = deepcopy(task_input)
        context.update(state=deepcopy(state), peer_states=[], round_index=index, agent_index=0, uniform=0.5)
        result = mechanism.evaluate(context, strength)
        state = result["state"]
        outputs.append(result)
    return outputs


def test_numeric_oracle_accumulates_reward_exposure_and_applies_conjunction():
    contexts = [
        {"phase": "baseline", "intrinsic_interest": 0.75, "reward_contingent": False, "reward_salience": 0.0, "baseline_choice_minutes": 12.0},
        {"phase": "reward", "intrinsic_interest": 0.75, "reward_contingent": True, "reward_salience": 0.4, "baseline_choice_minutes": 12.0},
        {"phase": "reward", "intrinsic_interest": 0.75, "reward_contingent": True, "reward_salience": 0.5, "baseline_choice_minutes": 12.0},
        {"phase": "post_reward", "intrinsic_interest": 0.75, "reward_contingent": False, "reward_salience": 0.0, "baseline_choice_minutes": 12.0},
    ]
    result = run(contexts, 0.8)[-1]
    dose = 1 - (1 - 0.4) * (1 - 0.5)
    expected = 12 * (1 - 0.8 * 0.75 * dose)
    assert result["metric"] == pytest.approx(expected)
    assert result["state"]["reward_dose"] == pytest.approx(dose)
    assert result["active"] is True
    assert "baseline_minutes×" in result["trace"][0]


def test_positive_scenario_reduces_final_probe_metric_vs_strength_zero():
    scenario = mechanism.scenarios()[0]
    at_zero = run(scenario["contexts"], 0.0)[-1]["metric"]
    at_intervention = run(scenario["contexts"], 0.8)[-1]["metric"]
    assert at_zero == pytest.approx(10.0)
    assert at_intervention < at_zero
    assert at_intervention == pytest.approx(10 * (1 - 0.8 * 0.8 * 0.7))


def test_no_prior_intrinsic_interest_is_a_real_boundary():
    scenario = mechanism.scenarios()[1]
    at_zero = run(scenario["contexts"], 0.0)[-1]["metric"]
    at_intervention = run(scenario["contexts"], 0.8)[-1]["metric"]
    assert scenario["contexts"][0]["intrinsic_interest"] == 0.0
    assert run(scenario["contexts"], 0.8)[1]["state"]["reward_dose"] > 0
    assert at_intervention == at_zero == 10.0
    assert run(scenario["contexts"], 0.8)[-1]["active"] is False


def test_strength_zero_is_the_unchanged_baseline_reference():
    scenario = mechanism.scenarios()[0]
    outputs = run(scenario["contexts"], 0.0)
    assert outputs[-1]["metric"] == outputs[0]["metric"]
    assert outputs[-1]["state"]["completed"] is True
    assert outputs[-1]["active"] is False


def test_missing_and_invalid_phase_specific_inputs_are_rejected():
    baseline = mechanism.scenarios()[0]["contexts"][0]
    with pytest.raises(ValueError, match="missing required task input"):
        mechanism.evaluate({key: value for key, value in baseline.items() if key != "intrinsic_interest"}, 0.8)
    invalid = dict(baseline, intrinsic_interest=float("nan"))
    with pytest.raises(ValueError, match="intrinsic_interest"):
        mechanism.evaluate(invalid, 0.8)
    with pytest.raises(ValueError, match="contingent reward"):
        mechanism.evaluate(dict(baseline, reward_contingent=True), 0.8)


def test_post_reward_requires_a_real_preceding_reward_and_baseline():
    post = mechanism.scenarios()[0]["contexts"][-1]
    fresh = dict(post, state=deepcopy(mechanism.scenarios()[0]["initial_state"]))
    with pytest.raises(ValueError, match="preceding baseline"):
        mechanism.evaluate(fresh, 0.8)
    baseline_state = mechanism.evaluate(mechanism.scenarios()[0]["contexts"][0], 0.8)["state"]
    fresh["state"] = baseline_state
    with pytest.raises(ValueError, match="preceding contingent reward"):
        mechanism.evaluate(fresh, 0.8)


def test_deterministic_and_nonmutating_for_context_and_nested_state():
    context = mechanism.scenarios()[0]["contexts"][1]
    context["state"] = {
        "baseline_seen": True, "baseline_interest": 0.8,
        "baseline_minutes": 10.0, "reward_dose": 0.0, "completed": False,
        "auxiliary": {"kept": [1, 2]},
    }
    before = deepcopy(context)
    first = mechanism.evaluate(context, 0.8)
    second = mechanism.evaluate(context, 0.8)
    assert context == before
    assert first == second
    assert first["state"]["auxiliary"] == {"kept": [1, 2]}


def test_invalid_strengths_are_rejected():
    baseline = mechanism.scenarios()[0]["contexts"][0]
    for value in (-0.01, 1.01, float("inf"), float("nan"), True):
        with pytest.raises(ValueError, match="strength"):
            mechanism.evaluate(baseline, value)
