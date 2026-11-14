from copy import deepcopy

import pytest

from mechanisms import telescoping_effect as plugin


def run_contexts(contexts, strength):
    state = {}
    outputs = []
    for index, fields in enumerate(contexts):
        context = dict(fields)
        context.update({
            'state': deepcopy(state),
            'peer_states': [],
            'round_index': index,
            'agent_index': 0,
            'uniform': 0.5,
        })
        result = plugin.evaluate(context, strength)
        state = result['state']
        outputs.append(result)
    return outputs


def test_directional_numeric_oracle_for_old_and_recent_events():
    old = plugin.evaluate({'event_id': 'old', 'event_day': 0, 'current_day': 100}, 0.8)
    assert old['state']['history'][-1]['recalled_age'] == pytest.approx(84.0)
    assert old['metric'] == pytest.approx(16.0)
    assert old['state']['history'][-1]['direction'] == 'forward'
    assert old['active'] is True

    recent = plugin.evaluate({'event_id': 'recent', 'event_day': 100, 'current_day': 110}, 0.8)
    assert recent['state']['history'][-1]['recalled_age'] == pytest.approx(11.6)
    assert recent['metric'] == pytest.approx(1.6)
    assert recent['state']['history'][-1]['direction'] == 'backward'


def test_positive_chronological_scenario_increases_final_age_error():
    scenario = next(s for s in plugin.scenarios() if s['name'] == 'positive')
    reference = run_contexts(scenario['contexts'], 0.0)[-1]['metric']
    intervention = run_contexts(scenario['contexts'], 0.8)[-1]['metric']
    assert len(run_contexts(scenario['contexts'], 0.8)[-1]['state']['history']) == 2
    assert intervention > reference
    assert intervention == pytest.approx(14.4)


def test_boundary_has_no_elapsed_age_to_shift():
    scenario = next(s for s in plugin.scenarios() if s['name'] == 'boundary')
    baseline = run_contexts(scenario['contexts'], 0.0)[-1]
    shifted = run_contexts(scenario['contexts'], 0.8)[-1]
    assert baseline['metric'] == shifted['metric'] == 0.0
    assert shifted['active'] is False
    assert shifted['state']['history'][-1]['direction'] == 'none'


def test_strength_zero_is_exact_dated_age_reference_across_history():
    contexts = [
        {'event_id': 'e1', 'event_day': 5, 'current_day': 15},
        {'event_id': 'e1', 'event_day': 5, 'current_day': 25},
    ]
    outputs = run_contexts(contexts, 0.0)
    assert [out['metric'] for out in outputs] == [0.0, 0.0]
    assert [entry['recalled_age'] for entry in outputs[-1]['state']['history']] == [10.0, 20.0]
    assert all(out['active'] is False for out in outputs)


def test_missing_and_invalid_task_evidence_is_rejected():
    with pytest.raises(ValueError, match='event_day'):
        plugin.evaluate({'event_id': 'x', 'current_day': 4}, 0.8)
    with pytest.raises(ValueError, match='later'):
        plugin.evaluate({'event_id': 'x', 'event_day': 5, 'current_day': 4}, 0.8)
    with pytest.raises(ValueError, match='finite'):
        plugin.evaluate({'event_id': 'x', 'event_day': float('nan'), 'current_day': 4}, 0.8)
    with pytest.raises(ValueError, match='strength'):
        plugin.evaluate({'event_id': 'x', 'event_day': 0, 'current_day': 4}, 1.1)


def test_history_requires_strict_chronology_and_consistent_event_dates():
    first = plugin.evaluate({'event_id': 'x', 'event_day': 0, 'current_day': 5}, 0.5)
    with pytest.raises(ValueError, match='advance strictly'):
        plugin.evaluate({
            'event_id': 'y', 'event_day': 5, 'current_day': 5,
            'state': first['state'],
        }, 0.5)
    with pytest.raises(ValueError, match='retain'):
        plugin.evaluate({
            'event_id': 'x', 'event_day': 1, 'current_day': 6,
            'state': first['state'],
        }, 0.5)


def test_evaluation_is_deterministic_and_does_not_mutate_context_or_state():
    prior = plugin.evaluate({'event_id': 'x', 'event_day': 0, 'current_day': 40}, 0.4)['state']
    context = {
        'event_id': 'x', 'event_day': 0, 'current_day': 45,
        'state': deepcopy(prior), 'peer_states': [{'history': []}],
        'round_index': 1, 'agent_index': 2, 'uniform': 0.25,
    }
    before = deepcopy(context)
    one = plugin.evaluate(context, 0.6)
    two = plugin.evaluate(context, 0.6)
    assert context == before
    assert prior['latest_day'] == 40.0
    assert one == two
