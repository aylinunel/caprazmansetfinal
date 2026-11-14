from copy import deepcopy

import pytest

from mechanisms import omission_bias as plugin


def context(**overrides):
    data = {
        'action_harm': 0.8,
        'omission_harm': 0.8,
        'actor_knew_risk': True,
        'duty_to_act': True,
        'intentional_choice': True,
        'consequences_comparable': True,
        'state': {},
        'peer_states': [],
        'round_index': 0,
        'agent_index': 0,
        'uniform': 0.5,
    }
    data.update(overrides)
    return data


def test_numeric_oracle_uses_shared_harm_and_asymmetric_action_premium():
    result = plugin.evaluate(context(action_harm=0.9, omission_harm=0.5), 0.8)
    # Reference difference .9-.5=.4; premium=.8*.25*min(.9,.5)=.1.
    assert result['state']['last_action_blame'] == pytest.approx(1.0)
    assert result['state']['last_omission_blame'] == pytest.approx(0.5)
    assert result['state']['last_action_premium'] == pytest.approx(0.1)
    assert result['metric'] == pytest.approx(0.5)
    assert result['active'] is True
    assert 'min(action_harm, omission_harm)' in result['trace'][0]


def test_positive_scenario_has_increased_action_minus_omission_blame():
    case = plugin.scenarios()[0]['contexts'][0]
    reference = plugin.evaluate(context(**case), 0.0)
    intervention = plugin.evaluate(context(**case), 0.8)
    assert intervention['metric'] > reference['metric']
    assert intervention['metric'] - reference['metric'] == pytest.approx(0.16)


def test_boundary_removes_comparability_and_matches_strength_zero():
    case = plugin.scenarios()[1]['contexts'][0]
    reference = plugin.evaluate(context(**case), 0.0)
    intervention = plugin.evaluate(context(**case), 0.8)
    assert case['consequences_comparable'] is False
    assert intervention['metric'] == pytest.approx(reference['metric'])
    assert intervention['state']['last_action_premium'] == 0.0
    assert intervention['active'] is False


def test_strength_zero_is_explicit_harm_weighted_reference():
    result = plugin.evaluate(context(action_harm=0.7, omission_harm=0.2), 0.0)
    assert result['metric'] == pytest.approx(0.5)
    assert result['state']['last_action_blame'] == pytest.approx(0.7)
    assert result['state']['last_omission_blame'] == pytest.approx(0.2)
    assert result['state']['last_action_premium'] == 0.0
    assert result['active'] is False


def test_missing_or_invalid_phase_inputs_are_rejected_not_silently_zeroed():
    missing = context()
    del missing['duty_to_act']
    with pytest.raises(ValueError, match='duty_to_act'):
        plugin.evaluate(missing, 0.8)
    with pytest.raises(ValueError, match='action_harm'):
        plugin.evaluate(context(action_harm=float('nan')), 0.8)
    with pytest.raises(ValueError, match='actor_knew_risk'):
        plugin.evaluate(context(actor_knew_risk=1), 0.8)
    with pytest.raises(ValueError, match='strength'):
        plugin.evaluate(context(), 1.1)


def test_deterministic_and_nonmutating_with_nested_prior_state():
    original = context(state={'case_count': 2, 'eligible_case_count': 1, 'memo': {'tag': 'kept'}})
    before = deepcopy(original)
    first = plugin.evaluate(original, 0.8)
    second = plugin.evaluate(original, 0.8)
    assert original == before
    assert first == second
    assert first['state']['case_count'] == 3
    assert first['state']['eligible_case_count'] == 2
    assert first['trace'] == second['trace']


def test_each_explicit_accountability_condition_gates_the_premium():
    for field in ('actor_knew_risk', 'duty_to_act', 'intentional_choice', 'consequences_comparable'):
        case = context(**{field: False})
        result = plugin.evaluate(case, 0.8)
        assert result['state']['last_action_premium'] == 0.0
        assert result['active'] is False


def test_scenario_contract_fields_are_flat_and_nonreserved():
    scenarios = plugin.scenarios()
    assert {s['name'] for s in scenarios} >= {'positive', 'boundary'}
    for scenario in scenarios:
        assert scenario['contexts']
        for phase in scenario['contexts']:
            assert set(plugin.METADATA['required_inputs']) <= phase.keys()
            assert not ({'state', 'peer_states', 'uniform', 'round_index', 'agent_index'} & phase.keys())
