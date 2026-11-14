from copy import deepcopy

import pytest

from mechanisms import illusion_of_transparency as mechanism


def _run(contexts, strength, initial_state=None):
    state = deepcopy(initial_state or {})
    results = []
    for round_index, task_context in enumerate(contexts):
        context = deepcopy(task_context)
        context.update(
            state=deepcopy(state),
            peer_states=[],
            round_index=round_index,
            agent_index=0,
            uniform=0.5,
        )
        result = mechanism.evaluate(context, strength)
        results.append(result)
        state = result["state"]
    return results


def test_numeric_oracle_for_private_state_projection():
    context = {"private_intensity": 0.9, "cue_visibility": 0.2, "audience_attention": 0.8}
    result = mechanism.evaluate(context, 0.8)
    # Reference .2*.8=.16; projection .8*.9*.8*(1-.2)=.4608.
    assert result["metric"] == pytest.approx(0.6208)
    assert result["state"]["last_forecast_probability"] == pytest.approx(0.6208)
    assert result["active"] is True
    assert result["trace"]


def test_positive_scenario_increases_forecast_against_reference():
    scenario = next(s for s in mechanism.scenarios() if s["name"] == "positive")
    high = _run(scenario["contexts"], 0.8, scenario["initial_state"])[-1]["metric"]
    reference = _run(scenario["contexts"], 0.0, scenario["initial_state"])[-1]["metric"]
    assert high > reference
    assert high == pytest.approx(0.6208)


def test_boundary_removing_private_state_is_equal_to_reference():
    scenario = next(s for s in mechanism.scenarios() if s["name"] == "boundary")
    biased = _run(scenario["contexts"], 0.8, scenario["initial_state"])[-1]["metric"]
    reference = _run(scenario["contexts"], 0.0, scenario["initial_state"])[-1]["metric"]
    assert biased == pytest.approx(reference)
    assert biased == pytest.approx(0.16)


def test_zero_strength_is_explicit_cue_only_reference_and_preserves_state():
    state = {"forecast_history": [0.3], "step_count": 1, "annotation": {"keep": True}}
    result = mechanism.evaluate(
        {"private_intensity": 1.0, "cue_visibility": 0.4, "audience_attention": 0.5, "state": state},
        0.0,
    )
    assert result["metric"] == pytest.approx(0.2)
    assert result["active"] is False
    assert result["state"]["forecast_history"] == pytest.approx([0.3, 0.2])
    assert result["state"]["step_count"] == 2
    assert result["state"]["annotation"] == {"keep": True}


def test_missing_or_impossible_evidence_is_rejected():
    with pytest.raises(ValueError, match="missing required input"):
        mechanism.evaluate({"cue_visibility": 0.5, "audience_attention": 0.5}, 0.8)
    with pytest.raises(ValueError, match="private_intensity"):
        mechanism.evaluate(
            {"private_intensity": 1.1, "cue_visibility": 0.5, "audience_attention": 0.5}, 0.8
        )
    with pytest.raises(ValueError, match="strength"):
        mechanism.evaluate(
            {"private_intensity": 0.5, "cue_visibility": 0.5, "audience_attention": 0.5}, float("nan")
        )


def test_determinism_and_nonmutation_with_nested_state():
    context = {
        "private_intensity": 0.7,
        "cue_visibility": 0.3,
        "audience_attention": 0.6,
        "state": {"forecast_history": [0.1], "step_count": 1, "metadata": {"tags": ["x"]}},
    }
    before = deepcopy(context)
    first = mechanism.evaluate(context, 0.8)
    second = mechanism.evaluate(context, 0.8)
    assert context == before
    assert first == second
    assert first["state"] is not context["state"]
    assert first["state"]["metadata"] is not context["state"]["metadata"]


def test_sequence_records_one_forecast_per_supplied_round():
    contexts = [
        {"private_intensity": 0.5, "cue_visibility": 0.2, "audience_attention": 0.8},
        {"private_intensity": 0.5, "cue_visibility": 0.6, "audience_attention": 0.8},
    ]
    results = _run(contexts, 0.8)
    assert len(results) == len(contexts)
    assert results[-1]["state"]["step_count"] == 2
    assert results[-1]["state"]["forecast_history"] == pytest.approx([0.416, 0.608])
