from copy import deepcopy
import math

import pytest

from mechanisms import survivorship_bias as plugin


def run_contexts(scenario, strength):
    """Run chronological task inputs while carrying the task-specific state."""
    state = deepcopy(scenario['initial_state'])
    outputs = []
    for index, raw in enumerate(scenario['contexts']):
        context = deepcopy(raw)
        context.update({
            'state': deepcopy(state),
            'peer_states': [],
            'round_index': index,
            'agent_index': 0,
            'uniform': 0.5,
        })
        result = plugin.evaluate(context, strength)
        state = deepcopy(result['state'])
        outputs.append(result)
    return outputs


def test_numeric_oracle_visibility_weighted_success_rate():
    # Four observed successes plus six omitted failures. At strength .8, omitted
    # failures have weight .2: 4 / (4 + 6*.2) = 10/13.
    result = plugin.evaluate(plugin.scenarios()[0]['contexts'][0], 0.8)
    assert result['metric'] == pytest.approx(10 / 13)
    assert result['state']['last_reference_rate'] == pytest.approx(0.4)
    assert result['active'] is True
    assert len(result['state']['last_selected_ids']) == 10


def test_positive_scenario_rate_increases_against_full_cohort_reference():
    scenario = next(s for s in plugin.scenarios() if s['name'] == 'positive')
    at_zero = run_contexts(scenario, 0.0)[-1]['metric']
    at_intervention = run_contexts(scenario, 0.8)[-1]['metric']
    assert at_intervention > at_zero


def test_boundary_visible_subset_question_is_unchanged():
    scenario = next(s for s in plugin.scenarios() if s['name'] == 'boundary')
    at_zero = run_contexts(scenario, 0.0)[-1]
    at_intervention = run_contexts(scenario, 0.8)[-1]
    assert at_zero['metric'] == at_intervention['metric'] == 1.0
    assert at_intervention['active'] is False
    assert len(at_intervention['state']['last_selected_ids']) == 4


def test_strength_zero_is_full_cohort_census_reference():
    context = plugin.scenarios()[0]['contexts'][0]
    result = plugin.evaluate(context, 0)
    assert result['metric'] == pytest.approx(4 / 10)
    assert result['state']['last_selected_ids'] == [f'survivor_{i}' for i in range(4)] + [f'failed_{i}' for i in range(6)]
    assert result['active'] is False


def test_rejects_missing_and_invalid_task_evidence():
    valid = plugin.scenarios()[0]['contexts'][0]
    with pytest.raises(ValueError, match='missing required task input target'):
        plugin.evaluate({'cohort': valid['cohort']}, 0.8)
    malformed = deepcopy(valid)
    malformed['cohort'][0]['success'] = 1
    with pytest.raises(ValueError, match='success must be a boolean'):
        plugin.evaluate(malformed, 0.8)
    no_observations = {'target': 'full_cohort', 'cohort': [
        {'id': 'hidden', 'success': False, 'observed': False}
    ]}
    with pytest.raises(ValueError, match='at least one observed case'):
        plugin.evaluate(no_observations, 1.0)


def test_determinism_nonmutation_and_state_carryover():
    context = deepcopy(plugin.scenarios()[0]['contexts'][0])
    context['state'] = {'analysis_count': 2, 'last_selected_ids': ['prior'], 'custom': {'keep': True}}
    before = deepcopy(context)
    first = plugin.evaluate(context, 0.8)
    second = plugin.evaluate(context, 0.8)
    assert context == before
    assert first == second
    assert first['state']['analysis_count'] == 3
    assert first['state']['custom'] == {'keep': True}
    assert math.isfinite(first['metric'])


def test_rejects_invalid_strength():
    context = plugin.scenarios()[0]['contexts'][0]
    with pytest.raises(ValueError, match='strength must be finite'):
        plugin.evaluate(context, float('nan'))
    with pytest.raises(ValueError, match='strength must be finite'):
        plugin.evaluate(context, True)
