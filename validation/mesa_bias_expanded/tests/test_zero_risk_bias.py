from copy import deepcopy

import pytest

from mechanisms import zero_risk_bias as mechanism


def task_context():
    return {
        "baseline_risks": {"small_event": 0.10, "common_event": 0.40},
        "harm_severities": {"small_event": 1.0, "common_event": 1.0},
        "options": {
            "eliminate_small_event": {"small_event": 0.0, "common_event": 0.39},
            "reduce_total_harm_more": {"small_event": 0.05, "common_event": 0.20},
        },
        "plan_costs": {"eliminate_small_event": 0.0, "reduce_total_harm_more": 0.0},
        "state": {},
        "peer_states": [],
        "round_index": 0,
        "agent_index": 0,
        "uniform": 0.5,
    }


def test_numeric_choice_oracle_and_real_zero_endpoint_selection():
    context = task_context()
    reference = mechanism.evaluate(context, 0.0)
    intervention = mechanism.evaluate(context, 0.8)
    assert reference["state"]["selected_option"] == "reduce_total_harm_more"
    assert reference["metric"] == pytest.approx(0.25)
    assert intervention["state"]["selected_option"] == "eliminate_small_event"
    assert intervention["metric"] == pytest.approx(0.39)
    # Gross reductions are .11 vs .25; endpoint credit is .8 * 2 * .10 = .16.
    assert intervention["state"]["selected_gross_reduction"] == pytest.approx(0.11)
    assert intervention["active"] is True


def test_positive_scenario_has_expected_increase_at_required_runner_seed():
    scenario = next(s for s in mechanism.scenarios() if s["name"] == "positive")
    context = dict(scenario["contexts"][0], state={}, peer_states=[], round_index=0, agent_index=0, uniform=0.5)
    delta = mechanism.evaluate(context, 0.8)["metric"] - mechanism.evaluate(context, 0.0)["metric"]
    assert delta > 0
    assert delta == pytest.approx(0.14)


def test_boundary_really_removes_exact_zero_condition_and_matches_reference():
    scenario = next(s for s in mechanism.scenarios() if s["name"] == "boundary")
    profiles = scenario["contexts"][0]["options"]
    assert all(value > 0 for profile in profiles.values() for value in profile.values())
    context = dict(scenario["contexts"][0], state={}, peer_states=[], round_index=0, agent_index=0, uniform=0.5)
    ref = mechanism.evaluate(context, 0.0)
    biased = mechanism.evaluate(context, 0.8)
    assert ref["state"]["selected_option"] == biased["state"]["selected_option"] == "reduce_total_harm_more"
    assert biased["metric"] == pytest.approx(ref["metric"])
    assert biased["active"] is False


def test_zero_strength_is_explicit_net_expected_harm_reduction_reference():
    context = task_context()
    result = mechanism.evaluate(context, 0.0)
    assert result["state"]["selected_option"] == "reduce_total_harm_more"
    assert result["metric"] == pytest.approx(0.20 + 0.05)
    assert result["active"] is False


def test_required_inputs_and_invalid_risk_profile_are_rejected():
    context = task_context()
    del context["options"]
    with pytest.raises(ValueError, match="options"):
        mechanism.evaluate(context, 0.8)
    invalid = task_context()
    invalid["options"]["eliminate_small_event"]["common_event"] = float("nan")
    with pytest.raises(ValueError, match="finite number"):
        mechanism.evaluate(invalid, 0.8)


def test_deterministic_and_nonmutating_including_nested_inputs():
    context = task_context()
    before = deepcopy(context)
    first = mechanism.evaluate(context, 0.8)
    second = mechanism.evaluate(context, 0.8)
    assert context == before
    assert first == second
    assert first["trace"] and isinstance(first["trace"][0], str)
    assert first["state"] is not context["state"]


def test_strength_validation_rejects_nonfinite_and_out_of_range_values():
    for strength in (-0.01, 1.01, float("nan"), float("inf"), True):
        with pytest.raises(ValueError, match="strength"):
            mechanism.evaluate(task_context(), strength)
