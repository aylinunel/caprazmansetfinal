from copy import deepcopy

import pytest

from mechanisms.less_is_better_effect import METADATA, evaluate, scenarios


OPTIONS = [
    {'label': 'compact', 'item_values': [6.0], 'total_cost': 0.5},
    {'label': 'large_bundle', 'item_values': [4.0, 4.0], 'total_cost': 2.0},
]


def direct(context, strength, state=None):
    full = deepcopy(context)
    full['state'] = {} if state is None else deepcopy(state)
    full['peer_states'] = []
    full['round_index'] = 0
    full['agent_index'] = 0
    full['uniform'] = 0.25
    return evaluate(full, strength)


def test_numeric_choice_oracle_uses_net_totals_and_per_item_scores():
    result = direct({'evaluation_mode': 'separate', 'options': OPTIONS}, 0.8)
    # compact: 6-.5=5.5 total/per-item; bundle: 8-2=6 total, 3 per-item.
    # Scores: compact 5.5; bundle .2*6 + .8*3 = 3.6.
    assert result['metric'] == pytest.approx(5.5)
    assert result['state']['last_choice'] == 'compact'
    assert result['active'] is True
    assert 'comparison scores=[5.5, 3.6]' in ' '.join(result['trace'])


def test_positive_separate_evaluation_reduces_selected_objective_value():
    context = {'evaluation_mode': 'separate', 'options': OPTIONS}
    assert direct(context, 0.8)['metric'] < direct(context, 0.0)['metric']
    assert direct(context, 0.0)['state']['last_choice'] == 'large_bundle'


def test_joint_boundary_removes_separate_evaluation_and_is_equal_to_reference():
    context = {'evaluation_mode': 'joint', 'options': OPTIONS}
    high = direct(context, 0.8)
    zero = direct(context, 0.0)
    assert high['metric'] == zero['metric'] == 6.0
    assert high['state']['last_choice'] == 'large_bundle'
    assert high['active'] is False


def test_zero_strength_is_total_net_reference_in_separate_context():
    result = direct({'evaluation_mode': 'separate', 'options': OPTIONS}, 0.0)
    assert result['metric'] == 6.0
    assert result['state']['last_choice'] == 'large_bundle'
    assert result['active'] is False


def test_rejects_missing_or_invalid_phase_specific_inputs_and_strength():
    with pytest.raises(ValueError, match='evaluation_mode'):
        direct({'options': OPTIONS}, 0.8)
    with pytest.raises(ValueError, match='exactly two'):
        direct({'evaluation_mode': 'separate', 'options': OPTIONS[:1]}, 0.8)
    bad_cost = deepcopy(OPTIONS)
    bad_cost[1]['total_cost'] = float('nan')
    with pytest.raises(ValueError, match='finite nonnegative'):
        direct({'evaluation_mode': 'separate', 'options': bad_cost}, 0.8)
    with pytest.raises(ValueError, match='strength'):
        direct({'evaluation_mode': 'separate', 'options': OPTIONS}, 1.1)


def test_deterministic_nonmutation_and_state_history_is_copied():
    context = {'evaluation_mode': 'separate', 'options': deepcopy(OPTIONS)}
    state = {'last_choice': 'previous', 'decision_count': 1, 'choice_history': ['previous']}
    before_context, before_state = deepcopy(context), deepcopy(state)
    first = direct(context, 0.8, state)
    second = direct(context, 0.8, state)
    assert first == second
    assert context == before_context
    assert state == before_state
    assert first['state'] == {
        'last_choice': 'compact', 'decision_count': 2,
        'choice_history': ['previous', 'compact'],
    }
    first['state']['choice_history'].append('external mutation')
    assert state['choice_history'] == ['previous']


def test_scenarios_have_valid_unreserved_contexts_and_metadata_inputs_are_top_level_only():
    cases = scenarios()
    assert {s['name'] for s in cases} >= {'positive', 'boundary'}
    reserved = {'state', 'peer_states', 'round_index', 'agent_index', 'uniform'}
    for scenario in cases:
        for context in scenario['contexts']:
            assert not reserved.intersection(context)
            assert set(METADATA['required_inputs']) <= set(context)
            assert set(METADATA['required_inputs']) == {'evaluation_mode', 'options'}
