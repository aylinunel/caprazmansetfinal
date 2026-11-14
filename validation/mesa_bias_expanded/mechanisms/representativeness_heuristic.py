"""Illustrative prototype-substitution process for a structured categorization task."""
from __future__ import annotations

from copy import deepcopy
import math


METADATA = {
    'id': 'representativeness_heuristic',
    'name': 'Representativeness Heuristic',
    'kind': 'cognitive_bias',
    'description': (
        'In a supplied two-or-more-option categorization task, blend the prior- and '
        'likelihood-based posterior ranking with explicit prototype-similarity scores.'
    ),
    'required_inputs': ['options', 'true_option'],
    'state_fields': ['last_choice', 'last_error'],
    'metric_name': 'selected_option_error',
    'metric_units': '0/1 task error indicator (not a diagnostic or population measure)',
    'assumptions': [
        'Each option supplies a prior frequency, evidence likelihood, and structured prototype similarity on [0, 1].',
        'Strength linearly controls substitution of normalized similarity for normalized posterior score; it is not calibrated.',
        'The supplied true_option is an oracle for this hypothetical task, not an inferred hidden state.',
        'Ties are resolved by the input option order.',
    ],
    'limitations': [
        'A deliberately narrow synthetic choice process, not a detector, diagnosis, or claim about people.',
        'Prototype similarity can be useful or task-relevant; this example only illustrates a case where it conflicts with supplied evidence.',
        'The model does not estimate whether priors, likelihoods, or prototypes are accurate in real settings.',
        'Representativeness and base-rate neglect are distinct labels; an observed choice alone does not establish either.',
    ],
    'empirically_validated': False,
    'synthetic_only': True,
}


def _unit_interval(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'{label} must be a finite number in [0, 1]')
    if not 0 <= value <= 1:
        raise ValueError(f'{label} must be in [0, 1]')
    return float(value)


def _validated_inputs(context):
    if not isinstance(context, dict):
        raise ValueError('context must be an object')
    for key in METADATA['required_inputs']:
        if key not in context:
            raise ValueError(f'missing required task input {key}')
    options = context['options']
    if not isinstance(options, list) or len(options) < 2:
        raise ValueError('options must contain at least two option objects')
    labels = []
    clean = []
    for index, option in enumerate(options):
        if not isinstance(option, dict):
            raise ValueError(f'options[{index}] must be an object')
        label = option.get('label')
        if not isinstance(label, str) or not label.strip():
            raise ValueError(f'options[{index}].label must be a nonempty string')
        if label in labels:
            raise ValueError('option labels must be unique')
        labels.append(label)
        clean.append({
            'label': label,
            'prior': _unit_interval(option.get('prior'), f'options[{index}].prior'),
            'likelihood': _unit_interval(option.get('likelihood'), f'options[{index}].likelihood'),
            'prototype_similarity': _unit_interval(
                option.get('prototype_similarity'), f'options[{index}].prototype_similarity'
            ),
        })
    if not isinstance(context['true_option'], str) or context['true_option'] not in labels:
        raise ValueError('true_option must match one supplied option label')
    raw = [o['prior'] * o['likelihood'] for o in clean]
    total = sum(raw)
    if not math.isfinite(total) or total <= 0:
        raise ValueError('prior × likelihood must have positive total evidence')
    posterior = [value / total for value in raw]
    similarity_total = sum(o['prototype_similarity'] for o in clean)
    if similarity_total <= 0:
        raise ValueError('prototype similarities must have positive total')
    similarity = [o['prototype_similarity'] / similarity_total for o in clean]
    state = context.get('state', {})
    if not isinstance(state, dict):
        raise ValueError('state must be an object when supplied')
    return clean, posterior, similarity, deepcopy(state)


def evaluate(context: dict, strength: float) -> dict:
    """Select by a blend of normalized posterior evidence and prototype similarity."""
    if isinstance(strength, bool) or not isinstance(strength, (int, float)) or not math.isfinite(strength) or not 0 <= strength <= 1:
        raise ValueError('strength must be finite and in [0, 1]')
    strength = float(strength)
    options, posterior, similarity, next_state = _validated_inputs(context)
    scores = [
        (1.0 - strength) * p + strength * s
        for p, s in zip(posterior, similarity)
    ]
    # max() preserves the first input option in case of a tie.
    chosen_index = max(range(len(options)), key=lambda index: scores[index])
    choice = options[chosen_index]['label']
    error = float(choice != context['true_option'])
    # A differential prototype cue is necessary to alter the option ranking.
    active = strength > 0 and max(similarity) - min(similarity) > 1e-12
    next_state['last_choice'] = choice
    next_state['last_error'] = error
    trace = (
        f"Scores=(1-{strength:g})*normalized(prior*likelihood)+"
        f"{strength:g}*normalized(prototype_similarity); "
        f"posterior={posterior!r}, similarity={similarity!r}, scores={scores!r}.",
        f"Selected {choice!r}; supplied true_option={context['true_option']!r}; task error={error:g}.",
    )
    return {'metric': error, 'active': active, 'state': next_state, 'trace': list(trace)}


def scenarios() -> list[dict]:
    return [
        {
            'name': 'positive',
            'initial_state': {},
            'contexts': [{
                'options': [
                    {'label': 'A', 'prior': 0.80, 'likelihood': 0.75, 'prototype_similarity': 0.10},
                    {'label': 'B', 'prior': 0.20, 'likelihood': 0.50, 'prototype_similarity': 0.90},
                ],
                'true_option': 'A',
            }],
            'expectation': 'increase',
        },
        {
            'name': 'boundary',
            'initial_state': {},
            'contexts': [{
                'options': [
                    {'label': 'A', 'prior': 0.80, 'likelihood': 0.75, 'prototype_similarity': 0.50},
                    {'label': 'B', 'prior': 0.20, 'likelihood': 0.50, 'prototype_similarity': 0.50},
                ],
                'true_option': 'A',
            }],
            'expectation': 'equal',
        },
    ]
