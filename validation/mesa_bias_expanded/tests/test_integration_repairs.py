"""Regression tests for saved modules' real interface mismatches."""
from copy import deepcopy

import pytest
import expanded_mesa as engine

REPAIRED = ('attentional_bias','causal_overclaim','google_effect','hindsight_bias','selective_statistics')


@pytest.mark.parametrize('concept', REPAIRED)
def test_repaired_modules_satisfy_shared_runner_without_changed_oracle(concept):
    result = engine.validate_one(concept)
    assert result['status'] == 'PASS', result


@pytest.mark.parametrize('concept', REPAIRED)
def test_common_required_metadata_contains_real_keys_not_descriptions(concept):
    plugin = engine.load_plugin(concept)
    for scenario in plugin.scenarios():
        for context in scenario['contexts']:
            assert set(plugin.METADATA['required_inputs']).issubset(context)


@pytest.mark.parametrize('concept,context', [
    ('google_effect', {'action':'study'}),
    ('google_effect', {'action':'retrieve'}),
    ('hindsight_bias', {'stage':'forecast'}),
])
def test_conditional_evidence_still_rejected_if_missing(concept, context):
    context = deepcopy(context)
    context.update({'state':{},'peer_states':[],'round_index':0,'agent_index':0,'uniform':0.25})
    with pytest.raises(ValueError):
        engine.checked_evaluate(engine.load_plugin(concept), context, 0.8)


def test_selective_statistics_scenarios_cannot_override_rng_draw():
    plugin = engine.load_plugin('selective_statistics')
    for scenario in plugin.scenarios():
        assert all('uniform' not in context for context in scenario['contexts'])
    a = engine.ExpandedDecisionModel('selective_statistics',n_agents=4,seed=42)
    b = engine.ExpandedDecisionModel('selective_statistics',n_agents=4,seed=42,strength=0)
    assert (a.uniforms == b.uniforms).all()
