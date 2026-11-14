"""Illustrative source-monitoring process for remembered information."""

import math


METADATA = {
    'id': 'source_confusion',
    'name': 'Source Confusion',
    'kind': 'cognitive_bias',
    'description': (
        'Models source attribution as a competition between retained source-cue '
        'evidence and content familiarity; intervention strength shifts weight '
        'from source-specific cues to familiarity.'
    ),
    # Only fields present in every phase belong here; candidate details are
    # validated within evaluate because their valid shape differs by scenario.
    'required_inputs': ['origin_source', 'candidate_sources'],
    'state_fields': [
        'items_processed', 'misattributions', 'last_attributed_source',
        'last_source_score_margin',
    ],
    'metric_name': 'source_misattribution',
    'metric_units': 'binary error per remembered item (1 = attributed to a non-origin source)',
    'assumptions': [
        'Each candidate source has supplied source-cue-match and content-familiarity scores in [0, 1].',
        'Strength linearly changes the relative weight of source-cue evidence and content familiarity; coefficients are illustrative, not fitted.',
        'The strongest blended candidate score determines attribution; ties use lexicographic source ID for reproducibility.',
        'Source-cue and familiarity scores are task inputs, not inferred psychological measurements.',
    ],
    'limitations': [
        'This compact process does not detect source confusion in text or diagnose people.',
        'It models wrong attribution, not whether remembered content is true or whether its source was simply forgotten.',
        'The score margin is only a simulated separation measure, not calibrated confidence.',
        'Strength is an uncalibrated intervention setting and results are not empirical or population claims.',
    ],
    'empirically_validated': False,
    'synthetic_only': True,
}


def _score(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f'{label} must be a finite number in [0, 1]')
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError(f'{label} must be a finite number in [0, 1]')
    return float(value)


def _state(context):
    prior = context.get('state', {})
    if not isinstance(prior, dict):
        raise ValueError('state must be an object')
    items = prior.get('items_processed', 0)
    errors = prior.get('misattributions', 0)
    for value, label in ((items, 'state.items_processed'), (errors, 'state.misattributions')):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f'{label} must be a nonnegative integer')
    if errors > items:
        raise ValueError('state.misattributions cannot exceed state.items_processed')
    last = prior.get('last_attributed_source')
    if last is not None and not isinstance(last, str):
        raise ValueError('state.last_attributed_source must be a string or null')
    margin = prior.get('last_source_score_margin')
    if margin is not None:
        margin = _score(margin, 'state.last_source_score_margin')
    return items, errors


def evaluate(context: dict, strength: float) -> dict:
    """Choose an item's source from competing source cues and item familiarity."""
    if isinstance(strength, bool) or not isinstance(strength, (int, float)):
        raise ValueError('strength must be finite and in [0, 1]')
    if not math.isfinite(strength) or not 0 <= strength <= 1:
        raise ValueError('strength must be finite and in [0, 1]')
    strength = float(strength)
    for key in METADATA['required_inputs']:
        if key not in context:
            raise ValueError(f'missing required task input {key}')

    origin = context['origin_source']
    candidates = context['candidate_sources']
    if not isinstance(origin, str) or not origin:
        raise ValueError('origin_source must be a nonempty source ID')
    if not isinstance(candidates, list) or not candidates:
        raise ValueError('candidate_sources must be a nonempty list')

    parsed = []
    seen = set()
    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, dict):
            raise ValueError(f'candidate_sources[{index}] must be an object')
        source = candidate.get('source_id')
        if not isinstance(source, str) or not source:
            raise ValueError(f'candidate_sources[{index}].source_id must be a nonempty string')
        if source in seen:
            raise ValueError('candidate source IDs must be unique')
        seen.add(source)
        if 'source_cue_match' not in candidate or 'content_familiarity' not in candidate:
            raise ValueError('each candidate requires source_cue_match and content_familiarity')
        cue = _score(candidate['source_cue_match'], f'{source}.source_cue_match')
        familiarity = _score(candidate['content_familiarity'], f'{source}.content_familiarity')
        parsed.append((source, cue, familiarity))
    if origin not in seen:
        raise ValueError('origin_source must be represented among candidate_sources')

    # Strength zero is the explicit source-monitoring reference: select the
    # candidate with greatest retained, source-specific cue match.
    baseline = max(parsed, key=lambda row: (row[1], row[0]))[0]
    # At nonzero strength, familiarity for the remembered content competes with
    # source-specific evidence, enabling a familiar item's origin to be confused.
    scored = [
        (source, (1.0 - strength) * cue + strength * familiarity)
        for source, cue, familiarity in parsed
    ]
    attributed, winning_score = max(scored, key=lambda row: (row[1], row[0]))
    ordered_scores = sorted((score for _, score in scored), reverse=True)
    margin = winning_score - (ordered_scores[1] if len(ordered_scores) > 1 else 0.0)

    prior_items, prior_errors = _state(context)
    is_error = attributed != origin
    next_state = {
        'items_processed': prior_items + 1,
        'misattributions': prior_errors + int(is_error),
        'last_attributed_source': attributed,
        'last_source_score_margin': margin,
    }
    return {
        'metric': float(is_error),
        'active': attributed != baseline,
        'state': next_state,
        'trace': [
            f'Candidate score = (1 - {strength:g}) * source_cue_match + {strength:g} * content_familiarity; '
            f'source-cue reference chose {baseline!r}, blended evidence chose {attributed!r}, '
            f'origin is {origin!r}, source-score margin is {margin:.6g}.'
        ],
    }


def scenarios() -> list[dict]:
    return [
        {
            'name': 'positive',
            'initial_state': {
                'items_processed': 0,
                'misattributions': 0,
                'last_attributed_source': None,
                'last_source_score_margin': None,
            },
            'contexts': [{
                'origin_source': 'journal_a',
                'candidate_sources': [
                    {'source_id': 'journal_a', 'source_cue_match': 0.95, 'content_familiarity': 0.25},
                    {'source_id': 'forum_b', 'source_cue_match': 0.35, 'content_familiarity': 0.95},
                ],
            }],
            'expectation': 'increase',
        },
        {
            'name': 'boundary',
            'initial_state': {
                'items_processed': 0,
                'misattributions': 0,
                'last_attributed_source': None,
                'last_source_score_margin': None,
            },
            # With no competing source candidate, familiarity cannot produce a
            # wrong-source attribution: the necessary confusion alternative is absent.
            'contexts': [{
                'origin_source': 'journal_a',
                'candidate_sources': [
                    {'source_id': 'journal_a', 'source_cue_match': 0.20, 'content_familiarity': 0.95},
                ],
            }],
            'expectation': 'equal',
        },
    ]
