"""Illustrative multiplicity-ignorance process for a searched test family."""
from __future__ import annotations

import math
from copy import deepcopy


METADATA = {
    'id': 'look_elsewhere_effect',
    'name': 'Look-elsewhere Effect',
    'kind': 'cognitive_bias',
    'description': (
        'Select the most extreme supplied test statistic from an explored family; '
        'intervention strength controls how much the report relies on its unadjusted '
        'single-test evidence rather than a family-wise evidence reference.'
    ),
    # This is the only task field required in every phase. Runner-owned fields are excluded.
    'required_inputs': ['candidate_z_scores'],
    'state_fields': [
        'candidate_count', 'selected_index', 'selected_z', 'single_test_p',
        'familywise_p', 'reported_log10_evidence',
    ],
    'metric_name': 'reported_log10_evidence',
    'metric_units': '-log10(two-sided p-value)',
    'assumptions': [
        'The supplied list is the complete family of tests searched in this task step.',
        'Candidate statistics are comparable standard-normal z statistics under their nulls.',
        'The illustrative family-wise reference treats tests as independent; this can be inaccurate for correlated tests.',
        'Strength linearly mixes the family-adjusted and selected single-test evidence policies; it is not calibrated.',
    ],
    'limitations': [
        'This is a hypothetical structured-data process, not a detector of real analyses or intent.',
        'The model does not estimate dependence, preregistration, replication, or the scientific meaning of hypotheses.',
        'Exploratory discovery can be useful and honest; the modeled error is overstating selected evidence as confirmatory.',
        'No coefficient or behavior is empirically validated, and strength is only an intervention setting.',
    ],
    'empirically_validated': False,
    'synthetic_only': True,
}


def _validated_scores(context: dict) -> list[float]:
    if 'candidate_z_scores' not in context:
        raise ValueError('missing required task input candidate_z_scores')
    values = context['candidate_z_scores']
    if not isinstance(values, (list, tuple)) or not values:
        raise ValueError('candidate_z_scores must be a nonempty list or tuple')
    if len(values) > 10000:
        raise ValueError('candidate_z_scores may contain at most 10000 tests')
    scores = []
    for index, value in enumerate(values):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f'candidate_z_scores[{index}] must be numeric')
        if not math.isfinite(value) or not -8.0 <= value <= 8.0:
            raise ValueError(f'candidate_z_scores[{index}] must be finite and in [-8, 8]')
        scores.append(float(value))
    return scores


def evaluate(context: dict, strength: float) -> dict:
    """Return evidence reported after selection from one explicitly supplied test family."""
    if isinstance(strength, bool) or not isinstance(strength, (int, float)):
        raise ValueError('strength must be numeric and finite in [0, 1]')
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError('strength must be numeric and finite in [0, 1]')
    strength = float(strength)
    scores = _validated_scores(context)
    prior = context.get('state', {})
    if not isinstance(prior, dict):
        raise ValueError('state must be a dictionary')

    # Selection itself is an explicit search over the supplied family.
    selected_index = max(range(len(scores)), key=lambda i: abs(scores[i]))
    selected_z = scores[selected_index]
    single_p = math.erfc(abs(selected_z) / math.sqrt(2.0))
    count = len(scores)
    # P(at least one equally/extremely significant result) under independent tests.
    familywise_p = 1.0 if single_p >= 1.0 else -math.expm1(count * math.log1p(-single_p))
    single_evidence = -math.log10(single_p)
    familywise_evidence = -math.log10(familywise_p)

    # Strength interpolates between the explicit multiplicity-aware reference and
    # the selected, unadjusted evidence that can overstate a searched result.
    reported = familywise_evidence + strength * (single_evidence - familywise_evidence)
    next_state = deepcopy(prior)
    next_state.update({
        'candidate_count': count,
        'selected_index': selected_index,
        'selected_z': selected_z,
        'single_test_p': single_p,
        'familywise_p': familywise_p,
        'reported_log10_evidence': reported,
    })
    active = strength > 0.0 and count > 1 and single_evidence > familywise_evidence
    return {
        'metric': reported,
        'active': active,
        'state': next_state,
        'trace': [
            f'Searched {count} supplied z scores; selected index {selected_index} '
            f'(z={selected_z:g}) by maximum absolute value.',
            f'Two-sided p_single=erfc(|z|/sqrt(2))={single_p:.12g}; '
            f'p_family=1-(1-p_single)^{count}={familywise_p:.12g} under independence.',
            f'Reported -log10(p)=(1-{strength:g})*family_adjusted+'
            f'{strength:g}*single_test={reported:.12g}.',
        ],
    }


def scenarios() -> list[dict]:
    return [
        {
            'name': 'positive',
            'initial_state': {},
            'contexts': [{'candidate_z_scores': [0.35, -1.1, 2.2, 2.8, -0.6]}],
            'expectation': 'increase',
        },
        {
            'name': 'boundary',
            'initial_state': {},
            # With one test, searching/selecting among alternatives is absent.
            'contexts': [{'candidate_z_scores': [2.8]}],
            'expectation': 'equal',
        },
    ]
