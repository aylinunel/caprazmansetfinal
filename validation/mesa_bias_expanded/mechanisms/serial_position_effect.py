"""Illustrative serial-position recallability process; not a fitted human model."""
from __future__ import annotations

import math


METADATA = {
    'id': 'serial_position_effect',
    'name': 'Serial Position Effect',
    'kind': 'cognitive_bias',
    'description': (
        'After an ordered list is encoded, estimate recallability from the '
        'target item’s combined, centered primacy and recency position weight.'
    ),
    # These are the only task fields common to every phase. Phase-specific
    # fields are validated by evaluate(), not declared as unconditional inputs.
    'required_inputs': ['phase', 'list_id', 'list_length'],
    'state_fields': ['list_id', 'list_length', 'presented_items', 'last_metric'],
    'metric_name': 'predicted_target_recallability',
    'metric_units': 'unit-interval probability-like score (illustrative, not calibrated)',
    'assumptions': [
        'A single finite list is presented in chronological order before one target is probed.',
        'Primacy and recency contribute jointly to one serial-position pattern; they are not counted as separate findings.',
        'The combined positional weight is centered within the presented list, so a one-item list has no positional deviation.',
        'At strength zero, the explicit reference assigns every target a recallability score of 0.5.',
        'The decay rate and log-odds scale are illustrative user-settable modeling assumptions, not empirical effect sizes.',
    ],
    'limitations': [
        'This compact process models one probe and one list; it does not simulate free recall, output order, interference, rehearsal, or individual memory.',
        'The score is not a measured recall probability, a detector, a diagnosis, or evidence of a population-level effect.',
        'Primacy and recency may arise from distinct processes; this umbrella implementation does not identify their causes or count them independently.',
    ],
    'empirically_validated': False,
    'synthetic_only': True,
}

_BASELINE = 0.5
_DECAY = 0.9
_LOG_ODDS_SCALE = 1.2


def _check_strength(strength: float) -> float:
    if isinstance(strength, bool) or not isinstance(strength, (int, float)) or not math.isfinite(strength) or not 0 <= strength <= 1:
        raise ValueError('strength must be finite and in [0, 1]')
    return float(strength)


def _nonempty_string(value, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{name} must be a nonempty string')
    return value


def evaluate(context: dict, strength: float) -> dict:
    """Advance list encoding or score a probe without mutating context/state."""
    strength = _check_strength(strength)
    if not isinstance(context, dict):
        raise ValueError('context must be an object')
    for key in METADATA['required_inputs']:
        if key not in context:
            raise ValueError(f'missing required task input {key}')

    phase = context['phase']
    if phase not in ('present', 'probe'):
        raise ValueError("phase must be 'present' or 'probe'")
    list_id = _nonempty_string(context['list_id'], 'list_id')
    list_length = context['list_length']
    if isinstance(list_length, bool) or not isinstance(list_length, int) or list_length < 1:
        raise ValueError('list_length must be a positive integer')

    old_state = context.get('state', {})
    if not isinstance(old_state, dict):
        raise ValueError('state must be an object')
    state = {
        'list_id': old_state.get('list_id'),
        'list_length': old_state.get('list_length'),
        'presented_items': [dict(item) for item in old_state.get('presented_items', [])],
        'last_metric': old_state.get('last_metric', _BASELINE),
    }
    items = state['presented_items']
    if not isinstance(state['last_metric'], (int, float)) or isinstance(state['last_metric'], bool) or not math.isfinite(state['last_metric']):
        raise ValueError('state.last_metric must be finite numeric')
    if state['list_id'] is None:
        if items or state['list_length'] is not None:
            raise ValueError('incomplete list history in state')
    else:
        if state['list_id'] != list_id or state['list_length'] != list_length:
            raise ValueError('context list identity/length does not match chronological history')
        if not isinstance(items, list):
            raise ValueError('state.presented_items must be a list')
        for index, item in enumerate(items, 1):
            if (not isinstance(item, dict) or item.get('position') != index
                    or not isinstance(item.get('item_id'), str) or not item['item_id'].strip()):
                raise ValueError('state contains invalid or nonconsecutive presentation history')
        if len({item['item_id'] for item in items}) != len(items):
            raise ValueError('an item cannot appear twice in one list')

    if phase == 'present':
        item_id = _nonempty_string(context.get('item_id'), 'item_id')
        position = context.get('position')
        if isinstance(position, bool) or not isinstance(position, int):
            raise ValueError('position must be an integer')
        expected_position = len(items) + 1
        if position != expected_position or position > list_length:
            raise ValueError('presentations must be chronological and within list_length')
        if any(item['item_id'] == item_id for item in items):
            raise ValueError('item_id must be unique within the list')
        if state['list_id'] is None:
            state['list_id'] = list_id
            state['list_length'] = list_length
        items.append({'item_id': item_id, 'position': position})
        state['last_metric'] = _BASELINE
        return {
            'metric': _BASELINE,
            'active': False,
            'state': state,
            'trace': [f'Encoded item {item_id!r} at chronological position {position}/{list_length}; recall probe not yet evaluated.'],
        }

    target_id = _nonempty_string(context.get('target_item'), 'target_item')
    if len(items) != list_length:
        raise ValueError('probe requires the complete chronological list history')
    positions = {item['item_id']: item['position'] for item in items}
    if target_id not in positions:
        raise ValueError('target_item must identify an item in the presented list')

    # Summed edge kernels represent the umbrella U-shaped pattern. Centering
    # by the list mean makes this a relative position effect rather than a
    # generic positive offset and guarantees equality for a singleton list.
    weights = [
        math.exp(-_DECAY * (p - 1)) + math.exp(-_DECAY * (list_length - p))
        for p in range(1, list_length + 1)
    ]
    mean_weight = sum(weights) / list_length
    centered_weight = weights[positions[target_id] - 1] - mean_weight
    log_odds = strength * _LOG_ODDS_SCALE * centered_weight
    metric = 1.0 / (1.0 + math.exp(-log_odds))
    state['last_metric'] = metric
    active = strength > 0 and abs(metric - _BASELINE) > 1e-15
    return {
        'metric': metric,
        'active': active,
        'state': state,
        'trace': [
            f'Probe {target_id!r} at position {positions[target_id]}/{list_length}: '
            f'logit(score)=strength({_LOG_ODDS_SCALE:g}*centered combined edge-kernel '
            f'{centered_weight:.6f}); score={metric:.6f}.',
        ],
    }


def scenarios() -> list[dict]:
    list_id = 'ordered-five-item-list'
    contexts = [
        {'phase': 'present', 'list_id': list_id, 'list_length': 5,
         'item_id': f'item-{position}', 'position': position}
        for position in range(1, 6)
    ]
    contexts.append({'phase': 'probe', 'list_id': list_id, 'list_length': 5,
                     'target_item': 'item-1'})

    singleton_id = 'singleton-list'
    boundary = [
        {'phase': 'present', 'list_id': singleton_id, 'list_length': 1,
         'item_id': 'only-item', 'position': 1},
        {'phase': 'probe', 'list_id': singleton_id, 'list_length': 1,
         'target_item': 'only-item'},
    ]
    return [
        {
            'name': 'positive',
            'initial_state': {},
            'contexts': contexts,
            'expectation': 'increase',
        },
        {
            'name': 'boundary',
            'initial_state': {},
            'contexts': boundary,
            'expectation': 'equal',
        },
    ]
