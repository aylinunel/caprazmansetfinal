"""Illustrative serial-order weighting process for a synthetic sequence judgment."""
import math


METADATA = {
    'id': 'recency_effect',
    'name': 'Recency Effect',
    'kind': 'cognitive_bias',
    'description': (
        'For an explicitly ordered stream of A/B observations, progressively '
        'weights older observations less when choosing which option was better '
        'represented in the stream.'
    ),
    # These two task fields occur in every phase; reserved runner fields are excluded.
    'required_inputs': ['observation', 'sequence_ordered'],
    'state_fields': ['history', 'choice'],
    'metric_name': 'choice_is_B',
    'metric_units': 'binary choice indicator (1 = B, 0 = A)',
    'assumptions': [
        'The task is a judgment about which option is more represented in this specific chronological stream.',
        'Illustrative age decay is 0.55 per position; strength interpolates it with equal weighting.',
        'At strength zero, the reference counts all observed items equally and resolves ties by retaining the prior choice, or A initially.',
    ],
    'limitations': [
        'A synthetic sequence process, not a detector, diagnosis, population claim, or fitted account of human memory.',
        'An anecdote used to infer real-world prevalence may be availability or another process; this task only concerns explicitly ordered task observations.',
        'The decay coefficient and strength are uncalibrated intervention assumptions, not empirical effect sizes.',
    ],
    'empirically_validated': False,
    'synthetic_only': True,
}

_DECAY = 0.55
_OPTIONS = {'A', 'B'}


def _valid_strength(strength):
    if isinstance(strength, bool) or not isinstance(strength, (int, float)):
        raise ValueError('strength must be a finite number in [0, 1]')
    if not math.isfinite(strength) or not 0 <= strength <= 1:
        raise ValueError('strength must be a finite number in [0, 1]')
    return float(strength)


def _counts(history):
    return {'A': history.count('A'), 'B': history.count('B')}


def _choose(scores, previous_choice):
    if scores['A'] > scores['B']:
        return 'A'
    if scores['B'] > scores['A']:
        return 'B'
    return previous_choice if previous_choice in _OPTIONS else 'A'


def evaluate(context: dict, strength: float) -> dict:
    """Update the sequence judgment; never mutate supplied context or state."""
    strength = _valid_strength(strength)
    if not isinstance(context, dict):
        raise ValueError('context must be an object')
    for key in METADATA['required_inputs']:
        if key not in context:
            raise ValueError(f'missing required task input {key}')
    observation = context['observation']
    if not isinstance(observation, str) or observation not in _OPTIONS:
        raise ValueError("observation must be exactly 'A' or 'B'")
    ordered = context['sequence_ordered']
    if not isinstance(ordered, bool):
        raise ValueError('sequence_ordered must be a boolean')

    prior = context.get('state', {})
    if not isinstance(prior, dict):
        raise ValueError('state must be an object')
    history = prior.get('history', [])
    if not isinstance(history, list) or any(not isinstance(item, str) or item not in _OPTIONS for item in history):
        raise ValueError("state.history must be a list containing only 'A'/'B'")
    previous_choice = prior.get('choice')
    if previous_choice is not None and (not isinstance(previous_choice, str) or previous_choice not in _OPTIONS):
        raise ValueError("state.choice must be None, 'A', or 'B'")

    updated_history = history + [observation]
    counts = _counts(updated_history)
    baseline_choice = _choose(counts, previous_choice)

    if ordered:
        weights = [
            (1.0 - strength) + strength * (_DECAY ** age)
            for age in range(len(updated_history) - 1, -1, -1)
        ]
        weighted = {
            option: sum(weight for item, weight in zip(updated_history, weights) if item == option)
            for option in _OPTIONS
        }
        choice = _choose(weighted, previous_choice)
        total_weight = sum(weights)
        active = strength > 0 and choice != baseline_choice
        trace = (
            f"Ordered stream {updated_history}: age 0 is newest; w(age)=(1-{strength:g})+{strength:g}*{_DECAY}^age. "
            f"Weighted support A={weighted['A']:.6g}, B={weighted['B']:.6g}; equal-count reference chooses {baseline_choice}."
        )
    else:
        # Without an ordered sequence, there is no justified position-based memory advantage.
        choice = baseline_choice
        active = False
        trace = (
            f"Sequence is explicitly unordered; position weights are inapplicable. "
            f"Equal-count supports A={counts['A']}, B={counts['B']}; reference and process choose {choice}."
        )

    return {
        'metric': 1.0 if choice == 'B' else 0.0,
        'active': active,
        'state': {'history': updated_history, 'choice': choice},
        'trace': [trace],
    }


def scenarios() -> list[dict]:
    return [
        {
            'name': 'positive',
            'initial_state': {'history': [], 'choice': None},
            'contexts': [
                {'observation': item, 'sequence_ordered': True}
                for item in ['A', 'A', 'A', 'A', 'B', 'B', 'B']
            ],
            'expectation': 'increase',
        },
        {
            'name': 'boundary',
            'initial_state': {'history': [], 'choice': None},
            # The same evidence lacks the necessary temporal-order condition.
            'contexts': [
                {'observation': item, 'sequence_ordered': False}
                for item in ['A', 'A', 'A', 'A', 'B', 'B', 'B']
            ],
            'expectation': 'equal',
        },
    ]
