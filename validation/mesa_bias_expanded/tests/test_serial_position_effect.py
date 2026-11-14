from copy import deepcopy
import math

import pytest

from mechanisms import serial_position_effect as plugin


def drive(contexts, strength, initial_state=None):
    state = deepcopy(initial_state or {})
    result = None
    for round_index, task_input in enumerate(contexts):
        context = deepcopy(task_input)
        context.update({
            'state': deepcopy(state),
            'peer_states': [],
            'round_index': round_index,
            'agent_index': 0,
            'uniform': 0.25,
        })
        result = plugin.evaluate(context, strength)
        state = deepcopy(result['state'])
    return result


def five_item_contexts(target='item-1'):
    items = [
        {'phase': 'present', 'list_id': 'L', 'list_length': 5,
         'item_id': f'item-{position}', 'position': position}
        for position in range(1, 6)
    ]
    items.append({'phase': 'probe', 'list_id': 'L', 'list_length': 5,
                  'target_item': target})
    return items


def test_numeric_oracle_for_centered_combined_primacy_recency_curve():
    contexts = five_item_contexts()
    output = drive(contexts, 0.8)

    weights = [
        math.exp(-0.9 * (position - 1)) + math.exp(-0.9 * (5 - position))
        for position in range(1, 6)
    ]
    centered = weights[0] - sum(weights) / len(weights)
    expected = 1 / (1 + math.exp(-(0.8 * 1.2 * centered)))
    assert output['metric'] == pytest.approx(expected)
    assert output['metric'] > 0.5
    assert output['state']['presented_items'][-1] == {'item_id': 'item-5', 'position': 5}
    assert 'centered combined edge-kernel' in output['trace'][0]


def test_middle_target_is_less_recallable_than_boundary_target():
    edge = drive(five_item_contexts('item-1'), 0.8)['metric']
    middle = drive(five_item_contexts('item-3'), 0.8)['metric']
    assert edge > 0.5 > middle


def test_positive_scenario_direction_and_singleton_boundary_equivalence():
    positive, boundary = plugin.scenarios()
    positive_effect = drive(positive['contexts'], 0.8)['metric'] - drive(positive['contexts'], 0.0)['metric']
    boundary_effect = drive(boundary['contexts'], 0.8)['metric'] - drive(boundary['contexts'], 0.0)['metric']
    assert positive_effect > 0
    assert boundary_effect == pytest.approx(0.0, abs=1e-15)
    assert boundary['contexts'][0]['list_length'] == 1  # no positional variation exists


def test_zero_strength_is_explicit_uniform_reference_policy():
    assert drive(five_item_contexts('item-1'), 0.0)['metric'] == pytest.approx(0.5)
    assert drive(five_item_contexts('item-3'), 0.0)['metric'] == pytest.approx(0.5)
    assert drive(five_item_contexts('item-1'), 0.0)['active'] is False


def test_required_and_phase_specific_inputs_are_rejected_when_missing_or_invalid():
    with pytest.raises(ValueError, match='missing required task input phase'):
        plugin.evaluate({'list_id': 'L', 'list_length': 2}, 0.5)
    with pytest.raises(ValueError, match='position must be an integer'):
        plugin.evaluate({'phase': 'present', 'list_id': 'L', 'list_length': 1,
                         'item_id': 'x', 'position': True, 'state': {}}, 0.5)
    with pytest.raises(ValueError, match='complete chronological list history'):
        plugin.evaluate({'phase': 'probe', 'list_id': 'L', 'list_length': 1,
                         'target_item': 'x', 'state': {}}, 0.5)
    with pytest.raises(ValueError, match=r'strength must be finite'):
        plugin.evaluate({'phase': 'present', 'list_id': 'L', 'list_length': 1,
                         'item_id': 'x', 'position': 1}, float('nan'))


def test_chronological_constraints_reject_skipped_positions_and_unknown_targets():
    skipped = {'phase': 'present', 'list_id': 'L', 'list_length': 2,
               'item_id': 'second', 'position': 2, 'state': {}}
    with pytest.raises(ValueError, match='chronological'):
        plugin.evaluate(skipped, 0.8)

    contexts = five_item_contexts('absent')
    with pytest.raises(ValueError, match='target_item'):
        drive(contexts, 0.8)


def test_evaluation_is_deterministic_and_does_not_mutate_nested_input():
    task = five_item_contexts()[-1]
    state = {
        'list_id': 'L',
        'list_length': 5,
        'presented_items': [
            {'item_id': f'item-{position}', 'position': position}
            for position in range(1, 6)
        ],
        'last_metric': 0.5,
    }
    context = {**task, 'state': state, 'peer_states': [{'opaque': [1, 2]}],
               'round_index': 5, 'agent_index': 0, 'uniform': 0.75}
    before = deepcopy(context)
    first = plugin.evaluate(context, 0.8)
    second = plugin.evaluate(context, 0.8)
    assert context == before
    assert first == second
    assert first['state'] is not state
    assert first['state']['presented_items'] is not state['presented_items']


def test_scenarios_obey_reserved_context_and_metadata_contract():
    assert plugin.METADATA['required_inputs'] == ['phase', 'list_id', 'list_length']
    scenarios = plugin.scenarios()
    assert {scenario['name'] for scenario in scenarios} >= {'positive', 'boundary'}
    reserved = {'state', 'peer_states', 'uniform', 'round_index', 'agent_index'}
    assert all(not reserved.intersection(context)
               for scenario in scenarios for context in scenario['contexts'])
