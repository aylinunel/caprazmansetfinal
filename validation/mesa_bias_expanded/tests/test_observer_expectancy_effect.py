from copy import deepcopy
import math
import pytest

from mechanisms import observer_expectancy_effect as plugin


def context(**overrides):
    value = {
        'observer_present': True,
        'observer_expectation': 0.8,
        'cue_visibility': 0.5,
        'participant_responsiveness': 0.4,
        'task_susceptibility': 0.6,
        'baseline_performance': 5.0,
        'state': {'participant_expectancy': 0.2},
        'peer_states': [],
        'round_index': 0,
        'agent_index': 0,
        'uniform': 0.3,
    }
    value.update(overrides)
    return value


def run_scenario(scenario, strength):
    state = deepcopy(scenario['initial_state'])
    outputs = []
    for index, task_inputs in enumerate(scenario['contexts']):
        step = {**deepcopy(task_inputs), 'state': deepcopy(state),
                'peer_states': [], 'round_index': index, 'agent_index': 0,
                'uniform': 0.3}
        result = plugin.evaluate(step, strength)
        outputs.append(result)
        state = result['state']
    return outputs


def test_numeric_oracle_for_expectancy_transmission_and_performance():
    # alpha=.5*.5*.4=.1; E'=0.2+.1*(0.8-.2)=0.26; metric=5+.6*.26.
    result = plugin.evaluate(context(), 0.5)
    assert result['state']['participant_expectancy'] == pytest.approx(0.26)
    assert result['metric'] == pytest.approx(5.156)
    assert result['active'] is True
    assert len(result['trace']) == 2


def test_positive_scenario_increases_task_performance():
    positive = next(s for s in plugin.scenarios() if s['name'] == 'positive')
    intervention = run_scenario(positive, 0.8)
    reference = run_scenario(positive, 0.0)
    assert intervention[-1]['metric'] > reference[-1]['metric']
    assert intervention[-1]['state']['participant_expectancy'] > 0


def test_boundary_removes_conveyed_expectation_and_matches_reference():
    boundary = next(s for s in plugin.scenarios() if s['name'] == 'boundary')
    assert all(c['observer_present'] and c['observer_expectation'] > 0 for c in boundary['contexts'])
    assert all(c['cue_visibility'] == 0 for c in boundary['contexts'])
    intervention = run_scenario(boundary, 0.8)
    reference = run_scenario(boundary, 0.0)
    assert [r['metric'] for r in intervention] == pytest.approx([r['metric'] for r in reference])
    assert all(r['active'] is False for r in intervention)


def test_zero_strength_is_no_transmission_from_zero_reference_state():
    result = plugin.evaluate(context(state={'participant_expectancy': 0.0}), 0.0)
    assert result['metric'] == pytest.approx(5.0)
    assert result['state'] == {'participant_expectancy': 0.0}
    assert result['active'] is False


def test_missing_and_invalid_task_inputs_are_rejected():
    missing = context()
    del missing['cue_visibility']
    with pytest.raises(ValueError, match='cue_visibility'):
        plugin.evaluate(missing, 0.8)
    with pytest.raises(ValueError, match='observer_expectation'):
        plugin.evaluate(context(observer_expectation=float('nan')), 0.8)
    with pytest.raises(ValueError, match='cue_visibility'):
        plugin.evaluate(context(cue_visibility=1.1), 0.8)
    with pytest.raises(ValueError, match='observer_present'):
        plugin.evaluate(context(observer_present=1), 0.8)


def test_invalid_strength_and_invalid_carried_state_are_rejected():
    for strength in (-0.1, 1.1, float('inf'), True):
        with pytest.raises(ValueError):
            plugin.evaluate(context(), strength)
    with pytest.raises(ValueError, match='participant_expectancy'):
        plugin.evaluate(context(state={'participant_expectancy': 2.0}), 0.8)


def test_deterministic_and_nonmutating_for_nested_context():
    supplied = context()
    before = deepcopy(supplied)
    first = plugin.evaluate(supplied, 0.8)
    second = plugin.evaluate(supplied, 0.8)
    assert supplied == before
    assert first == second
    assert math.isfinite(first['metric'])
