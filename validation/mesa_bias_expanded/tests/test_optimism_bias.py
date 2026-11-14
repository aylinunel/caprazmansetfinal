from copy import deepcopy

import pytest

from mechanisms import optimism_bias as mechanism


def call(context, strength):
    return mechanism.evaluate({
        **deepcopy(context),
        'state': {},
        'peer_states': [],
        'round_index': 0,
        'agent_index': 0,
        'uniform': 0.5,
    }, strength)


def run_scenario(scenario, strength):
    state = deepcopy(scenario['initial_state'])
    results = []
    for round_index, task_context in enumerate(scenario['contexts']):
        context = deepcopy(task_context)
        context.update({
            'state': deepcopy(state),
            'peer_states': [],
            'round_index': round_index,
            'agent_index': 0,
            'uniform': 0.5,
        })
        result = mechanism.evaluate(context, strength)
        state = deepcopy(result['state'])
        results.append(result)
    return results


def test_numeric_oracle_for_selective_failure_discount():
    result = call({'comparable_successes': 6, 'comparable_failures': 4}, 0.8)
    assert result['state']['reference_probability'] == pytest.approx(7 / 12)
    assert result['state']['weighted_failures'] == pytest.approx(0.8)
    assert result['metric'] == pytest.approx(7 / 8.8)
    assert result['active'] is True
    assert result['state']['forecast_probability'] == result['metric']


def test_positive_scenario_raises_forecast_relative_to_reference():
    positive = next(s for s in mechanism.scenarios() if s['name'] == 'positive')
    intervention = run_scenario(positive, 0.8)[-1]['metric']
    reference = run_scenario(positive, 0.0)[-1]['metric']
    assert intervention > reference
    assert intervention - reference == pytest.approx(7 / 8.8 - 7 / 12)


def test_boundary_without_failures_is_equal_to_reference():
    boundary = next(s for s in mechanism.scenarios() if s['name'] == 'boundary')
    intervention = run_scenario(boundary, 0.8)[-1]
    reference = run_scenario(boundary, 0.0)[-1]
    assert intervention['metric'] == pytest.approx(reference['metric'])
    assert intervention['active'] is False


def test_zero_strength_is_explicit_laplace_reference():
    result = call({'comparable_successes': 2, 'comparable_failures': 5}, 0.0)
    assert result['metric'] == pytest.approx(3 / 9)
    assert result['metric'] == pytest.approx(result['state']['reference_probability'])
    assert result['active'] is False


def test_rejects_missing_empty_and_invalid_count_inputs():
    with pytest.raises(ValueError, match='comparable_failures'):
        call({'comparable_successes': 3}, 0.8)
    with pytest.raises(ValueError, match='at least one'):
        call({'comparable_successes': 0, 'comparable_failures': 0}, 0.8)
    for invalid in (-1, 1.2, True, '4'):
        with pytest.raises(ValueError, match='nonnegative integer'):
            call({'comparable_successes': invalid, 'comparable_failures': 2}, 0.8)


def test_rejects_invalid_strength():
    context = {'comparable_successes': 2, 'comparable_failures': 3}
    for strength in (-0.1, 1.1, float('nan'), float('inf'), True):
        with pytest.raises(ValueError, match='strength'):
            call(context, strength)


def test_deterministic_and_does_not_mutate_nested_context():
    context = {
        'comparable_successes': 5,
        'comparable_failures': 3,
        'state': {'prior': {'note': 'kept by caller'}},
        'peer_states': [{'x': [1, 2]}],
        'round_index': 2,
        'agent_index': 4,
        'uniform': 0.7,
    }
    before = deepcopy(context)
    first = mechanism.evaluate(context, 0.65)
    second = mechanism.evaluate(context, 0.65)
    assert context == before
    assert first == second
    assert first['metric'] == pytest.approx(6 / (5 + 1.05 + 2))
    assert set(first['state']) == set(mechanism.METADATA['state_fields'])


def test_metadata_required_inputs_are_unconditional_scenario_keys():
    required = mechanism.METADATA['required_inputs']
    assert required == ['comparable_successes', 'comparable_failures']
    for scenario in mechanism.scenarios():
        assert all(required_key in context for required_key in required for context in scenario['contexts'])
