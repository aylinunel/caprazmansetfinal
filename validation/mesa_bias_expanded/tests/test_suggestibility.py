from copy import deepcopy

import pytest

from mechanisms import suggestibility


def make_context(**overrides):
    context = {
        "target_quantity": 10.0,
        "unaided_recall": 10.0,
        "suggested_quantity": 18.0,
        "suggestion_is_external": True,
        "suggestion_is_unsupported": True,
        "independent_appraisal": 0.25,
        # Runner-reserved values are present in direct calls but are not task inputs.
        "state": {},
        "peer_states": [],
        "round_index": 0,
        "agent_index": 0,
        "uniform": 0.5,
    }
    context.update(overrides)
    return context


def run_scenario(scenario, strength):
    state = deepcopy(scenario["initial_state"])
    results = []
    for round_index, phase in enumerate(scenario["contexts"]):
        context = deepcopy(phase)
        context.update(
            state=deepcopy(state),
            peer_states=[],
            round_index=round_index,
            agent_index=0,
            uniform=0.5,
        )
        result = suggestibility.evaluate(context, strength)
        state = deepcopy(result["state"])
        results.append(result)
    return results


def test_numeric_oracle_uses_external_unsupported_suggestion_and_appraisal():
    # R = 10 + .8 * (1 - .25) * (18 - 10) = 14.8; |14.8 - 10| = 4.8.
    result = suggestibility.evaluate(make_context(), 0.8)
    assert result["metric"] == pytest.approx(4.8)
    assert result["active"] is True
    assert result["state"] == {}
    assert any("R=14.8" in line for line in result["trace"])


def test_positive_scenario_error_increases_against_strength_zero():
    scenario = next(s for s in suggestibility.scenarios() if s["name"] == "positive")
    baseline = run_scenario(scenario, 0.0)[-1]["metric"]
    influenced = run_scenario(scenario, 0.8)[-1]["metric"]
    assert baseline == pytest.approx(0.0)
    assert influenced > baseline


def test_supported_suggestion_removes_necessary_condition_at_boundary():
    scenario = next(s for s in suggestibility.scenarios() if s["name"] == "boundary")
    baseline = run_scenario(scenario, 0.0)[-1]
    intervention = run_scenario(scenario, 0.8)[-1]
    assert baseline["metric"] == pytest.approx(intervention["metric"])
    assert intervention["metric"] == pytest.approx(0.0)
    assert intervention["active"] is False


def test_zero_strength_is_explicit_unaided_recall_reference():
    result = suggestibility.evaluate(make_context(), 0.0)
    assert result["metric"] == pytest.approx(abs(10.0 - 10.0))
    assert result["active"] is False


def test_missing_and_invalid_required_inputs_are_rejected():
    missing = make_context()
    del missing["suggestion_is_unsupported"]
    with pytest.raises(ValueError, match="missing required task input"):
        suggestibility.evaluate(missing, 0.8)

    with pytest.raises(ValueError, match="independent_appraisal"):
        suggestibility.evaluate(make_context(independent_appraisal=1.1), 0.8)
    with pytest.raises(ValueError, match="finite nonnegative"):
        suggestibility.evaluate(make_context(suggested_quantity=float("nan")), 0.8)
    with pytest.raises(ValueError, match="booleans"):
        suggestibility.evaluate(make_context(suggestion_is_external=1), 0.8)
    with pytest.raises(ValueError, match="strength"):
        suggestibility.evaluate(make_context(), float("inf"))


def test_evaluation_is_deterministic_and_does_not_mutate_nested_inputs():
    context = make_context(
        state={"prior_note": {"kept": [1, 2]}},
        peer_states=[{"last": {"metric": 3.0}}],
    )
    before = deepcopy(context)
    first = suggestibility.evaluate(context, 0.65)
    second = suggestibility.evaluate(context, 0.65)
    assert context == before
    assert first == second


def test_independent_appraisal_at_full_strength_cancels_suggestion_pull():
    weak = suggestibility.evaluate(make_context(independent_appraisal=0.0), 0.8)
    full = suggestibility.evaluate(make_context(independent_appraisal=1.0), 0.8)
    assert weak["metric"] > full["metric"]
    assert full["metric"] == pytest.approx(0.0)
    assert full["active"] is False
