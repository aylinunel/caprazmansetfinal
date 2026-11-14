"""Illustrative messenger-cue effect on reception of a fixed message."""
import math


METADATA = {
    'id': 'messenger_effect',
    'name': 'Messenger Effect',
    'kind': 'cognitive_bias',
    'description': (
        'Models how an explicitly supplied, non-status messenger-affinity cue '
        'changes reception of otherwise fixed message evidence.'
    ),
    'required_inputs': ['message_support', 'messenger_affinity', 'cue_salience'],
    'state_fields': ['last_reception', 'reception_count'],
    'metric_name': 'reception_probability',
    'metric_units': 'Expected acceptance probability on a 0–1 scale',
    'assumptions': [
        'message_support is the strength-zero reference reception probability for the fixed message.',
        'messenger_affinity is an explicit signed relational/familiarity response, not status or authority.',
        'The cue acts multiplicatively on message-reception odds; coefficient 1.5 is illustrative and strength is an uncalibrated intervention.',
    ],
    'limitations': [
        'A stylized process, not a detector, diagnosis, population claim, or empirically fitted effect.',
        'Affinity may be informative or benign; the model does not label it irrational and cannot adjudicate whether the cue is warranted.',
        'The one-step metric is expected reception, not a realized human choice or message truth.',
    ],
    'empirically_validated': False,
    'synthetic_only': True,
}


def _number(context, key, low, high, *, open_low=False, open_high=False):
    value = context[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'{key} must be a finite number')
    if (value <= low if open_low else value < low) or (value >= high if open_high else value > high):
        left = '(' if open_low else '['
        right = ')' if open_high else ']'
        raise ValueError(f'{key} must be in {left}{low}, {high}{right}')
    return float(value)


def evaluate(context: dict, strength: float) -> dict:
    if not isinstance(context, dict):
        raise ValueError('context must be a dict')
    if isinstance(strength, bool) or not isinstance(strength, (int, float)) or not math.isfinite(strength) or not 0 <= strength <= 1:
        raise ValueError('strength must be finite and in [0, 1]')
    for key in METADATA['required_inputs']:
        if key not in context:
            raise ValueError(f'missing required task input {key}')

    support = _number(context, 'message_support', 0.0, 1.0, open_low=True, open_high=True)
    affinity = _number(context, 'messenger_affinity', -1.0, 1.0)
    salience = _number(context, 'cue_salience', 0.0, 1.0)
    state = context.get('state', {})
    if not isinstance(state, dict):
        raise ValueError('state must be a dict')
    count = state.get('reception_count', 0)
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        raise ValueError('state.reception_count must be a nonnegative integer')
    prior = state.get('last_reception')
    if prior is not None and (isinstance(prior, bool) or not isinstance(prior, (int, float)) or not math.isfinite(prior) or not 0 <= prior <= 1):
        raise ValueError('state.last_reception must be a finite probability')

    # The strength-zero reference follows the supplied message support. The
    # messenger changes log-odds only when an identity/presentation cue is both
    # salient and has nonzero signed affinity; status/authority is not modeled.
    cue_log_odds = float(strength) * 1.5 * affinity * salience
    reception = 1.0 / (1.0 + math.exp(-(math.log(support / (1.0 - support)) + cue_log_odds)))
    next_state = dict(state)
    next_state.update({'last_reception': reception, 'reception_count': count + 1})
    active = cue_log_odds != 0.0
    trace = [
        f'Fixed-message reference support={support:.6g}; messenger affinity={affinity:.6g}, cue salience={salience:.6g}.',
        f'Reception odds multiply by exp(strength × 1.5 × affinity × salience) = exp({cue_log_odds:.6g}); reception={reception:.6g}.',
    ]
    return {'metric': reception, 'active': active, 'state': next_state, 'trace': trace}


def scenarios() -> list[dict]:
    return [
        {
            'name': 'positive',
            'initial_state': {},
            'contexts': [{
                'message_support': 0.60,
                'messenger_affinity': 0.80,
                'cue_salience': 0.90,
            }],
            'expectation': 'increase',
        },
        {
            'name': 'boundary',
            'initial_state': {},
            'contexts': [{
                'message_support': 0.60,
                'messenger_affinity': 0.80,
                'cue_salience': 0.0,
            }],
            'expectation': 'equal',
        },
    ]
