from copy import deepcopy

import pytest

from mechanisms import self_serving_bias as mechanism


def context(outcome='success', evidence_internal_share=0.35, evidence_quality=0.20, state=None):
    return {
        'outcome': outcome,
        'evidence_internal_share': evidence_internal_share,
        'evidence_quality': evidence_quality,
        'state': {} if state is None else state,
        'peer_states': [],
        'round_index': 0,
        'agent_index': 0,
        'uniform': 0.3,
    }


def play(scenario, strength):
    state = deepcopy(scenario['initial_state'])
    result = None
    for round_index, event in enumerate(scenario['contexts']):
        ctx = deepcopy(event)
        ctx.update(state=deepcopy(state), peer_states=[], round_index=round_index,
                   agent_index=0, uniform=0.3)
        result = mechanism.evaluate(ctx, strength)
        state = result['state']
    return result


def test_numeric_oracle_directional_formula_for_success_and_failure():
    success = mechanism.evaluate(context('success'), 0.8)
    failure = mechanism.evaluate(context('failure'), 0.8)
    assert success['metric'] == pytest.approx(0.766)
    assert failure['metric'] == pytest.approx(0.126)
    assert success['active'] is True and failure['active'] is True
    assert success['state']['outcomes'] == ['success']
    assert failure['state']['outcomes'] == ['failure']


def test_positive_chronological_scenario_decreases_final_internal_share():
    scenario = next(s for s in mechanism.scenarios() if s['name'] == 'positive')
    reference = play(scenario, 0.0)
    intervention = play(scenario, 0.8)
    assert reference['metric'] == pytest.approx(0.35)
    assert intervention['metric'] == pytest.approx(0.126)
    assert intervention['metric'] < reference['metric']
    assert intervention['state']['outcomes'] == ['success', 'failure']
    assert intervention['state']['events_seen'] == 2


def test_complete_causal_evidence_removes_necessary_ambiguity_condition():
    scenario = next(s for s in mechanism.scenarios() if s['name'] == 'boundary')
    reference = play(scenario, 0.0)
    intervention = play(scenario, 0.8)
    assert reference['metric'] == pytest.approx(0.8)
    assert intervention['metric'] == pytest.approx(reference['metric'])
    assert intervention['active'] is False


def test_strength_zero_is_explicit_evidence_share_reference():
    for outcome in ('success', 'failure'):
        result = mechanism.evaluate(context(outcome, 0.43, 0.15), 0.0)
        assert result['metric'] == pytest.approx(0.43)
        assert result['active'] is False


def test_missing_required_and_invalid_phase_specific_inputs_are_rejected():
    with pytest.raises(ValueError, match='missing required'):
        mechanism.evaluate({'outcome': 'success', 'evidence_internal_share': 0.5}, 0.8)
    for bad in ('unknown', None, True):
        with pytest.raises(ValueError, match='outcome'):
            mechanism.evaluate(context(outcome=bad), 0.8)
    for bad_share in (-0.1, 1.1, float('nan'), '0.4', True):
        with pytest.raises(ValueError, match='evidence_internal_share'):
            mechanism.evaluate(context(evidence_internal_share=bad_share), 0.8)
    for bad_quality in (-0.1, 1.1, float('inf'), None):
        with pytest.raises(ValueError, match='evidence_quality'):
            mechanism.evaluate(context(evidence_quality=bad_quality), 0.8)
    for bad_strength in (-0.1, 1.1, float('nan'), True):
        with pytest.raises(ValueError, match='strength'):
            mechanism.evaluate(context(), bad_strength)


def test_deterministic_and_nonmutating_even_with_nested_prior_state():
    prior = {
        'events_seen': 1,
        'cumulative_internal_share': 0.6,
        'cumulative_evidence_share': 0.5,
        'outcomes': ['success'],
    }
    ctx = context('failure', 0.5, 0.4, prior)
    before = deepcopy(ctx)
    first = mechanism.evaluate(ctx, 0.6)
    second = mechanism.evaluate(ctx, 0.6)
    assert ctx == before
    assert first == second
    assert first['metric'] == pytest.approx(0.32)
    assert first['state']['events_seen'] == 2
    assert first['state']['outcomes'] == ['success', 'failure']
    assert prior['outcomes'] == ['success']
