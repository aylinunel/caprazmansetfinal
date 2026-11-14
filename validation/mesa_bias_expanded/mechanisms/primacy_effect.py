"""Illustrative serial-position weighting in a bounded impression task."""
from __future__ import annotations

import math


_BETA = 0.6  # hypothetical intervention coefficient; not an empirical estimate

METADATA = {
    'id': 'primacy_effect',
    'name': 'Primacy Effect',
    'kind': 'cognitive_bias',
    'description': (
        'In an explicitly ordered sequence, earlier equally exposed items receive '
        'an extra weight when forming a bounded numeric impression.'
    ),
    'required_inputs': ['score', 'sequence_length', 'exposure', 'distinctiveness', 'order_cue_present'],
    'state_fields': [
        'item_count', 'sequence_length', 'reference_mass', 'reference_total',
        'primacy_mass', 'primacy_total',
    ],
    'metric_name': 'weighted_impression',
    'metric_units': 'bounded score units on the input score scale [0, 1]',
    'assumptions': [
        'Each context is one successive item in the same explicitly declared finite sequence.',
        'The strength-scaled early-position multiplier is a hypothetical process assumption.',
        'Exposure and distinctiveness jointly set the reference contribution of each item.',
        'The reference policy uses exposure-distinctiveness weighting without a position bonus.',
    ],
    'limitations': [
        'This is a small illustrative process, not a fitted or empirically validated effect size.',
        'Input scores and order cues are supplied structured facts, not detected from text or media.',
        'An altered impression is not necessarily harmful, irrational, or evidence of an individual trait.',
        'Serial-position effects include phenomena beyond this narrow early-item weighting.',
    ],
    'empirically_validated': False,
    'synthetic_only': True,
}


def _finite_number(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'{name} must be a finite number')
    return float(value)


def evaluate(context: dict, strength: float) -> dict:
    """Accumulate one observed score and recompute the sequence impression."""
    if isinstance(strength, bool) or not isinstance(strength, (int, float)) or not math.isfinite(strength) or not 0 <= strength <= 1:
        raise ValueError('strength must be finite and in [0, 1]')
    if not isinstance(context, dict):
        raise ValueError('context must be an object')
    for key in METADATA['required_inputs']:
        if key not in context:
            raise ValueError(f'missing required task input {key}')

    score = _finite_number(context['score'], 'score')
    exposure = _finite_number(context['exposure'], 'exposure')
    distinctiveness = _finite_number(context['distinctiveness'], 'distinctiveness')
    length = context['sequence_length']
    if not 0 <= score <= 1:
        raise ValueError('score must be in [0, 1]')
    if exposure <= 0 or distinctiveness <= 0:
        raise ValueError('exposure and distinctiveness must be positive')
    if isinstance(length, bool) or not isinstance(length, int) or length < 2:
        raise ValueError('sequence_length must be an integer >= 2')
    cue = context['order_cue_present']
    if not isinstance(cue, bool):
        raise ValueError('order_cue_present must be boolean')
    round_index = context.get('round_index', 0)
    if isinstance(round_index, bool) or not isinstance(round_index, int) or round_index < 0:
        raise ValueError('round_index must be a nonnegative integer')
    position = round_index + 1
    if position > length:
        raise ValueError('sequence contains more contexts than sequence_length')

    old = context.get('state', {})
    if not isinstance(old, dict):
        raise ValueError('state must be an object')
    fields = METADATA['state_fields']
    if old:
        if set(old) != set(fields):
            raise ValueError('state must contain the complete primacy task state')
        if (isinstance(old['item_count'], bool) or not isinstance(old['item_count'], int)
                or isinstance(old['sequence_length'], bool) or not isinstance(old['sequence_length'], int)
                or old['sequence_length'] != length or old['item_count'] != round_index):
            raise ValueError('state and chronological sequence position disagree')
        reference_mass = _finite_number(old['reference_mass'], 'state.reference_mass')
        reference_total = _finite_number(old['reference_total'], 'state.reference_total')
        primacy_mass = _finite_number(old['primacy_mass'], 'state.primacy_mass')
        primacy_total = _finite_number(old['primacy_total'], 'state.primacy_total')
        if (reference_mass <= 0 or primacy_mass <= 0
                or not 0 <= reference_total <= reference_mass
                or not 0 <= primacy_total <= primacy_mass):
            raise ValueError('state masses and totals are impossible for bounded positive-weight scores')
    else:
        if round_index != 0:
            raise ValueError('noninitial sequence position requires accumulated state')
        reference_mass = reference_total = primacy_mass = primacy_total = 0.0

    base_weight = exposure * distinctiveness
    # Earlier ordinal positions get a larger multiplier only when an explicit
    # serial-order cue is available. The last item's position bonus is zero.
    position_fraction = (length - position) / (length - 1)
    position_bonus = _BETA * float(strength) * position_fraction if cue else 0.0
    primacy_weight = base_weight * (1.0 + position_bonus)
    reference_mass += base_weight
    reference_total += base_weight * score
    primacy_mass += primacy_weight
    primacy_total += primacy_weight * score
    metric = primacy_total / primacy_mass
    state = {
        'item_count': position,
        'sequence_length': length,
        'reference_mass': reference_mass,
        'reference_total': reference_total,
        'primacy_mass': primacy_mass,
        'primacy_total': primacy_total,
    }
    active = bool(position_bonus > 0 and strength > 0 and score >= 0 and base_weight > 0)
    return {
        'metric': metric,
        'active': active,
        'state': state,
        'trace': [
            f'Item {position}/{length}: reference mass={base_weight:.6g}; '
            f'primacy multiplier=1+{position_bonus:.6g} from strength, ordinal '
            f'position, and order_cue_present={cue}; cumulative impression='
            f'{metric:.6g} ({primacy_total:.6g}/{primacy_mass:.6g}).'
        ],
    }


def scenarios() -> list[dict]:
    def item(score, cue=True):
        return {
            'score': score,
            'sequence_length': 3,
            'exposure': 1.0,
            'distinctiveness': 1.0,
            'order_cue_present': cue,
        }

    return [
        {
            'name': 'positive',
            'initial_state': {},
            'contexts': [item(0.9), item(0.2), item(0.2)],
            'expectation': 'increase',
        },
        {
            'name': 'boundary',
            'initial_state': {},
            # With no serial-order cue, the necessary ordinal-position condition
            # is absent and all items retain reference weight.
            'contexts': [item(0.9, False), item(0.2, False), item(0.2, False)],
            'expectation': 'equal',
        },
    ]
