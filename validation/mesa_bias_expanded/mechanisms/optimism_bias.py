"""Illustrative selective-discount process for a hypothetical project forecast."""
from __future__ import annotations

import math

METADATA = {
    'id': 'optimism_bias',
    'name': 'Optimism Bias',
    'kind': 'cognitive_bias',
    'description': (
        'In a comparable-case success forecast, selectively discounts observed failures '
        'while retaining successes, producing an over-optimistic success estimate.'
    ),
    'required_inputs': ['comparable_successes', 'comparable_failures'],
    'state_fields': ['forecast_probability', 'reference_probability', 'weighted_failures'],
    'metric_name': 'project_success_forecast',
    'metric_units': 'probability from 0 to 1 (illustrative Laplace-smoothed forecast)',
    'assumptions': [
        'Comparable successes and failures are supplied counts and are the available evidence.',
        'The strength parameter linearly reduces the weight assigned to failures; it is not calibrated.',
        'A symmetric Beta(1,1) / Laplace prior defines the explicit strength-zero reference.',
    ],
    'limitations': [
        'This is a hypothetical count-based process, not a detector, diagnosis, population claim, or fitted psychological model.',
        'The counts are assumed comparable and trustworthy; omitted covariates, selection, or genuine changes in conditions are not modeled.',
        'A favorable forecast supported by evidence and ordinary hope are not by themselves bias; only this stipulated selective failure discount is represented.',
        'The intervention strength is uncalibrated and no empirical validity or effect size is claimed.',
    ],
    'empirically_validated': False,
    'synthetic_only': True,
}


def _count(context: dict, key: str) -> int:
    if key not in context:
        raise ValueError(f'missing required task input {key}')
    value = context[key]
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f'{key} must be a nonnegative integer count')
    return value


def evaluate(context: dict, strength: float) -> dict:
    """Return a Laplace-smoothed success forecast with selective failure discount."""
    if isinstance(strength, bool) or not isinstance(strength, (int, float)):
        raise ValueError('strength must be finite and in [0, 1]')
    if not math.isfinite(strength) or not 0 <= strength <= 1:
        raise ValueError('strength must be finite and in [0, 1]')
    successes = _count(context, 'comparable_successes')
    failures = _count(context, 'comparable_failures')
    if successes + failures == 0:
        raise ValueError('at least one comparable outcome is required')

    # Reference: symmetric Laplace estimate. The intervention discounts only
    # observed adverse cases, rather than adding a generic optimism offset.
    reference = (successes + 1) / (successes + failures + 2)
    weighted_failures = (1.0 - float(strength)) * failures
    forecast = (successes + 1) / (successes + weighted_failures + 2)
    active = bool(strength > 0 and failures > 0)
    return {
        'metric': forecast,
        'active': active,
        'state': {
            'forecast_probability': forecast,
            'reference_probability': reference,
            'weighted_failures': weighted_failures,
        },
        'trace': [
            f'Laplace reference=(successes+1)/(successes+failures+2)={reference:.6f}; '
            f'failure weight=1-strength={1.0-float(strength):.6f}; '
            f'forecast=(successes+1)/(successes+weighted_failures+2)={forecast:.6f}.'
        ],
    }


def scenarios() -> list[dict]:
    return [
        {
            'name': 'positive',
            'initial_state': {},
            'contexts': [{'comparable_successes': 6, 'comparable_failures': 4}],
            'expectation': 'increase',
        },
        {
            'name': 'boundary',
            'initial_state': {},
            # No adverse comparable cases exist to discount; equality follows
            # from the formula, not a scenario-specific zero override.
            'contexts': [{'comparable_successes': 8, 'comparable_failures': 0}],
            'expectation': 'equal',
        },
    ]
