from copy import deepcopy

import pytest

from mechanisms import source_confusion as plugin


def _context(task, state=None):
    return {
        **deepcopy(task),
        'state': deepcopy(state if state is not None else {
            'items_processed': 0,
            'misattributions': 0,
            'last_attributed_source': None,
            'last_source_score_margin': None,
        }),
        'peer_states': [],
        'round_index': 0,
        'agent_index': 0,
        'uniform': 0.42,
    }


def _run(task, strength, state=None):
    return plugin.evaluate(_context(task, state), strength)


def test_numeric_and_choice_oracle_for_source_evidence_blend():
    task = plugin.scenarios()[0]['contexts'][0]
    result = _run(task, 0.8)
    # Target score = .2*.95 + .8*.25 = .39; lure score = .2*.35 + .8*.95 = .83.
    assert result['metric'] == 1.0
    assert result['state']['last_attributed_source'] == 'forum_b'
    assert result['state']['last_source_score_margin'] == pytest.approx(0.44)
    assert 'source-cue reference chose \'journal_a\'' in result['trace'][0]
    assert result['state']['misattributions'] == 1


def test_positive_strength_increases_misattribution_against_source_cue_reference():
    task = plugin.scenarios()[0]['contexts'][0]
    assert _run(task, 0.0)['metric'] == 0.0
    intervention = _run(task, 0.8)
    assert intervention['metric'] > _run(task, 0.0)['metric']
    assert intervention['active'] is True


def test_boundary_removes_competing_source_and_matches_zero_strength():
    scenario = plugin.scenarios()[1]
    task = scenario['contexts'][0]
    assert len(task['candidate_sources']) == 1
    assert _run(task, 0.8)['metric'] == _run(task, 0.0)['metric'] == 0.0
    assert _run(task, 0.8)['active'] is False


def test_zero_strength_is_source_cue_reference_even_when_content_is_familiar_elsewhere():
    task = plugin.scenarios()[0]['contexts'][0]
    result = _run(task, 0.0)
    assert result['metric'] == 0.0
    assert result['state']['last_attributed_source'] == 'journal_a'
    assert result['active'] is False


def test_rejects_missing_and_invalid_phase_specific_evidence_and_strength():
    with pytest.raises(ValueError, match='missing required task input'):
        plugin.evaluate(_context({'origin_source': 'journal_a'}), 0.5)
    task = deepcopy(plugin.scenarios()[0]['contexts'][0])
    task['candidate_sources'][1]['content_familiarity'] = float('nan')
    with pytest.raises(ValueError, match='finite number'):
        _run(task, 0.5)
    with pytest.raises(ValueError, match='strength'):
        _run(plugin.scenarios()[0]['contexts'][0], 1.1)
    missing_candidate_field = {
        'origin_source': 'journal_a',
        'candidate_sources': [{'source_id': 'journal_a', 'source_cue_match': 0.9}],
    }
    with pytest.raises(ValueError, match='each candidate requires'):
        _run(missing_candidate_field, 0.5)


def test_deterministic_nonmutation_and_complete_chronological_state():
    task = plugin.scenarios()[0]['contexts'][0]
    context = _context(task)
    before = deepcopy(context)
    first = plugin.evaluate(context, 0.8)
    second = plugin.evaluate(context, 0.8)
    assert context == before
    assert first == second
    next_context = _context(task, first['state'])
    next_result = plugin.evaluate(next_context, 0.8)
    assert next_result['state']['items_processed'] == 2
    assert next_result['state']['misattributions'] == 2
    assert next_result['state']['last_attributed_source'] == 'forum_b'
