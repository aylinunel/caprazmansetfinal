"""Illustrative chronological model of forward/backward telescoping."""
from __future__ import annotations

import math


METADATA = {
    'id': 'telescoping_effect',
    'name': 'Telescoping Effect',
    'kind': 'cognitive_bias',
    'description': (
        'For dated recalled events, old events may be placed closer to the present '
        'and recent events farther away; this is a hypothetical process, not a detector.'
    ),
    'required_inputs': ['event_id', 'event_day', 'current_day'],
    'state_fields': ['history', 'latest_day'],
    'metric_name': 'absolute recalled-age error',
    'metric_units': 'days of absolute difference between recalled and actual event age',
    'assumptions': [
        'Illustrative operational rule: ages of at least 30 days telescope forward; ages from above 0 to under 30 days telescope backward.',
        'The maximum proportional displacement is 20% of actual age times strength; this coefficient and threshold are user-settable assumptions, not measured effects.',
        'At strength zero, the explicit reference reports the supplied event age exactly.',
    ],
    'limitations': [
        'A compact synthetic rule for already-dated events, not a memory experiment, NLP detector, diagnosis, or population claim.',
        'Real recollections may be accurate, differently distorted, or affected by other processes; the age threshold and proportional rule are not empirically calibrated.',
        'A zero-age event has no elapsed temporal distance for this process to shift.',
    ],
    'empirically_validated': False,
    'synthetic_only': True,
}

_OLD_EVENT_DAYS = 30.0
_MAX_PROPORTIONAL_SHIFT = 0.20


def _finite_day(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError(f'{name} must be a finite, nonnegative day count')
    return float(value)


def _read_state(state):
    if not isinstance(state, dict):
        raise ValueError('state must be an object')
    if not state:
        return [], None
    if set(state) != {'history', 'latest_day'}:
        raise ValueError('state must contain exactly history and latest_day')
    history = state['history']
    latest = _finite_day(state['latest_day'], 'state.latest_day')
    if not isinstance(history, list) or not history:
        raise ValueError('state.history must be a nonempty chronological list')
    prior_day = None
    for item in history:
        if not isinstance(item, dict) or not {'event_id', 'event_day', 'current_day', 'actual_age', 'recalled_age', 'direction'} <= set(item):
            raise ValueError('each history entry must preserve its dated event and report')
        if not isinstance(item['event_id'], str) or not item['event_id']:
            raise ValueError('history event_id must be a nonempty string')
        event_day = _finite_day(item['event_day'], 'history.event_day')
        current_day = _finite_day(item['current_day'], 'history.current_day')
        actual_age = _finite_day(item['actual_age'], 'history.actual_age')
        recalled_age = _finite_day(item['recalled_age'], 'history.recalled_age')
        if event_day > current_day or not math.isclose(current_day - event_day, actual_age, rel_tol=0, abs_tol=1e-9):
            raise ValueError('history dates and actual_age are inconsistent')
        if prior_day is not None and current_day <= prior_day:
            raise ValueError('state history must be strictly chronological')
        if item['direction'] not in ('forward', 'backward', 'none'):
            raise ValueError('history direction is invalid')
        prior_day = current_day
    if not math.isclose(latest, prior_day, rel_tol=0, abs_tol=1e-9):
        raise ValueError('state.latest_day must equal the last history day')
    return history, latest


def evaluate(context: dict, strength: float) -> dict:
    """Report an event's recalled age after an illustrative telescoping shift."""
    if isinstance(strength, bool) or not isinstance(strength, (int, float)) or not math.isfinite(strength) or not 0 <= strength <= 1:
        raise ValueError('strength must be finite and in [0, 1]')
    if not isinstance(context, dict):
        raise ValueError('context must be an object')
    for field in METADATA['required_inputs']:
        if field not in context:
            raise ValueError(f'missing required task input {field}')

    event_id = context['event_id']
    if not isinstance(event_id, str) or not event_id.strip():
        raise ValueError('event_id must be a nonempty string')
    event_day = _finite_day(context['event_day'], 'event_day')
    current_day = _finite_day(context['current_day'], 'current_day')
    if event_day > current_day:
        raise ValueError('event_day cannot be later than current_day')

    history, latest_day = _read_state(context.get('state', {}))
    if latest_day is not None and current_day <= latest_day:
        raise ValueError('current_day must advance strictly beyond prior history')
    for prior in history:
        if prior['event_id'] == event_id and not math.isclose(prior['event_day'], event_day, rel_tol=0, abs_tol=1e-9):
            raise ValueError('a remembered event_id must retain its supplied event_day')

    actual_age = current_day - event_day
    if actual_age >= _OLD_EVENT_DAYS:
        direction = 'forward'
        recalled_age = actual_age * (1.0 - _MAX_PROPORTIONAL_SHIFT * float(strength))
    elif actual_age > 0:
        direction = 'backward'
        recalled_age = actual_age * (1.0 + _MAX_PROPORTIONAL_SHIFT * float(strength))
    else:
        direction = 'none'
        recalled_age = actual_age

    metric = abs(recalled_age - actual_age)
    entry = {
        'event_id': event_id,
        'event_day': event_day,
        'current_day': current_day,
        'actual_age': actual_age,
        'recalled_age': recalled_age,
        'direction': direction,
    }
    next_history = [dict(item) for item in history]
    next_history.append(entry)
    active = bool(strength > 0 and actual_age > 0)
    trace = [
        f"{direction} telescoping at age {actual_age:g} days: recalled_age = actual_age {'× (1 − 0.20 × strength)' if direction == 'forward' else '× (1 + 0.20 × strength)' if direction == 'backward' else '(unchanged; zero elapsed age)'}; strength={float(strength):g}, absolute error={metric:g} days."
    ]
    return {
        'metric': metric,
        'active': active,
        'state': {'history': next_history, 'latest_day': current_day},
        'trace': trace,
    }


def scenarios() -> list[dict]:
    return [
        {
            'name': 'positive',
            'initial_state': {},
            'contexts': [
                {'event_id': 'market-opening', 'event_day': 0, 'current_day': 60},
                {'event_id': 'market-opening', 'event_day': 0, 'current_day': 90},
            ],
            'expectation': 'increase',
        },
        {
            'name': 'boundary',
            'initial_state': {},
            'contexts': [
                {'event_id': 'today-a', 'event_day': 60, 'current_day': 60},
                {'event_id': 'today-b', 'event_day': 90, 'current_day': 90},
            ],
            'expectation': 'equal',
        },
    ]
