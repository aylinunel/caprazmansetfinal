from copy import deepcopy

import pytest

from mechanisms import representativeness_heuristic as plugin


def direct_context(task, state=None):
    context = deepcopy(task)
    context.update({
        'state': {} if state is None else deepcopy(state),
        'peer_states': [],
        'round_index': 0,
        'agent_index': 0,
        'uniform': 0.25,
    })
    return context


def run_contexts(scenario, strength):
    state = deepcopy(scenario['initial_state'])
    results = []
    for index, task in enumerate(scenario['contexts']):
        context = direct_context(task, state)
        context['round_index'] = index
        result = plugin.evaluate(context, strength)
        state = deepcopy(result['state'])
        results.append(result)
    return results


def by_name(name):
    return next(s for s in plugin.scenarios() if s['name'] == name)


def test_numeric_score_oracle_selects_prototype_match_despite_posterior():
    scenario = by_name('positive')
    result = run_contexts(scenario, 0.8)[0]
    # A posterior is 6/7, B posterior is 1/7. Normalized similarities are .1/.9.
    expected_a = 0.2 * (6 / 7) + 0.8 * 0.1
    expected_b = 0.2 * (1 / 7) + 0.8 * 0.9
    assert expected_b > expected_a
    assert result['state']['last_choice'] == 'B'
    assert result['metric'] == 1.0
    assert 'scores=' in result['trace'][0]


def test_positive_scenario_error_increases_vs_strength_zero():
    scenario = by_name('positive')
    reference = run_contexts(scenario, 0.0)[-1]['metric']
    intervention = run_contexts(scenario, 0.8)[-1]['metric']
    assert reference == 0.0
    assert intervention > reference
    assert run_contexts(scenario, 0.8)[-1]['active'] is True


def test_boundary_equal_similarity_removes_necessary_prototype_contrast():
    scenario = by_name('boundary')
    assert scenario['contexts'][0]['options'][0]['prototype_similarity'] == scenario['contexts'][0]['options'][1]['prototype_similarity']
    reference = run_contexts(scenario, 0.0)[-1]
    intervention = run_contexts(scenario, 0.8)[-1]
    assert intervention['metric'] == reference['metric'] == 0.0
    assert intervention['state']['last_choice'] == reference['state']['last_choice'] == 'A'
    assert intervention['active'] is False


def test_zero_strength_is_explicit_posterior_reference():
    context = direct_context(by_name('positive')['contexts'][0])
    result = plugin.evaluate(context, 0.0)
    assert result['state']['last_choice'] == 'A'
    assert result['metric'] == 0.0
    assert result['active'] is False


def test_missing_and_invalid_phase_inputs_are_rejected():
    task = by_name('positive')['contexts'][0]
    missing = deepcopy(task)
    del missing['true_option']
    with pytest.raises(ValueError, match='missing required task input'):
        plugin.evaluate(direct_context(missing), 0.8)

    invalid = deepcopy(task)
    invalid['options'][0]['likelihood'] = float('nan')
    with pytest.raises(ValueError, match='finite number'):
        plugin.evaluate(direct_context(invalid), 0.8)

    zero_evidence = deepcopy(task)
    for option in zero_evidence['options']:
        option['prior'] = 0.0
    with pytest.raises(ValueError, match='positive total evidence'):
        plugin.evaluate(direct_context(zero_evidence), 0.8)


def test_evaluation_is_deterministic_and_does_not_mutate_nested_context():
    context = direct_context(by_name('positive')['contexts'][0], {'history': {'keep': [1, 2]}})
    before = deepcopy(context)
    first = plugin.evaluate(context, 0.8)
    second = plugin.evaluate(context, 0.8)
    assert context == before
    assert first == second
    assert first['state']['history'] == {'keep': [1, 2]}
    assert first['state'] is not context['state']


def test_strength_rejects_values_outside_contract():
    context = direct_context(by_name('positive')['contexts'][0])
    for strength in (-0.1, 1.1, float('inf'), True):
        with pytest.raises(ValueError, match='strength'):
            plugin.evaluate(context, strength)
