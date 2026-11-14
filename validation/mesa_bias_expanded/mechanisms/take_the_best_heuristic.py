"""Illustrative take-the-best choice process; not a detector or fitted model."""
from __future__ import annotations

import math

METADATA = {
    'id': 'take_the_best_heuristic',
    'name': 'Take-the-best Heuristic',
    'kind': 'heuristic',
    'description': ('When enabled, inspect cues in the supplied priority order and select '
                    'the highest-rated option on the first cue whose rating range reaches '
                    'the minimum difference; otherwise use an equal-weight cue-aggregation reference.'),
    'required_inputs': ['options', 'cue_order', 'cue_values', 'minimum_difference', 'task_scores'],
    'state_fields': ['choice_history', 'last_choice', 'last_policy', 'selected_cue'],
    'metric_name': 'selected_option_task_score',
    'metric_units': 'Illustrative task-score points for the chosen option (arbitrary supplied scale)',
    'assumptions': [
        'Cue ratings, cue priority, discrimination threshold, and task scores are explicit synthetic task facts.',
        'At strength zero, the reference selects the option with the largest sum of ratings across all cues; ties use option order.',
        'At positive strength, the supplied uniform draw chooses whether to use take-the-best with probability equal to strength.',
        'Strength is an uncalibrated intervention setting, not a population prevalence or confidence estimate.',
    ],
    'limitations': [
        'This is a hypothetical policy comparison, not a model of all human decision-making or a classifier.',
        'The task score is stipulated input, and the highest-priority cue is not assumed generally valid or beneficial.',
        'Only supplied structured ratings are used; no hidden motives, cue meanings, or real-world outcomes are inferred.',
        'No empirical validity or effect size is claimed; coefficients and scenarios are illustrative.',
    ],
    'empirically_validated': False,
    'synthetic_only': True,
}


def _finite_number(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'{name} must be a finite number')
    return float(value)


def evaluate(context: dict, strength: float) -> dict:
    """Compare first-discriminating-cue choice with an explicit aggregate reference."""
    if isinstance(strength, bool) or not isinstance(strength, (int, float)) or not math.isfinite(strength) or not 0 <= strength <= 1:
        raise ValueError('strength must be finite and in [0, 1]')
    if not isinstance(context, dict):
        raise ValueError('context must be an object')
    for key in METADATA['required_inputs']:
        if key not in context:
            raise ValueError(f'missing required task input {key}')

    options = context['options']
    order = context['cue_order']
    values = context['cue_values']
    if (not isinstance(options, list) or len(options) < 2 or
            not all(isinstance(x, str) and x for x in options) or len(set(options)) != len(options)):
        raise ValueError('options must be a list of at least two unique nonempty strings')
    if not isinstance(order, list) or not order or not all(isinstance(x, str) for x in order) or len(set(order)) != len(order):
        raise ValueError('cue_order must be a nonempty list of unique cue names')
    if not isinstance(values, dict) or set(values) != set(order):
        raise ValueError('cue_values must define exactly the cues in cue_order')
    ratings = {}
    for cue in order:
        row = values[cue]
        if not isinstance(row, dict) or set(row) != set(options):
            raise ValueError(f'cue {cue!r} must provide a rating for every option and no others')
        ratings[cue] = {option: _finite_number(row[option], f'cue_values[{cue!r}][{option!r}]') for option in options}
    threshold = _finite_number(context['minimum_difference'], 'minimum_difference')
    if threshold <= 0:
        raise ValueError('minimum_difference must be greater than zero')
    scores = context['task_scores']
    if not isinstance(scores, dict) or set(scores) != set(options):
        raise ValueError('task_scores must provide a score for every option and no others')
    scores = {option: _finite_number(scores[option], f'task_scores[{option!r}]') for option in options}

    # Explicit reference: aggregate every cue rating equally, with stable option-order ties.
    aggregate = {option: sum(ratings[cue][option] for cue in order) for option in options}
    reference_choice = max(options, key=lambda option: aggregate[option])

    # TTB condition: first priority cue with a max-minus-min range meeting threshold.
    discriminating_cue = None
    heuristic_choice = None
    for cue in order:
        row = ratings[cue]
        if max(row.values()) - min(row.values()) >= threshold:
            discriminating_cue = cue
            heuristic_choice = max(options, key=lambda option: row[option])
            break

    use_heuristic = False
    if discriminating_cue is not None and float(strength) > 0:
        uniform = context.get('uniform')
        if isinstance(uniform, bool) or not isinstance(uniform, (int, float)) or not math.isfinite(uniform) or not 0 <= uniform < 1:
            raise ValueError('positive-strength evaluation requires runner uniform in [0, 1)')
        use_heuristic = uniform < float(strength)

    choice = heuristic_choice if use_heuristic else reference_choice
    policy = 'take_the_best' if use_heuristic else 'aggregate_reference'
    prior_state = context.get('state', {})
    if not isinstance(prior_state, dict):
        raise ValueError('state must be an object when supplied')
    old_history = prior_state.get('choice_history', [])
    if not isinstance(old_history, list) or not all(isinstance(x, str) for x in old_history):
        raise ValueError('state.choice_history must be a list of option names')
    next_state = {
        'choice_history': old_history + [choice],
        'last_choice': choice,
        'last_policy': policy,
        'selected_cue': discriminating_cue if use_heuristic else None,
    }
    activated = use_heuristic and choice != reference_choice
    trace = [
        f'Aggregate-reference sums={aggregate}; reference choice={reference_choice!r}.',
        (f'First discriminating cue={discriminating_cue!r}; its ratings={ratings[discriminating_cue]}; '
         f'TTB choice={heuristic_choice!r}.' if discriminating_cue is not None else
         f'No cue range met minimum_difference={threshold:g}; the necessary TTB condition was absent.'),
        f'uniform={context.get("uniform", "not needed")}; strength={float(strength):g}; policy={policy}; choice={choice!r}; task score={scores[choice]:g}.',
    ]
    return {'metric': scores[choice], 'active': activated, 'state': next_state, 'trace': trace}


def scenarios() -> list[dict]:
    common = {
        'options': ['A', 'B'],
        'cue_order': ['priority_cue', 'secondary_cue'],
        'minimum_difference': 1.0,
    }
    return [
        {
            'name': 'positive',
            'initial_state': {'choice_history': [], 'last_choice': None, 'last_policy': None, 'selected_cue': None},
            'contexts': [{
                **common,
                'cue_values': {
                    'priority_cue': {'A': 1.0, 'B': 0.0},
                    'secondary_cue': {'A': 0.0, 'B': 3.0},
                },
                'task_scores': {'A': 9.0, 'B': 4.0},
            }],
            'expectation': 'increase',
        },
        {
            'name': 'boundary',
            'initial_state': {'choice_history': [], 'last_choice': None, 'last_policy': None, 'selected_cue': None},
            'contexts': [{
                **common,
                # Removing all cue differentiation removes the necessary TTB condition.
                'cue_values': {
                    'priority_cue': {'A': 0.0, 'B': 0.0},
                    'secondary_cue': {'A': 0.0, 'B': 0.0},
                },
                'task_scores': {'A': 5.0, 'B': 2.0},
            }],
            'expectation': 'equal',
        },
    ]
