from copy import deepcopy

import pytest

from mechanisms import nostalgia_effect


def _scenario(name):
    return next(item for item in nostalgia_effect.scenarios() if item['name'] == name)


def _run(scenario, strength):
    state = deepcopy(scenario['initial_state'])
    outputs = []
    for round_index, data in enumerate(scenario['contexts']):
        context = deepcopy(data)
        context.update({
            'state': deepcopy(state), 'peer_states': [],
            'round_index': round_index, 'agent_index': 0, 'uniform': 0.5,
        })
        result = nostalgia_effect.evaluate(context, strength)
        state = deepcopy(result['state'])
        outputs.append(result)
    return outputs


def test_numeric_oracle_and_positive_direction_for_matched_warm_memory():
    case = _scenario('positive')
    reference = _run(case, 0)[-1]
    intervention = _run(case, 0.8)[-1]

    # 0.8 × 0.9 warmth × 0.8 match × 4 = 2.304; WTP rises to 10.804.
    assert reference['state']['reference_wtp'] == 8.5
    assert reference['metric'] == 0.0
    assert intervention['state']['reservation_adjustment'] == pytest.approx(2.304)
    assert intervention['state']['adjusted_wtp'] == pytest.approx(10.804)
    assert intervention['state']['purchased'] is True
    assert intervention['metric'] == 10.0
    assert intervention['metric'] > reference['metric']
    assert intervention['active'] is True


def test_scenario_positive_direction_at_strength_point_eight():
    case = _scenario('positive')
    assert case['expectation'] == 'increase'
    assert _run(case, 0.8)[-1]['metric'] > _run(case, 0)[-1]['metric']


def test_boundary_mismatched_memory_link_matches_strength_zero():
    case = _scenario('boundary')
    assert case['contexts'][1]['item_memory_link'] != case['contexts'][0]['episode_id']
    reference = _run(case, 0)[-1]
    intervention = _run(case, 0.8)[-1]
    assert reference['metric'] == intervention['metric'] == 0.0
    assert intervention['state']['reservation_adjustment'] == 0.0
    assert intervention['state']['adjusted_wtp'] == 8.5
    assert intervention['active'] is False
    assert case['expectation'] == 'equal'


def test_zero_strength_is_explicit_baseline_reference_and_memory_alone_has_no_spend():
    outputs = _run(_scenario('positive'), 0)
    assert outputs[0]['metric'] == 0.0
    assert outputs[0]['active'] is False
    final = outputs[-1]
    assert final['state']['reference_wtp'] == final['state']['adjusted_wtp'] == 8.5
    assert final['state']['reservation_adjustment'] == 0.0
    assert final['state']['purchased'] is False
    assert final['metric'] == 0.0


def test_missing_phase_specific_evidence_and_invalid_values_are_rejected():
    with pytest.raises(ValueError, match='missing required input: phase'):
        nostalgia_effect.evaluate({}, 0.5)
    with pytest.raises(ValueError, match='memory phase missing required input: episode_id'):
        nostalgia_effect.evaluate({'phase': 'memory'}, 0.5)
    bad_memory = deepcopy(_scenario('positive')['contexts'][0])
    bad_memory['event_year'] = bad_memory['observed_year']
    with pytest.raises(ValueError, match='must precede'):
        nostalgia_effect.evaluate(bad_memory, 0.5)
    with pytest.raises(ValueError, match='warmth'):
        nostalgia_effect.evaluate({**_scenario('positive')['contexts'][0], 'warmth': float('nan')}, 0.5)
    with pytest.raises(ValueError, match='strength'):
        nostalgia_effect.evaluate(_scenario('positive')['contexts'][0], float('inf'))


def test_purchase_requires_prior_chronological_memory_and_valid_purchase_facts():
    purchase = deepcopy(_scenario('positive')['contexts'][1])
    with pytest.raises(ValueError, match='prior memory-phase state'):
        nostalgia_effect.evaluate({'phase': 'purchase', **purchase}, 0.8)
    memory_result = nostalgia_effect.evaluate(_scenario('positive')['contexts'][0], 0.8)
    context = {'phase': 'purchase', **purchase, 'state': memory_result['state']}
    context['current_year'] = 2025
    with pytest.raises(ValueError, match='cannot precede'):
        nostalgia_effect.evaluate(context, 0.8)
    context['current_year'] = 2026
    context['association_strength'] = 1.1
    with pytest.raises(ValueError, match='association_strength'):
        nostalgia_effect.evaluate(context, 0.8)


def test_deterministic_nonmutating_complete_state_and_trace():
    context = deepcopy(_scenario('positive')['contexts'][0])
    context.update({'state': {'memo': ['retained']}, 'peer_states': [],
                    'round_index': 0, 'agent_index': 2, 'uniform': 0.75})
    before = deepcopy(context)
    first = nostalgia_effect.evaluate(context, 0.8)
    second = nostalgia_effect.evaluate(context, 0.8)
    assert context == before
    assert first == second
    assert first['state']['memo'] == ['retained']
    assert first['state']['memory_episode']['episode_id'] == 'summer-fair'
    assert all(isinstance(line, str) and line for line in first['trace'])
    assert first['active'] is False


def test_scenario_contexts_respect_reserved_fields_and_metadata_required_inputs():
    assert nostalgia_effect.METADATA['required_inputs'] == ['phase']
    for scenario in nostalgia_effect.scenarios():
        for context in scenario['contexts']:
            assert not {'state', 'peer_states', 'uniform', 'round_index', 'agent_index'} & context.keys()
