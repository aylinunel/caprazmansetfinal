from copy import deepcopy

import pytest

from mechanisms import regret_aversion as plugin


POSITIVE = plugin.scenarios()[0]['contexts'][0]
BOUNDARY = plugin.scenarios()[1]['contexts'][0]


def test_numeric_oracle_and_choice_change_match_downside_regret_equation():
    result = plugin.evaluate(deepcopy(POSITIVE), 0.8)
    # EV(action)=4, EV(status quo)=3, expected downside regret=.5*(3-0)=1.5.
    # At strength .8 the action score is 4 - .8*1.5 = 2.8, so status quo wins.
    assert result['metric'] == 0.0
    assert result['state']['last_choice'] == 'status_quo'
    assert result['state']['cumulative_expected_regret'] == pytest.approx(1.5)
    assert result['active'] is True
    baseline = plugin.evaluate(deepcopy(POSITIVE), 0.0)
    assert baseline['metric'] == 1.0
    assert baseline['state']['last_choice'] == 'action'


def test_positive_scenario_has_expected_mean_direction():
    at_zero = plugin.evaluate(deepcopy(POSITIVE), 0.0)['metric']
    at_point_eight = plugin.evaluate(deepcopy(POSITIVE), 0.8)['metric']
    assert at_point_eight < at_zero


def test_boundary_without_counterfactual_feedback_matches_reference():
    reference = plugin.evaluate(deepcopy(BOUNDARY), 0.0)
    intervention = plugin.evaluate(deepcopy(BOUNDARY), 0.8)
    assert intervention['metric'] == reference['metric'] == 1.0
    assert intervention['active'] is False
    assert intervention['state']['cumulative_expected_regret'] == 0.0


def test_zero_strength_is_explicit_expected_value_reference():
    result = plugin.evaluate(deepcopy(POSITIVE), 0.0)
    assert result['metric'] == 1.0
    assert result['state']['last_choice'] == 'action'
    assert result['active'] is False


@pytest.mark.parametrize('strength', [-0.01, 1.01, float('nan'), float('inf'), True])
def test_invalid_strength_is_rejected(strength):
    with pytest.raises(ValueError):
        plugin.evaluate(deepcopy(POSITIVE), strength)


def test_missing_and_invalid_phase_specific_inputs_are_rejected():
    missing = deepcopy(POSITIVE)
    del missing['comparison_feedback']
    with pytest.raises(ValueError, match='comparison_feedback'):
        plugin.evaluate(missing, 0.8)

    missing = deepcopy(POSITIVE)
    del missing['options']
    with pytest.raises(ValueError, match='options'):
        plugin.evaluate(missing, 0.8)

    invalid = deepcopy(POSITIVE)
    invalid['options'][0]['outcomes'][0]['probability'] = 0.9
    with pytest.raises(ValueError, match='sum to 1'):
        plugin.evaluate(invalid, 0.8)

    invalid = deepcopy(POSITIVE)
    invalid['comparison_feedback'] = 1.1
    with pytest.raises(ValueError, match='<= 1'):
        plugin.evaluate(invalid, 0.8)


def test_deterministic_nonmutation_and_chronological_state_carry():
    context = deepcopy(POSITIVE)
    context['state'] = {
        'last_choice': None,
        'decision_count': 2,
        'cumulative_expected_regret': 0.25,
    }
    before = deepcopy(context)
    first = plugin.evaluate(context, 0.8)
    second = plugin.evaluate(context, 0.8)
    assert context == before
    assert first == second
    assert first['state']['decision_count'] == 3
    assert first['state']['cumulative_expected_regret'] == pytest.approx(1.75)
    next_context = deepcopy(BOUNDARY)
    next_context['state'] = deepcopy(first['state'])
    next_result = plugin.evaluate(next_context, 0.8)
    assert next_result['state']['decision_count'] == 4
    assert next_result['state']['last_choice'] == 'action'
    assert next_result['state']['cumulative_expected_regret'] == pytest.approx(1.75)
