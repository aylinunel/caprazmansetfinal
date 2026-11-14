"""Illustrative option-choice model for status quo bias (not a detector)."""
from copy import deepcopy
import math


METADATA = {
    'id': 'status_quo_bias',
    'name': 'Status Quo Bias',
    'kind': 'cognitive_bias',
    'description': (
        'When an incumbent option is genuinely worse after explicit switching costs, '
        'an intervention-scaled continuity premium can make it win selection.'
    ),
    # These scenario keys occur in every phase; all detailed checks are in evaluate.
    'required_inputs': ['options', 'incumbent', 'switching_cost'],
    'state_fields': ['selected_option', 'last_metric', 'decision_count', 'last_status_quo_premium'],
    'metric_name': 'selected_net_task_utility',
    'metric_units': 'illustrative task-utility units after explicit switching cost',
    'assumptions': [
        'Option utilities and switching cost are explicit hypothetical task inputs.',
        'The incumbent premium is 1.5 times strength times the positive adjusted-utility gap.',
        'Strength is an uncalibrated intervention setting, not a measured human effect.',
    ],
    'limitations': [
        'A single synthetic choice task omits learning, uncertainty, option search, and social context.',
        'Continuity can be sensible when switching costs are real; this model does not label that as bias.',
        'The coefficient and all outcomes are illustrative and have no empirical validation claim.',
    ],
    'empirically_validated': False,
    'synthetic_only': True,
}


def _finite_number(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'{name} must be a finite number')
    return float(value)


def evaluate(context: dict, strength: float) -> dict:
    """Select an option, with a premium only for an inferior feasible incumbent."""
    strength = _finite_number(strength, 'strength')
    if not 0.0 <= strength <= 1.0:
        raise ValueError('strength must be in [0, 1]')
    if not isinstance(context, dict):
        raise ValueError('context must be a mapping')
    missing = [key for key in METADATA['required_inputs'] if key not in context]
    if missing:
        raise ValueError(f"missing required task input: {missing[0]}")

    options = context['options']
    if not isinstance(options, dict) or not options:
        raise ValueError('options must be a nonempty mapping of option names to utilities')
    utilities = {}
    for name, value in options.items():
        if not isinstance(name, str) or not name:
            raise ValueError('option names must be nonempty strings')
        utilities[name] = _finite_number(value, f'utility for {name}')
    incumbent = context['incumbent']
    if incumbent is not None and (not isinstance(incumbent, str) or incumbent not in utilities):
        raise ValueError('incumbent must be None or name an available option')
    switching_cost = _finite_number(context['switching_cost'], 'switching_cost')
    if switching_cost < 0:
        raise ValueError('switching_cost must be nonnegative')

    prior = context.get('state', {})
    if not isinstance(prior, dict):
        raise ValueError('state must be a mapping')
    count = prior.get('decision_count', 0)
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        raise ValueError('state.decision_count must be a nonnegative integer')

    # The zero-strength reference already accounts for explicit switching costs.
    net = {
        name: utility - (switching_cost if incumbent is not None and name != incumbent else 0.0)
        for name, utility in utilities.items()
    }
    reference_choice = min(net, key=lambda name: (-net[name], name))
    premium = 0.0
    if incumbent is not None:
        best_challenger = max((value for name, value in net.items() if name != incumbent), default=net[incumbent])
        gap = max(0.0, best_challenger - net[incumbent])
        # The premium is tied to the actual utility gap, not an unconditional offset.
        premium = 1.5 * strength * gap
    biased_scores = dict(net)
    if incumbent is not None:
        biased_scores[incumbent] += premium
    selected = min(biased_scores, key=lambda name: (-biased_scores[name], name))
    metric = net[selected]

    next_state = deepcopy(prior)
    next_state.update({
        'selected_option': selected,
        'last_metric': metric,
        'decision_count': count + 1,
        'last_status_quo_premium': premium,
    })
    changed_choice = selected != reference_choice
    trace = (
        f"Reference scores after explicit switching cost: {net}; reference choice={reference_choice}.",
        f"Incumbent={incumbent!r}; utility-gap-based status-quo premium={premium:g}; selected={selected}; metric=net utility {metric:g}.",
    )
    return {
        'metric': metric,
        'active': changed_choice,
        'state': next_state,
        'trace': list(trace),
    }


def scenarios() -> list[dict]:
    return [
        {
            'name': 'positive',
            'initial_state': {},
            'contexts': [{
                'options': {'incumbent': 1.0, 'alternative': 1.4},
                'incumbent': 'incumbent',
                'switching_cost': 0.05,
            }],
            'expectation': 'decrease',
        },
        {
            'name': 'boundary',
            'initial_state': {},
            'contexts': [{
                'options': {'incumbent': 1.0, 'alternative': 1.4},
                'incumbent': 'incumbent',
                # Actual switching costs erase the alternative's net advantage.
                'switching_cost': 0.5,
            }],
            'expectation': 'equal',
        },
    ]
