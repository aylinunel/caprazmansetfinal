from copy import deepcopy
import math

import pytest

from mechanisms import rosy_retrospection as rr


def run(task_contexts, strength, initial_state=None):
    state = deepcopy(initial_state or {'episodes': {}, 'recall_history': []})
    outputs = []
    for round_index, task_input in enumerate(task_contexts):
        context = deepcopy(task_input)
        context.update({'state': state, 'peer_states': [], 'round_index': round_index,
                        'agent_index': 0, 'uniform': 0.5})
        output = rr.evaluate(context, strength)
        outputs.append(output)
        state = output['state']
    return outputs


def contexts(positive=(1.0,), negative=(1.0,), rating=50):
    return [
        {'phase': 'experience', 'episode_id': 'journey', 'experience_score': rating,
         'positive_cues': list(positive), 'negative_cues': list(negative)},
        {'phase': 'recall', 'episode_id': 'journey'},
    ]


def test_numeric_choice_oracle_uses_asymmetric_accessibility_equation():
    output = run(contexts(), 0.8)[-1]
    positive_access = math.exp(-0.10)
    negative_access = math.exp(-0.45)
    encoded = 0.0  # equal positive/negative encoded cue salience
    recalled = (positive_access - negative_access) / (positive_access + negative_access)
    expected = 50 + 0.8 * 20 * (recalled - encoded)
    assert output['metric'] == pytest.approx(expected)
    assert output['metric'] > 50
    assert output['active'] is True
    assert 'exp(-0.10t)' in output['trace'][0]


def test_positive_scenario_increases_recalled_rating_over_reference():
    scenario = next(s for s in rr.scenarios() if s['name'] == 'positive')
    baseline = run(scenario['contexts'], 0.0)[-1]['metric']
    intervention = run(scenario['contexts'], 0.8)[-1]['metric']
    assert baseline == 50
    assert intervention > baseline


def test_boundary_without_negative_cues_is_equal_to_strength_zero():
    scenario = next(s for s in rr.scenarios() if s['name'] == 'boundary')
    baseline = run(scenario['contexts'], 0.0)[-1]
    intervention = run(scenario['contexts'], 0.8)[-1]
    assert intervention['metric'] == baseline['metric'] == 50
    assert intervention['active'] is False


def test_zero_strength_is_explicit_recorded_rating_reference_and_keeps_state():
    first, recalled = run(contexts(rating=63), 0.0)
    assert first['metric'] == recalled['metric'] == 63
    assert recalled['active'] is False
    assert recalled['state']['episodes']['journey']['experience_score'] == 63
    assert recalled['state']['recall_history'][-1]['recalled_rating'] == 63


def test_phase_specific_missing_or_invalid_inputs_are_rejected():
    with pytest.raises(ValueError, match='phase'):
        rr.evaluate({}, 0.5)
    with pytest.raises(ValueError, match='experience phase missing'):
        rr.evaluate({'phase': 'experience', 'episode_id': 'x', 'round_index': 0}, 0.5)
    bad = {'phase': 'experience', 'episode_id': 'x', 'experience_score': 101,
           'positive_cues': [1], 'negative_cues': [], 'round_index': 0}
    with pytest.raises(ValueError, match='experience_score'):
        rr.evaluate(bad, 0.5)
    with pytest.raises(ValueError, match='strength'):
        rr.evaluate({'phase': 'recall', 'episode_id': 'x', 'round_index': 0}, float('nan'))


def test_recall_requires_chronological_prior_experience():
    with pytest.raises(ValueError, match='previously experienced'):
        rr.evaluate({'phase': 'recall', 'episode_id': 'missing', 'round_index': 1,
                     'state': {'episodes': {}, 'recall_history': []}}, 0.8)
    state = run(contexts(), 0.0)[0]['state']
    same_round = {'phase': 'recall', 'episode_id': 'journey', 'round_index': 0,
                  'state': state}
    with pytest.raises(ValueError, match='at least one simulated round'):
        rr.evaluate(same_round, 0.8)


def test_deterministic_and_nonmutating_for_nested_context_and_state():
    state = {'episodes': {}, 'recall_history': [], 'caller_note': {'keep': [1, 2]}}
    original_state = deepcopy(state)
    input_contexts = contexts()
    original_contexts = deepcopy(input_contexts)
    first = run(input_contexts, 0.8, state)
    second = run(input_contexts, 0.8, state)
    assert input_contexts == original_contexts
    assert state == original_state
    assert first == second
    assert first[-1]['state']['caller_note'] == {'keep': [1, 2]}
