"""Illustrative response distortion under an explicitly evaluative survey audience."""
from __future__ import annotations

from copy import deepcopy
import math


METADATA = {
    'id': 'response_bias',
    'name': 'Response Bias',
    'kind': 'cognitive_bias',
    'description': (
        'On a sensitive item answered in an evaluative, non-private setting, '
        'the selected response trades off task utility against explicit social approval.'
    ),
    'required_inputs': ['options', 'sensitive_item', 'evaluative_audience', 'private_mode'],
    'state_fields': ['cumulative_regret', 'eligible_items', 'responses'],
    'metric_name': 'mean response utility regret',
    'metric_units': 'utility points per eligible item (illustrative option utilities in [0, 1])',
    'assumptions': [
        'Each option has an explicitly supplied task utility and social-approval score in [0, 1].',
        'At strength zero, the reference respondent selects the option with greatest task utility.',
        'An evaluative audience shifts choice scores toward options with higher supplied approval scores only for sensitive, non-private items.',
        'The strength coefficient is an uncalibrated intervention setting, not a prevalence or effect-size estimate.',
    ],
    'limitations': [
        'This is a hypothetical choice process, not a detector, diagnosis, or claim about actual respondents.',
        'It models one audience-induced social-approval pathway, not all response styles or questioning effects.',
        'Utilities, approval scores, sensitivity, and audience conditions are supplied inputs, not inferred facts.',
        'A single unusual answer or a deliberate privacy choice is not evidence of a general response tendency; sampling bias is outside scope.',
    ],
    'empirically_validated': False,
    'synthetic_only': True,
}


def _finite_unit(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'{label} must be a finite number in [0, 1]')
    if not 0 <= value <= 1:
        raise ValueError(f'{label} must be a finite number in [0, 1]')
    return float(value)


def _validate_context(context):
    if not isinstance(context, dict):
        raise ValueError('context must be an object')
    for key in METADATA['required_inputs']:
        if key not in context:
            raise ValueError(f'missing required task input {key}')
    for key in ('sensitive_item', 'evaluative_audience', 'private_mode'):
        if not isinstance(context[key], bool):
            raise ValueError(f'{key} must be an explicit boolean')
    options = context['options']
    if not isinstance(options, list) or len(options) < 2:
        raise ValueError('options must contain at least two explicit response options')
    seen = set()
    validated = []
    for option in options:
        if not isinstance(option, dict) or not isinstance(option.get('id'), str) or not option['id']:
            raise ValueError('each option needs a nonempty string id')
        if option['id'] in seen:
            raise ValueError('option ids must be unique within an item')
        seen.add(option['id'])
        if 'task_utility' not in option or 'social_approval' not in option:
            raise ValueError('each option needs task_utility and social_approval')
        validated.append((option['id'], _finite_unit(option['task_utility'], 'task_utility'),
                          _finite_unit(option['social_approval'], 'social_approval')))
    return validated


def _prior_state(raw):
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ValueError('state must be an object')
    regret = raw.get('cumulative_regret', 0.0)
    count = raw.get('eligible_items', 0)
    responses = raw.get('responses', [])
    if isinstance(regret, bool) or not isinstance(regret, (int, float)) or not math.isfinite(regret) or regret < 0:
        raise ValueError('state.cumulative_regret must be finite and nonnegative')
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        raise ValueError('state.eligible_items must be a nonnegative integer')
    if not isinstance(responses, list) or not all(isinstance(item, str) for item in responses):
        raise ValueError('state.responses must be a list of strings')
    return deepcopy(raw), float(regret), count


def evaluate(context: dict, strength: float) -> dict:
    """Select a response and report cumulative mean regret on eligible items."""
    if isinstance(strength, bool) or not isinstance(strength, (int, float)) or not math.isfinite(strength) or not 0 <= strength <= 1:
        raise ValueError('strength must be finite and in [0, 1]')
    options = _validate_context(context)
    state, cumulative_regret, eligible_items = _prior_state(context.get('state', {}))

    # Stable first-option tie breaking makes the reference fully reproducible.
    baseline = max(enumerate(options), key=lambda pair: (pair[1][1], -pair[0]))[1]
    eligible = context['sensitive_item'] and context['evaluative_audience'] and not context['private_mode']
    selected = baseline
    if eligible:
        # The actual response selection process: maximize task utility plus an
        # intervention-weighted evaluative-audience approval term.
        selected = max(
            enumerate(options),
            key=lambda pair: (pair[1][1] + float(strength) * pair[1][2], -pair[0]),
        )[1]
        cumulative_regret += max(0.0, baseline[1] - selected[1])
        eligible_items += 1

    state['cumulative_regret'] = cumulative_regret
    state['eligible_items'] = eligible_items
    state['responses'] = list(state.get('responses', [])) + [selected[0]]
    metric = cumulative_regret / eligible_items if eligible_items else 0.0
    changed = eligible and selected[0] != baseline[0]
    return {
        'metric': float(metric),
        'active': bool(changed),
        'state': state,
        'trace': [
            f"eligible={eligible}; baseline={baseline[0]} (task utility {baseline[1]:.3f}); "
            f"selected={selected[0]} using task_utility + strength({float(strength):.3f})*social_approval; "
            f"cumulative mean regret={metric:.3f} over {eligible_items} eligible item(s)."
        ],
    }


def scenarios() -> list[dict]:
    options_a = [
        {'id': 'accurate_low_approval', 'task_utility': 0.75, 'social_approval': 0.10},
        {'id': 'approved_less_accurate', 'task_utility': 0.40, 'social_approval': 0.90},
    ]
    options_b = [
        {'id': 'direct_answer', 'task_utility': 0.80, 'social_approval': 0.15},
        {'id': 'audience_favored_answer', 'task_utility': 0.45, 'social_approval': 0.95},
    ]
    return [
        {
            'name': 'positive',
            'initial_state': {'cumulative_regret': 0.0, 'eligible_items': 0, 'responses': []},
            'contexts': [
                {'options': options_a, 'sensitive_item': True, 'evaluative_audience': True, 'private_mode': False},
                {'options': options_b, 'sensitive_item': True, 'evaluative_audience': True, 'private_mode': False},
            ],
            'expectation': 'increase',
        },
        {
            'name': 'boundary',
            'initial_state': {'cumulative_regret': 0.0, 'eligible_items': 0, 'responses': []},
            # The necessary evaluative-audience condition is removed; the item
            # remains sensitive and the response is not private by stipulation.
            'contexts': [
                {'options': options_a, 'sensitive_item': True, 'evaluative_audience': False, 'private_mode': False},
                {'options': options_b, 'sensitive_item': True, 'evaluative_audience': False, 'private_mode': False},
            ],
            'expectation': 'equal',
        },
    ]
