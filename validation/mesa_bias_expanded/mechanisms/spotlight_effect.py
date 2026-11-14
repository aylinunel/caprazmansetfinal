"""Illustrative external-attention overestimation process; not a detector or diagnosis."""
from __future__ import annotations

import math


# Illustrative gain only; it is not an empirical effect-size estimate.
_SELF_SALIENCE_GAIN = 2.5

METADATA = {
    'id': 'spotlight_effect',
    'name': 'Spotlight Effect',
    'kind': 'cognitive_bias',
    'description': (
        'Models an estimate of audience attention that overweights the focal '
        'event relative to competing visible events in proportion to the '
        'agent\'s explicit self-salience.'
    ),
    # These are the only ordinary task fields required in every scenario phase.
    'required_inputs': ['focal_prominence', 'other_prominence', 'self_salience'],
    'state_fields': ['last_reference_share', 'last_estimated_share', 'last_overestimate'],
    'metric_name': 'modeled_external_attention_overestimate',
    'metric_units': 'audience-attention share points (estimated share minus reference share)',
    'assumptions': [
        'Prominence values are hypothetical, externally visible salience ratings on [0, 1].',
        'At strength zero, estimated audience attention follows the normalized prominence share.',
        'Self-salience multiplicatively increases the estimated prominence of the focal event; the gain is illustrative and user-settable.',
        'The modeled share is a task observable, not a measured human belief or an estimate of actual audience behavior.',
    ],
    'limitations': [
        'The two-option allocation omits audience heterogeneity, context, attention costs, and individual differences.',
        'Self-salience is an explicit hypothetical input and is not inferred from behavior or language.',
        'Strength is an uncalibrated intervention setting; no empirical validity or population claim is made.',
        'This external-attention model does not represent perceived visibility of private thoughts or feelings (illusion of transparency).',
    ],
    'empirically_validated': False,
    'synthetic_only': True,
}


def _unit_interval(context: dict, key: str) -> float:
    value = context[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f'{key} must be a finite number in [0, 1]')
    value = float(value)
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f'{key} must be a finite number in [0, 1]')
    return value


def evaluate(context: dict, strength: float) -> dict:
    """Estimate focal-event audience share after self-salience reweights its prominence."""
    if not isinstance(context, dict):
        raise ValueError('context must be an object')
    if isinstance(strength, bool) or not isinstance(strength, (int, float)):
        raise ValueError('strength must be finite and in [0, 1]')
    strength = float(strength)
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError('strength must be finite and in [0, 1]')
    for key in METADATA['required_inputs']:
        if key not in context:
            raise ValueError(f'missing required task input {key}')

    focal = _unit_interval(context, 'focal_prominence')
    other = _unit_interval(context, 'other_prominence')
    self_salience = _unit_interval(context, 'self_salience')
    if focal + other <= 0.0:
        raise ValueError('at least one visible event must have positive prominence')

    reference_share = focal / (focal + other)
    # Reweight the focal event's prominence rather than adding a constant penalty.
    weighted_focal = focal * (1.0 + _SELF_SALIENCE_GAIN * strength * self_salience)
    estimated_share = weighted_focal / (weighted_focal + other)
    overestimate = estimated_share - reference_share

    previous = context.get('state', {})
    if not isinstance(previous, dict):
        raise ValueError('state must be an object')
    next_state = dict(previous)
    next_state.update({
        'last_reference_share': reference_share,
        'last_estimated_share': estimated_share,
        'last_overestimate': overestimate,
    })
    active = overestimate > 0.0
    return {
        'metric': overestimate,
        'active': active,
        'state': next_state,
        'trace': [
            'Reference share = focal_prominence / (focal_prominence + other_prominence); '
            'estimated share = focal_prominence*(1 + 2.5*strength*self_salience) / '
            '(focal_prominence*(1 + 2.5*strength*self_salience) + other_prominence); '
            'metric = estimated share - reference share. '
            f'Inputs: focal={focal:g}, other={other:g}, self_salience={self_salience:g}, strength={strength:g}.'
        ],
    }


def scenarios() -> list[dict]:
    return [
        {
            'name': 'positive',
            'initial_state': {},
            'contexts': [{
                'focal_prominence': 0.20,
                'other_prominence': 0.80,
                'self_salience': 0.90,
            }],
            'expectation': 'increase',
        },
        {
            'name': 'boundary',
            'initial_state': {},
            # Necessary self-salience condition is removed; prominence evidence remains.
            'contexts': [{
                'focal_prominence': 0.20,
                'other_prominence': 0.80,
                'self_salience': 0.0,
            }],
            'expectation': 'equal',
        },
    ]
