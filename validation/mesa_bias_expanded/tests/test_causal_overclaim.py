from copy import deepcopy

import pytest

from mechanisms import causal_overclaim


def context(**overrides):
    value = {
        "explicit_causal_statement": True,
        "evidence_kind": "covariation",
        "paired_observations": [[1, 2], [2, 4], [3, 6]],
        "claim_force": 0.4,
        "plausible_alternatives": 4,
        "addressed_alternatives": 1,
        "state": {"last_causal_force": 0.1, "steps_evaluated": 2},
        "peer_states": [],
        "round_index": 0,
        "agent_index": 0,
        "uniform": 0.5,
    }
    value.update(overrides)
    return value


def run_sequence(inputs, strength, initial_state=None):
    state = deepcopy(initial_state or {"last_causal_force": 0.0, "steps_evaluated": 0})
    results = []
    for index, item in enumerate(inputs):
        current = deepcopy(item)
        current.update(
            state=deepcopy(state),
            peer_states=[],
            round_index=index,
            agent_index=0,
            uniform=0.5,
        )
        result = causal_overclaim.evaluate(current, strength)
        state = result["state"]
        results.append(result)
    return results


def test_positive_direction_and_numeric_causal_force_oracle():
    result = causal_overclaim.evaluate(context(), 0.8)
    # .4 + .8 * (1 - .4) * (3 / 4) = .76
    assert result["metric"] == pytest.approx(0.76)
    assert result["metric"] > 0.4
    assert result["active"] is True
    assert result["state"]["last_causal_force"] == pytest.approx(0.76)
    assert any("force-allocation formula" in line for line in result["trace"])


def test_explicit_boundary_chronology_without_causal_claim_matches_reference():
    boundary = {
        "explicit_causal_statement": False,
        "evidence_kind": "time_order",
        "event_sequence": [
            {"event": "intervention", "time": 2},
            {"event": "outcome", "time": 5},
        ],
        "claim_force": 0.6,
        "plausible_alternatives": 3,
        "addressed_alternatives": 0,
        "state": {"last_causal_force": 0.0, "steps_evaluated": 0},
    }
    at_zero = causal_overclaim.evaluate(deepcopy(boundary), 0.0)
    at_strength = causal_overclaim.evaluate(deepcopy(boundary), 0.8)
    assert at_zero["metric"] == 0.0
    assert at_strength["metric"] == at_zero["metric"]
    assert at_strength["active"] is False


def test_zero_strength_preserves_explicit_claim_force_as_reference():
    result = causal_overclaim.evaluate(context(), 0.0)
    assert result["metric"] == pytest.approx(0.4)
    assert result["active"] is False
    assert result["state"]["steps_evaluated"] == 3


def test_all_plausible_alternatives_addressed_removes_overclaim_condition():
    no_unaddressed = context(addressed_alternatives=4)
    at_zero = causal_overclaim.evaluate(deepcopy(no_unaddressed), 0.0)
    at_strength = causal_overclaim.evaluate(deepcopy(no_unaddressed), 0.8)
    assert at_strength["metric"] == at_zero["metric"] == pytest.approx(0.4)
    assert at_strength["active"] is False


def test_missing_or_impossible_evidence_is_rejected():
    with pytest.raises(ValueError, match="paired_observations"):
        causal_overclaim.evaluate(context(paired_observations=None), 0.8)
    with pytest.raises(ValueError, match="non-zero co-variation"):
        causal_overclaim.evaluate(
            context(paired_observations=[[1, 2], [2, 2], [3, 2]]), 0.8
        )
    with pytest.raises(ValueError, match="strictly increasing"):
        causal_overclaim.evaluate(
            context(
                evidence_kind="time_order",
                event_sequence=[{"event": "a", "time": 1}, {"event": "b", "time": 1}],
            ),
            0.8,
        )


def test_required_input_types_ranges_and_strength_are_validated():
    with pytest.raises(ValueError, match="explicit_causal_statement"):
        causal_overclaim.evaluate(context(explicit_causal_statement=1), 0.8)
    with pytest.raises(ValueError, match="plausible_alternatives"):
        causal_overclaim.evaluate(context(plausible_alternatives=0), 0.8)
    with pytest.raises(ValueError, match="strength"):
        causal_overclaim.evaluate(context(), float("nan"))


def test_deterministic_and_nonmutating_with_chronological_state_carry():
    inputs = [context(), context(claim_force=0.2, addressed_alternatives=2)]
    before = deepcopy(inputs)
    first = run_sequence(inputs, 0.8)
    second = run_sequence(inputs, 0.8)
    assert inputs == before
    assert first == second
    assert first[0]["metric"] == pytest.approx(0.76)
    assert first[1]["state"]["steps_evaluated"] == 2


def test_scenarios_expose_required_positive_and_boundary_cases():
    scenarios = {scenario["name"]: scenario for scenario in causal_overclaim.scenarios()}
    assert set(("positive", "boundary")).issubset(scenarios)
    positive = run_sequence(scenarios["positive"]["contexts"], 0.8,
                            scenarios["positive"]["initial_state"])[-1]["metric"]
    positive_reference = run_sequence(scenarios["positive"]["contexts"], 0.0,
                                      scenarios["positive"]["initial_state"])[-1]["metric"]
    assert positive > positive_reference
    boundary = scenarios["boundary"]
    assert run_sequence(boundary["contexts"], 0.8, boundary["initial_state"])[-1]["metric"] == run_sequence(
        boundary["contexts"], 0.0, boundary["initial_state"]
    )[-1]["metric"]
