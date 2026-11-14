from copy import deepcopy

import pytest

from mechanisms.take_the_best_heuristic import METADATA, evaluate, scenarios


def positive_context(**overrides):
    context = {
        'options': ['A', 'B'],
        'cue_order': ['priority_cue', 'secondary_cue'],
        'cue_values': {
            'priority_cue': {'A': 1.0, 'B': 0.0},
            'secondary_cue': {'A': 0.0, 'B': 3.0},
        },
        'minimum_difference': 1.0,
        'task_scores': {'A': 9.0, 'B': 4.0},
        'uniform': 0.1,
        'state': {'choice_history': ['older-choice'], 'last_choice': 'B'},
        'peer_states': [], 'round_index': 1, 'agent_index': 0,
    }
    context.update(overrides)
    return context


def test_numeric_choice_oracle_first_discriminating_cue_beats_aggregate():
    result = evaluate(positive_context(), 0.8)
    assert result['state']['last_choice'] == 'A'
    assert result['state']['last_policy'] == 'take_the_best'
    assert result['state']['selected_cue'] == 'priority_cue'
    assert result['metric'] == 9.0
    assert result['active'] is True
    assert result['state']['choice_history'] == ['older-choice', 'A']


def test_positive_scenario_has_expected_uplift_for_runner_seed_and_three_agents():
    scenario = next(x for x in scenarios() if x['name'] == 'positive')
    # The runner supplies identical exogenous draws to paired strength-zero and .8 runs.
    import numpy as np
    draws = np.random.default_rng(42).random((1, 3))[0]
    baseline = [evaluate({**scenario['contexts'][0], 'uniform': float(u), 'state': scenario['initial_state']}, 0.0)['metric'] for u in draws]
    intervention = [evaluate({**scenario['contexts'][0], 'uniform': float(u), 'state': scenario['initial_state']}, 0.8)['metric'] for u in draws]
    assert sum(intervention) / 3 > sum(baseline) / 3


def test_boundary_removes_discrimination_and_matches_reference():
    scenario = next(x for x in scenarios() if x['name'] == 'boundary')
    context = {**scenario['contexts'][0], 'state': scenario['initial_state'], 'uniform': 0.2}
    assert all(max(row.values()) - min(row.values()) < context['minimum_difference'] for row in context['cue_values'].values())
    reference = evaluate(context, 0.0)
    intervention = evaluate(context, 0.8)
    assert reference['metric'] == intervention['metric'] == 5.0
    assert intervention['state']['last_choice'] == 'A'
    assert intervention['state']['last_policy'] == 'aggregate_reference'
    assert intervention['active'] is False


def test_strength_zero_is_explicit_aggregate_reference_even_without_uniform():
    context = positive_context()
    context.pop('uniform')
    result = evaluate(context, 0.0)
    assert result['state']['last_choice'] == 'B'
    assert result['state']['last_policy'] == 'aggregate_reference'
    assert result['metric'] == 4.0
    assert result['active'] is False


def test_missing_and_malformed_phase_inputs_are_rejected():
    missing = positive_context()
    del missing['task_scores']
    with pytest.raises(ValueError, match='task_scores'):
        evaluate(missing, 0.8)
    invalid = positive_context(cue_values={'priority_cue': {'A': 1.0, 'B': float('nan')}, 'secondary_cue': {'A': 0.0, 'B': 3.0}})
    with pytest.raises(ValueError, match='finite'):
        evaluate(invalid, 0.8)
    with pytest.raises(ValueError, match='uniform'):
        evaluate(positive_context(uniform=1.0), 0.8)
    with pytest.raises(ValueError, match='strength'):
        evaluate(positive_context(), float('inf'))


def test_deterministic_and_nonmutating_with_complete_state_and_trace():
    context = positive_context()
    before = deepcopy(context)
    first = evaluate(context, 0.8)
    second = evaluate(context, 0.8)
    assert context == before
    assert first == second
    assert set(first['state']) == set(METADATA['state_fields'])
    assert isinstance(first['metric'], float)
    assert first['active'] is True
    assert first['trace'] and all(isinstance(line, str) for line in first['trace'])


def test_only_unconditional_scenario_keys_are_declared_as_required():
    assert METADATA['required_inputs'] == ['options', 'cue_order', 'cue_values', 'minimum_difference', 'task_scores']
