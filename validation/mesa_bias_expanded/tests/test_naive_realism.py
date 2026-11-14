from copy import deepcopy

import pytest

from mechanisms import naive_realism


def make_context(**updates):
    context = {
        "own_estimate": 0.8,
        "evidence_target": 0.2,
        "evidence_weight": 0.5,
        "dissenting_estimate": 0.2,
        "self_view_as_neutral": True,
        "dissent_defect_attribution": 0.8,
        "state": {"rounds_seen": 2, "history_tag": {"keep": True}},
        "peer_states": [],
        "round_index": 2,
        "agent_index": 0,
        "uniform": 0.5,
    }
    context.update(updates)
    return context


def run_sequence(contexts, strength, initial_state=None):
    state = deepcopy(initial_state or {})
    results = []
    for index, supplied in enumerate(contexts):
        context = deepcopy(supplied)
        context.update(
            state=deepcopy(state),
            peer_states=[],
            round_index=index,
            agent_index=0,
            uniform=0.5,
        )
        result = naive_realism.evaluate(context, strength)
        results.append(result)
        state = result["state"]
    return results


def test_positive_scenario_reduces_counterevidence_weight_at_strength_point_eight():
    scenario = next(s for s in naive_realism.scenarios() if s["name"] == "positive")
    at_strength = run_sequence(scenario["contexts"], 0.8, scenario["initial_state"])[-1]["metric"]
    reference = run_sequence(scenario["contexts"], 0.0, scenario["initial_state"])[-1]["metric"]
    assert at_strength > reference
    assert at_strength == pytest.approx(0.692)
    assert reference == pytest.approx(0.5)


def test_boundary_well_supported_fact_matches_reference_when_no_disagreement():
    scenario = next(s for s in naive_realism.scenarios() if s["name"] == "boundary")
    at_strength = run_sequence(scenario["contexts"], 0.8, scenario["initial_state"])[-1]
    reference = run_sequence(scenario["contexts"], 0.0, scenario["initial_state"])[-1]
    assert at_strength["metric"] == pytest.approx(0.89)
    assert at_strength["metric"] == reference["metric"]
    assert at_strength["active"] is False


def test_zero_strength_is_the_stated_linear_reference_update():
    result = naive_realism.evaluate(make_context(), 0.0)
    # p + w(target-p) = .8 + .5(.2-.8) = .5
    assert result["metric"] == pytest.approx(0.5)
    assert result["active"] is False
    assert result["state"]["rounds_seen"] == 3


def test_each_missing_required_input_is_rejected():
    context = make_context()
    del context["dissent_defect_attribution"]
    with pytest.raises(ValueError, match="dissent_defect_attribution"):
        naive_realism.evaluate(context, 0.8)


@pytest.mark.parametrize(
    "field,value",
    [
        ("own_estimate", 1.01),
        ("evidence_weight", float("nan")),
        ("dissenting_estimate", "0.2"),
        ("self_view_as_neutral", 1),
        ("dissent_defect_attribution", -0.1),
    ],
)
def test_invalid_required_input_types_and_ranges_are_rejected(field, value):
    with pytest.raises(ValueError):
        naive_realism.evaluate(make_context(**{field: value}), 0.8)


def test_invalid_strengths_are_rejected():
    for strength in (-0.01, 1.01, float("inf"), True):
        with pytest.raises(ValueError):
            naive_realism.evaluate(make_context(), strength)


def test_evaluation_is_deterministic_nonmutating_and_preserves_extra_state():
    context = make_context()
    before = deepcopy(context)
    first = naive_realism.evaluate(context, 0.8)
    second = naive_realism.evaluate(context, 0.8)
    assert context == before
    assert first == second
    assert first["state"]["history_tag"] == {"keep": True}
    assert first["metric"] == pytest.approx(0.692)
    assert first["active"] is True
    assert len(first["trace"]) == 1


def test_missing_disagreement_or_missing_neutral_attribution_condition_uses_reference():
    for changes in (
        {"self_view_as_neutral": False},
        {"dissent_defect_attribution": 0.0},
        {"dissenting_estimate": 0.8},
        {"dissenting_estimate": 0.2, "evidence_target": 0.95},
    ):
        result = naive_realism.evaluate(make_context(**changes), 0.8)
        baseline = naive_realism.evaluate(make_context(**changes), 0.0)
        assert result["metric"] == pytest.approx(baseline["metric"])
        assert result["active"] is False
