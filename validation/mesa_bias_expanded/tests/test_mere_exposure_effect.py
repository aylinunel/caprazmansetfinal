from copy import deepcopy
import math

import pytest

from mechanisms import mere_exposure_effect as effect


def run(contexts, strength, initial_state=None):
    state = deepcopy(initial_state or {'exposure_counts': {}, 'last_choice': None})
    results = []
    for round_index, data in enumerate(contexts):
        context = deepcopy(data)
        context.update({
            'state': deepcopy(state), 'peer_states': [], 'round_index': round_index,
            'agent_index': 0, 'uniform': 0.5,
        })
        result = effect.evaluate(context, strength)
        results.append(result)
        state = deepcopy(result['state'])
    return results


def test_numeric_oracle_and_choice_change_after_three_neutral_exposures():
    data = {'options': {'A': 0.50, 'B': 0.62}, 'exposures': ['A']}
    observed = run([data, data, data], 0.8)
    expected = 0.8 * 0.30 * (1.0 - math.exp(-1.0))
    assert observed[-1]['state']['last_choice'] == 'A'
    assert observed[-1]['metric'] == pytest.approx(expected)
    assert observed[-1]['active'] is True
    assert observed[-1]['state']['exposure_counts'] == {'A': 3}


def test_positive_scenario_has_increased_final_liking_metric():
    positive = effect.scenarios()[0]
    treated = run(positive['contexts'], 0.8, positive['initial_state'])[-1]
    reference = run(positive['contexts'], 0.0, positive['initial_state'])[-1]
    assert treated['metric'] > reference['metric']
    assert treated['state']['last_choice'] == 'A'
    assert reference['state']['last_choice'] == 'B'


def test_boundary_scenario_has_no_repeat_and_matches_reference():
    boundary = effect.scenarios()[1]
    treated = run(boundary['contexts'], 0.8, boundary['initial_state'])[-1]
    reference = run(boundary['contexts'], 0.0, boundary['initial_state'])[-1]
    assert treated['state']['exposure_counts'] == {'A': 1, 'B': 1}
    assert treated['metric'] == reference['metric'] == 0.0
    assert treated['state']['last_choice'] == reference['state']['last_choice'] == 'B'
    assert treated['active'] is False


def test_zero_strength_is_the_explicit_baseline_choice():
    result = run([
        {'options': {'A': 0.50, 'B': 0.62}, 'exposures': ['A']},
        {'options': {'A': 0.50, 'B': 0.62}, 'exposures': ['A']},
        {'options': {'A': 0.50, 'B': 0.62}, 'exposures': ['A']},
    ], 0.0)[-1]
    assert result['state']['last_choice'] == 'B'
    assert result['metric'] == 0.0
    assert result['active'] is False


def test_missing_or_invalid_task_evidence_is_rejected():
    with pytest.raises(ValueError, match='missing required task input exposures'):
        effect.evaluate({'options': {'A': 1.0}}, 0.5)
    with pytest.raises(ValueError, match='finite number'):
        effect.evaluate({'options': {'A': float('nan')}, 'exposures': []}, 0.5)
    with pytest.raises(ValueError, match='every exposure'):
        effect.evaluate({'options': {'A': 1.0}, 'exposures': ['unknown']}, 0.5)
    with pytest.raises(ValueError, match='strength'):
        effect.evaluate({'options': {'A': 1.0}, 'exposures': []}, 1.1)


def test_deterministic_trace_and_input_state_nonmutation():
    context = {
        'options': {'A': 0.61, 'B': 0.62}, 'exposures': ['A'],
        'state': {'exposure_counts': {'A': 1}, 'last_choice': 'B'},
        'peer_states': [{'untouched': [1, 2]}], 'round_index': 1,
        'agent_index': 0, 'uniform': 0.25,
    }
    before = deepcopy(context)
    first = effect.evaluate(context, 0.8)
    second = effect.evaluate(context, 0.8)
    assert context == before
    assert first == second
    assert first['metric'] > 0
    assert first['state']['exposure_counts'] == {'A': 2}
    assert isinstance(first['trace'], list) and first['trace']


def test_strength_and_phase_inputs_are_validated():
    with pytest.raises(ValueError):
        effect.evaluate({'options': {'A': 1.0}, 'exposures': []}, float('inf'))
    with pytest.raises(ValueError, match='nonnegative integers'):
        effect.evaluate({
            'options': {'A': 1.0}, 'exposures': [],
            'state': {'exposure_counts': {'A': -1}},
        }, 0.2)
