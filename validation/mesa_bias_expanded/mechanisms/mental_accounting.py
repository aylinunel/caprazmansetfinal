"""Illustrative envelope-segregation choice model; not a detector or fitted theory."""
from __future__ import annotations

import math


METADATA = {
    'id': 'mental_accounting',
    'name': 'Mental Accounting',
    'kind': 'cognitive_bias',
    'description': (
        'When an explicitly separate spending envelope matches a purchase category, '
        'unmatched funds are only partly treated as available, even though dollars '
        'are interchangeable.'
    ),
    'required_inputs': ['task'],
    'state_fields': ['purchase_count', 'last_choice', 'last_effective_funds', 'last_surplus'],
    'metric_name': 'realized_net_surplus',
    'metric_units': 'illustrative utility units per purchase opportunity',
    'assumptions': [
        'The supplied account labels and category match are explicit hypothetical task facts.',
        'A purchase is worthwhile when its supplied benefit is at least its price.',
        'Strength linearly controls how much unmatched money is treated as spendable.',
        'All coefficients and utilities are illustrative; strength is not calibrated.',
    ],
    'limitations': [
        'Does not model real household budgeting, preferences, liquidity, or inferred motives.',
        'Purposeful budgets and liquidity constraints may be beneficial or economically real; '
        'category labels alone do not establish an error.',
        'This synthetic process is not empirically validated and is not a person-level classifier.',
    ],
    'empirically_validated': False,
    'synthetic_only': True,
}

_TASK_FIELDS = {
    'benefit', 'price', 'matched_funds', 'unmatched_funds',
    'accounts_separated', 'category_match',
}


def _finite_nonnegative(task, key):
    value = task[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError(f'task.{key} must be a finite nonnegative number')
    return float(value)


def evaluate(context: dict, strength: float) -> dict:
    """Choose a purchase by comparing its benefit with price and recognized funds."""
    if isinstance(strength, bool) or not isinstance(strength, (int, float)) or not math.isfinite(strength) or not 0 <= strength <= 1:
        raise ValueError('strength must be finite and in [0, 1]')
    if not isinstance(context, dict) or 'task' not in context:
        raise ValueError('missing required task input')
    task = context['task']
    if not isinstance(task, dict) or set(task) != _TASK_FIELDS:
        raise ValueError(f'task must contain exactly {_TASK_FIELDS}')
    benefit = _finite_nonnegative(task, 'benefit')
    price = _finite_nonnegative(task, 'price')
    matched = _finite_nonnegative(task, 'matched_funds')
    unmatched = _finite_nonnegative(task, 'unmatched_funds')
    if price <= 0:
        raise ValueError('task.price must be greater than zero')
    for key in ('accounts_separated', 'category_match'):
        if type(task[key]) is not bool:
            raise ValueError(f'task.{key} must be a bool')

    prior = context.get('state', {})
    if not isinstance(prior, dict):
        raise ValueError('state must be an object')
    count = prior.get('purchase_count', 0)
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        raise ValueError('state.purchase_count must be a nonnegative integer')

    # The category mechanism requires both an explicitly segregated envelope and
    # a matching purchase category. Otherwise the reference's fungible total applies.
    tagged = task['accounts_separated'] and task['category_match']
    total_funds = matched + unmatched
    effective_funds = matched + (1.0 - float(strength)) * unmatched if tagged else total_funds
    worthwhile = benefit >= price
    reference_buys = worthwhile and total_funds >= price
    buys = worthwhile and effective_funds >= price
    surplus = benefit - price if buys else 0.0
    next_state = {
        'purchase_count': count + int(buys),
        'last_choice': 'buy' if buys else 'defer',
        'last_effective_funds': effective_funds,
        'last_surplus': surplus,
    }
    return {
        'metric': surplus,
        'active': bool(buys != reference_buys),
        'state': next_state,
        'trace': [
            f"tagged={tagged}; effective_funds=matched({matched:g}) + "
            f"(1-strength) * unmatched({unmatched:g}) = {effective_funds:g}; "
            f"buy iff benefit({benefit:g}) >= price({price:g}) and "
            f"effective_funds >= price; total_funds={total_funds:g}, "
            f"reference_buys={reference_buys}, choice={'buy' if buys else 'defer'}, "
            f"realized_net_surplus={surplus:g}.",
        ],
    }


def scenarios() -> list[dict]:
    return [
        {
            'name': 'positive',
            'initial_state': {},
            'contexts': [{
                'task': {
                    'benefit': 15, 'price': 10,
                    'matched_funds': 5, 'unmatched_funds': 20,
                    'accounts_separated': True, 'category_match': True,
                },
            }],
            'expectation': 'decrease',
        },
        {
            'name': 'boundary',
            'initial_state': {},
            'contexts': [{
                'task': {
                    'benefit': 15, 'price': 10,
                    'matched_funds': 5, 'unmatched_funds': 20,
                    'accounts_separated': False, 'category_match': True,
                },
            }],
            'expectation': 'equal',
        },
    ]
