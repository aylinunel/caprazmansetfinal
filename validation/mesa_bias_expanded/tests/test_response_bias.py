from copy import deepcopy

import pytest

from mechanisms import response_bias


PLUGIN = response_bias
SCENARIO = {item['name']: item for item in PLUGIN.scenarios()}


def run(contexts, strength, initial_state=None):
    state = deepcopy(initial_state or {})
    results = []
    for round_index, task_context in enumerate(contexts):
        context = deepcopy(task_context)
        context.update({
            'state': deepcopy(state),
            'peer_states': [],
            'round_index': round_index,
            'agent_index': 0,
            'uniform': 0.25,
        })
        result = PLUGIN.evaluate(context, strength)
        state = deepcopy(result['state'])
        results.append(result)
    return results


def test_numeric_choice_oracle_and_cumulative_metric():
    first = SCENARIO['positive']['contexts'][0]
    context = deepcopy(first)
    context.update({'state': {}, 'peer_states': [], 'round_index': 0, 'agent_index': 0, 'uniform': 0.5})
    result = PLUGIN.evaluate(context, 0.8)
    # Scores: accurate=.75+.8*.10=.83; approved=.40+.8*.90=1.12.
    assert result['state']['responses'] == ['approved_less_accurate']
    assert result['active'] is True
    assert result['metric'] == pytest.approx(0.35)

    history = run(SCENARIO['positive']['contexts'], 0.8, SCENARIO['positive']['initial_state'])
    assert [entry['state']['responses'][-1] for entry in history] == [
        'approved_less_accurate', 'audience_favored_answer'
    ]
    assert history[-1]['state']['eligible_items'] == 2
    assert history[-1]['metric'] == pytest.approx(0.35)


def test_positive_scenario_increases_regret_over_strength_zero():
    scenario = SCENARIO['positive']
    baseline = run(scenario['contexts'], 0.0, scenario['initial_state'])[-1]
    intervention = run(scenario['contexts'], 0.8, scenario['initial_state'])[-1]
    assert baseline['metric'] == pytest.approx(0.0)
    assert intervention['metric'] > baseline['metric']


def test_boundary_removes_evaluative_audience_and_matches_reference():
    scenario = SCENARIO['boundary']
    reference = run(scenario['contexts'], 0.0, scenario['initial_state'])[-1]
    intervention = run(scenario['contexts'], 0.8, scenario['initial_state'])[-1]
    assert all(not context['evaluative_audience'] for context in scenario['contexts'])
    assert intervention['metric'] == pytest.approx(reference['metric']) == 0.0
    assert intervention['state']['eligible_items'] == 0
    assert intervention['active'] is False


def test_zero_strength_is_explicit_task_utility_reference():
    task = SCENARIO['positive']['contexts'][0]
    context = deepcopy(task)
    context.update({'state': {}, 'peer_states': [], 'round_index': 0, 'agent_index': 1, 'uniform': 0.9})
    result = PLUGIN.evaluate(context, 0.0)
    assert result['state']['responses'] == ['accurate_low_approval']
    assert result['metric'] == 0.0
    assert result['active'] is False


def test_required_and_phase_specific_inputs_are_rejected_when_missing_or_invalid():
    context = deepcopy(SCENARIO['positive']['contexts'][0])
    with pytest.raises(ValueError, match='evaluative_audience'):
        PLUGIN.evaluate({key: value for key, value in context.items() if key != 'evaluative_audience'}, 0.8)
    invalid = deepcopy(context)
    invalid['sensitive_item'] = 'yes'
    with pytest.raises(ValueError, match='sensitive_item'):
        PLUGIN.evaluate(invalid, 0.8)
    invalid = deepcopy(context)
    invalid['options'][0]['task_utility'] = float('nan')
    with pytest.raises(ValueError, match='task_utility'):
        PLUGIN.evaluate(invalid, 0.8)


def test_deterministic_and_nonmutating_even_with_nested_prior_state():
    context = deepcopy(SCENARIO['positive']['contexts'][1])
    context.update({
        'state': {'cumulative_regret': 0.1, 'eligible_items': 1, 'responses': ['prior_answer']},
        'peer_states': [{'memo': ['not read or changed']}],
        'round_index': 1,
        'agent_index': 2,
        'uniform': 0.37,
    })
    before = deepcopy(context)
    first = PLUGIN.evaluate(context, 0.8)
    second = PLUGIN.evaluate(context, 0.8)
    assert context == before
    assert first == second
    assert first['state']['responses'] == ['prior_answer', 'audience_favored_answer']
    first['state']['responses'].append('outside mutation')
    assert context == before
    assert second['state']['responses'] == ['prior_answer', 'audience_favored_answer']


def test_invalid_strength_is_rejected():
    context = deepcopy(SCENARIO['positive']['contexts'][0])
    with pytest.raises(ValueError, match='strength'):
        PLUGIN.evaluate(context, float('inf'))
    with pytest.raises(ValueError, match='strength'):
        PLUGIN.evaluate(context, True)
