from copy import deepcopy
import math

import pytest

from mechanisms import messenger_effect as plugin


def context(**overrides):
    value = {
        'message_support': 0.60,
        'messenger_affinity': 0.80,
        'cue_salience': 0.90,
        'state': {},
        'peer_states': [],
        'round_index': 0,
        'agent_index': 0,
        'uniform': 0.4,
    }
    value.update(overrides)
    return value


def test_numeric_oracle_and_complete_state():
    actual = plugin.evaluate(context(), 0.8)
    log_odds = math.log(0.60 / 0.40) + 0.8 * 1.5 * 0.8 * 0.9
    expected = 1.0 / (1.0 + math.exp(-log_odds))
    assert actual['metric'] == pytest.approx(expected, abs=1e-12)
    assert actual['metric'] > 0.60
    assert actual['state'] == {'last_reception': pytest.approx(expected), 'reception_count': 1}
    assert actual['active'] is True
    assert len(actual['trace']) >= 1
    assert all(isinstance(line, str) for line in actual['trace'])


def test_positive_scenario_direction_and_boundary_removes_cue_condition():
    positive, boundary = plugin.scenarios()
    pos_effect = plugin.evaluate(context(**positive['contexts'][0]), 0.8)['metric'] - plugin.evaluate(context(**positive['contexts'][0]), 0.0)['metric']
    boundary_effect = plugin.evaluate(context(**boundary['contexts'][0]), 0.8)['metric'] - plugin.evaluate(context(**boundary['contexts'][0]), 0.0)['metric']
    assert positive['name'] == 'positive' and pos_effect > 0
    assert boundary['name'] == 'boundary' and boundary['contexts'][0]['cue_salience'] == 0.0
    assert boundary_effect == pytest.approx(0.0, abs=1e-12)


def test_strength_zero_is_explicit_message_support_reference():
    result = plugin.evaluate(context(message_support=0.23, messenger_affinity=-1.0), 0.0)
    assert result['metric'] == pytest.approx(0.23, abs=1e-12)
    assert result['active'] is False


def test_missing_and_invalid_phase_inputs_are_rejected():
    missing = context()
    del missing['messenger_affinity']
    with pytest.raises(ValueError, match='messenger_affinity'):
        plugin.evaluate(missing, 0.8)
    for key, value in [('message_support', 1.0), ('messenger_affinity', 1.1), ('cue_salience', float('nan'))]:
        with pytest.raises(ValueError, match=key):
            plugin.evaluate(context(**{key: value}), 0.8)


def test_invalid_strength_and_state_rejected():
    for strength in (-0.01, 1.01, float('inf'), True):
        with pytest.raises(ValueError, match='strength'):
            plugin.evaluate(context(), strength)
    with pytest.raises(ValueError, match='reception_count'):
        plugin.evaluate(context(state={'reception_count': -1}), 0.5)


def test_deterministic_and_nonmutating_including_nested_state():
    original = context(state={'reception_count': 2, 'last_reception': 0.4, 'memo': {'tags': ['x']}})
    snapshot = deepcopy(original)
    first = plugin.evaluate(original, 0.6)
    second = plugin.evaluate(original, 0.6)
    assert first == second
    assert original == snapshot
    assert first['state']['reception_count'] == 3
    assert first['state']['memo'] == {'tags': ['x']}
