from copy import deepcopy

import pytest

from mechanisms import sexual_overperception_bias as plugin


def context(**overrides):
    data = {
        'direct_reciprocal_evidence': 0.1,
        'ambiguous_warmth': 0.8,
        'personalized_attention': 0.75,
        'state': {},
        'peer_states': [],
        'round_index': 0,
        'agent_index': 0,
        'uniform': 0.42,
    }
    data.update(overrides)
    return data


def test_numeric_interaction_oracle_and_trace():
    result = plugin.evaluate(context(), 0.8)
    # 0.1 + 0.8 * 0.5 * 0.8 * 0.75 * (1 - 0.1) = 0.316
    assert result['metric'] == pytest.approx(0.316)
    assert result['active'] is True
    assert result['state'] == {'last_estimate': pytest.approx(0.316), 'step_count': 1}
    assert 'ambiguous warmth' in result['trace'][0]


def test_positive_scenario_increases_over_direct_evidence_reference():
    case = plugin.scenarios()[0]
    inputs = context(**case['contexts'][0])
    baseline = plugin.evaluate(inputs, 0.0)['metric']
    intervention = plugin.evaluate(inputs, 0.8)['metric']
    assert intervention > baseline
    assert baseline == pytest.approx(0.1)


def test_boundary_removes_necessary_personal_attention_and_is_equal():
    case = plugin.scenarios()[1]
    inputs = context(**case['contexts'][0])
    assert inputs['ambiguous_warmth'] > 0  # friendliness/warmth alone remains
    baseline = plugin.evaluate(inputs, 0.0)['metric']
    intervention = plugin.evaluate(inputs, 0.8)['metric']
    assert intervention == pytest.approx(baseline)
    assert plugin.evaluate(inputs, 0.8)['active'] is False


def test_either_ambiguous_cue_alone_does_not_add_interest():
    only_warmth = plugin.evaluate(context(personalized_attention=0.0), 0.8)
    only_attention = plugin.evaluate(context(ambiguous_warmth=0.0), 0.8)
    assert only_warmth['metric'] == pytest.approx(0.1)
    assert only_attention['metric'] == pytest.approx(0.1)
    assert only_warmth['active'] is False
    assert only_attention['active'] is False


def test_zero_strength_is_explicit_reference_and_preserves_state():
    inputs = context(state={'step_count': 3, 'last_estimate': 0.2, 'caller_tag': 'kept'})
    result = plugin.evaluate(inputs, 0.0)
    assert result['metric'] == pytest.approx(inputs['direct_reciprocal_evidence'])
    assert result['state'] == {'step_count': 4, 'last_estimate': pytest.approx(0.1), 'caller_tag': 'kept'}
    assert result['active'] is False


def test_missing_and_invalid_phase_inputs_are_rejected():
    missing = context()
    del missing['personalized_attention']
    with pytest.raises(ValueError, match='missing required task input personalized_attention'):
        plugin.evaluate(missing, 0.8)
    for invalid in (-0.01, 1.01, float('nan'), float('inf'), True, '0.5'):
        with pytest.raises(ValueError):
            plugin.evaluate(context(ambiguous_warmth=invalid), 0.8)
    for invalid_strength in (-0.1, 1.1, float('nan'), True):
        with pytest.raises(ValueError, match='strength'):
            plugin.evaluate(context(), invalid_strength)


def test_deterministic_and_nonmutating_even_with_nested_state():
    original = context(state={'step_count': 2, 'last_estimate': 0.3, 'nested': {'items': [1, 2]}})
    before = deepcopy(original)
    first = plugin.evaluate(original, 0.8)
    second = plugin.evaluate(original, 0.8)
    assert original == before
    assert first == second
    assert first['state']['step_count'] == 3
    assert first['state']['nested'] == {'items': [1, 2]}
    assert first['trace'] == second['trace']


def test_metadata_and_scenarios_do_not_put_reserved_runner_fields_in_contexts():
    assert plugin.METADATA['required_inputs'] == [
        'direct_reciprocal_evidence', 'ambiguous_warmth', 'personalized_attention'
    ]
    cases = plugin.scenarios()
    assert {c['name'] for c in cases} >= {'positive', 'boundary'}
    for case in cases:
        for row in case['contexts']:
            assert not ({'state', 'peer_states', 'uniform', 'round_index', 'agent_index'} & row.keys())
