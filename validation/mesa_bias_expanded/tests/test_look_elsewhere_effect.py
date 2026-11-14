import copy
import math

import pytest

from mechanisms import look_elsewhere_effect as plugin


def run_context(context, strength=0.8, state=None):
    """Call one chronological step with runner-reserved fields supplied."""
    supplied = copy.deepcopy(context)
    supplied.update({
        'state': copy.deepcopy(state or {}),
        'peer_states': [],
        'round_index': 0,
        'agent_index': 0,
        'uniform': 0.5,
    })
    return plugin.evaluate(supplied, strength)


def test_numeric_selection_and_familywise_evidence_oracle():
    result = run_context({'candidate_z_scores': [0.5, -2.0, 2.5]})
    selected = 2.5  # highest absolute z-score, with stable first-index tie behavior
    p_single = math.erfc(abs(selected) / math.sqrt(2.0))
    p_family = 1.0 - (1.0 - p_single) ** 3
    expected = -math.log10(p_family) + 0.8 * (
        -math.log10(p_single) + math.log10(p_family)
    )
    assert result['state']['selected_index'] == 2
    assert result['state']['selected_z'] == selected
    assert result['state']['candidate_count'] == 3
    assert result['state']['single_test_p'] == pytest.approx(p_single)
    assert result['state']['familywise_p'] == pytest.approx(p_family)
    assert result['metric'] == pytest.approx(expected)
    assert result['active'] is True
    assert any('maximum absolute value' in line for line in result['trace'])


def test_positive_strength_increases_unadjusted_reported_evidence():
    context = {'candidate_z_scores': [0.2, 1.4, -2.7, 0.9]}
    reference = run_context(context, strength=0.0)
    intervention = run_context(context, strength=0.8)
    assert intervention['metric'] > reference['metric']
    assert intervention['state']['familywise_p'] > intervention['state']['single_test_p']


def test_boundary_without_search_multiplicity_matches_reference():
    context = {'candidate_z_scores': [2.8]}
    reference = run_context(context, strength=0.0)
    intervention = run_context(context, strength=0.8)
    assert intervention['metric'] == pytest.approx(reference['metric'], abs=1e-15)
    assert intervention['state']['familywise_p'] == pytest.approx(
        intervention['state']['single_test_p']
    )
    assert intervention['active'] is False


def test_zero_strength_is_the_explicit_familywise_reference_and_preserves_state():
    context = {'candidate_z_scores': [-1.0, 2.0], 'state': {'other_task_fact': 17}}
    result = plugin.evaluate(context, 0.0)
    p_family = 1.0 - (1.0 - math.erfc(2.0 / math.sqrt(2.0))) ** 2
    assert result['metric'] == pytest.approx(-math.log10(p_family))
    assert result['state']['other_task_fact'] == 17
    assert result['active'] is False


def test_missing_and_impossible_task_evidence_are_rejected():
    with pytest.raises(ValueError, match='candidate_z_scores'):
        run_context({})
    for invalid in ([], [True], ['2.0'], [float('nan')], [float('inf')], [8.01]):
        with pytest.raises(ValueError):
            run_context({'candidate_z_scores': invalid})
    for invalid_strength in (-0.1, 1.1, float('nan'), float('inf'), True):
        with pytest.raises(ValueError):
            run_context({'candidate_z_scores': [1.0]}, invalid_strength)


def test_deterministic_and_nonmutating_including_nested_prior_state():
    context = {
        'candidate_z_scores': [1.0, -2.1, 0.4],
        'state': {'history': [{'label': 'prior', 'count': 3}]},
    }
    before = copy.deepcopy(context)
    first = plugin.evaluate(context, 0.65)
    second = plugin.evaluate(context, 0.65)
    assert context == before
    assert first == second
    first['state']['history'][0]['count'] = -1
    assert context['state']['history'][0]['count'] == 3
