from copy import deepcopy

import pytest

from mechanisms import status_quo_bias as plugin


def ctx(**updates):
    value = {
        'options': {'incumbent': 1.0, 'alternative': 1.4},
        'incumbent': 'incumbent',
        'switching_cost': 0.05,
    }
    value.update(updates)
    return value


def test_numeric_choice_oracle_uses_gap_scaled_premium_and_net_utility():
    result = plugin.evaluate(ctx(), 0.8)
    # Alternative net=1.35; gap=.35; premium=1.5*.8*.35=.42,
    # so incumbent's selection score is 1.42. Report its uninflated task utility.
    assert result['state']['last_status_quo_premium'] == pytest.approx(0.42)
    assert result['state']['selected_option'] == 'incumbent'
    assert result['metric'] == pytest.approx(1.0)
    assert result['active'] is True
    assert result['trace'] and '0.42' in result['trace'][1]


def test_positive_scenario_decreases_selected_task_utility():
    scenario = plugin.scenarios()[0]
    reference = plugin.evaluate(scenario['contexts'][0], 0.0)
    intervention = plugin.evaluate(scenario['contexts'][0], 0.8)
    assert scenario['name'] == 'positive'
    assert intervention['metric'] < reference['metric']
    assert intervention['state']['selected_option'] != reference['state']['selected_option']


def test_boundary_switching_cost_justifies_continuity_and_removes_gap():
    scenario = plugin.scenarios()[1]
    inputs = scenario['contexts'][0]
    baseline = plugin.evaluate(inputs, 0.0)
    intervention = plugin.evaluate(inputs, 0.8)
    assert inputs['options']['alternative'] - inputs['switching_cost'] < inputs['options']['incumbent']
    assert intervention['state']['last_status_quo_premium'] == 0.0
    assert intervention['state']['selected_option'] == baseline['state']['selected_option'] == 'incumbent'
    assert intervention['metric'] == baseline['metric']
    assert intervention['active'] is False


def test_zero_strength_is_explicit_cost_adjusted_reference():
    result = plugin.evaluate(ctx(), 0.0)
    assert result['state']['selected_option'] == 'alternative'
    assert result['metric'] == pytest.approx(1.35)
    assert result['state']['last_status_quo_premium'] == 0.0
    assert result['active'] is False


def test_required_and_impossible_inputs_are_rejected():
    missing = ctx()
    del missing['switching_cost']
    with pytest.raises(ValueError, match='missing required task input'):
        plugin.evaluate(missing, 0.8)
    with pytest.raises(ValueError, match='nonempty mapping'):
        plugin.evaluate(ctx(options={}), 0.8)
    with pytest.raises(ValueError, match='available option'):
        plugin.evaluate(ctx(incumbent='absent'), 0.8)
    with pytest.raises(ValueError, match='nonnegative'):
        plugin.evaluate(ctx(switching_cost=-0.1), 0.8)
    with pytest.raises(ValueError, match='finite number'):
        plugin.evaluate(ctx(options={'incumbent': 1.0, 'alternative': float('nan')}), 0.8)
    with pytest.raises(ValueError, match='finite number'):
        plugin.evaluate(ctx(), float('inf'))
    with pytest.raises(ValueError, match=r'\[0, 1\]'):
        plugin.evaluate(ctx(), 1.1)


def test_deterministic_nonmutation_and_state_carry_forward():
    inputs = ctx(state={'decision_count': 3, 'memo': {'tag': 'retain'}})
    before = deepcopy(inputs)
    first = plugin.evaluate(inputs, 0.8)
    second = plugin.evaluate(inputs, 0.8)
    assert inputs == before
    assert first == second
    assert first['state']['decision_count'] == 4
    assert first['state']['memo'] == {'tag': 'retain'}
    assert inputs['state']['decision_count'] == 3
