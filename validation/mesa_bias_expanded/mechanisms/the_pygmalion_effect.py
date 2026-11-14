"""Illustrative expectation -> treatment -> performance process model.

This is a hypothetical task mechanism, not a detector or a fitted psychological
model. Strength controls the expectation-linked change in support allocation.
"""
from __future__ import annotations

import math


METADATA = {
    'id': 'the_pygmalion_effect',
    'name': 'The Pygmalion effect',
    'kind': 'motivational_mechanism',
    'description': (
        'An evaluator expectation above a stated neutral reference increases '
        'available support; support efficacy can then raise task performance.'
    ),
    'required_inputs': [
        'evaluator_expectation', 'neutral_expectation', 'support_opportunity',
        'baseline_support', 'baseline_score', 'support_effect', 'score_ceiling',
    ],
    'state_fields': ['last_expectation', 'last_treatment', 'last_performance_score', 'last_reference_score'],
    'metric_name': 'task_performance_score',
    'metric_units': 'illustrative task-score points (0–100 scale)',
    'assumptions': [
        'Expectations and the neutral reference are explicit hypothetical inputs, not inferred motives.',
        'Expectation-linked support is proportional to positive expectation excess and available opportunity.',
        'The stated support_effect is a hypothetical task-specific efficacy in score points per full support unit.',
        'Strength is an uncalibrated intervention setting; zero means fixed baseline support.',
    ],
    'limitations': [
        'Does not model real people, institutions, feedback loops, or empirical effect sizes.',
        'Support and score inputs are simplified; other causes of performance are omitted.',
        'An observed expectation-performance association alone is not evidence of this causal pathway.',
        'The effect is not inherently a cognitive error and may represent beneficial treatment.',
    ],
    'empirically_validated': False,
    'synthetic_only': True,
}


def _number(context: dict, key: str) -> float:
    value = context[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'{key} must be a finite number')
    return float(value)


def evaluate(context: dict, strength: float) -> dict:
    """Compute one task score from the explicit expectation/support pathway."""
    if isinstance(strength, bool) or not isinstance(strength, (int, float)) or not math.isfinite(strength) or not 0 <= strength <= 1:
        raise ValueError('strength must be finite and in [0, 1]')
    missing = [key for key in METADATA['required_inputs'] if key not in context]
    if missing:
        raise ValueError('missing required task input(s): ' + ', '.join(missing))

    expectation = _number(context, 'evaluator_expectation')
    neutral = _number(context, 'neutral_expectation')
    opportunity = _number(context, 'support_opportunity')
    baseline_support = _number(context, 'baseline_support')
    baseline_score = _number(context, 'baseline_score')
    support_effect = _number(context, 'support_effect')
    ceiling = _number(context, 'score_ceiling')
    for key, value in (('evaluator_expectation', expectation), ('neutral_expectation', neutral),
                       ('support_opportunity', opportunity), ('baseline_support', baseline_support)):
        if not 0 <= value <= 1:
            raise ValueError(f'{key} must be in [0, 1]')
    if not 0 <= baseline_score <= ceiling <= 100:
        raise ValueError('scores must satisfy 0 <= baseline_score <= score_ceiling <= 100')
    if support_effect < 0:
        raise ValueError('support_effect must be nonnegative')

    state = context.get('state', {})
    if not isinstance(state, dict):
        raise ValueError('state must be an object')

    # A high expectation affects treatment only through an available opportunity.
    excess_expectation = max(expectation - neutral, 0.0)
    allocated_support = min(1.0, baseline_support + float(strength) * opportunity * excess_expectation)
    reference_score = min(ceiling, baseline_score + baseline_support * support_effect)
    performance = min(ceiling, baseline_score + allocated_support * support_effect)
    gain = performance - reference_score
    active = allocated_support > baseline_support and gain > 0.0

    next_state = dict(state)
    next_state.update({
        'last_expectation': expectation,
        'last_treatment': allocated_support,
        'last_performance_score': performance,
        'last_reference_score': reference_score,
    })
    trace = [
        'Treatment = min(1, baseline_support + strength * support_opportunity * max(evaluator_expectation - neutral_expectation, 0)).',
        f'Inputs yielded support {allocated_support:.6g} (fixed-support reference {baseline_support:.6g}); '
        f'score {performance:.6g} versus reference {reference_score:.6g} points, with ceiling {ceiling:.6g}.',
    ]
    return {'metric': performance, 'active': active, 'state': next_state, 'trace': trace}


def scenarios() -> list[dict]:
    shared = {
        'evaluator_expectation': 0.9,
        'neutral_expectation': 0.5,
        'baseline_support': 0.1,
        'baseline_score': 50.0,
        'support_effect': 20.0,
        'score_ceiling': 100.0,
    }
    return [
        {
            'name': 'positive',
            'initial_state': {},
            'contexts': [{**shared, 'support_opportunity': 0.5}],
            'expectation': 'increase',
        },
        {
            'name': 'boundary',
            'initial_state': {},
            # No opportunity to deliver expectation-linked treatment: a required causal link is absent.
            'contexts': [{**shared, 'support_opportunity': 0.0}],
            'expectation': 'equal',
        },
    ]
