from copy import deepcopy

import pytest

from mechanisms import naive_allocation as plugin


def context(**values):
    return {'state': {}, 'peer_states': [], 'round_index': 0, 'agent_index': 0,
            'uniform': 0.5, **values}


def paired_metric(scenario, strength):
    state = deepcopy(scenario['initial_state'])
    metrics = []
    for index, task_inputs in enumerate(scenario['contexts']):
        result = plugin.evaluate({**deepcopy(task_inputs), 'state': deepcopy(state),
                                  'peer_states': [], 'round_index': index,
                                  'agent_index': 0, 'uniform': 0.5}, strength)
        metrics.append(result['metric'])
        state = result['state']
    return metrics[-1], state


def test_numeric_allocation_oracle_and_conservation():
    result = plugin.evaluate(context(budget=100, options=[
        {'id': 'A', 'utility': 9}, {'id': 'B', 'utility': 1},
    ]), 0.8)
    assert result['state']['last_allocations'] == pytest.approx({'A': 58, 'B': 42})
    assert sum(result['state']['last_allocations'].values()) == pytest.approx(100)
    assert result['metric'] == pytest.approx(564)
    assert result['active'] is True
    assert result['state']['steps'] == 1


def test_positive_scenario_lowers_utility_yield_at_strength_point_eight():
    scenario = next(item for item in plugin.scenarios() if item['name'] == 'positive')
    reference, _ = paired_metric(scenario, 0)
    intervention, _ = paired_metric(scenario, 0.8)
    assert reference == pytest.approx(820)
    assert intervention == pytest.approx(564)
    assert intervention < reference


def test_boundary_equal_utilities_remove_necessary_condition():
    scenario = next(item for item in plugin.scenarios() if item['name'] == 'boundary')
    reference, _ = paired_metric(scenario, 0)
    intervention, state = paired_metric(scenario, 0.8)
    assert reference == intervention == pytest.approx(400)
    assert state['last_allocations'] == pytest.approx({'option_a': 50, 'option_b': 50})


def test_zero_strength_is_the_explicit_proportional_reference():
    result = plugin.evaluate(context(budget=20, options=[
        {'id': 'A', 'utility': 3}, {'id': 'B', 'utility': 1},
    ]), 0)
    assert result['state']['last_allocations'] == pytest.approx({'A': 15, 'B': 5})
    assert result['metric'] == pytest.approx(50)
    assert result['active'] is False


def test_missing_and_invalid_task_evidence_are_rejected():
    with pytest.raises(ValueError, match='budget and options'):
        plugin.evaluate(context(options=[{'id': 'A', 'utility': 1}, {'id': 'B', 'utility': 2}]), 0.5)
    with pytest.raises(ValueError, match='utility'):
        plugin.evaluate(context(budget=5, options=[{'id': 'A'}, {'id': 'B', 'utility': 1}]), 0.5)
    with pytest.raises(ValueError, match='unique'):
        plugin.evaluate(context(budget=5, options=[{'id': 'A', 'utility': 1}, {'id': 'A', 'utility': 2}]), 0.5)
    with pytest.raises(ValueError, match='nonnegative'):
        plugin.evaluate(context(budget=5, options=[{'id': 'A', 'utility': -1}, {'id': 'B', 'utility': 2}]), 0.5)


def test_invalid_strength_and_state_are_rejected():
    inputs = context(budget=5, options=[{'id': 'A', 'utility': 1}, {'id': 'B', 'utility': 2}])
    for bad in (-0.01, 1.01, float('nan'), float('inf'), True):
        with pytest.raises(ValueError, match='strength'):
            plugin.evaluate(inputs, bad)
    with pytest.raises(ValueError, match='steps'):
        plugin.evaluate({**inputs, 'state': {'steps': -1}}, 0.5)


def test_repeatable_and_nonmutating_with_nested_inputs_and_state():
    inputs = context(budget=30, options=[{'id': 'A', 'utility': 7}, {'id': 'B', 'utility': 2}],
                     state={'steps': 3, 'history': [{'note': 'untouched'}]})
    before = deepcopy(inputs)
    one = plugin.evaluate(inputs, 0.35)
    two = plugin.evaluate(inputs, 0.35)
    assert inputs == before
    assert one == two
    assert one['state']['steps'] == 4
    assert one['state']['history'] == [{'note': 'untouched'}]


def test_scenario_contexts_obey_reserved_key_boundary_and_have_required_phases():
    scenarios = plugin.scenarios()
    assert {item['name'] for item in scenarios} >= {'positive', 'boundary'}
    assert plugin.METADATA['required_inputs'] == ['budget', 'options']
    reserved = {'state', 'peer_states', 'round_index', 'agent_index', 'uniform'}
    assert all(not (reserved & context.keys()) for item in scenarios for context in item['contexts'])
    assert all({'budget', 'options'} <= context.keys() for item in scenarios for context in item['contexts'])
