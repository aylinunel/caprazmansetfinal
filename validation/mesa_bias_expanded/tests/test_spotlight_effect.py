from copy import deepcopy

import pytest

from mechanisms import spotlight_effect as plugin


def context(**overrides):
    result = {
        'focal_prominence': 0.20,
        'other_prominence': 0.80,
        'self_salience': 0.90,
        'state': {},
        'peer_states': [],
        'round_index': 0,
        'agent_index': 0,
        'uniform': 0.5,
    }
    result.update(overrides)
    return result


def test_numeric_oracle_matches_normalized_reweighting_equation():
    result = plugin.evaluate(context(), 0.8)
    reference = 0.20 / (0.20 + 0.80)
    weighted_focal = 0.20 * (1.0 + 2.5 * 0.8 * 0.90)
    expected_estimate = weighted_focal / (weighted_focal + 0.80)
    assert result['state']['last_reference_share'] == pytest.approx(reference)
    assert result['state']['last_estimated_share'] == pytest.approx(expected_estimate)
    assert result['metric'] == pytest.approx(expected_estimate - reference)
    assert result['metric'] > 0
    assert result['active'] is True


def test_positive_scenario_increases_overestimate_vs_strength_zero():
    scenario = plugin.scenarios()[0]
    inputs = scenario['contexts'][0]
    baseline = plugin.evaluate({**inputs, 'state': {}}, 0.0)
    intervention = plugin.evaluate({**inputs, 'state': {}}, 0.8)
    assert scenario['name'] == 'positive'
    assert intervention['metric'] > baseline['metric']


def test_boundary_removes_self_salience_condition_and_matches_reference():
    scenario = plugin.scenarios()[1]
    inputs = scenario['contexts'][0]
    baseline = plugin.evaluate({**inputs, 'state': {}}, 0.0)
    intervention = plugin.evaluate({**inputs, 'state': {}}, 0.8)
    assert inputs['self_salience'] == 0.0
    assert intervention['metric'] == pytest.approx(baseline['metric'])
    assert intervention['active'] is False


def test_strength_zero_is_explicit_reference_policy():
    result = plugin.evaluate(context(), 0.0)
    assert result['metric'] == pytest.approx(0.0)
    assert result['state']['last_estimated_share'] == pytest.approx(0.20)
    assert result['active'] is False


def test_missing_and_impossible_or_invalid_inputs_are_rejected():
    with pytest.raises(ValueError, match='missing required'):
        plugin.evaluate(context_without('self_salience'), 0.8)
    with pytest.raises(ValueError, match='positive prominence'):
        plugin.evaluate(context(focal_prominence=0.0, other_prominence=0.0), 0.8)
    with pytest.raises(ValueError, match='finite number'):
        plugin.evaluate(context(self_salience=float('nan')), 0.8)
    with pytest.raises(ValueError, match='finite number'):
        plugin.evaluate(context(focal_prominence=True), 0.8)
    with pytest.raises(ValueError, match='strength'):
        plugin.evaluate(context(), 1.1)


def context_without(key):
    value = context()
    del value[key]
    return value


def test_deterministic_and_nonmutating_including_nested_runner_fields():
    value = context(state={'prior': {'keep': [1, 2]}}, peer_states=[{'x': [3]}])
    before = deepcopy(value)
    first = plugin.evaluate(value, 0.65)
    second = plugin.evaluate(value, 0.65)
    assert value == before
    assert first == second
    assert first['state']['prior'] == {'keep': [1, 2]}
    assert first['trace']


def test_metadata_scenarios_use_exact_shared_required_keys():
    assert plugin.METADATA['required_inputs'] == [
        'focal_prominence', 'other_prominence', 'self_salience'
    ]
    assert {scenario['name'] for scenario in plugin.scenarios()} >= {'positive', 'boundary'}
    reserved = {'state', 'peer_states', 'uniform', 'round_index', 'agent_index'}
    for scenario in plugin.scenarios():
        for phase in scenario['contexts']:
            assert not reserved.intersection(phase)
