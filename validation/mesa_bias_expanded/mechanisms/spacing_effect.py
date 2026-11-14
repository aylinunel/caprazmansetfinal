"""Illustrative spaced-versus-massed study process; not a fitted learner model."""
import copy
import math


# These are explicit illustrative coefficients, not empirical effect estimates.
ENCODING_RATE = 0.7
FORGETTING_RATE = 0.25
STABILITY_GAIN = 0.8
GAP_SCALE_DAYS = 1.0

METADATA = {
    'id': 'spacing_effect',
    'name': 'Spacing Effect',
    'kind': 'learning_effect',
    'description': (
        'For a studied item, each later study on a distinct day adds an '
        'interval-dependent stability term that slows modeled forgetting; '
        'same-day repetitions add no spacing stability.'
    ),
    'required_inputs': ['item_id', 'event', 'elapsed_days'],
    'state_fields': ['items[item_id].study_days', 'items[item_id].spacing_stability', 'last_elapsed_days'],
    'metric_name': 'normalized_retrieval_score',
    'metric_units': 'illustrative unitless score in [0, 1]; not a probability calibrated to people',
    'assumptions': [
        'Each context is one study or retrieval event for the named item, ordered by elapsed_days.',
        'A positive gap between successive studies is the necessary condition for this spacing process.',
        'Strength scales the assumed stability contribution; it is an uncalibrated intervention setting.',
        'The score combines saturating encoding from study count with exponential age-related forgetting.',
    ],
    'limitations': [
        'Coefficients and functional form are hypothetical and are not empirically validated.',
        'The model omits item difficulty, learner differences, retrieval practice, interference, and study quality.',
        'It distinguishes spaced from same-day massed repetitions only; it does not model lag effects among spaced schedules.',
        'It is an illustrative task process, not a detector, diagnosis, or population-level claim.',
    ],
    'empirically_validated': False,
    'synthetic_only': True,
}


def _number(value, name, *, minimum=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'{name} must be a finite number')
    result = float(value)
    if minimum is not None and result < minimum:
        raise ValueError(f'{name} must be >= {minimum}')
    return result


def _validated_state(raw_state):
    if not isinstance(raw_state, dict):
        raise ValueError('state must be an object')
    state = copy.deepcopy(raw_state)
    items = state.setdefault('items', {})
    if not isinstance(items, dict):
        raise ValueError('state.items must be an object')
    if 'last_elapsed_days' in state:
        state['last_elapsed_days'] = _number(state['last_elapsed_days'], 'state.last_elapsed_days', minimum=0)
    for item_id, item in items.items():
        if not isinstance(item_id, str) or not isinstance(item, dict):
            raise ValueError('each item state must be an object keyed by item_id')
        days = item.get('study_days')
        if not isinstance(days, list):
            raise ValueError('item study_days must be a list')
        clean_days = [_number(day, 'study day', minimum=0) for day in days]
        if any(later < earlier for earlier, later in zip(clean_days, clean_days[1:])):
            raise ValueError('study_days must be chronological')
        item['study_days'] = clean_days
        item['spacing_stability'] = _number(item.get('spacing_stability', 0.0), 'spacing_stability', minimum=0)
    return state


def evaluate(context: dict, strength: float) -> dict:
    """Apply the spacing-specific stability transition and compute retention potential."""
    if isinstance(strength, bool) or not isinstance(strength, (int, float)) or not math.isfinite(strength) or not 0 <= strength <= 1:
        raise ValueError('strength must be finite and in [0, 1]')
    if not isinstance(context, dict):
        raise ValueError('context must be an object')
    for key in METADATA['required_inputs']:
        if key not in context:
            raise ValueError(f'missing required task input {key}')

    item_id = context['item_id']
    if not isinstance(item_id, str) or not item_id.strip():
        raise ValueError('item_id must be a nonempty string')
    event = context['event']
    if event not in ('study', 'probe'):
        raise ValueError("event must be 'study' or 'probe'")
    day = _number(context['elapsed_days'], 'elapsed_days', minimum=0)
    state = _validated_state(context.get('state', {}))
    prior_day = state.get('last_elapsed_days')
    if prior_day is not None and day < prior_day:
        raise ValueError('elapsed_days must be chronological across contexts')

    items = state['items']
    item = items.setdefault(item_id, {'study_days': [], 'spacing_stability': 0.0})
    study_days = item['study_days']
    prior_stability = item['spacing_stability']
    stability_added = 0.0
    gap = None

    if event == 'study':
        if study_days:
            gap = day - study_days[-1]
            # A distinct-day repeat contributes according to its interval,
            # saturating rather than growing without bound with longer gaps.
            if gap > 0:
                stability_added = float(strength) * STABILITY_GAIN * gap / (gap + GAP_SCALE_DAYS)
                item['spacing_stability'] = prior_stability + stability_added
        study_days.append(day)
    elif not study_days:
        raise ValueError('a probe requires at least one prior study of the item')

    exposure_count = len(study_days)
    age_days = day - study_days[-1]
    stability = item['spacing_stability']
    encoding = 1.0 - math.exp(-ENCODING_RATE * exposure_count)
    # Strength-zero reference: same exposure/recency policy with no spacing
    # stability. Distributed study changes the forgetting denominator itself.
    metric = encoding * math.exp(-FORGETTING_RATE * age_days / (1.0 + stability))
    state['last_elapsed_days'] = day

    changed_now = stability_added > 0 if event == 'study' else (stability > 0 and age_days > 0)
    trace = [
        f"event={event}, item={item_id!r}, day={day:g}, exposures={exposure_count}, "
        f"previous-study-gap={gap if gap is not None else 'n/a'}, stability={stability:.6f}; "
        f"score=(1-exp(-{ENCODING_RATE}*exposures))*exp(-{FORGETTING_RATE}*age_days/(1+stability))="
        f'{metric:.6f}. Distinct-day repeats add strength*{STABILITY_GAIN}*gap/(gap+{GAP_SCALE_DAYS}); '
        'same-day repeats add zero.'
    ]
    return {'metric': metric, 'active': bool(changed_now), 'state': state, 'trace': trace}


def scenarios() -> list[dict]:
    return [
        {
            'name': 'positive',
            'initial_state': {},
            'contexts': [
                {'item_id': 'A', 'event': 'study', 'elapsed_days': 0},
                {'item_id': 'A', 'event': 'study', 'elapsed_days': 2},
                {'item_id': 'A', 'event': 'study', 'elapsed_days': 5},
                {'item_id': 'A', 'event': 'probe', 'elapsed_days': 9},
            ],
            'expectation': 'increase',
        },
        {
            'name': 'boundary',
            'initial_state': {},
            # Two exposures are retained, but both are on the same day, so
            # the necessary distinct-day spacing condition is absent.
            'contexts': [
                {'item_id': 'A', 'event': 'study', 'elapsed_days': 0},
                {'item_id': 'A', 'event': 'study', 'elapsed_days': 0},
                {'item_id': 'A', 'event': 'probe', 'elapsed_days': 0},
            ],
            'expectation': 'equal',
        },
    ]
