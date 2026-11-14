"""Illustrative intertemporal-choice process; not a detector or fitted model."""
import math


METADATA = {
    'id': 'hyperbolic_discounting',
    'name': 'Hyperbolic Discounting',
    'kind': 'cognitive_bias',
    'description': (
        'Chooses between smaller-sooner and larger-later rewards using a '
        'strength-weighted interpolation of exponential and hyperbolic values; '
        'retains choices across chronological choice trials.'
    ),
    'required_inputs': [
        'smaller_sooner_amount', 'smaller_sooner_delay',
        'larger_later_amount', 'larger_later_delay',
    ],
    'state_fields': ['choices', 'larger_later_choices', 'choice_reversals', 'trials'],
    'metric_name': 'cumulative_larger_later_choices',
    'metric_units': 'count of larger-later selections across the current and prior trials',
    'assumptions': [
        'Rewards are positive scalar amounts and delays are nonnegative days.',
        'The strength-zero reference discounts exponentially at an illustrative rate of 0.15 per day.',
        'The intervention interpolates exponential and simple-hyperbolic discount factors; its hyperbolic rate is 0.20 times strength.',
        'Ties are resolved in favor of the smaller-sooner option; choices are hypothetical task outputs.',
    ],
    'limitations': [
        'Coefficients and interpolation are illustrative and are not estimated or calibrated human parameters.',
        'A choice reversal is compatible with decreasing impatience but does not establish an exact hyperbolic law and overlaps with present-bias accounts.',
        'The model does not infer preferences, motives, financial competence, or real-world behavior from language or people.',
    ],
    'empirically_validated': False,
    'synthetic_only': True,
}

_EXPONENTIAL_RATE = 0.15
_HYPERBOLIC_RATE = 0.20
_STATE_KEYS = ('choices', 'larger_later_choices', 'choice_reversals', 'trials')


def _finite_number(value, name, *, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'{name} must be a finite number')
    if positive and value <= 0:
        raise ValueError(f'{name} must be positive')
    if not positive and value < 0:
        raise ValueError(f'{name} must be nonnegative')
    return float(value)


def _choice(context, strength, family):
    ss_amount = _finite_number(context['smaller_sooner_amount'], 'smaller_sooner_amount', positive=True)
    ss_delay = _finite_number(context['smaller_sooner_delay'], 'smaller_sooner_delay')
    ll_amount = _finite_number(context['larger_later_amount'], 'larger_later_amount', positive=True)
    ll_delay = _finite_number(context['larger_later_delay'], 'larger_later_delay')
    if ll_amount <= ss_amount:
        raise ValueError('larger_later_amount must exceed smaller_sooner_amount')
    if ll_delay < ss_delay:
        raise ValueError('larger_later_delay must not precede smaller_sooner_delay')

    # The same exponential reference applies at strength zero. Increasing strength
    # interpolates its discounted reward values toward a genuine hyperbolic rule.
    k = _HYPERBOLIC_RATE * strength
    if family == 'intervention':
        def value(amount, delay):
            exponential = amount * math.exp(-_EXPONENTIAL_RATE * delay)
            hyperbolic = amount / (1.0 + k * delay)
            return (1.0 - strength) * exponential + strength * hyperbolic
    else:
        def value(amount, delay):
            return amount * math.exp(-_EXPONENTIAL_RATE * delay)

    ss_value = value(ss_amount, ss_delay)
    ll_value = value(ll_amount, ll_delay)
    # A tie has an explicit deterministic smaller-sooner reference choice.
    return ('larger_later' if ll_value > ss_value else 'smaller_sooner', ss_value, ll_value)


def evaluate(context: dict, strength: float) -> dict:
    if isinstance(strength, bool) or not isinstance(strength, (int, float)) or not math.isfinite(strength) or not 0 <= strength <= 1:
        raise ValueError('strength must be finite and in [0, 1]')
    for key in METADATA['required_inputs']:
        if key not in context:
            raise ValueError(f'missing required task input {key}')

    state_in = context.get('state', {})
    if not isinstance(state_in, dict):
        raise ValueError('state must be an object')
    choices = state_in.get('choices', [])
    if (not isinstance(choices, list) or
            any(choice not in ('smaller_sooner', 'larger_later') for choice in choices)):
        raise ValueError('state.choices must be a list of valid prior choices')
    prior_count = state_in.get('larger_later_choices', sum(c == 'larger_later' for c in choices))
    prior_reversals = state_in.get('choice_reversals', sum(a != b for a, b in zip(choices, choices[1:])))
    prior_trials = state_in.get('trials', len(choices))
    for name, value in (('larger_later_choices', prior_count), ('choice_reversals', prior_reversals), ('trials', prior_trials)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f'state.{name} must be a nonnegative integer')
    if prior_count != sum(c == 'larger_later' for c in choices) or prior_trials != len(choices) or prior_reversals != sum(a != b for a, b in zip(choices, choices[1:])):
        raise ValueError('state counters must agree with retained choices')

    selected, ss_value, ll_value = _choice(context, float(strength), 'intervention')
    baseline, _, _ = _choice(context, float(strength), 'reference')
    new_choices = choices + [selected]
    count = prior_count + (selected == 'larger_later')
    reversals = prior_reversals + bool(choices and choices[-1] != selected)
    next_state = {
        'choices': new_choices,
        'larger_later_choices': count,
        'choice_reversals': reversals,
        'trials': prior_trials + 1,
    }
    return {
        'metric': count,
        'active': selected != baseline,
        'state': next_state,
        'trace': [
            f'Intervention values: smaller-sooner={ss_value:.8g}, larger-later={ll_value:.8g}; selected {selected}.',
            f'Strength-zero exponential reference selected {baseline}; cumulative larger-later choices={count}, reversals={reversals}.',
        ],
    }


def scenarios() -> list[dict]:
    def trial(ss_delay, ll_delay):
        return {
            'smaller_sooner_amount': 18.0,
            'smaller_sooner_delay': ss_delay,
            'larger_later_amount': 20.0,
            'larger_later_delay': ll_delay,
        }

    return [
        {
            'name': 'positive',
            'initial_state': {'choices': [], 'larger_later_choices': 0, 'choice_reversals': 0, 'trials': 0},
            # Two ordered trials at different horizons; the pair's ordering reverses
            # under the hyperbolic valuation, and state retains that choice history.
            'contexts': [trial(30.0, 31.0), trial(0.0, 1.0)],
            'expectation': 'increase',
        },
        {
            'name': 'boundary',
            'initial_state': {'choices': [], 'larger_later_choices': 0, 'choice_reversals': 0, 'trials': 0},
            # Equal delays remove the intertemporal tradeoff; both discount rules
            # then rank the larger amount higher, so no concept-specific change occurs.
            'contexts': [trial(10.0, 10.0), trial(20.0, 20.0)],
            'expectation': 'equal',
        },
    ]
