from copy import deepcopy

import pytest

from mechanisms import mental_accounting as plugin


def context(task, state=None):
    return {
        'task': deepcopy(task),
        'state': deepcopy(state or {}),
        'peer_states': [],
        'round_index': 0,
        'agent_index': 0,
        'uniform': 0.25,
    }


def positive_task(**overrides):
    task = {
        'benefit': 15,
        'price': 10,
        'matched_funds': 5,
        'unmatched_funds': 20,
        'accounts_separated': True,
        'category_match': True,
    }
    task.update(overrides)
    return task


def test_numeric_oracle_category_envelope_blocks_otherwise_worthwhile_purchase():
    result = plugin.evaluate(context(positive_task()), 0.8)
    assert result['state']['last_effective_funds'] == pytest.approx(9.0)
    assert result['state']['last_choice'] == 'defer'
    assert result['metric'] == 0
    assert result['active'] is True
    assert 'matched(5)' in result['trace'][0]


def test_positive_scenario_reduces_realized_surplus_at_strength_point_eight():
    task = plugin.scenarios()[0]['contexts'][0]['task']
    baseline = plugin.evaluate(context(task), 0.0)
    intervention = plugin.evaluate(context(task), 0.8)
    assert baseline['metric'] == pytest.approx(5)
    assert intervention['metric'] < baseline['metric']


def test_boundary_without_separate_accounts_equals_fungible_reference():
    task = plugin.scenarios()[1]['contexts'][0]['task']
    baseline = plugin.evaluate(context(task), 0.0)
    intervention = plugin.evaluate(context(task), 0.8)
    assert intervention['metric'] == baseline['metric'] == pytest.approx(5)
    assert intervention['active'] is False
    assert intervention['state']['last_effective_funds'] == pytest.approx(25)


def test_zero_strength_is_explicit_fungible_reference_and_updates_state():
    result = plugin.evaluate(context(positive_task(), {'purchase_count': 2}), 0.0)
    assert result['state'] == {
        'purchase_count': 3,
        'last_choice': 'buy',
        'last_effective_funds': 25.0,
        'last_surplus': 5.0,
    }
    assert result['metric'] == pytest.approx(5)
    assert result['active'] is False


def test_missing_or_invalid_phase_specific_evidence_is_rejected():
    with pytest.raises(ValueError, match='missing required task'):
        plugin.evaluate({'state': {}}, 0.8)
    with pytest.raises(ValueError, match='task must contain exactly'):
        plugin.evaluate(context({'benefit': 15}), 0.8)
    with pytest.raises(ValueError, match='matched_funds'):
        plugin.evaluate(context(positive_task(matched_funds=float('nan'))), 0.8)
    with pytest.raises(ValueError, match='category_match'):
        plugin.evaluate(context(positive_task(category_match=1)), 0.8)
    with pytest.raises(ValueError, match='strength'):
        plugin.evaluate(context(positive_task()), float('inf'))


def test_deterministic_and_does_not_mutate_context_or_nested_inputs():
    task = positive_task()
    ctx = context(task, {'purchase_count': 4, 'other_history': ['kept']})
    before = deepcopy(ctx)
    first = plugin.evaluate(ctx, 0.8)
    second = plugin.evaluate(ctx, 0.8)
    assert first == second
    assert ctx == before


def test_only_explicit_category_match_triggers_category_partition():
    matched = plugin.evaluate(context(positive_task()), 0.8)
    unmatched = plugin.evaluate(context(positive_task(category_match=False)), 0.8)
    assert matched['state']['last_effective_funds'] == pytest.approx(9)
    assert unmatched['state']['last_effective_funds'] == pytest.approx(25)
    assert unmatched['metric'] == pytest.approx(5)
