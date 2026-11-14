"""Shared mechanics and full-scope contracts, not empirical psychological tests."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import pytest

import expanded_mesa as engine

IDS = engine.expected_ids()


def test_exact_scope_is_138_unique_missing_ids_and_no_renamed_legacy_rules():
    assert len(IDS) == len(set(IDS)) == 138
    assert not {'anchoring_bias','confirmation_bias','bandwagon_effect','social_norms'}.intersection(IDS)
    specs=json.loads((engine.ROOT/'missing_concepts.json').read_text())
    assert sum(s['layer']=='mercek_cognitive_concept' for s in specs)==112
    assert sum(s['layer']!='mercek_cognitive_concept' for s in specs)==26


@pytest.mark.parametrize('concept', IDS)
def test_each_new_plugin_executable_contract(concept):
    result=engine.validate_one(concept)
    assert result['status']=='PASS', result


@pytest.mark.parametrize('concept', IDS)
def test_each_plugin_has_real_module_tests_and_implementation_note(concept):
    assert (engine.ROOT/'mechanisms'/f'{concept}.py').is_file()
    assert (engine.ROOT/'tests'/f'test_{concept}.py').is_file()
    assert (engine.ROOT/'specs'/f'{concept}_implementation.md').is_file()
    assert (engine.ROOT/'specs'/f'{concept}_implementation.md').stat().st_size>100


@pytest.mark.parametrize('concept', IDS)
def test_plugins_preserve_context_and_are_deterministic_on_supplied_draw(concept):
    plugin=engine.load_plugin(concept)
    scenario=engine.check_scenario(plugin.scenarios()[0])
    context=deepcopy(scenario['contexts'][0])
    context.update({'state':deepcopy(scenario['initial_state']),
                    'peer_states':[deepcopy(scenario['initial_state']) for _ in range(2)],
                    'round_index':0,'agent_index':0,'uniform':0.25})
    original=deepcopy(context)
    a=engine.checked_evaluate(plugin,context,0.8)
    b=engine.checked_evaluate(plugin,context,0.8)
    assert a==b
    assert context==original


@pytest.mark.parametrize('value',[-0.1,1.1,float('nan'),float('inf'),True,None])
def test_invalid_strength_rejected(value):
    with pytest.raises(ValueError):engine.valid_strength(value)


def test_unknown_concept_not_silently_substituted():
    with pytest.raises(ValueError):engine.load_plugin('made_up_bias')


def test_context_cannot_replace_previous_peer_states_or_uniform_draw():
    for key in ('state','peer_states','uniform','agent_index','round_index'):
        with pytest.raises(ValueError):
            engine.check_scenario({'name':'bad','initial_state':{},
                                   'contexts':[{key:1}],'expectation':'equal'})


def test_staged_proposals_use_frozen_previous_state_and_do_not_commit_early():
    concept=IDS[0]
    model=engine.ExpandedDecisionModel(concept,n_agents=5,seed=42)
    before=model.snapshot()
    model.previous_states=deepcopy(before)
    model.agents.do('propose')
    assert model.snapshot()==before
    for agent in model.agents:
        assert agent.proposed is not None
    model.agents.do('commit')


def test_matched_strength_conditions_receive_identical_draws():
    concept=IDS[0]
    a=engine.ExpandedDecisionModel(concept,n_agents=5,strength=0,seed=10)
    b=engine.ExpandedDecisionModel(concept,n_agents=5,strength=.8,seed=10)
    np.testing.assert_array_equal(a.uniforms,b.uniforms)
    assert a.snapshot()==b.snapshot()
    assert a.neighbors==b.neighbors


def test_same_seed_reproduces_full_traces():
    concept=IDS[0]
    a=engine.ExpandedDecisionModel(concept,n_agents=3,seed=23).run_task()
    b=engine.ExpandedDecisionModel(concept,n_agents=3,seed=23).run_task()
    assert a.traces==b.traces


def test_round_zero_and_all_explicit_context_rounds_collected():
    concept=IDS[0]
    model=engine.ExpandedDecisionModel(concept,n_agents=3,seed=23).run_task()
    table=model.datacollector.get_model_vars_dataframe()
    assert len(table)==len(model.scenario_data['contexts'])+1
    assert table.iloc[0]['round']==0
    assert len(model.traces)==3*len(model.scenario_data['contexts'])


def test_zero_strength_paired_control_is_exactly_identical():
    concept=IDS[0]
    scenario=engine.load_plugin(concept).scenarios()[0]
    rows,_=engine.paired_run(concept,scenario,3,0,42)
    assert all(row['paired_delta']==0 for row in rows)


def test_summary_uses_seed_not_agent_as_sampling_unit():
    rows=[{'concept':'x','scenario':'y','seed':seed,'paired_delta':delta,
           'reference_metric':0,'intervention_metric':delta,'metric_name':'x','metric_units':'toy'}
          for seed,delta in [(1,1),(1,1),(2,3),(2,3)]]
    result=engine.summarize_pairs(rows)[0]
    assert result['replicates']==2
    assert result['mean_paired_delta']==2
    assert result['sd_paired_delta_across_seeds']==pytest.approx(np.sqrt(2))
