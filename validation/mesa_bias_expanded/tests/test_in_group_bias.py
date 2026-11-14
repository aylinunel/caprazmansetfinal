from copy import deepcopy

import pytest

from mechanisms import in_group_bias


def _context(data, state=None):
    result = deepcopy(data)
    result.update({
        'state': {} if state is None else state,
        'peer_states': [],
        'round_index': 0,
        'agent_index': 0,
        'uniform': 0.5,
    })
    return result


def _scenario(name):
    return next(item for item in in_group_bias.scenarios() if item['name'] == name)


def test_positive_strength_changes_choice_and_reduces_selected_qualification():
    case = _scenario('positive')
    data = case['contexts'][0]
    reference = in_group_bias.evaluate(_context(data), 0)
    biased = in_group_bias.evaluate(_context(data), 0.8)

    # Numeric/choice oracle: 82 + .8*15 = 94 outranks 90, while baseline selects 90.
    assert reference['state']['selected_id'] == 'other'
    assert reference['metric'] == 90
    assert biased['state']['selected_id'] == 'colleague'
    assert biased['state']['adjusted_scores'] == {'colleague': 94.0, 'other': 90.0}
    assert biased['metric'] == 82
    assert biased['metric'] < reference['metric']
    assert case['expectation'] == 'decrease'
    assert biased['active'] is True


def test_boundary_without_in_group_candidate_matches_reference_metric():
    case = _scenario('boundary')
    data = case['contexts'][0]
    reference = in_group_bias.evaluate(_context(data), 0)
    at_strength = in_group_bias.evaluate(_context(data), 0.8)

    assert reference['metric'] == at_strength['metric'] == 90
    assert reference['state']['selected_id'] == at_strength['state']['selected_id'] == 'candidate-b'
    assert at_strength['active'] is False
    assert case['expectation'] == 'equal'


def test_zero_strength_is_qualification_only_reference_and_preserves_prior_state():
    data = _scenario('positive')['contexts'][0]
    result = in_group_bias.evaluate(_context(data, {'notes': 'kept'}), 0)

    assert result['state']['selected_id'] == 'other'
    assert result['state']['reference_selected_id'] == 'other'
    assert result['state']['selection_changed_from_reference'] is False
    assert result['state']['notes'] == 'kept'
    assert result['active'] is False
    assert result['metric'] == 90


def test_missing_or_impossible_evidence_is_rejected():
    with pytest.raises(ValueError, match='missing required input: candidates'):
        in_group_bias.evaluate(_context({'group_bonus': 2}), 0.5)
    with pytest.raises(ValueError, match='qualification'):
        in_group_bias.evaluate(_context({
            'candidates': [
                {'id': 'a', 'qualification': float('nan'), 'same_group': True},
                {'id': 'b', 'qualification': 50, 'same_group': False},
            ],
            'group_bonus': 2,
        }), 0.5)
    with pytest.raises(ValueError, match='same_group must be bool'):
        in_group_bias.evaluate(_context({
            'candidates': [
                {'id': 'a', 'qualification': 60, 'same_group': 1},
                {'id': 'b', 'qualification': 50, 'same_group': False},
            ],
            'group_bonus': 2,
        }), 0.5)


def test_invalid_strength_and_ranges_are_rejected():
    data = _scenario('positive')['contexts'][0]
    for strength in (-0.01, 1.01, float('inf'), float('nan'), True):
        with pytest.raises(ValueError, match='strength'):
            in_group_bias.evaluate(_context(data), strength)
    invalid = deepcopy(data)
    invalid['group_bonus'] = 101
    with pytest.raises(ValueError, match='group_bonus'):
        in_group_bias.evaluate(_context(invalid), 0.5)


def test_deterministic_and_nonmutating_including_nested_inputs():
    original = _scenario('positive')['contexts'][0]
    context = _context(original, {'history': ['prior']})
    before = deepcopy(context)

    first = in_group_bias.evaluate(context, 0.8)
    second = in_group_bias.evaluate(context, 0.8)

    assert context == before
    assert first == second
    assert first['metric'] == 82
    assert all(isinstance(line, str) and line for line in first['trace'])


def test_output_is_finite_and_state_record_is_complete():
    result = in_group_bias.evaluate(_context(_scenario('positive')['contexts'][0]), 0.8)

    assert isinstance(result['metric'], (int, float))
    assert result['metric'] == result['metric']  # not NaN
    assert set(('selected_id', 'reference_selected_id', 'adjusted_scores',
                'selection_changed_from_reference')).issubset(result['state'])
    assert result['state']['selection_changed_from_reference'] is True
