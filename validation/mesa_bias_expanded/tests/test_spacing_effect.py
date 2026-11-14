from copy import deepcopy
import math

import pytest

from mechanisms import spacing_effect as plugin


def run_contexts(contexts, strength, initial_state=None):
    state = deepcopy(initial_state or {})
    results = []
    for index, values in enumerate(contexts):
        context = deepcopy(values)
        context.update({
            'state': deepcopy(state),
            'peer_states': [],
            'round_index': index,
            'agent_index': 0,
            'uniform': 0.5,
        })
        result = plugin.evaluate(context, strength)
        state = deepcopy(result['state'])
        results.append(result)
    return results


def test_numeric_oracle_for_spaced_retention_and_transition():
    contexts = plugin.scenarios()[0]['contexts']
    results = run_contexts(contexts, 0.8)
    # Distinct-day gaps 2 and 3 add .8*.8*(2/3 + 3/4) stability.
    expected_stability = 0.8 * 0.8 * (2 / 3 + 3 / 4)
    expected = (1 - math.exp(-0.7 * 3)) * math.exp(-0.25 * 4 / (1 + expected_stability))
    assert results[1]['state']['items']['A']['spacing_stability'] == pytest.approx(0.8 * 0.8 * 2 / 3)
    assert results[-1]['state']['items']['A']['spacing_stability'] == pytest.approx(expected_stability)
    assert results[-1]['metric'] == pytest.approx(expected)
    assert results[-1]['active'] is True
    assert 'exp(-0.25*age_days/(1+stability))' in results[-1]['trace'][0]


def test_positive_scenario_improves_final_retrieval_score():
    contexts = plugin.scenarios()[0]['contexts']
    reference = run_contexts(contexts, 0.0)[-1]['metric']
    intervention = run_contexts(contexts, 0.8)[-1]['metric']
    assert intervention > reference


def test_boundary_removes_distinct_day_condition_and_matches_reference():
    scenario = plugin.scenarios()[1]
    reference = run_contexts(scenario['contexts'], 0.0)[-1]
    intervention = run_contexts(scenario['contexts'], 0.8)[-1]
    assert scenario['expectation'] == 'equal'
    assert intervention['state']['items']['A']['study_days'] == [0.0, 0.0]
    assert intervention['state']['items']['A']['spacing_stability'] == 0
    assert intervention['metric'] == pytest.approx(reference['metric'], abs=1e-12)


def test_zero_strength_is_explicit_no_spacing_stability_reference():
    contexts = plugin.scenarios()[0]['contexts']
    results = run_contexts(contexts, 0.0)
    final = results[-1]
    expected = (1 - math.exp(-0.7 * 3)) * math.exp(-0.25 * 4)
    assert final['metric'] == pytest.approx(expected)
    assert final['state']['items']['A']['spacing_stability'] == 0
    assert not any(result['active'] for result in results)


def test_required_and_phase_specific_evidence_rejections():
    with pytest.raises(ValueError, match='missing required'):
        plugin.evaluate({'item_id': 'A', 'event': 'study'}, 0.8)
    with pytest.raises(ValueError, match='event must'):
        plugin.evaluate({'item_id': 'A', 'event': 'review', 'elapsed_days': 0}, 0.8)
    with pytest.raises(ValueError, match='finite number'):
        plugin.evaluate({'item_id': 'A', 'event': 'study', 'elapsed_days': float('nan')}, 0.8)
    with pytest.raises(ValueError, match='prior study'):
        plugin.evaluate({'item_id': 'A', 'event': 'probe', 'elapsed_days': 1}, 0.8)
    with pytest.raises(ValueError, match=r'\[0, 1\]'):
        plugin.evaluate({'item_id': 'A', 'event': 'study', 'elapsed_days': 0}, 1.1)


def test_determinism_nonmutation_and_complete_chronological_state():
    context = {
        'item_id': 'B', 'event': 'study', 'elapsed_days': 3,
        'state': {'items': {'B': {'study_days': [1], 'spacing_stability': 0.1}}, 'last_elapsed_days': 1},
        'peer_states': [{'unrelated': [1, 2]}], 'round_index': 1, 'agent_index': 0, 'uniform': 0.4,
    }
    original = deepcopy(context)
    first = plugin.evaluate(context, 0.5)
    second = plugin.evaluate(context, 0.5)
    assert context == original
    assert first == second
    assert first['state']['items']['B']['study_days'] == [1.0, 3.0]
    assert first['state']['last_elapsed_days'] == 3.0
    assert first['active'] is True
    assert first['trace'] and all(isinstance(line, str) for line in first['trace'])


def test_rejects_nonchronological_history_without_mutating_input():
    context = {
        'item_id': 'A', 'event': 'study', 'elapsed_days': 2,
        'state': {'items': {'A': {'study_days': [1, 3], 'spacing_stability': 0.2}}, 'last_elapsed_days': 3},
    }
    before = deepcopy(context)
    with pytest.raises(ValueError, match='chronological'):
        plugin.evaluate(context, 0.8)
    assert context == before
