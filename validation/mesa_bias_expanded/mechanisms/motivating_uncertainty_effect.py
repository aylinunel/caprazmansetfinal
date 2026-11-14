"""Illustrative effort choice under uncertainty about a pursued reward."""
from __future__ import annotations

import math


METADATA = {
    'id': 'motivating_uncertainty_effect',
    'name': 'Motivating Uncertainty Effect',
    'kind': 'motivational_mechanism',
    'description': (
        'Selects effort to maximize expected reward net of convex effort cost; '
        'uncertain reward size adds a pursuit-focused excitement premium.'
    ),
    'required_inputs': [
        'reward_mean', 'reward_spread', 'effort_cost', 'pursuit_focus', 'effort_cap'
    ],
    'state_fields': ['chosen_effort', 'chosen_utility', 'uncertainty_premium'],
    'metric_name': 'chosen_effort',
    'metric_units': 'discrete effort units per decision (integer from 0 through effort_cap)',
    'assumptions': [
        'Reward mean is held fixed while reward_spread represents uncertainty in payout size.',
        'When the agent is focused on pursuing the reward, uncertainty adds a linear, non-monetary excitement value per effort unit.',
        'Strength scales only that illustrative excitement premium; it is not a calibrated effect size.',
        'The strength-zero policy maximizes expected reward minus quadratic effort cost over the same choices.'
    ],
    'limitations': [
        'A hypothetical utility rule, not a fitted or empirically validated psychology model.',
        'Does not infer motivation, uncertainty, or reward properties from people or text.',
        'Reward spread and focus are explicit task inputs; other responses to uncertainty are out of scope.'
    ],
    'empirically_validated': False,
    'synthetic_only': True,
}

_EXCITEMENT_RATE = 0.5  # illustrative utility units per spread unit and effort unit
_MAX_INPUT = 1_000_000.0


def _number(context: dict, key: str, *, minimum: float, maximum: float = _MAX_INPUT) -> float:
    value = context[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f'{key} must be a finite number')
    value = float(value)
    if not math.isfinite(value) or not minimum <= value <= maximum:
        raise ValueError(f'{key} must be finite and in [{minimum}, {maximum}]')
    return value


def evaluate(context: dict, strength: float) -> dict:
    """Return the utility-maximizing discrete effort choice without mutating context."""
    if not isinstance(context, dict):
        raise ValueError('context must be a dictionary')
    if isinstance(strength, bool) or not isinstance(strength, (int, float)):
        raise ValueError('strength must be finite and in [0, 1]')
    strength = float(strength)
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError('strength must be finite and in [0, 1]')
    missing = [key for key in METADATA['required_inputs'] if key not in context]
    if missing:
        raise ValueError(f'missing required task input(s): {", ".join(missing)}')

    mean = _number(context, 'reward_mean', minimum=0.0)
    spread = _number(context, 'reward_spread', minimum=0.0)
    cost = _number(context, 'effort_cost', minimum=1e-12)
    focus = _number(context, 'pursuit_focus', minimum=0.0, maximum=1.0)
    cap = context['effort_cap']
    if isinstance(cap, bool) or not isinstance(cap, int) or not 1 <= cap <= 100:
        raise ValueError('effort_cap must be an integer in [1, 100]')
    prior = context.get('state', {})
    if not isinstance(prior, dict):
        raise ValueError('state must be a dictionary when supplied')

    # For effort e, U(e) = e*mean - cost*e^2/2
    #                 + strength*0.5*spread*focus*e.
    # The last term is the task-specific pursuit excitement premium. Ties choose
    # the lower effort, making the strength-zero reference conservative.
    premium_per_unit = strength * _EXCITEMENT_RATE * spread * focus
    utilities = [
        effort * mean - cost * effort * effort / 2.0 + premium_per_unit * effort
        for effort in range(cap + 1)
    ]
    chosen = max(range(cap + 1), key=lambda effort: (utilities[effort], -effort))
    state = dict(prior)
    state.update({
        'chosen_effort': chosen,
        'chosen_utility': utilities[chosen],
        'uncertainty_premium': premium_per_unit * chosen,
    })
    return {
        'metric': chosen,
        'active': bool(premium_per_unit > 0.0 and chosen != _baseline_choice(mean, cost, cap)),
        'state': state,
        'trace': [
            f'Chose effort {chosen} from 0..{cap} maximizing '
            'e*reward_mean - effort_cost*e^2/2 '
            f'+ strength*{_EXCITEMENT_RATE}*reward_spread*pursuit_focus*e; '
            f'excitement premium per effort unit={premium_per_unit:.6g}.'
        ],
    }


def _baseline_choice(mean: float, cost: float, cap: int) -> int:
    return max(
        range(cap + 1),
        key=lambda effort: (effort * mean - cost * effort * effort / 2.0, -effort),
    )


def scenarios() -> list[dict]:
    shared = {
        'reward_mean': 0.8,
        'reward_spread': 3.0,
        'effort_cost': 2.0,
        'pursuit_focus': 1.0,
        'effort_cap': 4,
    }
    positive = dict(shared)
    boundary = dict(shared, reward_spread=0.0)  # no reward-size uncertainty
    return [
        {
            'name': 'positive',
            'initial_state': {},
            'contexts': [positive],
            'expectation': 'increase',
        },
        {
            'name': 'boundary',
            'initial_state': {},
            'contexts': [boundary],
            'expectation': 'equal',
        },
    ]
