from copy import deepcopy

import pytest

from mechanisms import law_of_the_instrument as mechanism


TOOLS = [
    {'name': 'familiar_spreadsheet', 'capabilities': ['calculate'], 'familiarity': 1.0},
    {'name': 'specialist_suite', 'capabilities': ['calculate', 'visualize'], 'familiarity': 0.1},
]
BASE = {
    'requirements': ['calculate', 'visualize'],
    'tools': TOOLS,
    'application_mode': 'transfer',
}


def run_one(context, strength):
    payload = deepcopy(context)
    payload.setdefault('state', {})
    payload.setdefault('peer_states', [])
    payload.setdefault('round_index', 0)
    payload.setdefault('agent_index', 0)
    payload.setdefault('uniform', 0.5)
    return mechanism.evaluate(payload, strength)


def test_positive_transfer_numeric_and_choice_oracle():
    reference = run_one(BASE, 0.0)
    biased = run_one(BASE, 0.8)
    assert reference['state']['last_choice'] == 'specialist_suite'
    assert reference['metric'] == 0.0
    assert biased['state']['last_choice'] == 'familiar_spreadsheet'
    assert biased['metric'] == 1.0  # Exactly one required capability is missing.
    assert biased['active'] is True


def test_customary_use_boundary_matches_reference_metric_and_choice():
    context = {**BASE, 'application_mode': 'customary'}
    baseline = run_one(context, 0.0)
    at_boundary_strength = run_one(context, 0.8)
    assert at_boundary_strength['metric'] == baseline['metric']
    assert at_boundary_strength['state']['last_choice'] == baseline['state']['last_choice']
    assert at_boundary_strength['state']['last_choice'] == 'specialist_suite'
    assert at_boundary_strength['active'] is False


def test_zero_strength_is_best_coverage_reference_rule():
    result = run_one(BASE, 0.0)
    assert result['state']['last_reference_choice'] == 'specialist_suite'
    assert result['state']['last_choice'] == 'specialist_suite'
    assert result['metric'] == 0.0
    assert result['active'] is False


@pytest.mark.parametrize('bad_strength', [-0.01, 1.01, float('nan'), float('inf'), True])
def test_invalid_strength_rejected(bad_strength):
    with pytest.raises(ValueError):
        run_one(BASE, bad_strength)


def test_missing_evidence_and_invalid_tool_data_rejected():
    with pytest.raises(ValueError, match='missing required input'):
        run_one({'requirements': ['calculate'], 'tools': TOOLS}, 0.8)
    with pytest.raises(ValueError, match='familiarity'):
        run_one({**BASE, 'tools': [{**TOOLS[0], 'familiarity': 1.5}, TOOLS[1]]}, 0.8)


def test_deterministic_and_nonmutating():
    context = deepcopy(BASE)
    original = deepcopy(context)
    first = run_one(context, 0.8)
    second = run_one(context, 0.8)
    assert context == original
    assert first == second


def test_state_is_complete_and_history_carries_across_calls():
    first = run_one(BASE, 0.8)
    second_context = {**BASE, 'state': first['state']}
    second = run_one(second_context, 0.0)
    assert second['state']['decision_count'] == 2
    assert second['state']['choice_history'] == [
        'familiar_spreadsheet', 'specialist_suite'
    ]
    for field in mechanism.METADATA['state_fields']:
        assert field in second['state']
    assert isinstance(second['trace'], list) and second['trace']
