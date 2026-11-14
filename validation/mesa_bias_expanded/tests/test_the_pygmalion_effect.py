from copy import deepcopy

import pytest

from mechanisms import the_pygmalion_effect as mechanism


def context(**overrides):
    value = {
        'evaluator_expectation': 0.9,
        'neutral_expectation': 0.5,
        'support_opportunity': 0.5,
        'baseline_support': 0.1,
        'baseline_score': 50.0,
        'support_effect': 20.0,
        'score_ceiling': 100.0,
        'state': {},
        'peer_states': [],
        'round_index': 0,
        'agent_index': 0,
        'uniform': 0.25,
    }
    value.update(overrides)
    return value


def run(contexts, strength, initial_state=None):
    state = {} if initial_state is None else deepcopy(initial_state)
    result = None
    for index, item in enumerate(contexts):
        supplied = deepcopy(item)
        supplied.update({'state': deepcopy(state), 'peer_states': [], 'round_index': index,
                         'agent_index': 0, 'uniform': 0.25})
        result = mechanism.evaluate(supplied, strength)
        state = deepcopy(result['state'])
    return result


def test_numeric_oracle_exposes_expectation_treatment_performance_chain():
    result = mechanism.evaluate(context(), 0.8)
    # .1 + .8 * .5 * (.9 - .5) = .26 treatment; 50 + .26*20 = 55.2.
    assert result['state']['last_treatment'] == pytest.approx(0.26)
    assert result['metric'] == pytest.approx(55.2)
    assert result['state']['last_reference_score'] == pytest.approx(52.0)
    assert result['active'] is True
    assert len(result['trace']) >= 2


def test_positive_scenario_score_increases_over_fixed_support_reference():
    positive = next(s for s in mechanism.scenarios() if s['name'] == 'positive')
    treated = run(positive['contexts'], 0.8, positive['initial_state'])
    reference = run(positive['contexts'], 0.0, positive['initial_state'])
    assert treated['metric'] > reference['metric']
    assert treated['metric'] - reference['metric'] == pytest.approx(3.2)


def test_boundary_removes_support_opportunity_and_matches_reference():
    boundary = next(s for s in mechanism.scenarios() if s['name'] == 'boundary')
    treated = run(boundary['contexts'], 0.8, boundary['initial_state'])
    reference = run(boundary['contexts'], 0.0, boundary['initial_state'])
    assert boundary['contexts'][0]['support_opportunity'] == 0.0
    assert treated['metric'] == pytest.approx(reference['metric'])
    assert treated['active'] is False


def test_zero_strength_is_fixed_baseline_support_policy():
    result = mechanism.evaluate(context(), 0.0)
    assert result['state']['last_treatment'] == pytest.approx(0.1)
    assert result['metric'] == pytest.approx(52.0)
    assert result['active'] is False


def test_missing_and_invalid_phase_inputs_are_rejected():
    missing = context()
    del missing['support_opportunity']
    with pytest.raises(ValueError, match='support_opportunity'):
        mechanism.evaluate(missing, 0.8)
    with pytest.raises(ValueError, match='support_opportunity'):
        mechanism.evaluate(context(support_opportunity=1.01), 0.8)
    with pytest.raises(ValueError, match='finite number'):
        mechanism.evaluate(context(support_effect=float('nan')), 0.8)


def test_strength_validation_and_deterministic_nonmutating_state():
    original = context(state={'prior_note': 'retain me', 'last_treatment': 0.05})
    before = deepcopy(original)
    first = mechanism.evaluate(original, 0.8)
    second = mechanism.evaluate(original, 0.8)
    assert original == before
    assert first == second
    assert first['state']['prior_note'] == 'retain me'
    assert first['state']['last_treatment'] == pytest.approx(0.26)
    for invalid in (-0.1, 1.1, float('inf'), float('nan'), True):
        with pytest.raises(ValueError, match='strength'):
            mechanism.evaluate(context(), invalid)


def test_expectations_not_above_neutral_do_not_increase_support():
    result = mechanism.evaluate(context(evaluator_expectation=0.4), 0.8)
    assert result['state']['last_treatment'] == pytest.approx(0.1)
    assert result['metric'] == pytest.approx(52.0)
    assert result['active'] is False
