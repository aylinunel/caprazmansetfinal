from copy import deepcopy

import pytest

from mechanisms import motivating_uncertainty_effect as mechanism


POSITIVE = {
    'reward_mean': 0.8,
    'reward_spread': 3.0,
    'effort_cost': 2.0,
    'pursuit_focus': 1.0,
    'effort_cap': 4,
}


def run_contexts(contexts, strength, initial_state=None):
    """Call the plugin chronologically, carrying task state between contexts."""
    state = deepcopy(initial_state or {})
    results = []
    for round_index, task_inputs in enumerate(contexts):
        context = deepcopy(task_inputs)
        context.update({
            'state': deepcopy(state),
            'peer_states': [],
            'round_index': round_index,
            'agent_index': 0,
            'uniform': 0.5,
        })
        result = mechanism.evaluate(context, strength)
        state = deepcopy(result['state'])
        results.append(result)
    return results


def test_numeric_choice_oracle_selects_effort_one_and_explains_premium():
    result = mechanism.evaluate(POSITIVE, 0.8)
    # At effort 0..4, utilities are [0, 1, 0, -3, -8]; the unique maximum is 1.
    assert result['metric'] == 1
    assert result['state']['chosen_effort'] == 1
    assert result['state']['chosen_utility'] == pytest.approx(1.0)
    assert result['state']['uncertainty_premium'] == pytest.approx(1.2)
    assert 'reward_spread*pursuit_focus' in result['trace'][0]
    assert result['active'] is True


def test_positive_scenario_increases_effort_vs_same_task_reference():
    scenario = next(s for s in mechanism.scenarios() if s['name'] == 'positive')
    reference = run_contexts(scenario['contexts'], 0.0, scenario['initial_state'])[-1]
    intervention = run_contexts(scenario['contexts'], 0.8, scenario['initial_state'])[-1]
    assert intervention['metric'] > reference['metric']


def test_boundary_removes_uncertainty_and_matches_reference():
    scenario = next(s for s in mechanism.scenarios() if s['name'] == 'boundary')
    assert scenario['contexts'][0]['reward_spread'] == 0.0
    reference = run_contexts(scenario['contexts'], 0.0)[-1]
    intervention = run_contexts(scenario['contexts'], 0.8)[-1]
    assert intervention['metric'] == reference['metric'] == 0
    assert intervention['active'] is False


def test_strength_zero_is_expected_reward_minus_effort_cost_reference():
    result = mechanism.evaluate(POSITIVE, 0.0)
    # U(e)=0.8e - 2e^2/2; the best discrete option is no effort.
    assert result['metric'] == 0
    assert result['state']['uncertainty_premium'] == 0.0
    assert result['active'] is False


def test_missing_and_invalid_task_inputs_are_rejected():
    missing = dict(POSITIVE)
    del missing['pursuit_focus']
    with pytest.raises(ValueError, match='pursuit_focus'):
        mechanism.evaluate(missing, 0.8)

    for key, invalid in [
        ('reward_spread', -0.1),
        ('pursuit_focus', 1.1),
        ('effort_cost', float('nan')),
        ('effort_cap', True),
    ]:
        context = dict(POSITIVE, **{key: invalid})
        with pytest.raises(ValueError):
            mechanism.evaluate(context, 0.8)
    with pytest.raises(ValueError, match='strength'):
        mechanism.evaluate(POSITIVE, float('inf'))


def test_deterministic_and_nonmutating_with_nested_prior_state():
    context = dict(POSITIVE, state={'memo': {'tag': 'keep'}, 'older': 7})
    before = deepcopy(context)
    first = mechanism.evaluate(context, 0.8)
    second = mechanism.evaluate(context, 0.8)
    assert first == second
    assert context == before
    assert first['state']['memo'] == {'tag': 'keep'}
    assert first['state']['older'] == 7


def test_scenarios_have_contract_names_and_no_runner_reserved_context_fields():
    scenarios = mechanism.scenarios()
    assert {'positive', 'boundary'} <= {s['name'] for s in scenarios}
    reserved = {'state', 'peer_states', 'uniform', 'round_index', 'agent_index'}
    assert all(not (reserved & set(c)) for s in scenarios for c in s['contexts'])
    assert all(set(c) == set(mechanism.METADATA['required_inputs'])
               for s in scenarios for c in s['contexts'])
