"""Illustrative, synthetic choice model for in-group preferential evaluation."""

import math
from numbers import Real


METADATA = {
    'id': 'in_group_bias',
    'name': 'In-group Bias',
    'kind': 'cognitive_bias',
    'description': (
        'Ranks candidates by structured qualification points plus an explicit '
        'same-group evaluation bonus; the reference policy ranks by qualifications alone.'
    ),
    'required_inputs': ['candidates', 'group_bonus'],
    'state_fields': [
        'selected_id', 'reference_selected_id', 'adjusted_scores',
        'selection_changed_from_reference',
    ],
    'metric_name': 'selected_candidate_qualification',
    'metric_units': 'qualification points on a supplied 0–100 scale',
    'assumptions': [
        'Candidate qualifications and shared-group membership are explicit, task-provided facts.',
        'group_bonus is an illustrative user-supplied evaluation bonus in qualification-point units, not a fitted effect size.',
        'Candidate list order resolves exact score ties for both policies.',
        'A choice is the simulated preferential-evaluation outcome; no hidden group identity or motive is inferred.',
    ],
    'limitations': [
        'This toy ranking task omits context, uncertainty, intersectional identity, and many forms of preferential treatment.',
        'It is not an empirical psychology model, detector, diagnosis, or population claim.',
        'Qualifications are treated as comparable supplied scores; real-world qualification measurement may be disputed or incomplete.',
    ],
    'empirically_validated': False,
    'synthetic_only': True,
}


def _finite_number(value, name, low, high):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f'{name} must be a finite number in [{low}, {high}]')
    value = float(value)
    if not math.isfinite(value) or value < low or value > high:
        raise ValueError(f'{name} must be a finite number in [{low}, {high}]')
    return value


def _validate(context):
    if not isinstance(context, dict):
        raise ValueError('context must be a dict')
    if 'candidates' not in context:
        raise ValueError('missing required input: candidates')
    if 'group_bonus' not in context:
        raise ValueError('missing required input: group_bonus')
    candidates = context['candidates']
    if not isinstance(candidates, list) or len(candidates) < 2:
        raise ValueError('candidates must be a list containing at least two candidates')
    bonus = _finite_number(context['group_bonus'], 'group_bonus', 0, 100)
    seen = set()
    normalized = []
    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, dict):
            raise ValueError(f'candidate {index} must be a dict')
        for field in ('id', 'qualification', 'same_group'):
            if field not in candidate:
                raise ValueError(f'candidate {index} missing required field: {field}')
        cid = candidate['id']
        if not isinstance(cid, str) or not cid:
            raise ValueError(f'candidate {index} id must be a non-empty string')
        if cid in seen:
            raise ValueError(f'duplicate candidate id: {cid}')
        seen.add(cid)
        qualification = _finite_number(candidate['qualification'], f'candidate {cid} qualification', 0, 100)
        if type(candidate['same_group']) is not bool:
            raise ValueError(f'candidate {cid} same_group must be bool')
        normalized.append({
            'id': cid,
            'qualification': qualification,
            'same_group': candidate['same_group'],
        })
    state = context.get('state', {})
    if not isinstance(state, dict):
        raise ValueError('state must be a dict')
    return normalized, bonus, state


def _winner(candidates, scores):
    # max() is stable: original order resolves exact ties.
    return max(range(len(candidates)), key=lambda i: scores[i])


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one explicit candidate-choice task without mutating its inputs."""
    intensity = _finite_number(strength, 'strength', 0, 1)
    candidates, bonus, prior_state = _validate(context)

    reference_scores = [candidate['qualification'] for candidate in candidates]
    adjusted_scores = [
        candidate['qualification'] + intensity * bonus * int(candidate['same_group'])
        for candidate in candidates
    ]
    reference_index = _winner(candidates, reference_scores)
    chosen_index = _winner(candidates, adjusted_scores)
    selected = candidates[chosen_index]
    active = (
        intensity > 0 and bonus > 0
        and any(candidate['same_group'] for candidate in candidates)
        and any(not candidate['same_group'] for candidate in candidates)
    )

    # Preserve prior task state and replace this task's complete current decision record.
    next_state = dict(prior_state)
    next_state.update({
        'selected_id': selected['id'],
        'reference_selected_id': candidates[reference_index]['id'],
        'adjusted_scores': {
            candidate['id']: adjusted_scores[i]
            for i, candidate in enumerate(candidates)
        },
        'selection_changed_from_reference': chosen_index != reference_index,
    })
    changed = chosen_index != reference_index
    trace = [
        'Reference score for each candidate is qualification in supplied points; '
        'reference choice is the maximum qualification (first listed wins exact ties).',
        f"Adjusted score = qualification + strength({intensity:g}) × group_bonus({bonus:g}) × same_group_indicator.",
        f"Adjusted scores by candidate id: {next_state['adjusted_scores']!r}.",
        f"Selected {selected['id']!r} with qualification {selected['qualification']:g}; "
        f"reference selected {candidates[reference_index]['id']!r}; choice changed={changed}.",
    ]
    return {
        'metric': selected['qualification'],
        'active': bool(active),
        'state': next_state,
        'trace': trace,
    }


def scenarios() -> list[dict]:
    return [
        {
            'name': 'positive',
            'initial_state': {},
            'contexts': [{
                'candidates': [
                    {'id': 'colleague', 'qualification': 82, 'same_group': True},
                    {'id': 'other', 'qualification': 90, 'same_group': False},
                ],
                'group_bonus': 15,
            }],
            'expectation': 'decrease',
        },
        {
            'name': 'boundary',
            'initial_state': {},
            'contexts': [{
                'candidates': [
                    {'id': 'candidate-a', 'qualification': 82, 'same_group': False},
                    {'id': 'candidate-b', 'qualification': 90, 'same_group': False},
                ],
                'group_bonus': 15,
            }],
            'expectation': 'equal',
        },
    ]
