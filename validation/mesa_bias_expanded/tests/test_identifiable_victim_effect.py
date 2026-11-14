from copy import deepcopy
import math

import pytest

from mechanisms import identifiable_victim_effect as mechanism


def _context(**overrides):
    context = {
        "identified": True,
        "identified_effectiveness": 1.0,
        "anonymous_effectiveness": 1.0,
        "budget": 12.0,
        "state": {},
        "peer_states": [],
        "round_index": 0,
        "agent_index": 0,
        "uniform": 0.5,
    }
    context.update(overrides)
    return context


def _run(contexts, strength):
    state = {}
    outputs = []
    for index, task_context in enumerate(contexts):
        context = deepcopy(task_context)
        context.update(
            state=deepcopy(state),
            peer_states=[],
            round_index=index,
            agent_index=0,
            uniform=0.5,
        )
        output = mechanism.evaluate(context, strength)
        state = output["state"]
        outputs.append(output)
    return outputs


def test_positive_identity_increases_allocation_with_task_numeric_oracle():
    context = _context()
    baseline = mechanism.evaluate(context, 0.0)
    result = mechanism.evaluate(context, 0.8)

    # With equal effectiveness the specified rule gives (1 + .5*.8)/(2 + .5*.8) = 7/12.
    assert result["metric"] == pytest.approx(12.0 * 7.0 / 12.0)
    assert result["metric"] > baseline["metric"] == pytest.approx(6.0)
    assert result["active"] is True
    assert result["state"]["total_identified_help"] == pytest.approx(7.0)


def test_boundary_without_individual_identification_matches_reference():
    context = _context(identified=False)
    reference = mechanism.evaluate(context, 0.0)
    result = mechanism.evaluate(context, 0.8)

    assert result["metric"] == pytest.approx(reference["metric"])
    assert result["metric"] == pytest.approx(6.0)
    assert result["active"] is False


def test_zero_strength_is_effectiveness_proportional_reference():
    context = _context(identified_effectiveness=3.0, anonymous_effectiveness=1.0)
    result = mechanism.evaluate(context, 0.0)

    assert result["metric"] == pytest.approx(9.0)
    assert result["active"] is False
    assert result["state"]["decisions"] == 1


def test_differing_effectiveness_is_reference_not_identification_bonus():
    context = _context(identified_effectiveness=2.0, anonymous_effectiveness=1.0)
    baseline = mechanism.evaluate(context, 0.0)
    result = mechanism.evaluate(context, 0.8)

    assert result["metric"] == pytest.approx(8.0)
    assert result["metric"] == pytest.approx(baseline["metric"])
    assert result["active"] is False


def test_missing_or_invalid_evidence_is_rejected():
    with pytest.raises(ValueError, match="missing required input"):
        mechanism.evaluate(_context_without("anonymous_effectiveness"), 0.8)
    for invalid in (True, 0, -1, math.inf, math.nan):
        with pytest.raises(ValueError):
            mechanism.evaluate(_context(budget=invalid), 0.8)
    with pytest.raises(ValueError, match="identified must be a bool"):
        mechanism.evaluate(_context(identified=1), 0.8)


def _context_without(key):
    context = _context()
    del context[key]
    return context


def test_strength_range_and_numeric_type_are_validated():
    for invalid_strength in (-0.01, 1.01, math.inf, math.nan, True):
        with pytest.raises(ValueError):
            mechanism.evaluate(_context(), invalid_strength)


def test_deterministic_and_nonmutating_across_chronological_state():
    contexts = [
        _context(budget=12.0),
        _context(budget=6.0, identified_effectiveness=2.0, anonymous_effectiveness=2.0),
    ]
    before = deepcopy(contexts)
    first = _run(contexts, 0.8)
    second = _run(contexts, 0.8)

    assert contexts == before
    assert first == second
    assert first[-1]["state"]["decisions"] == 2
    assert first[-1]["state"]["total_identified_help"] == pytest.approx(10.5)
    assert all(math.isfinite(output["metric"]) for output in first)


def test_required_scenarios_include_positive_and_boundary():
    scenarios = {item["name"]: item for item in mechanism.scenarios()}
    assert set(scenarios) >= {"positive", "boundary"}
    for scenario in scenarios.values():
        assert scenario["contexts"]
        assert scenario["initial_state"] == {}
    assert _run(scenarios["positive"]["contexts"], 0.8)[-1]["metric"] > _run(
        scenarios["positive"]["contexts"], 0.0
    )[-1]["metric"]
    assert _run(scenarios["boundary"]["contexts"], 0.8)[-1]["metric"] == pytest.approx(
        _run(scenarios["boundary"]["contexts"], 0.0)[-1]["metric"]
    )
