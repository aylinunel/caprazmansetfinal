"""Illustrative, task-specific self-serving attribution process (not a detector)."""
import math


METADATA = {
    'id': 'self_serving_bias',
    'name': 'Self-serving Bias',
    'kind': 'cognitive_bias',
    'description': (
        'For an explicitly supplied success/failure and causal evidence share, '
        'ambiguous evidence permits an intervention-strength pull toward internal '
        'credit for success or external attribution for failure.'
    ),
    # These keys occur in every scenario context. Phase-specific values are checked below.
    'required_inputs': ['outcome', 'evidence_internal_share', 'evidence_quality'],
    'state_fields': [
        'events_seen', 'cumulative_internal_share', 'cumulative_evidence_share', 'outcomes'
    ],
    'metric_name': 'internal_responsibility_share',
    'metric_units': 'fraction from 0 to 1 of causal responsibility attributed internally for the current hypothetical outcome',
    'assumptions': [
        'Outcome and evidence-based internal share are explicit hypothetical task inputs, not inferred motives.',
        'Ambiguity is represented as one minus evidence_quality; the intervention scales a directional pull toward a self-favoring endpoint.',
        'Strength is an uncalibrated intervention setting, and the strength-zero reference reports the supplied evidence-based share.',
    ],
    'limitations': [
        'This stylized equation is not an empirically fitted account, diagnosis, prevalence estimate, or detector of real statements.',
        'Evidence quality and the evidence-based share are supplied by the task designer; disputed causal facts and benign explanations are not adjudicated.',
        'Self-favorable attribution is not treated as bias when the supplied evidence is complete; the model cannot establish whether that evidence is actually sound.',
    ],
    'empirically_validated': False,
    'synthetic_only': True,
}


def _unit_interval(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f'{name} must be a finite number in [0, 1]')
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError(f'{name} must be a finite number in [0, 1]')
    return float(value)


def _prior_state(raw):
    if not isinstance(raw, dict):
        raise ValueError('state must be an object')
    if not raw:
        return 0, 0.0, 0.0, []
    expected = set(METADATA['state_fields'])
    if set(raw) != expected:
        raise ValueError('state must contain the complete self-serving attribution history')
    count = raw['events_seen']
    outcomes = raw['outcomes']
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        raise ValueError('state.events_seen must be a nonnegative integer')
    if not isinstance(outcomes, list) or len(outcomes) != count or any(x not in ('success', 'failure') for x in outcomes):
        raise ValueError('state.outcomes must list each prior success/failure in order')
    cumulative_internal = raw['cumulative_internal_share']
    cumulative_evidence = raw['cumulative_evidence_share']
    for value, name in ((cumulative_internal, 'cumulative_internal_share'),
                        (cumulative_evidence, 'cumulative_evidence_share')):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= count:
            raise ValueError(f'state.{name} must be finite and between 0 and events_seen')
    return count, float(cumulative_internal), float(cumulative_evidence), list(outcomes)


def evaluate(context: dict, strength: float) -> dict:
    """Return current internal-attribution share and an immutable-history update."""
    if isinstance(strength, bool) or not isinstance(strength, (int, float)) or not math.isfinite(strength) or not 0 <= strength <= 1:
        raise ValueError('strength must be finite and in [0, 1]')
    if not isinstance(context, dict):
        raise ValueError('context must be an object')
    missing = [key for key in METADATA['required_inputs'] if key not in context]
    if missing:
        raise ValueError(f'missing required task input(s): {", ".join(missing)}')

    outcome = context['outcome']
    if outcome not in ('success', 'failure'):
        raise ValueError("outcome must be exactly 'success' or 'failure'")
    evidence_share = _unit_interval(context['evidence_internal_share'], 'evidence_internal_share')
    evidence_quality = _unit_interval(context['evidence_quality'], 'evidence_quality')
    count, cumulative, cumulative_evidence, outcomes = _prior_state(context.get('state', {}))

    # The self-favoring endpoint depends on the result: internal credit for success,
    # external attribution (zero internal share) for failure. Pull is attenuated by
    # the lack of causal support, so complete evidence leaves the reference untouched.
    favorable_endpoint = 1.0 if outcome == 'success' else 0.0
    ambiguity = 1.0 - evidence_quality
    metric = evidence_share + float(strength) * ambiguity * (favorable_endpoint - evidence_share)
    metric = min(1.0, max(0.0, metric))

    next_outcomes = outcomes + [outcome]
    next_state = {
        'events_seen': count + 1,
        'cumulative_internal_share': cumulative + metric,
        'cumulative_evidence_share': cumulative_evidence + evidence_share,
        'outcomes': next_outcomes,
    }
    active = not math.isclose(metric, evidence_share, rel_tol=0.0, abs_tol=1e-15)
    return {
        'metric': metric,
        'active': active,
        'state': next_state,
        'trace': [
            f"outcome={outcome}; evidence_internal_share={evidence_share:.6g}; "
            f"evidence_quality={evidence_quality:.6g}; ambiguity=1-quality={ambiguity:.6g}; "
            f"favorable_endpoint={favorable_endpoint:.0f}; metric=evidence_share + "
            f"strength*ambiguity*(endpoint-evidence_share)={metric:.6g}; strength={float(strength):.6g}"
        ],
    }


def scenarios() -> list[dict]:
    return [
        {
            'name': 'positive',
            'initial_state': {},
            'contexts': [
                {'outcome': 'success', 'evidence_internal_share': 0.35, 'evidence_quality': 0.20},
                {'outcome': 'failure', 'evidence_internal_share': 0.35, 'evidence_quality': 0.20},
            ],
            'expectation': 'decrease',
        },
        {
            'name': 'boundary',
            'initial_state': {},
            'contexts': [
                {'outcome': 'success', 'evidence_internal_share': 0.80, 'evidence_quality': 1.0},
            ],
            'expectation': 'equal',
        },
    ]
