"""Illustrative selection-on-visibility process for survivorship bias."""
from __future__ import annotations

from copy import deepcopy
import math


METADATA = {
    'id': 'survivorship_bias',
    'name': 'Survivorship Bias',
    'kind': 'cognitive_bias',
    'description': (
        'For a full-cohort question, discounts unobserved cases and reports a '
        'visibility-weighted success rate; a question explicitly about visible '
        'cases is left scoped to that subset.'
    ),
    'required_inputs': ['target', 'cohort'],
    'state_fields': [
        'analysis_count', 'last_target', 'last_reported_rate',
        'last_reference_rate', 'last_selected_ids',
    ],
    'metric_name': 'reported_success_rate',
    'metric_units': 'fraction of analyzed case weight classified as successful (0–1)',
    'assumptions': [
        'Each supplied case has an explicit binary outcome and visibility status.',
        'For a full-cohort target, visibility weighting is 1 for observed cases and 1-strength for omitted cases.',
        'Strength is an illustrative intervention setting, not a calibrated human parameter.',
        'Strength zero is the complete-cohort census reference for a full-cohort question.',
    ],
    'limitations': [
        'This hypothetical calculation requires structured case-level outcomes and does not detect survivorship bias in text or real datasets.',
        'Visibility may be unrelated to outcomes; a high weighted rate alone does not establish a selection error or its cause.',
        'Only binary outcomes and a single explicit visibility process are modeled; uncertainty and alternative missingness mechanisms are omitted.',
        'For a descriptive question about visible cases, the visible subset is the estimand and is not treated as a biased estimate of the full cohort.',
    ],
    'empirically_validated': False,
    'synthetic_only': True,
}


def _finite_strength(value: float) -> float:
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or not 0 <= value <= 1):
        raise ValueError('strength must be finite and in [0, 1]')
    return float(value)


def _validate_cohort(context: dict) -> tuple[str, list[tuple[str, bool, bool]]]:
    if not isinstance(context, dict):
        raise ValueError('context must be an object')
    for key in METADATA['required_inputs']:
        if key not in context:
            raise ValueError(f'missing required task input {key}')
    target = context['target']
    if target not in ('full_cohort', 'visible_subset'):
        raise ValueError("target must be 'full_cohort' or 'visible_subset'")
    raw = context['cohort']
    if not isinstance(raw, list) or not raw:
        raise ValueError('cohort must be a nonempty list')
    cases: list[tuple[str, bool, bool]] = []
    seen: set[str] = set()
    for i, row in enumerate(raw):
        if not isinstance(row, dict):
            raise ValueError(f'cohort[{i}] must be an object')
        case_id, success, observed = row.get('id'), row.get('success'), row.get('observed')
        if not isinstance(case_id, str) or not case_id:
            raise ValueError(f'cohort[{i}].id must be a nonempty string')
        if case_id in seen:
            raise ValueError('cohort case ids must be unique')
        seen.add(case_id)
        if type(success) is not bool:
            raise ValueError(f'cohort[{i}].success must be a boolean')
        if type(observed) is not bool:
            raise ValueError(f'cohort[{i}].observed must be a boolean')
        cases.append((case_id, success, observed))
    if not any(observed for _, _, observed in cases):
        raise ValueError('at least one observed case is required')
    return target, cases


def _prior_state(raw: object) -> tuple[dict, int, list[str]]:
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ValueError('state must be an object')
    count = raw.get('analysis_count', 0)
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        raise ValueError('state.analysis_count must be a nonnegative integer')
    ids = raw.get('last_selected_ids', [])
    if not isinstance(ids, list) or not all(isinstance(item, str) for item in ids):
        raise ValueError('state.last_selected_ids must be a list of strings')
    for key in ('last_reported_rate', 'last_reference_rate'):
        value = raw.get(key)
        if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float))
                                  or not math.isfinite(value) or not 0 <= value <= 1):
            raise ValueError(f'state.{key} must be null or a finite rate in [0, 1]')
    last_target = raw.get('last_target')
    if last_target is not None and last_target not in ('full_cohort', 'visible_subset'):
        raise ValueError('state.last_target is invalid')
    return deepcopy(raw), count, list(ids)


def evaluate(context: dict, strength: float) -> dict:
    """Return the rate implied by selection, plus the corresponding reference."""
    strength = _finite_strength(strength)
    target, cases = _validate_cohort(context)
    state, prior_count, _ = _prior_state(context.get('state', {}))

    if target == 'visible_subset':
        # The question asks only about the visible cases: hidden cases are outside
        # the estimand, so filtering them is descriptive rather than an error.
        selected = [(case_id, success, 1.0) for case_id, success, observed in cases if observed]
        reference_cases = [(success, 1.0) for _, success, observed in cases if observed]
        process = 'visible-subset estimand; only observed cases are in scope'
    else:
        # At strength 0 this is the full-cohort census. Increasing selection
        # discounts omitted cases; at strength 1 only visible cases contribute.
        selected = [(case_id, success, 1.0 if observed else 1.0 - strength)
                    for case_id, success, observed in cases
                    if observed or strength < 1.0]
        reference_cases = [(success, 1.0) for _, success, _ in cases]
        process = 'full-cohort target; observed weight=1, omitted weight=1-strength'

    denominator = sum(weight for _, _, weight in selected)
    if denominator <= 0:
        raise ValueError('selection leaves no cases with positive weight')
    reported = sum(weight for _, success, weight in selected if success) / denominator
    reference_denominator = sum(weight for _, weight in reference_cases)
    reference = sum(weight for success, weight in reference_cases if success) / reference_denominator
    selected_ids = [case_id for case_id, _, weight in selected if weight > 0]

    state['analysis_count'] = prior_count + 1
    state['last_target'] = target
    state['last_reported_rate'] = float(reported)
    state['last_reference_rate'] = float(reference)
    state['last_selected_ids'] = selected_ids
    changed = not math.isclose(reported, reference, rel_tol=0.0, abs_tol=1e-12)
    observed_successes = sum(success and observed for _, success, observed in cases)
    omitted_failures = sum((not success) and (not observed) for _, success, observed in cases)
    return {
        'metric': float(reported),
        'active': bool(changed),
        'state': state,
        'trace': [
            f"target={target}; {process}; observed successes={observed_successes}, "
            f"omitted failures={omitted_failures}; weighted success rate={reported:.6f}; "
            f"reference rate={reference:.6f}; selected cases={len(selected_ids)}/{len(cases)}."
        ],
    }


def scenarios() -> list[dict]:
    cohort = [
        *({'id': f'survivor_{i}', 'success': True, 'observed': True} for i in range(4)),
        *({'id': f'failed_{i}', 'success': False, 'observed': False} for i in range(6)),
    ]
    return [
        {
            'name': 'positive',
            'initial_state': {'analysis_count': 0, 'last_selected_ids': []},
            'contexts': [{'target': 'full_cohort', 'cohort': deepcopy(cohort)}],
            'expectation': 'increase',
        },
        {
            'name': 'boundary',
            'initial_state': {'analysis_count': 0, 'last_selected_ids': []},
            # The estimand is explicitly the observed subset itself, not the full
            # cohort, so omitting failures outside that scope is not an error.
            'contexts': [{'target': 'visible_subset', 'cohort': deepcopy(cohort)}],
            'expectation': 'equal',
        },
    ]
