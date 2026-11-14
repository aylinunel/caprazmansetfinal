from copy import deepcopy

import pytest

from mechanisms import pluralistic_ignorance as pi


def context(**overrides):
    value = {
        'private_positions': [1, 1, 1],
        'perceived_support': [0.2, 0.2, 0.2],
        'state': {},
        'peer_states': [],
        'round_index': 0,
        'agent_index': 0,
        'uniform': 0.25,
    }
    value.update(overrides)
    return value


def test_numeric_choice_oracle_when_gate_and_uniform_select_conformity():
    result = pi.evaluate(context(), 0.8)
    assert result['state']['private_position'] == 1
    assert result['state']['public_position'] == 0
    assert result['metric'] == 1
    assert result['active'] is True
    assert result['state']['conforming_steps'] == 1
    assert 'necessary_misperception_gate=True' in result['trace'][0]


def test_positive_direction_against_private_expression_reference():
    scenario = pi.scenarios()[0]
    intervention = [
        pi.evaluate(context(private_positions=scenario['contexts'][0]['private_positions'],
                           perceived_support=scenario['contexts'][0]['perceived_support'],
                           agent_index=i, uniform=u), 0.8)['metric']
        for i, u in enumerate((0.1, 0.4, 0.9))
    ]
    reference = [
        pi.evaluate(context(private_positions=[1, 1, 1], perceived_support=[0.2] * 3,
                           agent_index=i, uniform=u), 0.0)['metric']
        for i, u in enumerate((0.1, 0.4, 0.9))
    ]
    assert sum(intervention) / 3 > sum(reference) / 3


def test_boundary_removes_misperception_condition_and_matches_reference():
    scenario = pi.scenarios()[1]
    fields = scenario['contexts'][0]
    for i, u in enumerate((0.0, 0.3, 0.7)):
        base = pi.evaluate(context(**fields, agent_index=i, uniform=u), 0.0)
        treated = pi.evaluate(context(**fields, agent_index=i, uniform=u), 0.8)
        assert treated['metric'] == base['metric'] == 0
        assert treated['active'] is False
        assert 'necessary_misperception_gate=False' in treated['trace'][0]


def test_zero_strength_always_uses_private_position_even_when_gate_holds():
    result = pi.evaluate(context(agent_index=1, uniform=0.0), 0.0)
    assert result['state']['public_position'] == 1
    assert result['metric'] == 0
    assert result['active'] is False


def test_strength_probability_cutoff_controls_the_choice():
    low_draw = pi.evaluate(context(uniform=0.79), 0.8)
    high_draw = pi.evaluate(context(uniform=0.81), 0.8)
    assert low_draw['state']['public_position'] == 0
    assert high_draw['state']['public_position'] == 1
    assert low_draw['metric'] == 1 and high_draw['metric'] == 0


def test_missing_and_invalid_phase_inputs_are_rejected():
    missing = context()
    del missing['perceived_support']
    with pytest.raises(ValueError, match='perceived_support'):
        pi.evaluate(missing, 0.8)
    with pytest.raises(ValueError, match='match'):
        pi.evaluate(context(perceived_support=[0.2]), 0.8)
    with pytest.raises(ValueError, match='fractions'):
        pi.evaluate(context(perceived_support=[0.2, float('nan'), 0.2]), 0.8)
    with pytest.raises(ValueError, match='binary'):
        pi.evaluate(context(private_positions=[1, 2, 1]), 0.8)
    with pytest.raises(ValueError, match='binary'):
        pi.evaluate(context(private_positions=[1.0, 1, 1]), 0.8)
    with pytest.raises(ValueError, match='strength'):
        pi.evaluate(context(), float('inf'))


def test_deterministic_and_nonmutating_with_nested_input_state():
    original = context(state={'conforming_steps': 2, 'history': {'tag': 'prior'}})
    before = deepcopy(original)
    first = pi.evaluate(original, 0.8)
    second = pi.evaluate(original, 0.8)
    assert first == second
    assert original == before
    assert first['state']['conforming_steps'] == 3
    assert first['state']['private_public_mismatch'] == 1


def test_non_shared_or_non_strict_majority_is_not_pluralistic_ignorance():
    # Person 0 privately opposes the strict actual support majority, so the
    # required private-view/actual-majority alignment is absent.
    result = pi.evaluate(context(private_positions=[0, 1, 1],
                                 perceived_support=[0.1, 0.1, 0.1], uniform=0.0), 1.0)
    assert result['active'] is False
    assert result['metric'] == 0


@pytest.mark.parametrize('n_agents', [2, 12, 50])
def test_population_factory_declares_exact_group_and_same_teaching_assumptions(n_agents):
    scenarios = pi.scenarios_for_population(n_agents)
    for scenario in scenarios:
        fields = scenario['contexts'][0]
        assert fields['private_positions'] == [1] * n_agents
        assert len(fields['perceived_support']) == n_agents
    assert scenarios[0]['contexts'][0]['perceived_support'] == [0.2] * n_agents
    assert scenarios[1]['contexts'][0]['perceived_support'] == [0.8] * n_agents


@pytest.mark.parametrize('n_agents', [12, 50])
def test_mesa_builtin_population_factory_runs_and_preserves_reference(n_agents):
    import expanded_mesa as engine
    intervention = engine.ExpandedDecisionModel('pluralistic_ignorance', n_agents=n_agents,
                                                strength=1.0, seed=42).run_task()
    reference = engine.ExpandedDecisionModel('pluralistic_ignorance', n_agents=n_agents,
                                             strength=0.0, seed=42).run_task()
    assert all(a.metric == 1 for a in intervention.agents)
    assert all(a.metric == 0 for a in reference.agents)
    boundary = pi.scenarios_for_population(n_agents)[1]
    model = engine.ExpandedDecisionModel('pluralistic_ignorance', scenario=boundary,
                                        n_agents=n_agents, strength=1.0, seed=42).run_task()
    assert all(a.metric == 0 for a in model.agents)


def test_custom_group_is_not_silently_resized_or_agent_index_wrapped():
    import expanded_mesa as engine
    custom = pi.scenarios()[0]
    before = deepcopy(custom)
    model = engine.ExpandedDecisionModel('pluralistic_ignorance', scenario=custom,
                                        n_agents=12, strength=0.8, seed=42)
    assert model.scenario_data['contexts'][0]['private_positions'] == [1, 1, 1]
    with pytest.raises(ValueError, match='agent_index'):
        model.run_task()
    assert custom == before


def test_population_factory_rejects_invalid_group_sizes():
    for value in (True, 1, 0, -1, 2.5):
        with pytest.raises(ValueError):
            pi.scenarios_for_population(value)
