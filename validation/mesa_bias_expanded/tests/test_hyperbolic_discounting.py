from copy import deepcopy
import math

import pytest

from mechanisms import hyperbolic_discounting as hd


def run(contexts, strength, initial_state=None):
    state = deepcopy(initial_state or {'choices': [], 'larger_later_choices': 0, 'choice_reversals': 0, 'trials': 0})
    outputs = []
    for i, task in enumerate(contexts):
        context = deepcopy(task)
        context.update(state=deepcopy(state), peer_states=[], round_index=i, agent_index=0, uniform=0.25)
        out = hd.evaluate(context, strength)
        state = deepcopy(out['state'])
        outputs.append(out)
    return outputs


def positive_contexts():
    return deepcopy(next(s for s in hd.scenarios() if s['name'] == 'positive')['contexts'])


def test_numeric_oracle_selects_far_larger_later_then_reverses_near():
    contexts = positive_contexts()
    far = hd.evaluate({**contexts[0], 'state': {'choices': [], 'larger_later_choices': 0, 'choice_reversals': 0, 'trials': 0}}, 1.0)
    near = hd.evaluate({**contexts[1], 'state': far['state']}, 1.0)
    # At far delay, hyperbolic values are 20/7.2 and 18/7; near they are 10 and 18.
    assert far['state']['choices'] == ['larger_later']
    assert far['trace'][0].startswith('Intervention values: smaller-sooner=2.5714286, larger-later=2.7777778')
    assert near['state']['choices'] == ['larger_later', 'smaller_sooner']
    assert near['state']['choice_reversals'] == 1
    assert near['metric'] == 1


def test_positive_scenario_final_metric_increases_vs_strength_zero():
    scenario = next(s for s in hd.scenarios() if s['name'] == 'positive')
    treated = run(scenario['contexts'], 0.8, scenario['initial_state'])[-1]
    reference = run(scenario['contexts'], 0.0, scenario['initial_state'])[-1]
    assert treated['metric'] > reference['metric']
    assert treated['metric'] == 1
    assert reference['metric'] == 0


def test_boundary_equal_delays_have_same_final_metric_as_reference():
    scenario = next(s for s in hd.scenarios() if s['name'] == 'boundary')
    treated = run(scenario['contexts'], 0.8, scenario['initial_state'])[-1]
    reference = run(scenario['contexts'], 0.0, scenario['initial_state'])[-1]
    assert treated['metric'] == reference['metric'] == 2
    assert not treated['active']


def test_zero_strength_is_explicit_exponential_reference_and_inactive():
    scenario = next(s for s in hd.scenarios() if s['name'] == 'positive')
    result = run(scenario['contexts'], 0.0, scenario['initial_state'])
    # Exponential rate .15: far LL is worth less than SS; near LL also loses.
    assert [out['state']['choices'][-1] for out in result] == ['smaller_sooner', 'smaller_sooner']
    assert all(out['active'] is False for out in result)
    assert result[-1]['state']['trials'] == 2


def test_missing_or_impossible_phase_input_is_rejected():
    ctx = deepcopy(positive_contexts()[0])
    ctx.pop('larger_later_delay')
    with pytest.raises(ValueError, match='missing required task input'):
        hd.evaluate(ctx, 0.8)
    ctx = deepcopy(positive_contexts()[0])
    ctx['larger_later_delay'] = float('nan')
    with pytest.raises(ValueError, match='finite'):
        hd.evaluate(ctx, 0.8)
    ctx = deepcopy(positive_contexts()[0])
    ctx['larger_later_amount'] = ctx['smaller_sooner_amount']
    with pytest.raises(ValueError, match='must exceed'):
        hd.evaluate(ctx, 0.8)


def test_deterministic_and_nonmutating_with_nested_history():
    context = deepcopy(positive_contexts()[1])
    context.update(state={'choices': ['larger_later'], 'larger_later_choices': 1, 'choice_reversals': 0, 'trials': 1},
                   peer_states=[{'choices': ['smaller_sooner']}], round_index=1, agent_index=2, uniform=0.7)
    before = deepcopy(context)
    one = hd.evaluate(context, 0.8)
    two = hd.evaluate(context, 0.8)
    assert context == before
    assert one == two
    assert one['state']['choices'] == ['larger_later', 'smaller_sooner']
    assert one['state']['choice_reversals'] == 1


def test_invalid_strength_and_state_are_rejected():
    ctx = positive_contexts()[0]
    for strength in (-0.1, 1.1, math.inf, True):
        with pytest.raises(ValueError):
            hd.evaluate(ctx, strength)
    bad_state_context = {**ctx, 'state': {'choices': ['larger_later'], 'larger_later_choices': 0, 'choice_reversals': 0, 'trials': 1}}
    with pytest.raises(ValueError, match='counters'):
        hd.evaluate(bad_state_context, 0.8)
