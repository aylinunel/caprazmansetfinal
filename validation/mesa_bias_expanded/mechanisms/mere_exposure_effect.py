"""Illustrative repeated-neutral-exposure process; not a detector or fitted model."""
from __future__ import annotations

import math


METADATA = {
    'id': 'mere_exposure_effect',
    'name': 'Mere Exposure Effect',
    'kind': 'learning_effect',
    'description': (
        'Repeated non-substantive exposure raises an option\'s modeled liking by a '
        'saturating familiarity term, which can change a preference choice.'
    ),
    'required_inputs': ['options', 'exposures'],
    'state_fields': ['exposure_counts', 'last_choice'],
    'metric_name': 'selected_option_familiarity_lift',
    'metric_units': 'illustrative utility points above the selected option\'s baseline utility',
    'assumptions': [
        'Options map stable item identifiers to finite baseline liking/utility values.',
        'Each exposure is neutral and supplies no new substantive information.',
        'Only the second and later exposures contribute; their contribution saturates.',
        'The 0.30 scale and 2-exposure saturation constant are illustrative, not estimated.',
        'The metric is the familiarity component of the selected option, not truth belief.',
    ],
    'limitations': [
        'This hypothetical process omits context, affect, attention, and individual differences.',
        'A supplied exposure history is assumed accurate; the plugin does not detect exposure.',
        'The model is not an empirical validity claim, diagnosis, or population prediction.',
        'Strength is an uncalibrated intervention setting, not a human effect-size estimate.',
    ],
    'empirically_validated': False,
    'synthetic_only': True,
}

_LIFT_SCALE = 0.30
_SATURATION_EXPOSURES = 2.0


def _finite_number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'{label} must be a finite number')
    return float(value)


def evaluate(context: dict, strength: float) -> dict:
    """Apply accumulated familiarity to a finite set of options, without mutation."""
    s = _finite_number(strength, 'strength')
    if not 0.0 <= s <= 1.0:
        raise ValueError('strength must be in [0, 1]')
    if not isinstance(context, dict):
        raise ValueError('context must be a dictionary')
    for field in METADATA['required_inputs']:
        if field not in context:
            raise ValueError(f'missing required task input {field}')

    options = context['options']
    if not isinstance(options, dict) or not options:
        raise ValueError('options must be a nonempty mapping of item IDs to baseline utilities')
    base = {}
    for item, utility in options.items():
        if not isinstance(item, str) or not item.strip():
            raise ValueError('option IDs must be nonempty strings')
        base[item] = _finite_number(utility, f'utility for {item!r}')

    exposures = context['exposures']
    if not isinstance(exposures, list):
        raise ValueError('exposures must be a list of item IDs')
    if any(not isinstance(item, str) or item not in base for item in exposures):
        raise ValueError('every exposure must name an option in this phase')

    supplied_state = context.get('state', {})
    if not isinstance(supplied_state, dict):
        raise ValueError('state must be a dictionary')
    old_counts = supplied_state.get('exposure_counts', {})
    if not isinstance(old_counts, dict):
        raise ValueError('state.exposure_counts must be a mapping')
    counts = {}
    for item, count in old_counts.items():
        if not isinstance(item, str) or isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError('stored exposure counts must map item IDs to nonnegative integers')
        counts[item] = count
    for item in exposures:
        counts[item] = counts.get(item, 0) + 1

    # A single encounter is not enough: the familiarity term starts on the second
    # encounter and asymptotically approaches a bounded liking increment.
    lift = {
        item: s * _LIFT_SCALE * (1.0 - math.exp(-max(count - 1, 0) / _SATURATION_EXPOSURES))
        for item, count in counts.items()
    }
    effective = {item: base[item] + lift.get(item, 0.0) for item in base}
    # Stable lexical tie-break: the reference and intervention use the same policy.
    choice = max(sorted(base), key=lambda item: effective[item])
    metric = lift.get(choice, 0.0)
    active = s > 0.0 and any(lift.get(item, 0.0) > 0.0 for item in base)
    next_state = {'exposure_counts': counts, 'last_choice': choice}
    trace = [
        f"Counts after current neutral exposures: {counts}.",
        f"For each option, lift = strength * {_LIFT_SCALE} * "
        f"(1 - exp(-max(count - 1, 0) / {_SATURATION_EXPOSURES})); "
        f"choice maximizes baseline utility + lift. Selected {choice!r} with "
        f"baseline={base[choice]:.6g}, lift={metric:.6g}, metric={metric:.6g}.",
    ]
    return {'metric': metric, 'active': active, 'state': next_state, 'trace': trace}


def scenarios() -> list[dict]:
    options = {'A': 0.50, 'B': 0.62}
    return [
        {
            'name': 'positive',
            'initial_state': {'exposure_counts': {}, 'last_choice': None},
            'contexts': [
                {'options': options, 'exposures': ['A']},
                {'options': options, 'exposures': ['A']},
                {'options': options, 'exposures': ['A']},
            ],
            'expectation': 'increase',
        },
        {
            'name': 'boundary',
            'initial_state': {'exposure_counts': {}, 'last_choice': None},
            # Each option is encountered once; the required repetition condition is absent.
            'contexts': [
                {'options': options, 'exposures': ['A']},
                {'options': options, 'exposures': ['B']},
                {'options': options, 'exposures': []},
            ],
            'expectation': 'equal',
        },
    ]
