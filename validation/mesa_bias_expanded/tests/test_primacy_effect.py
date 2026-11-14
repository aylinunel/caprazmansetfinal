from copy import deepcopy

import pytest

from mechanisms import primacy_effect as plugin


def _run(contexts, strength, initial_state=None):
    state = deepcopy(initial_state or {})
    result = None
    for index, item in enumerate(contexts):
        context = deepcopy(item)
        context.update({
            'state': deepcopy(state),
            'peer_states': [],
            'round_index': index,
            'agent_index': 0,
            'uniform': 0.5,
        })
        result = plugin.evaluate(context, strength)
        state = deepcopy(result['state'])
    return result


def _final(scenario, strength):
    return _run(scenario['contexts'], strength, scenario['initial_state'])['metric']


def test_numeric_oracle_for_two_ordered_items():
    # Item 1 multiplier=1+.6*.8*(2/2)=1.48; item 2 multiplier=1+.6*.8*(1/2)=1.24.
    # Thus impression=(.9*1.48 + .2*1.24)/(1.48+1.24).
    result = _run(plugin.scenarios()[0]['contexts'][:2], 0.8)
    assert result['metric'] == pytest.approx(1.58 / 2.72)
    assert result['state']['item_count'] == 2
    assert result['active'] is True
    assert 'ordinal position' in result['trace'][0]


def test_positive_scenario_shifts_toward_high_early_item():
    scenario = plugin.scenarios()[0]
    reference = _final(scenario, 0.0)
    treated = _final(scenario, 0.8)
    assert treated > reference


def test_boundary_without_order_cue_matches_reference():
    scenario = plugin.scenarios()[1]
    assert all(not c['order_cue_present'] for c in scenario['contexts'])
    assert _final(scenario, 0.8) == pytest.approx(_final(scenario, 0.0))


def test_zero_strength_is_exposure_distinctiveness_weighted_reference():
    contexts = [
        {'score': 0.8, 'sequence_length': 2, 'exposure': 2, 'distinctiveness': 1, 'order_cue_present': True},
        {'score': 0.2, 'sequence_length': 2, 'exposure': 1, 'distinctiveness': 1, 'order_cue_present': True},
    ]
    result = _run(contexts, 0.0)
    assert result['metric'] == pytest.approx((0.8 * 2 + 0.2) / 3)
    assert result['state']['primacy_total'] == pytest.approx(result['state']['reference_total'])
    assert result['state']['primacy_mass'] == pytest.approx(result['state']['reference_mass'])


def test_missing_and_invalid_inputs_are_rejected():
    context = deepcopy(plugin.scenarios()[0]['contexts'][0])
    with pytest.raises(ValueError, match='missing required task input score'):
        plugin.evaluate({k: v for k, v in context.items() if k != 'score'}, 0.8)
    for key, invalid in [('sequence_length', 1), ('exposure', 0), ('score', float('nan')), ('order_cue_present', 'yes')]:
        bad = deepcopy(context)
        bad[key] = invalid
        with pytest.raises(ValueError):
            plugin.evaluate(bad, 0.8)
    with pytest.raises(ValueError, match='strength'):
        plugin.evaluate(context, 1.1)


def test_evaluation_is_deterministic_and_does_not_mutate_context_or_state():
    context = deepcopy(plugin.scenarios()[0]['contexts'][1])
    context.update({
        'state': {
            'item_count': 1,
            'sequence_length': 3,
            'reference_mass': 1.0,
            'reference_total': 0.9,
            'primacy_mass': 1.48,
            'primacy_total': 1.332,
        },
        'peer_states': [], 'round_index': 1, 'agent_index': 0, 'uniform': 0.2,
    })
    before = deepcopy(context)
    first = plugin.evaluate(context, 0.8)
    second = plugin.evaluate(context, 0.8)
    assert first == second
    assert context == before
    assert first['state']['item_count'] == 2


def test_state_must_match_chronological_sequence():
    context = deepcopy(plugin.scenarios()[0]['contexts'][1])
    context.update({'state': {}, 'peer_states': [], 'round_index': 1, 'agent_index': 0, 'uniform': 0.5})
    with pytest.raises(ValueError, match='requires accumulated state'):
        plugin.evaluate(context, 0.8)


def test_impossible_carried_totals_are_rejected():
    context = deepcopy(plugin.scenarios()[0]['contexts'][1])
    context.update({
        'state': {
            'item_count': 1,
            'sequence_length': 3,
            'reference_mass': 1.0,
            'reference_total': 1.2,
            'primacy_mass': 1.48,
            'primacy_total': 1.332,
        },
        'peer_states': [], 'round_index': 1, 'agent_index': 0, 'uniform': 0.2,
    })
    with pytest.raises(ValueError, match='impossible'):
        plugin.evaluate(context, 0.8)
