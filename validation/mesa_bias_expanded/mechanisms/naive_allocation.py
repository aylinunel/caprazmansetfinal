"""Illustrative equal-share allocation despite supplied utility differences."""
from __future__ import annotations

import math


METADATA = {
    'id': 'naive_allocation',
    'name': 'Naive Allocation',
    'kind': 'cognitive_bias',
    'description': (
        'Intervenes on a utility-proportional reference by mixing in equal shares '
        'across listed options, irrespective of their supplied utility differences.'
    ),
    # These fields are present in every phase; nested and reserved data are validated in evaluate.
    'required_inputs': ['budget', 'options'],
    'state_fields': ['last_allocations', 'last_metric', 'steps'],
    'metric_name': 'utility-weighted resource yield',
    'metric_units': 'utility units (sum of each option utility coefficient times allocated resource)',
    'assumptions': [
        'Options have known, nonnegative, commensurable linear utility coefficients.',
        'At strength s, s is the share of an equal-allocation policy mixed into the proportional reference.',
        'The linear allocation model is an illustrative task rule, not a fitted human process.',
    ],
    'limitations': [
        'Does not model uncertainty, interactions, minimum commitments, costs, or real decision-makers.',
        'Equal division may be defensible for fairness, diversification, or unmodeled objectives.',
        'Strength is an uncalibrated intervention setting and results are not empirical evidence.',
    ],
    'empirically_validated': False,
    'synthetic_only': True,
}


def _finite_number(value, label, *, positive=False, nonnegative=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'{label} must be a finite number')
    if positive and value <= 0:
        raise ValueError(f'{label} must be positive')
    if nonnegative and value < 0:
        raise ValueError(f'{label} must be nonnegative')
    return float(value)


def evaluate(context: dict, strength: float) -> dict:
    if not isinstance(context, dict):
        raise ValueError('context must be an object')
    if isinstance(strength, bool) or not isinstance(strength, (int, float)) or not math.isfinite(strength) or not 0 <= strength <= 1:
        raise ValueError('strength must be finite and in [0, 1]')
    if 'budget' not in context or 'options' not in context:
        raise ValueError('budget and options are required')
    budget = _finite_number(context['budget'], 'budget', positive=True)
    options = context['options']
    if not isinstance(options, list) or len(options) < 2:
        raise ValueError('options must be a list of at least two option objects')

    names, utilities = [], []
    for option in options:
        if not isinstance(option, dict) or 'id' not in option or 'utility' not in option:
            raise ValueError('each option must contain id and utility')
        name = option['id']
        if not isinstance(name, str) or not name:
            raise ValueError('option id must be a nonempty string')
        if name in names:
            raise ValueError('option ids must be unique')
        names.append(name)
        utilities.append(_finite_number(option['utility'], f'utility for {name}', nonnegative=True))
    total_utility = sum(utilities)
    if total_utility <= 0 or not math.isfinite(total_utility):
        raise ValueError('at least one option must have positive utility and total utility must be finite')

    # Strength blends the explicit proportional reference with the concept's superficial equal split.
    count = len(options)
    allocations = {
        name: budget * ((1.0 - float(strength)) * utility / total_utility + float(strength) / count)
        for name, utility in zip(names, utilities)
    }
    metric = sum(allocation * utility for allocation, utility in zip(allocations.values(), utilities))
    prior = context.get('state', {})
    if not isinstance(prior, dict):
        raise ValueError('state must be an object')
    steps = prior.get('steps', 0)
    if isinstance(steps, bool) or not isinstance(steps, int) or steps < 0:
        raise ValueError('state.steps must be a nonnegative integer')
    next_state = dict(prior)
    next_state.update({'last_allocations': allocations, 'last_metric': metric, 'steps': steps + 1})
    heterogeneous = max(utilities) - min(utilities) > 0
    changed = any(abs(allocations[n] - budget * u / total_utility) > 1e-12 for n, u in zip(names, utilities))
    active = bool(float(strength) > 0 and heterogeneous and changed)
    trace = [
        f'Allocated budget {budget:g} across {count} listed options using '
        f'a {(1.0-float(strength)):.3g} utility-proportional reference and '
        f'{float(strength):.3g} equal-share component; utilities={utilities!r}.',
        f'Utility-weighted resource yield = {metric:.12g}; active={active}.',
    ]
    return {'metric': metric, 'active': active, 'state': next_state, 'trace': trace}


def scenarios() -> list[dict]:
    return [
        {
            'name': 'positive',
            'initial_state': {'steps': 0},
            'contexts': [{'budget': 100, 'options': [
                {'id': 'high_return', 'utility': 9}, {'id': 'low_return', 'utility': 1},
            ]}],
            'expectation': 'decrease',
        },
        {
            'name': 'boundary',
            'initial_state': {'steps': 0},
            # Removing utility differences removes the necessary condition for this error.
            'contexts': [{'budget': 100, 'options': [
                {'id': 'option_a', 'utility': 4}, {'id': 'option_b', 'utility': 4},
            ]}],
            'expectation': 'equal',
        },
    ]
